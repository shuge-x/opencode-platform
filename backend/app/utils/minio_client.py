"""
MinIO 对象存储客户端
"""
import hashlib
import io
from typing import Optional, BinaryIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO客户端封装"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket: {e}")
            raise
    
    async def upload_skill_package(
        self,
        skill_id: int,
        version: str,
        file_data: BinaryIO,
        file_size: int,
        content_type: str = "application/gzip"
    ) -> tuple[str, str]:
        """
        上传技能包到MinIO
        
        Args:
            skill_id: 技能ID
            version: 版本号
            file_data: 文件数据流
            file_size: 文件大小
            content_type: 内容类型
        
        Returns:
            tuple: (object_name, checksum)
        """
        object_name = f"skills/{skill_id}/{version}/package.tar.gz"
        
        try:
            # 计算checksum
            file_data.seek(0)
            content = file_data.read()
            checksum = hashlib.sha256(content).hexdigest()
            
            # 上传到MinIO
            file_data.seek(0)
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                file_size,
                content_type
            )
            
            logger.info(f"Uploaded skill package: {object_name}")
            return object_name, checksum
            
        except S3Error as e:
            logger.error(f"Failed to upload skill package: {e}")
            raise
    
    async def download_skill_package(
        self,
        skill_id: int,
        version: str
    ) -> Optional[io.BytesIO]:
        """
        从MinIO下载技能包
        
        Args:
            skill_id: 技能ID
            version: 版本号
        
        Returns:
            BytesIO: 文件数据流
        """
        object_name = f"skills/{skill_id}/{version}/package.tar.gz"
        
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = io.BytesIO(response.read())
            response.close()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning(f"Skill package not found: {object_name}")
                return None
            logger.error(f"Failed to download skill package: {e}")
            raise
    
    def get_download_url(
        self,
        skill_id: int,
        version: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        获取技能包下载URL（预签名URL）
        
        Args:
            skill_id: 技能ID
            version: 版本号
            expires: URL过期时间
        
        Returns:
            str: 预签名下载URL
        """
        object_name = f"skills/{skill_id}/{version}/package.tar.gz"
        
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise
    
    async def delete_skill_package(
        self,
        skill_id: int,
        version: str
    ) -> bool:
        """
        删除技能包
        
        Args:
            skill_id: 技能ID
            version: 版本号
        
        Returns:
            bool: 是否删除成功
        """
        object_name = f"skills/{skill_id}/{version}/package.tar.gz"
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted skill package: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete skill package: {e}")
            return False
    
    async def verify_integrity(
        self,
        skill_id: int,
        version: str,
        expected_checksum: str
    ) -> bool:
        """
        验证技能包完整性
        
        Args:
            skill_id: 技能ID
            version: 版本号
            expected_checksum: 预期的checksum
        
        Returns:
            bool: 是否通过验证
        """
        file_data = await self.download_skill_package(skill_id, version)
        if not file_data:
            return False
        
        content = file_data.read()
        actual_checksum = hashlib.sha256(content).hexdigest()
        
        return actual_checksum == expected_checksum


# 全局MinIO客户端实例
minio_client = MinIOClient()
