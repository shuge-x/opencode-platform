"""
错误码定义和错误响应标准化
"""
from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """标准化错误码"""
    
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = "ERR_1000"
    INVALID_REQUEST = "ERR_1001"
    VALIDATION_ERROR = "ERR_1002"
    RATE_LIMIT_EXCEEDED = "ERR_1003"
    
    # 认证错误 (2xxx)
    UNAUTHORIZED = "ERR_2000"
    INVALID_TOKEN = "ERR_2001"
    TOKEN_EXPIRED = "ERR_2002"
    INVALID_CREDENTIALS = "ERR_2003"
    PERMISSION_DENIED = "ERR_2004"
    
    # 资源错误 (3xxx)
    RESOURCE_NOT_FOUND = "ERR_3000"
    RESOURCE_ALREADY_EXISTS = "ERR_3001"
    RESOURCE_LOCKED = "ERR_3002"
    
    # 用户错误 (4xxx)
    USER_NOT_FOUND = "ERR_4000"
    USER_ALREADY_EXISTS = "ERR_4001"
    USER_INACTIVE = "ERR_4002"
    USER_NOT_VERIFIED = "ERR_4003"
    
    # 技能错误 (5xxx)
    SKILL_NOT_FOUND = "ERR_5000"
    SKILL_EXECUTION_FAILED = "ERR_5001"
    SKILL_PERMISSION_DENIED = "ERR_5002"
    SKILL_VERSION_CONFLICT = "ERR_5003"
    
    # 会话错误 (6xxx)
    SESSION_NOT_FOUND = "ERR_6000"
    SESSION_INACTIVE = "ERR_6001"
    SESSION_LIMIT_EXCEEDED = "ERR_6002"
    
    # 文件错误 (7xxx)
    FILE_NOT_FOUND = "ERR_7000"
    FILE_TOO_LARGE = "ERR_7001"
    FILE_TYPE_NOT_ALLOWED = "ERR_7002"
    FILE_UPLOAD_FAILED = "ERR_7003"
    
    # 数据库错误 (8xxx)
    DATABASE_ERROR = "ERR_8000"
    DATABASE_CONNECTION_ERROR = "ERR_8001"
    DATABASE_QUERY_ERROR = "ERR_8002"
    
    # 外部服务错误 (9xxx)
    EXTERNAL_SERVICE_ERROR = "ERR_9000"
    REDIS_ERROR = "ERR_9001"
    GIT_ERROR = "ERR_9002"
    CONTAINER_ERROR = "ERR_9003"


class ErrorResponse:
    """标准化错误响应"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 400
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.http_status = http_status
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details
            }
        }


# 错误码到HTTP状态的映射
ERROR_CODE_TO_HTTP_STATUS = {
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INVALID_TOKEN: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.PERMISSION_DENIED: 403,
    
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.RESOURCE_ALREADY_EXISTS: 409,
    ErrorCode.RESOURCE_LOCKED: 423,
    
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.USER_ALREADY_EXISTS: 409,
    ErrorCode.USER_INACTIVE: 403,
    ErrorCode.USER_NOT_VERIFIED: 403,
    
    ErrorCode.SKILL_NOT_FOUND: 404,
    ErrorCode.SKILL_EXECUTION_FAILED: 500,
    ErrorCode.SKILL_PERMISSION_DENIED: 403,
    ErrorCode.SKILL_VERSION_CONFLICT: 409,
    
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.SESSION_INACTIVE: 400,
    ErrorCode.SESSION_LIMIT_EXCEEDED: 429,
    
    ErrorCode.FILE_NOT_FOUND: 404,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.FILE_TYPE_NOT_ALLOWED: 415,
    ErrorCode.FILE_UPLOAD_FAILED: 500,
    
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.DATABASE_CONNECTION_ERROR: 503,
    ErrorCode.DATABASE_QUERY_ERROR: 500,
    
    ErrorCode.EXTERNAL_SERVICE_ERROR: 502,
    ErrorCode.REDIS_ERROR: 503,
    ErrorCode.GIT_ERROR: 500,
    ErrorCode.CONTAINER_ERROR: 500,
}


# 错误码到友好消息的映射
ERROR_CODE_TO_MESSAGE = {
    ErrorCode.UNKNOWN_ERROR: "An unexpected error occurred",
    ErrorCode.INVALID_REQUEST: "Invalid request parameters",
    ErrorCode.VALIDATION_ERROR: "Validation failed",
    ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please try again later",
    
    ErrorCode.UNAUTHORIZED: "Authentication required",
    ErrorCode.INVALID_TOKEN: "Invalid authentication token",
    ErrorCode.TOKEN_EXPIRED: "Authentication token has expired",
    ErrorCode.INVALID_CREDENTIALS: "Invalid email or password",
    ErrorCode.PERMISSION_DENIED: "You don't have permission to perform this action",
    
    ErrorCode.RESOURCE_NOT_FOUND: "Requested resource not found",
    ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource already exists",
    ErrorCode.RESOURCE_LOCKED: "Resource is currently locked",
    
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.USER_ALREADY_EXISTS: "User with this email or username already exists",
    ErrorCode.USER_INACTIVE: "User account is inactive",
    ErrorCode.USER_NOT_VERIFIED: "Email address not verified",
    
    ErrorCode.SKILL_NOT_FOUND: "Skill not found",
    ErrorCode.SKILL_EXECUTION_FAILED: "Skill execution failed",
    ErrorCode.SKILL_PERMISSION_DENIED: "You don't have permission to access this skill",
    ErrorCode.SKILL_VERSION_CONFLICT: "Skill version conflict detected",
    
    ErrorCode.SESSION_NOT_FOUND: "Session not found",
    ErrorCode.SESSION_INACTIVE: "Session is inactive",
    ErrorCode.SESSION_LIMIT_EXCEEDED: "Maximum number of sessions exceeded",
    
    ErrorCode.FILE_NOT_FOUND: "File not found",
    ErrorCode.FILE_TOO_LARGE: "File size exceeds maximum allowed",
    ErrorCode.FILE_TYPE_NOT_ALLOWED: "File type not allowed",
    ErrorCode.FILE_UPLOAD_FAILED: "File upload failed",
    
    ErrorCode.DATABASE_ERROR: "Database error occurred",
    ErrorCode.DATABASE_CONNECTION_ERROR: "Unable to connect to database",
    ErrorCode.DATABASE_QUERY_ERROR: "Database query failed",
    
    ErrorCode.EXTERNAL_SERVICE_ERROR: "External service error",
    ErrorCode.REDIS_ERROR: "Cache service unavailable",
    ErrorCode.GIT_ERROR: "Git operation failed",
    ErrorCode.CONTAINER_ERROR: "Container operation failed",
}


def create_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    创建标准化错误响应
    
    Args:
        error_code: 错误码
        message: 自定义消息（可选）
        details: 错误详情（可选）
    
    Returns:
        ErrorResponse对象
    """
    http_status = ERROR_CODE_TO_HTTP_STATUS.get(error_code, 500)
    error_message = message or ERROR_CODE_TO_MESSAGE.get(error_code, "Unknown error")
    
    return ErrorResponse(
        error_code=error_code,
        message=error_message,
        details=details,
        http_status=http_status
    )
