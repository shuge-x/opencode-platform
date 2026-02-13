"""
文件管理路由
"""
import os
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter()

# 文件存储目录
UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件
    """
    # 检查文件大小（50MB限制）
    max_size = 50 * 1024 * 1024
    content = await file.read()

    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 50MB)"
        )

    # 生成文件ID
    file_id = str(uuid.uuid4())

    # 用户目录
    user_dir = os.path.join(UPLOAD_DIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(user_dir, file_id)
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "uploaded_at": datetime.utcnow().isoformat()
    }


@router.get("")
async def list_files(
    current_user: User = Depends(get_current_user)
):
    """
    列出文件
    """
    user_dir = os.path.join(UPLOAD_DIR, current_user.id)

    if not os.path.exists(user_dir):
        return []

    files = []
    for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        stat = os.stat(file_path)

        files.append({
            "file_id": filename,
            "size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return files


@router.get("/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载文件
    """
    file_path = os.path.join(UPLOAD_DIR, current_user.id, file_id)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(
        file_path,
        filename=file_id,
        media_type="application/octet-stream"
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除文件
    """
    file_path = os.path.join(UPLOAD_DIR, current_user.id, file_id)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    os.remove(file_path)

    return None
