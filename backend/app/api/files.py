"""
文件管理路由 - 完整实现
"""
import os
import uuid
import mimetypes
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas.file import (
    FileUpdate, FileResponse, FileListResponse, FileUploadResponse
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 文件存储目录
UPLOAD_DIR = os.path.join(getattr(settings, 'BASE_DIR', '/tmp'), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    '.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.doc', '.docx',
    '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.tar', '.gz', '.json',
    '.xml', '.csv', '.md', '.py', '.js', '.java', '.cpp', '.c', '.h',
    '.yaml', '.yml', '.ini', '.cfg', '.log', '.sql', '.sh', '.bat'
}

# 最大文件大小（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文件
    
    - 支持50MB以内的文件
    - 自动检测MIME类型
    - 存储到用户专属目录
    """
    # 检查文件名
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # 检查文件类型
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # 生成唯一文件名
    file_ext = get_file_extension(file.filename)
    stored_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 创建用户目录
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(user_dir, stored_filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 检测MIME类型
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    # 创建数据库记录
    db_file = FileModel(
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime_type,
        description=description
    )
    
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    
    return FileUploadResponse(
        id=db_file.id,
        filename=db_file.filename,
        file_size=db_file.file_size,
        mime_type=db_file.mime_type,
        message="File uploaded successfully"
    )


@router.get("", response_model=FileListResponse)
async def list_files(
    search: Optional[str] = Query(None, description="搜索文件名"),
    mime_type: Optional[str] = Query(None, description="MIME类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出文件
    
    - 支持搜索文件名
    - 支持按MIME类型过滤
    - 支持分页
    """
    # 基础查询
    query = select(FileModel).where(FileModel.user_id == current_user.id)
    
    # 搜索过滤
    if search:
        search_term = f"%{search}%"
        query = query.where(FileModel.filename.ilike(search_term))
    
    # MIME类型过滤
    if mime_type:
        query = query.where(FileModel.mime_type.like(f"{mime_type}%"))
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(FileModel.created_at.desc())
    
    # 执行查询
    result = await db.execute(query)
    files = result.scalars().all()
    
    # 计算是否有更多
    has_more = (offset + len(files)) < total
    
    return FileListResponse(
        items=files,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    下载文件
    
    - 返回原始文件名
    - 自动设置Content-Type
    """
    # 查询文件记录
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user.id
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # 检查文件是否存在
    if not os.path.exists(db_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.filename,
        media_type=db_file.mime_type
    )


@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: int,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    编辑文件元数据
    
    - 更新文件名或描述
    - 不修改文件内容
    """
    # 查询文件记录
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user.id
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # 更新字段
    update_data = file_update.model_dump(exclude_unset=True)
    
    if "filename" in update_data:
        # 检查文件类型
        if not is_allowed_file(update_data["filename"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type"
            )
    
    for field, value in update_data.items():
        setattr(db_file, field, value)
    
    await db.commit()
    await db.refresh(db_file)
    
    return db_file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除文件
    
    - 删除数据库记录
    - 删除物理文件
    """
    # 查询文件记录
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user.id
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    file_path = db_file.file_path
    filename = db_file.filename
    
    # 先删除数据库记录（在事务中）
    try:
        await db.delete(db_file)
        await db.commit()
        logger.info(f"Database record deleted: file_id={file_id}, user_id={current_user.id}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete database record: file_id={file_id}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file record"
        )
    
    # 删除物理文件（数据库记录已删除，即使失败也不回滚）
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Physical file deleted: {file_path}")
        except PermissionError as e:
            logger.warning(f"Permission denied when deleting file: {file_path}, error={e}")
        except OSError as e:
            logger.error(f"Failed to delete physical file: {file_path}, error={e}")
    else:
        logger.warning(f"Physical file not found on disk: {file_path}")
    
    return None
