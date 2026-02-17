"""
工作流 Pydantic 模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class NodeDefinition(BaseModel):
    """节点定义"""
    id: str = Field(..., description="节点唯一标识")
    type: str = Field(..., description="节点类型: start, end, skill, condition, transform")
    position: Dict[str, float] = Field(..., description="节点位置 {x, y}")
    data: Optional[Dict[str, Any]] = Field(default=None, description="节点配置数据")


class EdgeDefinition(BaseModel):
    """边定义"""
    id: str = Field(..., description="边唯一标识")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    sourceHandle: Optional[str] = Field(None, description="源节点输出句柄")
    targetHandle: Optional[str] = Field(None, description="目标节点输入句柄")
    data: Optional[Dict[str, Any]] = Field(default=None, description="边配置数据")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    nodes: List[NodeDefinition] = Field(default_factory=list, description="节点列表")
    edges: List[EdgeDefinition] = Field(default_factory=list, description="边列表")


class VariableDefinition(BaseModel):
    """变量定义"""
    name: str = Field(..., description="变量名")
    type: str = Field(default="string", description="变量类型: string, number, boolean, object, array")
    description: Optional[str] = Field(None, description="变量描述")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(default=True, description="是否必填")


class WorkflowCreate(BaseModel):
    """创建工作流"""
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    definition: WorkflowDefinition = Field(..., description="工作流定义（节点和边）")
    variables: Optional[List[VariableDefinition]] = Field(None, description="输入变量定义")
    is_active: bool = Field(default=True, description="是否激活")

    @field_validator('definition', mode='before')
    @classmethod
    def validate_definition(cls, v):
        """验证 definition 结构"""
        if isinstance(v, dict):
            # 确保有 nodes 和 edges 字段
            if 'nodes' not in v:
                v['nodes'] = []
            if 'edges' not in v:
                v['edges'] = []
            return v
        return v


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    definition: Optional[WorkflowDefinition] = Field(None, description="工作流定义（节点和边）")
    variables: Optional[List[VariableDefinition]] = Field(None, description="输入变量定义")
    is_active: Optional[bool] = Field(None, description="是否激活")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: UUID
    name: str
    description: Optional[str] = None
    user_id: int
    definition: Dict[str, Any]
    variables: Optional[List[Dict[str, Any]]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    items: List[WorkflowResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
