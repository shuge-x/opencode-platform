"""
工作流执行上下文

管理工作流执行期间的变量存储、节点输出缓存和执行状态
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class ExecutionContext:
    """
    工作流执行上下文
    
    负责：
    - 变量存储与引用解析
    - 节点输出缓存
    - 执行状态追踪
    - 取消信号管理
    """
    
    def __init__(
        self,
        execution_id: int,
        workflow_id: int,
        input_data: Dict[str, Any],
        variables_definition: List[Dict[str, Any]] = None
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        
        # 变量存储
        self._variables: Dict[str, Any] = {}
        
        # 节点输出缓存 {node_id: output_data}
        self._node_outputs: Dict[str, Dict[str, Any]] = {}
        
        # 执行状态
        self._status = "pending"
        self._current_node_id: Optional[str] = None
        
        # 取消信号
        self._cancel_event = asyncio.Event()
        self._cancel_reason: Optional[str] = None
        
        # 日志缓冲
        self._logs: List[Dict[str, Any]] = []
        
        # 初始化变量
        self._initialize_variables(input_data, variables_definition or [])
        
        # 统计信息
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._step_count = 0
        self._completed_count = 0
        self._failed_count = 0
    
    def _initialize_variables(
        self,
        input_data: Dict[str, Any],
        variables_definition: List[Dict[str, Any]]
    ):
        """初始化变量"""
        # 设置输入变量
        self._variables["input"] = input_data
        
        # 根据变量定义初始化默认值
        for var_def in variables_definition:
            name = var_def.get("name")
            if name and name not in input_data:
                default = var_def.get("default")
                if default is not None:
                    self._variables[name] = default
    
    # ============ 变量管理 ============
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self._variables[name] = value
        logger.debug(f"[Execution {self.execution_id}] Set variable: {name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self._variables.get(name, default)
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        return self._variables.copy()
    
    def resolve_reference(self, expression: str) -> Any:
        """
        解析变量引用表达式
        
        支持格式：
        - $input.field_name
        - $nodes.node_id.output.field
        - $variables.var_name
        - 直接值
        
        示例：
        - "$input.text" -> input_data["text"]
        - "$nodes.process_1.output.result" -> node_outputs["process_1"]["output"]["result"]
        - "$variables.max_count" -> variables["max_count"]
        """
        if not isinstance(expression, str) or not expression.startswith("$"):
            return expression
        
        parts = expression[1:].split(".")
        if not parts:
            return expression
        
        root = parts[0]
        
        # 处理不同根路径
        if root == "input":
            value = self._variables.get("input", {})
        elif root == "nodes":
            value = self._node_outputs
        elif root == "variables":
            value = self._variables
        else:
            # 尝试从变量中直接获取
            value = self._variables.get(root)
            if value is None:
                return expression
        
        # 遍历路径
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def resolve_value(self, value: Any) -> Any:
        """
        递归解析值中的所有引用
        """
        if isinstance(value, str):
            return self.resolve_reference(value)
        elif isinstance(value, dict):
            return {k: self.resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_value(item) for item in value]
        return value
    
    # ============ 节点输出管理 ============
    
    def set_node_output(self, node_id: str, output: Dict[str, Any]) -> None:
        """设置节点输出"""
        self._node_outputs[node_id] = {
            "output": output,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.debug(f"[Execution {self.execution_id}] Set node output: {node_id}")
    
    def get_node_output(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点输出"""
        node_data = self._node_outputs.get(node_id)
        if node_data:
            return node_data.get("output")
        return None
    
    def get_all_node_outputs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有节点输出"""
        return self._node_outputs.copy()
    
    # ============ 执行状态管理 ============
    
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
        logger.info(f"[Execution {self.execution_id}] Status changed to: {value}")
    
    @property
    def current_node_id(self) -> Optional[str]:
        return self._current_node_id
    
    @current_node_id.setter
    def current_node_id(self, value: str):
        self._current_node_id = value
        if value:
            logger.debug(f"[Execution {self.execution_id}] Current node: {value}")
    
    # ============ 取消管理 ============
    
    def request_cancel(self, reason: str = None) -> None:
        """请求取消执行"""
        self._cancel_reason = reason
        self._cancel_event.set()
        logger.info(f"[Execution {self.execution_id}] Cancel requested: {reason}")
    
    def is_cancelled(self) -> bool:
        """检查是否被取消"""
        return self._cancel_event.is_set()
    
    def check_cancelled(self) -> None:
        """检查是否被取消，如果取消则抛出异常"""
        if self._cancel_event.is_set():
            from app.services.workflow_executor import ExecutionCancelledError
            raise ExecutionCancelledError(self._cancel_reason or "Execution cancelled")
    
    @property
    def cancel_reason(self) -> Optional[str]:
        return self._cancel_reason
    
    # ============ 日志管理 ============
    
    def add_log(
        self,
        level: str,
        message: str,
        node_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """添加日志"""
        log_entry = {
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": self.execution_id,
            "node_id": node_id,
            "metadata": metadata or {}
        }
        self._logs.append(log_entry)
        
        # 同时输出到日志系统
        log_msg = f"[Execution {self.execution_id}]"
        if node_id:
            log_msg += f" [Node {node_id}]"
        log_msg += f" {message}"
        
        if level == "DEBUG":
            logger.debug(log_msg)
        elif level == "INFO":
            logger.info(log_msg)
        elif level == "WARNING":
            logger.warning(log_msg)
        elif level == "ERROR":
            logger.error(log_msg)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志"""
        return self._logs.copy()
    
    # ============ 统计管理 ============
    
    def start(self) -> None:
        """开始执行"""
        self._start_time = datetime.utcnow()
        self.status = "running"
    
    def finish(self, success: bool = True) -> None:
        """完成执行"""
        self._end_time = datetime.utcnow()
        self.status = "completed" if success else "failed"
    
    @property
    def execution_time(self) -> Optional[float]:
        """获取执行时间（秒）"""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time).total_seconds()
        return None
    
    def increment_step(self) -> None:
        """增加步骤计数"""
        self._step_count += 1
    
    def increment_completed(self) -> None:
        """增加完成计数"""
        self._completed_count += 1
    
    def increment_failed(self) -> None:
        """增加失败计数"""
        self._failed_count += 1
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_steps": self._step_count,
            "completed_steps": self._completed_count,
            "failed_steps": self._failed_count,
            "execution_time": self.execution_time
        }
    
    # ============ 序列化 ============
    
    def to_dict(self) -> Dict[str, Any]:
        """导出上下文为字典"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "variables": self._variables,
            "node_outputs": self._node_outputs,
            "status": self._status,
            "current_node_id": self._current_node_id,
            "logs": self._logs,
            "statistics": self.statistics,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """从字典恢复上下文"""
        ctx = cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            input_data=data["variables"].get("input", {})
        )
        ctx._variables = data.get("variables", {})
        ctx._node_outputs = data.get("node_outputs", {})
        ctx._status = data.get("status", "pending")
        ctx._current_node_id = data.get("current_node_id")
        ctx._logs = data.get("logs", [])
        return ctx


class ExecutionContextManager:
    """
    执行上下文管理器
    
    管理多个执行上下文的生命周期
    """
    
    _instances: Dict[int, ExecutionContext] = {}
    
    @classmethod
    def create(
        cls,
        execution_id: int,
        workflow_id: int,
        input_data: Dict[str, Any],
        variables_definition: List[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """创建执行上下文"""
        ctx = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_id,
            input_data=input_data,
            variables_definition=variables_definition
        )
        cls._instances[execution_id] = ctx
        return ctx
    
    @classmethod
    def get(cls, execution_id: int) -> Optional[ExecutionContext]:
        """获取执行上下文"""
        return cls._instances.get(execution_id)
    
    @classmethod
    def remove(cls, execution_id: int) -> None:
        """移除执行上下文"""
        if execution_id in cls._instances:
            del cls._instances[execution_id]
    
    @classmethod
    def exists(cls, execution_id: int) -> bool:
        """检查执行上下文是否存在"""
        return execution_id in cls._instances
