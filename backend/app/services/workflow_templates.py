"""
工作流模板管理

从 workflow_templates.json 加载和管理预置模板
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class WorkflowTemplateManager:
    """工作流模板管理器"""
    
    _instance = None
    _templates: Dict[str, Dict[str, Any]] = {}
    _loaded = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_templates(cls) -> bool:
        """
        从文件加载模板
        
        Returns:
            是否加载成功
        """
        if cls._loaded:
            return True
        
        try:
            # 查找模板文件
            template_file = Path(__file__).parent.parent / "data" / "workflow_templates.json"
            
            if not template_file.exists():
                logger.warning(f"Template file not found: {template_file}")
                return False
            
            # 读取并解析模板
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 存储模板
            templates = data.get("templates", [])
            for template in templates:
                template_id = template.get("id")
                if template_id:
                    cls._templates[template_id] = template
            
            cls._loaded = True
            logger.info(f"Loaded {len(cls._templates)} workflow templates")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load workflow templates: {e}")
            return False
    
    @classmethod
    def get_template(cls, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            模板数据，如果不存在则返回 None
        """
        if not cls._loaded:
            cls.load_templates()
        
        return cls._templates.get(template_id)
    
    @classmethod
    def list_templates(
        cls,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        列出模板
        
        Args:
            category: 按分类过滤（可选）
            tags: 按标签过滤（可选）
            
        Returns:
            模板列表
        """
        if not cls._loaded:
            cls.load_templates()
        
        templates = list(cls._templates.values())
        
        # 按分类过滤
        if category:
            templates = [t for t in templates if t.get("category") == category]
        
        # 按标签过滤
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.get("tags", []) for tag in tags)
            ]
        
        return templates
    
    @classmethod
    def get_template_categories(cls) -> List[str]:
        """
        获取所有模板分类
        
        Returns:
            分类列表
        """
        if not cls._loaded:
            cls.load_templates()
        
        categories = set()
        for template in cls._templates.values():
            category = template.get("category")
            if category:
                categories.add(category)
        
        return sorted(list(categories))
    
    @classmethod
    def get_all_tags(cls) -> List[str]:
        """
        获取所有标签
        
        Returns:
            标签列表
        """
        if not cls._loaded:
            cls.load_templates()
        
        tags = set()
        for template in cls._templates.values():
            template_tags = template.get("tags", [])
            tags.update(template_tags)
        
        return sorted(list(tags))
    
    @classmethod
    def search_templates(cls, query: str) -> List[Dict[str, Any]]:
        """
        搜索模板
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的模板列表
        """
        if not cls._loaded:
            cls.load_templates()
        
        query_lower = query.lower()
        results = []
        
        for template in cls._templates.values():
            # 搜索名称
            if query_lower in template.get("name", "").lower():
                results.append(template)
                continue
            
            # 搜索描述
            if query_lower in template.get("description", "").lower():
                results.append(template)
                continue
            
            # 搜索标签
            tags = template.get("tags", [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(template)
                continue
        
        return results
    
    @classmethod
    def create_workflow_from_template(
        cls,
        template_id: str,
        name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从模板创建工作流
        
        Args:
            template_id: 模板 ID
            name: 工作流名称（可选，默认使用模板名称）
            variables: 变量配置（可选）
            
        Returns:
            工作流数据，如果模板不存在则返回 None
        """
        template = cls.get_template(template_id)
        if not template:
            return None
        
        # 复制模板定义
        workflow_data = {
            "name": name or template.get("name"),
            "description": template.get("description"),
            "definition": template.get("definition"),
            "variables": variables or template.get("variables", []),
            "metadata": {
                "created_from_template": template_id,
                "template_category": template.get("category"),
                "template_tags": template.get("tags")
            }
        }
        
        return workflow_data
    
    @classmethod
    def reload_templates(cls) -> bool:
        """
        重新加载模板
        
        Returns:
            是否重新加载成功
        """
        cls._loaded = False
        cls._templates.clear()
        return cls.load_templates()


# ============ 便捷函数 ============

def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    """获取模板"""
    return WorkflowTemplateManager.get_template(template_id)


def list_templates(
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """列出模板"""
    return WorkflowTemplateManager.list_templates(category, tags)


def search_templates(query: str) -> List[Dict[str, Any]]:
    """搜索模板"""
    return WorkflowTemplateManager.search_templates(query)


def create_from_template(
    template_id: str,
    name: Optional[str] = None,
    variables: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """从模板创建工作流"""
    return WorkflowTemplateManager.create_workflow_from_template(
        template_id, name, variables
    )


# ============ 导出 ============

__all__ = [
    "WorkflowTemplateManager",
    "get_template",
    "list_templates",
    "search_templates",
    "create_from_template"
]
