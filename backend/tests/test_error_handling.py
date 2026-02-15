"""
错误处理模块测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from app.core.exceptions import (
    AppException,
    validation_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    app_exception_handler,
    generic_exception_handler
)
from app.core.error_codes import (
    ErrorCode,
    create_error_response,
    ERROR_CODE_TO_HTTP_STATUS,
    ERROR_CODE_TO_MESSAGE
)


def test_error_code_enum():
    """测试错误码枚举"""
    assert ErrorCode.UNKNOWN_ERROR == "ERR_1000"
    assert ErrorCode.UNAUTHORIZED == "ERR_2000"
    assert ErrorCode.RESOURCE_NOT_FOUND == "ERR_3000"
    assert ErrorCode.USER_NOT_FOUND == "ERR_4000"
    assert ErrorCode.SKILL_NOT_FOUND == "ERR_5000"


def test_error_code_to_http_status():
    """测试错误码到HTTP状态的映射"""
    assert ERROR_CODE_TO_HTTP_STATUS[ErrorCode.UNAUTHORIZED] == 401
    assert ERROR_CODE_TO_HTTP_STATUS[ErrorCode.PERMISSION_DENIED] == 403
    assert ERROR_CODE_TO_HTTP_STATUS[ErrorCode.RESOURCE_NOT_FOUND] == 404
    assert ERROR_CODE_TO_HTTP_STATUS[ErrorCode.RATE_LIMIT_EXCEEDED] == 429
    assert ERROR_CODE_TO_HTTP_STATUS[ErrorCode.DATABASE_ERROR] == 500


def test_error_code_to_message():
    """测试错误码到消息的映射"""
    assert "Authentication required" in ERROR_CODE_TO_MESSAGE[ErrorCode.UNAUTHORIZED]
    assert "not found" in ERROR_CODE_TO_MESSAGE[ErrorCode.RESOURCE_NOT_FOUND]


def test_create_error_response():
    """测试创建错误响应"""
    response = create_error_response(
        error_code=ErrorCode.RESOURCE_NOT_FOUND,
        message="Custom not found message",
        details={"resource_type": "Skill"}
    )
    
    assert response.error_code == ErrorCode.RESOURCE_NOT_FOUND
    assert response.message == "Custom not found message"
    assert response.details == {"resource_type": "Skill"}
    assert response.http_status == 404
    
    response_dict = response.to_dict()
    assert "error" in response_dict
    assert response_dict["error"]["code"] == "ERR_3000"


def test_create_error_response_default_message():
    """测试使用默认消息创建错误响应"""
    response = create_error_response(ErrorCode.UNAUTHORIZED)
    
    assert response.message == ERROR_CODE_TO_MESSAGE[ErrorCode.UNAUTHORIZED]


def test_app_exception():
    """测试应用自定义异常"""
    exc = AppException(
        error_code=ErrorCode.PERMISSION_DENIED,
        message="You don't have permission",
        details={"resource": "skill", "action": "delete"}
    )
    
    assert exc.error_code == ErrorCode.PERMISSION_DENIED
    assert exc.message == "You don't have permission"
    assert exc.details == {"resource": "skill", "action": "delete"}


@pytest.mark.asyncio
class TestExceptionHandlers:
    """异常处理器测试"""
    
    async def test_validation_exception_handler(self):
        """测试验证异常处理器"""
        # Mock request
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.url = MagicMock()
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        # Mock validation error
        exc = MagicMock(spec=RequestValidationError)
        exc.errors = MagicMock(return_value=[
            {
                "loc": ["body", "email"],
                "msg": "Invalid email",
                "type": "value_error.email"
            }
        ])
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == 422
        # 可以进一步检查响应内容
    
    async def test_http_exception_handler(self):
        """测试HTTP异常处理器"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await http_exception_handler(request, exc)
        
        assert response.status_code == 404
    
    async def test_sqlalchemy_exception_handler_integrity_error(self):
        """测试数据库完整性错误处理器"""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = IntegrityError("", "", "")
        
        response = await sqlalchemy_exception_handler(request, exc)
        
        assert response.status_code == 409
    
    async def test_sqlalchemy_exception_handler_operational_error(self):
        """测试数据库连接错误处理器"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = OperationalError("", "", "")
        
        response = await sqlalchemy_exception_handler(request, exc)
        
        assert response.status_code == 503
    
    async def test_sqlalchemy_exception_handler_generic_error(self):
        """测试通用数据库错误处理器"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = SQLAlchemyError("Generic error")
        
        response = await sqlalchemy_exception_handler(request, exc)
        
        assert response.status_code == 500
    
    async def test_app_exception_handler(self):
        """测试应用异常处理器"""
        request = MagicMock(spec=Request)
        request.method = "DELETE"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = AppException(
            error_code=ErrorCode.PERMISSION_DENIED,
            message="Access denied"
        )
        
        response = await app_exception_handler(request, exc)
        
        assert response.status_code == 403
    
    async def test_generic_exception_handler(self):
        """测试通用异常处理器"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/test"
        str(request.url).return_value = "http://test/api/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        exc = Exception("Unexpected error")
        
        response = await generic_exception_handler(request, exc)
        
        assert response.status_code == 500
