"""
工作流执行引擎

负责解析和执行工作流 DAG
"""
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from uuid import uuid4
import asyncio
import logging
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from app.services.execution_context import ExecutionContext, ExecutionContextManager
from app.models.workflow_execution import (
    ExecutionStatus, StepStatus, TriggerType,
    WorkflowExecution, WorkflowExecutionStep, ExecutionLog
)

logger = logging.getLogger(__name__)


# ============ 异常定义 ============

class WorkflowExecutionError(Exception):
    """工作流执行错误"""
    pass


class ExecutionCancelledError(WorkflowExecutionError):
    """执行被取消"""
    pass


class NodeExecutionError(WorkflowExecutionError):
    """节点执行错误"""
    def __init__(self, node_id: str, message: str, original_error: Exception = None):
        self.node_id = node_id
        self.original_error = original_error
        super().__init__(f"Node {node_id}: {message}")


class DAGValidationError(WorkflowExecutionError):
    """DAG 验证错误"""
    pass


# ============ 数据结构 ============

@dataclass
class Node:
    """工作流节点"""
    id: str
    type: str
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Edge:
    """工作流边"""
    id: str
    source: str
    target: str
    condition: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DAG:
    """工作流 DAG"""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    start_node_id: Optional[str] = None
    end_node_ids: List[str] = field(default_factory=list)
    
    # 邻接表
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    reverse_adjacency: Dict[str, List[str]] = field(default_factory=dict)


# ============ DAG 解析器 ============

class DAGParser:
    """DAG 解析器"""
    
    @classmethod
    def parse(cls, definition: Dict[str, Any]) -> DAG:
        """
        解析工作流定义为 DAG
        
        Args:
            definition: 工作流定义 {"nodes": [...], "edges": [...]}
            
        Returns:
            DAG 对象
            
        Raises:
            DAGValidationError: 验证失败
        """
        dag = DAG()
        
        # 解析节点
        nodes_data = definition.get("nodes", [])
        for node_data in nodes_data:
            node = cls._parse_node(node_data)
            dag.nodes[node.id] = node
            
            # 记录开始和结束节点
            if node.type == "start":
                if dag.start_node_id is not None:
                    raise DAGValidationError(f"Multiple start nodes found: {dag.start_node_id}, {node.id}")
                dag.start_node_id = node.id
            elif node.type == "end":
                dag.end_node_ids.append(node.id)
        
        # 验证开始节点
        if dag.start_node_id is None:
            raise DAGValidationError("No start node found in workflow")
        
        # 解析边
        edges_data = definition.get("edges", [])
        for edge_data in edges_data:
            edge = cls._parse_edge(edge_data)
            dag.edges.append(edge)
            
            # 构建邻接表
            source, target = edge.source, edge.target
            
            if source not in dag.adjacency:
                dag.adjacency[source] = []
            dag.adjacency[source].append(target)
            
            if target not in dag.reverse_adjacency:
                dag.reverse_adjacency[target] = []
            dag.reverse_adjacency[target].append(source)
        
        # 验证 DAG
        cls._validate_dag(dag)
        
        return dag
    
    @classmethod
    def _parse_node(cls, data: Dict[str, Any]) -> Node:
        """解析节点数据"""
        node_data = data.get("data", {})
        
        return Node(
            id=data["id"],
            type=data["type"],
            name=node_data.get("label", ""),
            config=node_data.get("config", {}),
            retry_config=node_data.get("retry", {}),
            error_handling=node_data.get("error_handling", {})
        )
    
    @classmethod
    def _parse_edge(cls, data: Dict[str, Any]) -> Edge:
        """解析边数据"""
        return Edge(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            condition=data.get("condition", {})
        )
    
    @classmethod
    def _validate_dag(cls, dag: DAG) -> None:
        """验证 DAG"""
        # 检查所有边引用的节点是否存在
        for edge in dag.edges:
            if edge.source not in dag.nodes:
                raise DAGValidationError(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in dag.nodes:
                raise DAGValidationError(f"Edge references non-existent target node: {edge.target}")
        
        # 检测循环依赖
        cls._check_cycles(dag)
        
        # 检查孤立节点
        cls._check_isolated_nodes(dag)
    
    @classmethod
    def _check_cycles(cls, dag: DAG) -> None:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in dag.adjacency.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in dag.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    raise DAGValidationError(f"Cycle detected in workflow DAG")
    
    @classmethod
    def _check_isolated_nodes(cls, dag: DAG) -> None:
        """检查孤立节点"""
        for node_id, node in dag.nodes.items():
            # 开始节点没有前驱是正常的
            if node.type == "start":
                continue
            
            # 其他节点应该有前驱
            predecessors = dag.reverse_adjacency.get(node_id, [])
            if not predecessors:
                logger.warning(f"Node {node_id} has no predecessors and may be unreachable")


# ============ 工作流执行器 ============

class WorkflowExecutor:
    """
    工作流执行器
    
    负责：
    - DAG 解析与执行
    - 节点并行执行
    - 错误处理与重试
    - 执行日志记录
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    async def execute(
        self,
        workflow_id: int,
        execution_id: int,
        input_data: Dict[str, Any],
        variables_definition: List[Dict[str, Any]] = None,
        definition: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流 ID
            execution_id: 执行记录 ID
            input_data: 输入数据
            variables_definition: 变量定义
            definition: 工作流定义
            
        Returns:
            执行结果
        """
        # 创建执行上下文
        context = ExecutionContextManager.create(
            execution_id=execution_id,
            workflow_id=workflow_id,
            input_data=input_data,
            variables_definition=variables_definition
        )
        
        try:
            context.start()
            context.add_log("INFO", f"Starting workflow execution")
            
            # 解析 DAG
            dag = DAGParser.parse(definition)
            context.add_log("INFO", f"DAG parsed: {len(dag.nodes)} nodes, {len(dag.edges)} edges")
            
            # 更新总步骤数
            context._step_count = len(dag.nodes)
            
            # 执行 DAG
            result = await self._execute_dag(dag, context)
            
            # 完成
            context.finish(success=True)
            context.add_log("INFO", f"Workflow execution completed")
            
            return {
                "status": "completed",
                "output": result,
                "context": context.to_dict()
            }
            
        except ExecutionCancelledError as e:
            context.status = "cancelled"
            context.add_log("WARNING", f"Execution cancelled: {str(e)}")
            context.finish(success=False)
            
            return {
                "status": "cancelled",
                "error": str(e),
                "context": context.to_dict()
            }
            
        except Exception as e:
            context.status = "failed"
            context.add_log("ERROR", f"Workflow execution failed: {str(e)}")
            context.finish(success=False)
            
            logger.exception(f"Workflow execution failed: {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "context": context.to_dict()
            }
            
        finally:
            # 清理上下文
            ExecutionContextManager.remove(execution_id)
    
    async def _execute_dag(self, dag: DAG, context: ExecutionContext) -> Dict[str, Any]:
        """执行 DAG"""
        # 拓扑排序获取执行顺序
        execution_order = self._get_execution_order(dag, context)
        
        # 跟踪已完成的节点
        completed_nodes: Set[str] = set()
        failed_nodes: Set[str] = set()
        node_results: Dict[str, Dict[str, Any]] = {}
        
        # 按层级执行
        for level, nodes in enumerate(execution_order):
            context.add_log("INFO", f"Executing level {level} with {len(nodes)} nodes")
            
            # 检查取消
            context.check_cancelled()
            
            # 并行执行当前层级的节点
            tasks = []
            for node_id in nodes:
                node = dag.nodes[node_id]
                
                # 跳过已完成或失败的节点
                if node_id in completed_nodes or node_id in failed_nodes:
                    continue
                
                # 检查依赖是否满足
                deps = dag.reverse_adjacency.get(node_id, [])
                failed_deps = [d for d in deps if d in failed_nodes]
                if failed_deps:
                    context.add_log("WARNING", f"Skipping node {node_id} due to failed dependencies: {failed_deps}")
                    failed_nodes.add(node_id)
                    context.increment_failed()
                    continue
                
                # 创建执行任务
                task = self._execute_node_with_retry(node, context, dag)
                tasks.append((node_id, task))
            
            if not tasks:
                continue
            
            # 并行执行
            results = await asyncio.gather(
                *[t[1] for t in tasks],
                return_exceptions=True
            )
            
            # 处理结果
            for (node_id, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    context.add_log("ERROR", f"Node {node_id} failed: {str(result)}", node_id=node_id)
                    failed_nodes.add(node_id)
                    context.increment_failed()
                    node_results[node_id] = {"error": str(result)}
                else:
                    completed_nodes.add(node_id)
                    context.increment_completed()
                    node_results[node_id] = result
                    context.set_node_output(node_id, result)
        
        # 汇总结果
        final_output = {}
        for end_node_id in dag.end_node_ids:
            if end_node_id in node_results:
                final_output[end_node_id] = node_results[end_node_id]
        
        return final_output
    
    def _get_execution_order(self, dag: DAG, context: ExecutionContext) -> List[List[str]]:
        """
        获取按层级划分的执行顺序
        
        使用拓扑排序，返回按依赖关系分层的节点列表
        """
        # 计算入度
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for edge in dag.edges:
            in_degree[edge.target] += 1
        
        # 按层 BFS
        levels = []
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        while current_level:
            levels.append(current_level)
            
            # 减少下一层节点的入度
            next_level = []
            for node_id in current_level:
                for neighbor in dag.adjacency.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            
            current_level = next_level
        
        context.add_log("DEBUG", f"Execution order: {len(levels)} levels")
        return levels
    
    async def _execute_node_with_retry(
        self,
        node: Node,
        context: ExecutionContext,
        dag: DAG
    ) -> Dict[str, Any]:
        """带重试的节点执行"""
        max_retries = node.retry_config.get("max_retries", 0)
        backoff = node.retry_config.get("backoff", "exponential")
        initial_delay = node.retry_config.get("initial_delay", 1.0)
        max_delay = node.retry_config.get("max_delay", 60.0)
        
        last_error = None
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 检查取消
                context.check_cancelled()
                
                # 执行节点
                context.current_node_id = node.id
                context.add_log("INFO", f"Executing node: {node.name or node.id} (attempt {retry_count + 1})", node_id=node.id)
                
                result = await self._execute_node(node, context, dag)
                
                context.add_log("INFO", f"Node completed: {node.name or node.id}", node_id=node.id)
                return result
                
            except ExecutionCancelledError:
                raise
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count <= max_retries:
                    # 计算延迟
                    delay = self._calculate_retry_delay(backoff, retry_count, initial_delay, max_delay)
                    context.add_log(
                        "WARNING",
                        f"Node {node.id} failed, retrying in {delay}s (attempt {retry_count}/{max_retries})",
                        node_id=node.id,
                        metadata={"error": str(e)}
                    )
                    await asyncio.sleep(delay)
                else:
                    # 所有重试都失败，尝试错误处理
                    return await self._handle_node_error(node, e, context, dag)
        
        # 不应该到达这里
        raise last_error
    
    def _calculate_retry_delay(
        self,
        backoff: str,
        attempt: int,
        initial_delay: float,
        max_delay: float
    ) -> float:
        """计算重试延迟"""
        if backoff == "fixed":
            return min(initial_delay, max_delay)
        elif backoff == "linear":
            return min(initial_delay * attempt, max_delay)
        else:  # exponential
            return min(initial_delay * (2 ** (attempt - 1)), max_delay)
    
    async def _handle_node_error(
        self,
        node: Node,
        error: Exception,
        context: ExecutionContext,
        dag: DAG
    ) -> Dict[str, Any]:
        """处理节点错误"""
        error_handling = node.error_handling
        fallback_node_id = error_handling.get("fallback_node")
        continue_on_error = error_handling.get("continue_on_error", False)
        
        context.add_log(
            "ERROR",
            f"Node {node.id} failed after all retries: {str(error)}",
            node_id=node.id,
            metadata={"error_type": type(error).__name__}
        )
        
        if fallback_node_id:
            # 执行回退节点
            if fallback_node_id in dag.nodes:
                context.add_log("INFO", f"Executing fallback node: {fallback_node_id}", node_id=node.id)
                fallback_node = dag.nodes[fallback_node_id]
                try:
                    result = await self._execute_node(fallback_node, context, dag)
                    return {"fallback_result": result, "original_error": str(error)}
                except Exception as fallback_error:
                    context.add_log("ERROR", f"Fallback node also failed: {str(fallback_error)}", node_id=fallback_node_id)
                    return {"error": str(error), "fallback_error": str(fallback_error)}
        
        if continue_on_error:
            return {"error": str(error), "continued": True}
        
        # 不继续，抛出错误
        raise NodeExecutionError(node.id, str(error), error)
    
    async def _execute_node(
        self,
        node: Node,
        context: ExecutionContext,
        dag: DAG
    ) -> Dict[str, Any]:
        """执行单个节点"""
        node_type = node.type
        
        if node_type == "start":
            return await self._execute_start_node(node, context)
        elif node_type == "end":
            return await self._execute_end_node(node, context)
        elif node_type == "skill":
            return await self._execute_skill_node(node, context)
        elif node_type == "condition":
            return await self._execute_condition_node(node, context, dag)
        elif node_type == "transform":
            return await self._execute_transform_node(node, context)
        elif node_type == "parallel":
            return await self._execute_parallel_node(node, context, dag)
        else:
            raise NodeExecutionError(node.id, f"Unknown node type: {node_type}")
    
    async def _execute_start_node(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行开始节点"""
        return {"started": True, "input": context.get_variable("input", {})}
    
    async def _execute_end_node(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行结束节点"""
        return {"completed": True}
    
    async def _execute_skill_node(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行技能节点"""
        config = node.config
        skill_id = config.get("skill_id")
        skill_slug = config.get("skill_slug")
        
        # 解析参数
        params = config.get("params", {})
        resolved_params = context.resolve_value(params)
        
        context.add_log(
            "DEBUG",
            f"Executing skill: {skill_slug or skill_id}",
            node_id=node.id,
            metadata={"params": resolved_params}
        )
        
        # TODO: 实际调用技能执行器
        # 这里是占位实现，实际应该调用 SkillExecutor
        try:
            # 模拟技能执行
            result = {
                "skill_id": skill_id,
                "skill_slug": skill_slug,
                "output": f"Skill {skill_slug or skill_id} executed with params: {resolved_params}"
            }
            
            # 如果配置了输出变量，保存到上下文
            output_var = config.get("output_variable")
            if output_var:
                context.set_variable(output_var, result)
            
            return result
            
        except Exception as e:
            raise NodeExecutionError(node.id, f"Skill execution failed: {str(e)}", e)
    
    async def _execute_condition_node(
        self,
        node: Node,
        context: ExecutionContext,
        dag: DAG
    ) -> Dict[str, Any]:
        """执行条件节点"""
        config = node.config
        conditions = config.get("conditions", [])
        
        # 评估条件
        for condition in conditions:
            if await self._evaluate_condition(condition, context):
                return {"result": True, "matched_condition": condition.get("id")}
        
        return {"result": False}
    
    async def _execute_transform_node(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行数据变换节点"""
        config = node.config
        transform_type = config.get("type", "expression")
        
        if transform_type == "expression":
            # 表达式变换
            expression = config.get("expression")
            result = context.resolve_reference(expression)
            return {"result": result}
        
        elif transform_type == "mapping":
            # 字段映射
            source = context.resolve_value(config.get("source", {}))
            mapping = config.get("mapping", {})
            result = {}
            for target_key, source_expr in mapping.items():
                result[target_key] = context.resolve_reference(source_expr)
            return {"result": result}
        
        elif transform_type == "merge":
            # 合并多个数据源
            sources = config.get("sources", [])
            result = {}
            for source_expr in sources:
                source_data = context.resolve_reference(source_expr)
                if isinstance(source_data, dict):
                    result.update(source_data)
            return {"result": result}
        
        else:
            raise NodeExecutionError(node.id, f"Unknown transform type: {transform_type}")
    
    async def _execute_parallel_node(
        self,
        node: Node,
        context: ExecutionContext,
        dag: DAG
    ) -> Dict[str, Any]:
        """执行并行节点"""
        config = node.config
        branches = config.get("branches", [])
        
        # 并行执行所有分支
        tasks = []
        for branch in branches:
            branch_node_id = branch.get("node_id")
            if branch_node_id and branch_node_id in dag.nodes:
                branch_node = dag.nodes[branch_node_id]
                tasks.append(self._execute_node(branch_node, context, dag))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {
                "parallel_results": [
                    {"branch": i, "result": r if not isinstance(r, Exception) else {"error": str(r)}}
                    for i, r in enumerate(results)
                ]
            }
        
        return {"parallel_results": []}
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """评估条件"""
        condition_type = condition.get("type", "comparison")
        
        if condition_type == "always":
            return True
        
        if condition_type == "comparison":
            variable = condition.get("variable")
            operator = condition.get("operator", "eq")
            expected_value = context.resolve_reference(condition.get("value"))
            actual_value = context.resolve_reference(variable)
            
            return self._compare(actual_value, operator, expected_value)
        
        if condition_type == "expression":
            # 简单表达式评估（可扩展）
            expression = condition.get("expression", "")
            # TODO: 实现安全的表达式评估
            return bool(context.resolve_reference(expression))
        
        if condition_type == "exists":
            variable = condition.get("variable")
            value = context.resolve_reference(variable)
            return value is not None
        
        return False
    
    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """比较操作"""
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return actual > expected
            elif operator == "lt":
                return actual < expected
            elif operator == "gte":
                return actual >= expected
            elif operator == "lte":
                return actual <= expected
            elif operator == "contains":
                return expected in actual if actual else False
            elif operator == "not_contains":
                return expected not in actual if actual else True
            elif operator == "starts_with":
                return str(actual).startswith(str(expected)) if actual else False
            elif operator == "ends_with":
                return str(actual).endswith(str(expected)) if actual else False
            elif operator == "is_empty":
                return not actual
            elif operator == "is_not_empty":
                return bool(actual)
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.warning(f"Comparison failed: {e}")
            return False
    
    @staticmethod
    def cancel_execution(execution_id: int, reason: str = None) -> bool:
        """取消执行"""
        context = ExecutionContextManager.get(execution_id)
        if context:
            context.request_cancel(reason)
            return True
        return False


# ============ 导出 ============

__all__ = [
    "WorkflowExecutor",
    "DAGParser",
    "DAG",
    "Node",
    "Edge",
    "WorkflowExecutionError",
    "ExecutionCancelledError",
    "NodeExecutionError",
    "DAGValidationError"
]
