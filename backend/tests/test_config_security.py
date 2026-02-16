"""
测试配置安全性

验证 Issue #4 和 #6 的修复：
- SECRET_KEY 必须至少 32 字符
- SECRET_KEY 不能有默认值
- MINIO_ACCESS_KEY 不能使用默认值
- MINIO_SECRET_KEY 不能使用默认值
"""
import pytest
from pydantic import ValidationError
from backend.app.config import Settings


def test_secret_key_minimum_length():
    """测试 SECRET_KEY 最小长度为 32 字符"""
    # 短于 32 字符应该失败
    with pytest.raises(ValidationError) as exc_info:
        Settings(SECRET_KEY="short-key")
    
    errors = exc_info.value.errors()
    assert any("SECRET_KEY must be at least 32 characters" in str(e) for e in errors)


def test_secret_key_valid_length():
    """测试 SECRET_KEY 长度足够时可以正常加载"""
    settings = Settings(SECRET_KEY="this-is-a-valid-secret-key-with-32-chars")
    assert settings.SECRET_KEY == "this-is-a-valid-secret-key-with-32-chars"


def test_minio_access_key_cannot_use_default():
    """测试 MINIO_ACCESS_KEY 不能使用默认值 minioadmin"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            SECRET_KEY="test-secret-key-for-development-min-32-chars",
            MINIO_ACCESS_KEY="minioadmin"
        )
    
    errors = exc_info.value.errors()
    assert any("cannot use default value 'minioadmin'" in str(e) for e in errors)


def test_minio_access_key_valid():
    """测试 MINIO_ACCESS_KEY 使用有效值时可以正常加载"""
    settings = Settings(
        SECRET_KEY="test-secret-key-for-development-min-32-chars",
        MINIO_ACCESS_KEY="my-custom-access-key"
    )
    assert settings.MINIO_ACCESS_KEY == "my-custom-access-key"


def test_minio_secret_key_cannot_use_default():
    """测试 MINIO_SECRET_KEY 不能使用默认值 minioadmin"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            SECRET_KEY="test-secret-key-for-development-min-32-chars",
            MINIO_SECRET_KEY="minioadmin"
        )
    
    errors = exc_info.value.errors()
    assert any("cannot use default value 'minioadmin'" in str(e) for e in errors)


def test_minio_secret_key_valid():
    """测试 MINIO_SECRET_KEY 使用有效值时可以正常加载"""
    settings = Settings(
        SECRET_KEY="test-secret-key-for-development-min-32-chars",
        MINIO_SECRET_KEY="my-custom-secret-key"
    )
    assert settings.MINIO_SECRET_KEY == "my-custom-secret-key"


def test_secret_key_required():
    """测试 SECRET_KEY 是必填字段"""
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    
    errors = exc_info.value.errors()
    assert any("SECRET_KEY" in str(e) for e in errors)


def test_minio_keys_required():
    """测试 MINIO_ACCESS_KEY 和 MINIO_SECRET_KEY 是必填字段"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(SECRET_KEY="test-secret-key-for-development-min-32-chars")
    
    errors = exc_info.value.errors()
    field_names = [e.get("loc", [None])[0] for e in errors]
    assert "MINIO_ACCESS_KEY" in field_names or "MINIO_SECRET_KEY" in field_names
