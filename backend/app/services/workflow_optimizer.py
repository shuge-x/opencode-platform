"""
大工作流执行优化

针对 100+ 节点工作流的性能优化：
- DAG 分层并行执行
- 节点输出缓存
- 批量数据库操作
- 内存优化
"""
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class LargeWorkflowOptimizer:
    """大工作流执行优化器"""
    
    # 配置参数
    MAX_PARALLEL_NODES = 10  # 最大并行节点数
    BATCH_SIZE = 20  # 批量处理节点数
    CACHE_THRESHOLD = 50  # 节点数超过此值时启用缓存
    
    @staticmethod
    def optimize_execution_order(dag, context) -> List[List[str]]:
        """
        优化执行顺序
        
        对大工作流（100+ 节点）进行智能分层：
        - 按依赖关系分组
        - 平衡每层的节点数
        - 优先执行关键路径
        """
        node_count = len(dag.nodes)
        
        # 小工作流使用标准拓扑排序
        if node_count < LargeWorkflowOptimizer.CACHE_THRESHOLD:
            return LargeWorkflowOptimizer._standard_topological_sort(dag)
        
        logger.info(f"Optimizing execution order for large workflow: {node_count} nodes")
        
        # 1. 识别关键路径
        critical_path = LargeWorkflowOptimizer._find_critical_path(dag)
        if context:
            context.add_log("DEBUG", f"Critical path identified: {len(critical_path)} nodes")
        
        # 2. 按依赖关系和关键路径分层
        levels = LargeWorkflowOptimizer._priority_based_leveling(dag, critical_path)
        
        # 3. 平衡每层节点数
        balanced_levels = LargeWorkflowOptimizer._balance_levels(levels)
        
        if context:
            context.add_log(
                "INFO",
                f"Execution optimized: {len(balanced_levels)} levels, "
                f"avg {sum(len(l) for l in balanced_levels) / len(balanced_levels):.1f} nodes per level"
            )
        
        return balanced_levels
    
    @staticmethod
    def _standard_topological_sort(dag) -> List[List[str]]:
        """标准拓扑排序"""
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for edge in dag.edges:
            in_degree[edge.target] += 1
        
        levels = []
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        while current_level:
            levels.append(current_level)
            
            next_level = []
            for node_id in current_level:
                for neighbor in dag.adjacency.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            
            current_level = next_level
        
        return levels
    
    @staticmethod
    def _find_critical_path(dag) -> List[str]:
        """找到关键路径（最长路径）"""
        distances = {}
        predecessors = {}
        
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for edge in dag.edges:
            in_degree[edge.target] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        for node_id in queue:
            distances[node_id] = 1
            predecessors[node_id] = None
        
        while queue:
            current = queue.pop(0)
            
            for neighbor in dag.adjacency.get(current, []):
                new_distance = distances[current] + 1
                
                if neighbor not in distances or new_distance > distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = current
                
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if not distances:
            return []
        
        end_node = max(distances, key=distances.get)
        
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        return list(reversed(path))
    
    @staticmethod
    def _priority_based_leveling(dag, critical_path: List[str]) -> List[List[str]]:
        """基于优先级的分层"""
        critical_set = set(critical_path)
        
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for edge in dag.edges:
            in_degree[edge.target] += 1
        
        levels = []
        remaining = set(dag.nodes.keys())
        
        while remaining:
            ready = [
                node_id for node_id in remaining
                if in_degree[node_id] == 0
            ]
            
            if not ready:
                logger.warning(f"No ready nodes, but {len(remaining)} nodes remaining")
                break
            
            ready.sort(key=lambda n: (0 if n in critical_set else 1, n))
            
            current_level = ready[:LargeWorkflowOptimizer.MAX_PARALLEL_NODES]
            levels.append(current_level)
            
            for node_id in current_level:
                remaining.remove(node_id)
                
                for neighbor in dag.adjacency.get(node_id, []):
                    in_degree[neighbor] -= 1
        
        return levels
    
    @staticmethod
    def _balance_levels(levels: List[List[str]]) -> List[List[str]]:
        """平衡层级"""
        balanced = []
        
        for level in levels:
            if len(level) > LargeWorkflowOptimizer.BATCH_SIZE:
                for i in range(0, len(level), LargeWorkflowOptimizer.BATCH_SIZE):
                    batch = level[i:i + LargeWorkflowOptimizer.BATCH_SIZE]
                    balanced.append(batch)
            else:
                balanced.append(level)
        
        return balanced


__all__ = ["LargeWorkflowOptimizer"]
