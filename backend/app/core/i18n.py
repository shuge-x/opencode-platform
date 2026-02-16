"""
国际化 (i18n) 支持模块

提供多语言错误消息和提示文本
"""
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """支持的语言"""
    EN = "en"
    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    JA = "ja"


# 默认语言
DEFAULT_LANGUAGE = Language.EN


# 错误消息翻译字典
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    # 通用错误 (1xxx)
    "ERR_1000": {
        "en": "An unexpected error occurred",
        "zh-CN": "发生意外错误",
        "zh-TW": "發生意外錯誤",
        "ja": "予期しないエラーが発生しました"
    },
    "ERR_1001": {
        "en": "Invalid request parameters",
        "zh-CN": "请求参数无效",
        "zh-TW": "請求參數無效",
        "ja": "無効なリクエストパラメータ"
    },
    "ERR_1002": {
        "en": "Validation failed",
        "zh-CN": "验证失败",
        "zh-TW": "驗證失敗",
        "ja": "検証に失敗しました"
    },
    "ERR_1003": {
        "en": "Too many requests. Please try again later",
        "zh-CN": "请求过于频繁，请稍后再试",
        "zh-TW": "請求過於頻繁，請稍後再試",
        "ja": "リクエストが多すぎます。後でもう一度お試しください"
    },
    
    # 认证错误 (2xxx)
    "ERR_2000": {
        "en": "Authentication required",
        "zh-CN": "需要身份验证",
        "zh-TW": "需要身份驗證",
        "ja": "認証が必要です"
    },
    "ERR_2001": {
        "en": "Invalid authentication token",
        "zh-CN": "认证令牌无效",
        "zh-TW": "認證令牌無效",
        "ja": "無効な認証トークン"
    },
    "ERR_2002": {
        "en": "Authentication token has expired",
        "zh-CN": "认证令牌已过期",
        "zh-TW": "認證令牌已過期",
        "ja": "認証トークンの有効期限が切れています"
    },
    "ERR_2003": {
        "en": "Invalid email or password",
        "zh-CN": "邮箱或密码错误",
        "zh-TW": "郵箱或密碼錯誤",
        "ja": "メールアドレスまたはパスワードが正しくありません"
    },
    "ERR_2004": {
        "en": "You don't have permission to perform this action",
        "zh-CN": "您没有权限执行此操作",
        "zh-TW": "您沒有權限執行此操作",
        "ja": "この操作を実行する権限がありません"
    },
    
    # 资源错误 (3xxx)
    "ERR_3000": {
        "en": "Requested resource not found",
        "zh-CN": "请求的资源不存在",
        "zh-TW": "請求的資源不存在",
        "ja": "要求されたリソースが見つかりません"
    },
    "ERR_3001": {
        "en": "Resource already exists",
        "zh-CN": "资源已存在",
        "zh-TW": "資源已存在",
        "ja": "リソースは既に存在します"
    },
    "ERR_3002": {
        "en": "Resource is currently locked",
        "zh-CN": "资源当前已锁定",
        "zh-TW": "資源當前已鎖定",
        "ja": "リソースは現在ロックされています"
    },
    
    # 用户错误 (4xxx)
    "ERR_4000": {
        "en": "User not found",
        "zh-CN": "用户不存在",
        "zh-TW": "用戶不存在",
        "ja": "ユーザーが見つかりません"
    },
    "ERR_4001": {
        "en": "User with this email or username already exists",
        "zh-CN": "该邮箱或用户名的用户已存在",
        "zh-TW": "該郵箱或用戶名的用戶已存在",
        "ja": "このメールアドレスまたはユーザー名は既に使用されています"
    },
    "ERR_4002": {
        "en": "User account is inactive",
        "zh-CN": "用户账户已停用",
        "zh-TW": "用戶賬戶已停用",
        "ja": "ユーザーアカウントは無効です"
    },
    "ERR_4003": {
        "en": "Email address not verified",
        "zh-CN": "邮箱地址未验证",
        "zh-TW": "郵箱地址未驗證",
        "ja": "メールアドレスが確認されていません"
    },
    
    # 技能错误 (5xxx)
    "ERR_5000": {
        "en": "Skill not found",
        "zh-CN": "技能不存在",
        "zh-TW": "技能不存在",
        "ja": "スキルが見つかりません"
    },
    "ERR_5001": {
        "en": "Skill execution failed",
        "zh-CN": "技能执行失败",
        "zh-TW": "技能執行失敗",
        "ja": "スキルの実行に失敗しました"
    },
    "ERR_5002": {
        "en": "You don't have permission to access this skill",
        "zh-CN": "您没有权限访问此技能",
        "zh-TW": "您沒有權限訪問此技能",
        "ja": "このスキルにアクセスする権限がありません"
    },
    "ERR_5003": {
        "en": "Skill version conflict detected",
        "zh-CN": "检测到技能版本冲突",
        "zh-TW": "檢測到技能版本衝突",
        "ja": "スキルのバージョン競合が検出されました"
    },
    
    # 会话错误 (6xxx)
    "ERR_6000": {
        "en": "Session not found",
        "zh-CN": "会话不存在",
        "zh-TW": "會話不存在",
        "ja": "セッションが見つかりません"
    },
    "ERR_6001": {
        "en": "Session is inactive",
        "zh-CN": "会话已失效",
        "zh-TW": "會話已失效",
        "ja": "セッションは無効です"
    },
    "ERR_6002": {
        "en": "Maximum number of sessions exceeded",
        "zh-CN": "已达到最大会话数限制",
        "zh-TW": "已達到最大會話數限制",
        "ja": "セッションの最大数を超えました"
    },
    
    # 文件错误 (7xxx)
    "ERR_7000": {
        "en": "File not found",
        "zh-CN": "文件不存在",
        "zh-TW": "檔案不存在",
        "ja": "ファイルが見つかりません"
    },
    "ERR_7001": {
        "en": "File size exceeds maximum allowed",
        "zh-CN": "文件大小超过限制",
        "zh-TW": "檔案大小超過限制",
        "ja": "ファイルサイズが上限を超えています"
    },
    "ERR_7002": {
        "en": "File type not allowed",
        "zh-CN": "不允许的文件类型",
        "zh-TW": "不允許的檔案類型",
        "ja": "許可されていないファイル形式です"
    },
    "ERR_7003": {
        "en": "File upload failed",
        "zh-CN": "文件上传失败",
        "zh-TW": "檔案上傳失敗",
        "ja": "ファイルのアップロードに失敗しました"
    },
    
    # 数据库错误 (8xxx)
    "ERR_8000": {
        "en": "Database error occurred",
        "zh-CN": "数据库错误",
        "zh-TW": "資料庫錯誤",
        "ja": "データベースエラーが発生しました"
    },
    "ERR_8001": {
        "en": "Unable to connect to database",
        "zh-CN": "无法连接到数据库",
        "zh-TW": "無法連接到資料庫",
        "ja": "データベースに接続できません"
    },
    "ERR_8002": {
        "en": "Database query failed",
        "zh-CN": "数据库查询失败",
        "zh-TW": "資料庫查詢失敗",
        "ja": "データベースクエリに失敗しました"
    },
    
    # 外部服务错误 (9xxx)
    "ERR_9000": {
        "en": "External service error",
        "zh-CN": "外部服务错误",
        "zh-TW": "外部服務錯誤",
        "ja": "外部サービスエラー"
    },
    "ERR_9001": {
        "en": "Cache service unavailable",
        "zh-CN": "缓存服务不可用",
        "zh-TW": "緩存服務不可用",
        "ja": "キャッシュサービスが利用できません"
    },
    "ERR_9002": {
        "en": "Git operation failed",
        "zh-CN": "Git操作失败",
        "zh-TW": "Git操作失敗",
        "ja": "Git操作に失敗しました"
    },
    "ERR_9003": {
        "en": "Container operation failed",
        "zh-CN": "容器操作失败",
        "zh-TW": "容器操作失敗",
        "ja": "コンテナ操作に失敗しました"
    },
}


def get_message(
    error_code: str,
    language: Optional[str] = None,
    fallback_to_code: bool = False
) -> str:
    """
    获取指定语言的错误消息
    
    Args:
        error_code: 错误码 (如 "ERR_1001")
        language: 语言代码 (如 "zh-CN")，默认使用英语
        fallback_to_code: 如果消息不存在，是否返回错误码
    
    Returns:
        本地化的错误消息
    """
    # 标准化语言代码
    if language:
        language = language.lower().replace("_", "-")
    else:
        language = DEFAULT_LANGUAGE.value
    
    # 获取消息字典
    messages = ERROR_MESSAGES.get(error_code)
    if not messages:
        logger.warning(f"Unknown error code: {error_code}")
        return error_code if fallback_to_code else f"Unknown error: {error_code}"
    
    # 尝试获取指定语言的消息
    message = messages.get(language)
    if message:
        return message
    
    # 回退到英语
    message = messages.get(DEFAULT_LANGUAGE.value)
    if message:
        return message
    
    # 回退到第一个可用的语言
    if messages:
        return next(iter(messages.values()))
    
    return error_code if fallback_to_code else f"Error: {error_code}"


def get_supported_languages() -> list:
    """获取支持的语言列表"""
    return [lang.value for lang in Language]


class I18n:
    """国际化帮助类"""
    
    def __init__(self, default_language: str = DEFAULT_LANGUAGE.value):
        self.default_language = default_language
    
    def get(self, error_code: str, language: Optional[str] = None) -> str:
        """获取本地化消息"""
        return get_message(error_code, language or self.default_language)
    
    def get_with_fallback(self, error_code: str, language: Optional[str] = None) -> str:
        """获取本地化消息，不存在时返回错误码"""
        return get_message(error_code, language or self.default_language, fallback_to_code=True)


# 全局 i18n 实例
i18n = I18n()
