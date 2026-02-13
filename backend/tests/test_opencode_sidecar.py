"""
OpenCode Sidecar测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.utils.opencode_sidecar import OpenCodeSidecar


@pytest.mark.asyncio
async def test_opencode_sidecar():
    """测试opencode CLI调用"""
    # Mock测试（如果opencode不可用）
    sidecar = OpenCodeSidecar()
    
    # 如果opencode可用，测试真实调用
    # result = await sidecar.execute("Hello", "test-session", "test-user")
    # assert result['success'] is True
    
    # Mock测试
    # TODO: 使用unittest.mock模拟subprocess
    pass


@pytest.mark.asyncio
async def test_opencode_sidecar_mock_success():
    """测试opencode CLI调用（Mock成功场景）"""
    sidecar = OpenCodeSidecar()
    
    # Mock subprocess
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        # 创建mock进程
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Success output", b""))
        mock_exec.return_value = mock_proc
        
        # 执行测试
        result = await sidecar.execute(
            "Hello",
            "test-session",
            "test-user"
        )
        
        # 验证结果
        assert result['success'] is True
        assert result['output'] == "Success output"
        assert result['error'] is None


@pytest.mark.asyncio
async def test_opencode_sidecar_mock_failure():
    """测试opencode CLI调用（Mock失败场景）"""
    sidecar = OpenCodeSidecar()
    
    # Mock subprocess
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        # 创建mock进程
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error output"))
        mock_exec.return_value = mock_proc
        
        # 执行测试
        result = await sidecar.execute(
            "Hello",
            "test-session",
            "test-user"
        )
        
        # 验证结果
        assert result['success'] is False
        assert result['output'] is None
        assert result['error'] == "Error output"


@pytest.mark.asyncio
async def test_opencode_sidecar_health_check():
    """测试opencode CLI健康检查"""
    sidecar = OpenCodeSidecar()
    
    # Mock subprocess
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        # 创建mock进程
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"1.0.0", b""))
        mock_exec.return_value = mock_proc
        
        # 执行测试
        is_healthy = await sidecar.check_health()
        
        # 验证结果
        assert is_healthy is True
