"""
Pydantic schemas
"""
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse,
    SessionMessage, SessionConfig
)
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse
from app.schemas.skill_version import (
    VersionCreate, VersionRestore, VersionCompare,
    VersionResponse, VersionDetailResponse, VersionListResponse,
    VersionCompareResponse, VersionRestoreResponse, RepoStatusResponse,
    BranchResponse, BranchCreate, BranchSwitch
)
from app.schemas.skills_hub import (
    SkillPublishRequest, PublishedSkillResponse,
    SkillPackageResponse, UploadResponse,
    VersionCreateRequest as HubVersionCreateRequest,
    VersionListResponse as HubVersionListResponse,
    PermissionGrantRequest, PermissionResponse,
    SkillHubListResponse, SkillHubSearchRequest
)
from app.schemas.review import (
    ReviewCreateRequest, ReviewUpdateRequest, ReviewResponse, ReviewListResponse,
    RatingRequest, RatingResponse, RatingStatsResponse,
    BookmarkCreateRequest, BookmarkUpdateRequest, BookmarkResponse, BookmarkListResponse
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "SessionCreate", "SessionUpdate", "SessionResponse", 
    "SessionMessage", "SessionConfig",
    "SkillCreate", "SkillUpdate", "SkillResponse",
    # Version management
    "VersionCreate", "VersionRestore", "VersionCompare",
    "VersionResponse", "VersionDetailResponse", "VersionListResponse",
    "VersionCompareResponse", "VersionRestoreResponse", "RepoStatusResponse",
    "BranchResponse", "BranchCreate", "BranchSwitch",
    # Skills Hub
    "SkillPublishRequest", "PublishedSkillResponse",
    "SkillPackageResponse", "UploadResponse",
    "HubVersionCreateRequest", "HubVersionListResponse",
    "PermissionGrantRequest", "PermissionResponse",
    "SkillHubListResponse", "SkillHubSearchRequest",
    # Review, Rating, Bookmark
    "ReviewCreateRequest", "ReviewUpdateRequest", "ReviewResponse", "ReviewListResponse",
    "RatingRequest", "RatingResponse", "RatingStatsResponse",
    "BookmarkCreateRequest", "BookmarkUpdateRequest", "BookmarkResponse", "BookmarkListResponse"
]
