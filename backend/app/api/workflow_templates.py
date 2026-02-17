"""
工作流模板 API

提供模板列表、搜索、详情等接口
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.workflow_templates import WorkflowTemplateManager
from app.schemas.workflow import WorkflowCreate
from pydantic import BaseModel


router = APIRouter(prefix="/workflow-templates", tags=["workflow-templates"])


class TemplateResponse(BaseModel):
    """模板响应模型"""
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    variables: Optional[List[dict]] = None
    
    class Config:
        from_attributes = True


class TemplateDetailResponse(TemplateResponse):
    """模板详情响应模型"""
    definition: dict
    metadata: Optional[dict] = None


@router.get("", response_model=List[TemplateResponse])
async def list_workflow_templates(
    category: Optional[str] = Query(None, description="按分类过滤"),
    tags: Optional[str] = Query(None, description="按标签过滤（逗号分隔）")
):
    """
    列出工作流模板
    
    支持按分类和标签过滤
    
    **示例**：
    - 获取所有模板：`GET /workflow-templates`
    - 按分类过滤：`GET /workflow-templates?category=data`
    - 按标签过滤：`GET /workflow-templates?tags=并行,性能`
    """
    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
    
    # 获取模板列表
    templates = WorkflowTemplateManager.list_templates(category, tag_list)
    
    # 转换为响应模型
    return [
        TemplateResponse(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            category=t["category"],
            tags=t.get("tags", []),
            variables=t.get("variables")
        )
        for t in templates
    ]


@router.get("/categories", response_model=List[str])
async def get_template_categories():
    """
    获取所有模板分类
    
    返回所有可用的模板分类
    """
    return WorkflowTemplateManager.get_template_categories()


@router.get("/tags", response_model=List[str])
async def get_template_tags():
    """
    获取所有标签
    
    返回所有可用的标签
    """
    return WorkflowTemplateManager.get_all_tags()


@router.get("/search", response_model=List[TemplateResponse])
async def search_workflow_templates(
    q: str = Query(..., description="搜索关键词")
):
    """
    搜索模板
    
    在模板名称、描述和标签中搜索
    
    **示例**：
    - `GET /workflow-templates/search?q=并行`
    - `GET /workflow-templates/search?q=数据处理`
    """
    templates = WorkflowTemplateManager.search_templates(q)
    
    return [
        TemplateResponse(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            category=t["category"],
            tags=t.get("tags", []),
            variables=t.get("variables")
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_workflow_template(template_id: str):
    """
    获取模板详情
    
    返回完整的模板定义，包括节点和边
    
    **路径参数**：
    - `template_id`: 模板 ID（如 `data-processing-pipeline`）
    
    **可用模板 ID**：
    - `data-processing-pipeline`: 数据处理管道
    - `conditional-workflow`: 条件分支工作流
    - `parallel-processing`: 并行处理工作流
    - `api-orchestration`: API 编排工作流
    - `error-handling-workflow`: 错误处理工作流
    """
    template = WorkflowTemplateManager.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}"
        )
    
    return TemplateDetailResponse(
        id=template["id"],
        name=template["name"],
        description=template["description"],
        category=template["category"],
        tags=template.get("tags", []),
        variables=template.get("variables"),
        definition=template["definition"],
        metadata=template.get("metadata")
    )


@router.post("/{template_id}/create-workflow", response_model=dict)
async def create_workflow_from_template(
    template_id: str,
    name: Optional[str] = Query(None, description="工作流名称")
):
    """
    从模板创建工作流
    
    基于预置模板快速创建新工作流
    
    **路径参数**：
    - `template_id`: 模板 ID
    
    **查询参数**：
    - `name`: 自定义工作流名称（可选）
    
    **返回**：
    工作流创建数据，可用于 POST /workflows 接口
    """
    workflow_data = WorkflowTemplateManager.create_workflow_from_template(
        template_id,
        name=name
    )
    
    if not workflow_data:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}"
        )
    
    return {
        "success": True,
        "workflow_data": workflow_data,
        "message": f"Ready to create workflow from template: {template_id}"
    }


@router.post("/reload")
async def reload_templates():
    """
    重新加载模板
    
    从文件重新加载模板定义（管理员功能）
    """
    success = WorkflowTemplateManager.reload_templates()
    
    if success:
        return {
            "success": True,
            "message": "Templates reloaded successfully",
            "count": len(WorkflowTemplateManager.list_templates())
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to reload templates"
        )
