"""
工作流缓存策略

针对大工作流（100+ 节点）的性能优化：
- DAG 解析结果缓存
- 节点执行结果缓存
- 变量解析缓存
- 技能元数据缓存
"""
from typing import Dict, Any, Optional, List
from datetime import timedelta
import hashlib
import json
from app.core.cache import cache


class WorkflowCacheStrategy:
    """工作流缓存策略"""
    
    # 缓存键前缀
    PREFIX_DAG = "workflow:dag:"
    PREFIX_DEFINITION = "workflow:def:"
    PREFIX_SKILL_META = "workflow:skill:"
    PREFIX_EXECUTION_CTX = "workflow:ctx:"
    PREFIX_NODE_OUTPUT = "workflow:node_out:"
    
    # 缓存时间
    TTL_DAG = timedelta(hours=24)  # DAG 解析结果缓存 24 小时
    TTL_DEFINITION = timedelta(hours=1)  # 工作流定义缓存 1 小时
    TTL_SKILL_META = timedelta(hours=12)  # 技能元数据缓存 12 小时
    TTL_EXECUTION_CTX = timedelta(minutes=30)  # 执行上下文缓存 30 分钟
    TTL_NODE_OUTPUT = timedelta(hours=2)  # 节点输出缓存 2 小时
    
    @staticmethod
    def _generate_cache_key(prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return f"{prefix}{key_string}"
    
    @staticmethod
    def _hash_definition(definition: Dict[str, Any]) -> str:
        """计算工作流定义的哈希值"""
        definition_str = json.dumps(definition, sort_keys=True)
        return hashlib.sha256(definition_str.encode()).hexdigest()[:16]
    
    # ============ DAG 解析缓存 ============
    
    @classmethod
    async def cache_dag(cls, workflow_id: int, definition: Dict[str, Any], dag_data: Dict[str, Any]) -> bool:
        """
        缓存 DAG 解析结果
        
        Args:
            workflow_id: 工作流 ID
            definition: 工作流定义
            dag_data: 解析后的 DAG 数据
            
        Returns:
            是否缓存成功
        """
        if not cache._connected:
            return False
        
        definition_hash = cls._hash_definition(definition)
        cache_key = cls._generate_cache_key(cls.PREFIX_DAG, workflow_id, definition_hash)
        
        return await cache.set(cache_key, dag_data, ttl=cls.TTL_DAG)
    
    @classmethod
    async def get_cached_dag(cls, workflow_id: int, definition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取缓存的 DAG 解析结果
        
        Args:
            workflow_id: 工作流 ID
            definition: 工作流定义
            
        Returns:
            缓存的 DAG 数据，如果没有则返回 None
        """
        if not cache._connected:
            return None
        
        definition_hash = cls._hash_definition(definition)
        cache_key = cls._generate_cache_key(cls.PREFIX_DAG, workflow_id, definition_hash)
        
        return await cache.get(cache_key)
    
    # ============ 工作流定义缓存 ============
    
    @classmethod
    async def cache_workflow_definition(cls, workflow_id: int, definition: Dict[str, Any]) -> bool:
        """
        缓存工作流定义
        
        Args:
            workflow_id: 工作流 ID
            definition: 工作流定义
            
        Returns:
            是否缓存成功
        """
        if not cache._connected:
            return False
        
        cache_key = cls._generate_cache_key(cls.PREFIX_DEFINITION, workflow_id)
        return await cache.set(cache_key, definition, ttl=cls.TTL_DEFINITION)
    
    @classmethod
    async def get_cached_definition(cls, workflow_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的工作流定义
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            缓存的工作流定义
        """
        if not cache._connected:
            return None
        
        cache_key = cls._generate_cache_key(cls.PREFIX_DEFINITION, workflow_id)
        return await cache.get(cache_key)
    
    @classmethod
    async def invalidate_definition(cls, workflow_id: int) -> bool:
        """
        使工作流定义缓存失效
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            是否成功失效
        """
        if not cache._connected:
            return False
        
        cache_key = cls._generate_cache_key(cls.PREFIX_DEFINITION, workflow_id)
        return await cache.delete(cache_key)
    
    # ============ 技能元数据缓存 ============
    
    @classmethod
    async def cache_skill_metadata(cls, skill_id: int, metadata: Dict[str, Any]) -> bool:
        """
        缓存技能元数据
        
        Args:
            skill_id: 技能 ID
            metadata: 技能元数据
            
        Returns:
            是否缓存成功
        """
        if not cache._connected:
            return False
        
        cache_key = cls._generate_cache_key(cls.PREFIX_SKILL_META, skill_id)
        return await cache.set(cache_key, metadata, ttl=cls.TTL_SKILL_META)
    
    @classmethod
    async def get_cached_skill_metadata(cls, skill_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的技能元数据
        
        Args:
            skill_id: 技能 ID
            
        Returns:
            缓存的技能元数据
        """
        if not cache._connected:
            return None
        
        cache_key = cls._generate_cache_key(cls.PREFIX_SKILL_META, skill_id)
        return await cache.get(cache_key)
    
    # ============ 执行上下文缓存 ============
    
    @classmethod
    async def cache_execution_context(cls, execution_id: int, context_data: Dict[str, Any]) -> bool:
        """
        缓存执行上下文
        
        Args:
            execution_id: 执行 ID
            context_data: 上下文数据
            
        Returns:
            是否缓存成功
        """
        if not cache._connected:
            return False
        
        cache_key = cls._generate_cache_key(cls.PREFIX_EXECUTION_CTX, execution_id)
        return await cache.set(cache_key, context_data, ttl=cls.TTL_EXECUTION_CTX)
    
    @classmethod
    async def get_cached_execution_context(cls, execution_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的执行上下文
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            缓存的执行上下文
        """
        if not cache._connected:
            return None
        
        cache_key = cls._generate_cache_key(cls.PREFIX_EXECUTION_CTX, execution_id)
        return await cache.get(cache_key)
    
    @classmethod
    async def update_execution_context(cls, execution_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新执行上下文缓存
        
        Args:
            execution_id: 执行 ID
            updates: 要更新的数据
            
        Returns:
            是否更新成功
        """
        if not cache._connected:
            return False
        
        cached_data = await cls.get_cached_execution_context(execution_id)
        if cached_data is None:
            return False
        
        cached_data.update(updates)
        return await cls.cache_execution_context(execution_id, cached_data)
    
    # ============ 节点输出缓存 ============
    
    @classmethod
    async def cache_node_output(
        cls,
        execution_id: int,
        node_id: str,
        output_data: Dict[str, Any]
    ) -> bool:
        """
        缓存节点输出结果
        
        Args:
            execution_id: 执行 ID
            node_id: 节点 ID
            output_data: 输出数据
            
        Returns:
            是否缓存成功
        """
        if not cache._connected:
            return False
        
        cache_key = cls._generate_cache_key(cls.PREFIX_NODE_OUTPUT, execution_id, node_id)
        return await cache.set(cache_key, output_data, ttl=cls.TTL_NODE_OUTPUT)
    
    @classmethod
    async def get_cached_node_output(
        cls,
        execution_id: int,
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的节点输出
        
        Args:
            execution_id: 执行 ID
            node_id: 节点 ID
            
        Returns:
            缓存的节点输出
        """
        if not cache._connected:
            return None
        
        cache_key = cls._generate_cache_key(cls.PREFIX_NODE_OUTPUT, execution_id, node_id)
        return await cache.get(cache_key)
    
    @classmethod
    async def batch_cache_node_outputs(
        cls,
        execution_id: int,
        outputs: Dict[str, Dict[str, Any]]
    ) -> int:
        """
        批量缓存节点输出
        
        Args:
            execution_id: 执行 ID
            outputs: 节点 ID -> 输出数据的映射
            
        Returns:
            成功缓存的数量
        """
        if not cache._connected:
            return 0
        
        success_count = 0
        for node_id, output_data in outputs.items():
            if await cls.cache_node_output(execution_id, node_id, output_data):
                success_count += 1
        
        return success_count
    
    # ============ 批量操作 ============
    
    @classmethod
    async def warm_cache(cls, workflow_id: int, definition: Dict[str, Any]) -> bool:
        """
        预热缓存
        
        在工作流执行前预加载和缓存相关数据
        
        Args:
            workflow_id: 工作流 ID
            definition: 工作流定义
            
        Returns:
            是否预热成功
        """
        if not cache._connected:
            return False
        
        # 缓存工作流定义
        await cls.cache_workflow_definition(workflow_id, definition)
        
        # TODO: 预加载技能元数据
        # 遍历定义中的所有技能节点，预加载技能元数据
        
        return True
    
    @classmethod
    async def cleanup_execution_cache(cls, execution_id: int) -> int:
        """
        清理执行相关缓存
        
        执行完成后清理缓存以释放内存
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            清理的缓存数量
        """
        if not cache._connected:
            return 0
        
        # 删除执行上下文
        ctx_key = cls._generate_cache_key(cls.PREFIX_EXECUTION_CTX, execution_id)
        await cache.delete(ctx_key)
        
        # 删除节点输出缓存（使用模式匹配）
        pattern = cls._generate_cache_key(cls.PREFIX_NODE_OUTPUT, execution_id, "*")
        # 注意：需要实现 cache.keys() 或 cache.delete_pattern() 方法
        # 这里暂时返回 1，表示删除了执行上下文
        return 1


# ============ 性能优化装饰器 ============

def cache_result(prefix: str, ttl: timedelta, key_builder=None):
    """
    缓存函数结果的装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 缓存时间
        key_builder: 自定义缓存键构建函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not cache._connected:
                return await func(*args, **kwargs)
            
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{prefix}:{':'.join(str(arg) for arg in args)}"
            
            # 尝试从缓存获取
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
