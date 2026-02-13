"""
文件相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class FileBase(BaseModel):
    """文件基础模型"""
    description: Optional[str] = Field(None, description="文件描述")


class FileCreate(FileBase):
    """文件创建模型（上传时使用）"""
    pass


class FileUpdate(BaseModel):
    """文件更新模型"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "updated_file.txt",
                "description": "Updated description"
            }
        }
    )


class FileResponse(BaseModel):
    """文件响应模型"""
    id: int
    filename: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """文件列表响应"""
    items: List[FileResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 10,
                "page": 1,
                "page_size": 20,
                "has_more": False
            }
        }
    )


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: int
    filename: str
    file_size: int
    mime_type: str
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "filename": "document.pdf",
                "file_size": 1024,
                "mime_type": "application/pdf",
                "message": "File uploaded successfully"
            }
        }
    )
