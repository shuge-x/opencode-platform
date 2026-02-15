"""
异步文件操作模块

提供高性能的异步文件读写操作
"""
import aiofiles
import os
from pathlib import Path
from typing import Optional, List, BinaryIO, Union
import logging
import asyncio
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class AsyncFileOperations:
    """异步文件操作工具类"""
    
    @staticmethod
    async def read_file(file_path: Union[str, Path], mode: str = 'r') -> str:
        """
        异步读取文件
        
        Args:
            file_path: 文件路径
            mode: 读取模式 ('r' 或 'rb')
        
        Returns:
            文件内容
        """
        try:
            async with aiofiles.open(file_path, mode=mode) as f:
                content = await f.read()
                logger.debug(f"Successfully read file: {file_path}")
                return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_file(
        file_path: Union[str, Path],
        content: Union[str, bytes],
        mode: str = 'w'
    ) -> int:
        """
        异步写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 写入模式 ('w', 'wb', 'a', 'ab')
        
        Returns:
            写入的字节数
        """
        try:
            # 确保目录存在
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, mode=mode) as f:
                bytes_written = await f.write(content)
                logger.debug(f"Successfully wrote {bytes_written} bytes to: {file_path}")
                return bytes_written
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            raise
    
    @staticmethod
    async def delete_file(file_path: Union[str, Path]) -> bool:
        """
        异步删除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                # 使用线程池执行删除操作
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, path.unlink)
                logger.debug(f"Successfully deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise
    
    @staticmethod
    async def copy_file(
        src_path: Union[str, Path],
        dst_path: Union[str, Path]
    ) -> int:
        """
        异步复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
        
        Returns:
            复制的字节数
        """
        try:
            # 确保目标目录存在
            dst = Path(dst_path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用线程池执行复制
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, str(src_path), str(dst_path))
            
            # 获取文件大小
            file_size = dst.stat().st_size
            logger.debug(f"Successfully copied {file_size} bytes from {src_path} to {dst_path}")
            return file_size
        except Exception as e:
            logger.error(f"Error copying file from {src_path} to {dst_path}: {e}")
            raise
    
    @staticmethod
    async def move_file(
        src_path: Union[str, Path],
        dst_path: Union[str, Path]
    ) -> bool:
        """
        异步移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
        
        Returns:
            是否成功
        """
        try:
            # 确保目标目录存在
            dst = Path(dst_path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用线程池执行移动
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.move, str(src_path), str(dst_path))
            
            logger.debug(f"Successfully moved file from {src_path} to {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving file from {src_path} to {dst_path}: {e}")
            raise
    
    @staticmethod
    async def list_files(
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        异步列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式 (glob格式)
            recursive: 是否递归查找
        
        Returns:
            文件路径列表
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                logger.warning(f"Directory not found: {directory}")
                return []
            
            # 使用线程池执行文件系统操作
            loop = asyncio.get_event_loop()
            
            if recursive:
                files = await loop.run_in_executor(
                    None,
                    lambda: list(dir_path.rglob(pattern))
                )
            else:
                files = await loop.run_in_executor(
                    None,
                    lambda: list(dir_path.glob(pattern))
                )
            
            logger.debug(f"Found {len(files)} files in {directory}")
            return files
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            raise
    
    @staticmethod
    async def create_directory(dir_path: Union[str, Path]) -> bool:
        """
        异步创建目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            是否成功
        """
        try:
            path = Path(dir_path)
            
            # 使用线程池执行创建
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: path.mkdir(parents=True, exist_ok=True)
            )
            
            logger.debug(f"Successfully created directory: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            raise
    
    @staticmethod
    async def delete_directory(dir_path: Union[str, Path]) -> bool:
        """
        异步删除目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            是否成功
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                return False
            
            # 使用线程池执行删除
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shutil.rmtree(str(path))
            )
            
            logger.debug(f"Successfully deleted directory: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")
            raise
    
    @staticmethod
    async def get_file_info(file_path: Union[str, Path]) -> dict:
        """
        异步获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            
            # 使用线程池获取文件信息
            loop = asyncio.get_event_loop()
            stat = await loop.run_in_executor(None, path.stat)
            
            return {
                "path": str(path),
                "name": path.name,
                "extension": path.suffix,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "accessed_at": datetime.fromtimestamp(stat.st_atime),
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise
    
    @staticmethod
    async def file_exists(file_path: Union[str, Path]) -> bool:
        """
        异步检查文件是否存在
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否存在
        """
        try:
            path = Path(file_path)
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, path.exists)
            return exists
        except Exception as e:
            logger.error(f"Error checking file existence for {file_path}: {e}")
            return False


# 便捷函数
async_file_ops = AsyncFileOperations()

# 导出常用函数
read_file = async_file_ops.read_file
write_file = async_file_ops.write_file
delete_file = async_file_ops.delete_file
copy_file = async_file_ops.copy_file
move_file = async_file_ops.move_file
list_files = async_file_ops.list_files
create_directory = async_file_ops.create_directory
delete_directory = async_file_ops.delete_directory
get_file_info = async_file_ops.get_file_info
file_exists = async_file_ops.file_exists
