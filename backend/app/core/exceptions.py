"""
全局异常处理器 - 增强版

提供统一的错误处理和详细的错误日志
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import logging
import traceback
import time
from typing import Dict, Any

from app.core.error_codes import (
    ErrorCode,
    create_error_response,
    ERROR_CODE_TO_HTTP_STATUS
)

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用自定义异常基类"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str = None,
        details: Dict[str, Any] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


async def log_error(
    request: Request,
    error_code: ErrorCode,
    message: str,
    details: Dict[str, Any] = None,
    exc: Exception = None
):
    """记录详细的错误日志"""
    error_log = {
        "timestamp": time.time(),
        "error_code": error_code.value,
        "message": message,
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "details": details or {}
    }
    
    # 根据错误类型选择日志级别
    if exc:
        error_log["exception_type"] = type(exc).__name__
        error_log["exception_message"] = str(exc)
        error_log["traceback"] = traceback.format_exc()
        
        # 5xx错误使用error级别
        if ERROR_CODE_TO_HTTP_STATUS.get(error_code, 500) >= 500:
            logger.error(f"Application error: {error_log}", exc_info=True)
        else:
            logger.warning(f"Application error: {error_log}")
    else:
        logger.warning(f"Application error: {error_log}")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # 记录详细日志
    await log_error(
        request=request,
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details={"validation_errors": errors},
        exc=exc
    )
    
    error_response = create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        details={"validation_errors": errors}
    )
    
    return JSONResponse(
        status_code=error_response.http_status,
        content=error_response.to_dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    # 将HTTP异常转换为错误码
    error_code_map = {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
    
    # 记录日志
    await log_error(
        request=request,
        error_code=error_code,
        message=exc.detail,
        exc=exc
    )
    
    error_response = create_error_response(
        error_code=error_code,
        message=str(exc.detail) if exc.detail else None
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理"""
    # 确定具体的错误码
    if isinstance(exc, IntegrityError):
        error_code = ErrorCode.RESOURCE_ALREADY_EXISTS
        message = "Database integrity constraint violated"
    elif isinstance(exc, OperationalError):
        error_code = ErrorCode.DATABASE_CONNECTION_ERROR
        message = "Database connection error"
    else:
        error_code = ErrorCode.DATABASE_ERROR
        message = "Database error occurred"
    
    # 记录详细日志（不暴露敏感信息）
    await log_error(
        request=request,
        error_code=error_code,
        message=message,
        details={"db_error_type": type(exc).__name__},
        exc=exc
    )
    
    error_response = create_error_response(
        error_code=error_code,
        message=message
    )
    
    return JSONResponse(
        status_code=error_response.http_status,
        content=error_response.to_dict()
    )


async def app_exception_handler(request: Request, exc: AppException):
    """自定义应用异常处理"""
    # 记录日志
    await log_error(
        request=request,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        exc=exc
    )
    
    error_response = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=error_response.http_status,
        content=error_response.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    # 记录详细日志
    await log_error(
        request=request,
        error_code=ErrorCode.UNKNOWN_ERROR,
        message="An unexpected error occurred",
        details={"exception_type": type(exc).__name__},
        exc=exc
    )
    
    error_response = create_error_response(
        error_code=ErrorCode.UNKNOWN_ERROR,
        message="An unexpected error occurred"
    )
    
    return JSONResponse(
        status_code=error_response.http_status,
        content=error_response.to_dict()
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
