"""
缓存模块测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.cache import (
    CacheManager,
    cache,
    cached,
    invalidate_cache,
    CacheKeys,
    CacheExpire
)


@pytest.mark.asyncio
class TestCacheManager:
    """缓存管理器测试"""
    
    async def test_connect_success(self):
        """测试成功连接"""
        cache_manager = CacheManager()
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_redis.return_value = mock_client
            
            await cache_manager.connect()
            
            assert cache_manager._connected is True
            mock_client.ping.assert_called_once()
    
    async def test_connect_failure(self):
        """测试连接失败"""
        cache_manager = CacheManager()
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
            mock_redis.return_value = mock_client
            
            await cache_manager.connect()
            
            assert cache_manager._connected is False
    
    async def test_get_cache_hit(self):
        """测试缓存命中"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        
        import json
        test_data = {"key": "value"}
        cache_manager.client.get = AsyncMock(return_value=json.dumps(test_data))
        
        result = await cache_manager.get("test_key")
        
        assert result == test_data
        cache_manager.client.get.assert_called_once_with("test_key")
    
    async def test_get_cache_miss(self):
        """测试缓存未命中"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        cache_manager.client.get = AsyncMock(return_value=None)
        
        result = await cache_manager.get("test_key")
        
        assert result is None
    
    async def test_get_cache_disabled(self):
        """测试缓存禁用时的get"""
        cache_manager = CacheManager()
        cache_manager._connected = False
        
        result = await cache_manager.get("test_key")
        
        assert result is None
    
    async def test_set_cache_success(self):
        """测试设置缓存成功"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        cache_manager.client.set = AsyncMock()
        
        test_data = {"key": "value"}
        result = await cache_manager.set("test_key", test_data, expire=300)
        
        assert result is True
        cache_manager.client.set.assert_called_once()
    
    async def test_set_cache_with_expire(self):
        """测试设置带过期时间的缓存"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        cache_manager.client.setex = AsyncMock()
        
        test_data = {"key": "value"}
        result = await cache_manager.set("test_key", test_data, expire=300)
        
        assert result is True
        cache_manager.client.setex.assert_called_once()
    
    async def test_delete_cache_success(self):
        """测试删除缓存成功"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        cache_manager.client.delete = AsyncMock()
        
        result = await cache_manager.delete("test_key")
        
        assert result is True
        cache_manager.client.delete.assert_called_once_with("test_key")
    
    async def test_delete_pattern(self):
        """测试删除匹配模式的缓存"""
        cache_manager = CacheManager()
        cache_manager._connected = True
        cache_manager.client = AsyncMock()
        
        # Mock scan_iter
        async def mock_scan_iter(match=None):
            for key in ["test:1", "test:2", "test:3"]:
                yield key
        
        cache_manager.client.scan_iter = mock_scan_iter
        cache_manager.client.delete = AsyncMock()
        
        result = await cache_manager.delete_pattern("test:*")
        
        assert result == 3
    
    async def test_generate_key_short(self):
        """测试生成短键"""
        cache_manager = CacheManager()
        
        key = cache_manager._generate_key("prefix", "arg1", "arg2", kwarg1="value1")
        
        assert "prefix" in key
        assert "arg1" in key
        assert "arg2" in key
        assert "kwarg1:value1" in key
    
    async def test_generate_key_long(self):
        """测试生成长键（使用哈希）"""
        cache_manager = CacheManager()
        
        # 创建一个很长的参数列表
        long_args = ["x" * 100 for _ in range(10)]
        key = cache_manager._generate_key("prefix", *long_args)
        
        # 应该使用哈希
        assert "hash:" in key
        assert len(key) < 300


@pytest.mark.asyncio
class TestCacheDecorator:
    """缓存装饰器测试"""
    
    async def test_cached_decorator_hit(self):
        """测试缓存装饰器命中"""
        
        @cached(prefix="test", expire=300)
        async def test_func(arg1, arg2):
            return {"result": f"{arg1}-{arg2}"}
        
        # Mock cache
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"result": "cached-value"})
            mock_cache._generate_key = MagicMock(return_value="test:key")
            
            result = await test_func("a", "b")
            
            # 应该返回缓存值
            assert result == {"result": "cached-value"}
            mock_cache.get.assert_called_once()
    
    async def test_cached_decorator_miss(self):
        """测试缓存装饰器未命中"""
        
        @cached(prefix="test", expire=300)
        async def test_func(arg1, arg2):
            return {"result": f"{arg1}-{arg2}"}
        
        # Mock cache
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache._generate_key = MagicMock(return_value="test:key")
            
            result = await test_func("a", "b")
            
            # 应该执行函数并缓存结果
            assert result == {"result": "a-b"}
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
    
    async def test_invalidate_cache_decorator(self):
        """测试缓存失效装饰器"""
        
        @invalidate_cache(pattern="test:*")
        async def test_func():
            return "success"
        
        # Mock cache
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.delete_pattern = AsyncMock(return_value=3)
            
            result = await test_func()
            
            # 应该删除缓存并返回结果
            assert result == "success"
            mock_cache.delete_pattern.assert_called_once_with("test:*")


def test_cache_keys():
    """测试缓存键常量"""
    assert CacheKeys.USER_PROFILE == "user:profile"
    assert CacheKeys.SKILL_DETAIL == "skill:detail"
    assert CacheKeys.SESSION_DETAIL == "session:detail"


def test_cache_expire():
    """测试缓存过期时间常量"""
    assert CacheExpire.SHORT == 60
    assert CacheExpire.MEDIUM == 300
    assert CacheExpire.LONG == 3600
    assert CacheExpire.VERY_LONG == 86400
