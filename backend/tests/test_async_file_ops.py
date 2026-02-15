"""
异步文件操作测试
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.async_file_ops import (
    AsyncFileOperations,
    read_file,
    write_file,
    delete_file,
    copy_file,
    move_file,
    list_files,
    create_directory,
    delete_directory,
    get_file_info,
    file_exists
)


@pytest.mark.asyncio
class TestAsyncFileOperations:
    """异步文件操作测试"""
    
    async def test_read_file_text(self):
        """测试读取文本文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_file = f.name
        
        try:
            content = await read_file(temp_file)
            assert content == "Test content"
        finally:
            os.unlink(temp_file)
    
    async def test_read_file_binary(self):
        """测试读取二进制文件"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Binary content")
            temp_file = f.name
        
        try:
            content = await read_file(temp_file, mode='rb')
            assert content == b"Binary content"
        finally:
            os.unlink(temp_file)
    
    async def test_read_file_not_found(self):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            await read_file("/nonexistent/file.txt")
    
    async def test_write_file_text(self):
        """测试写入文本文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            
            bytes_written = await write_file(file_path, "Test content")
            
            assert bytes_written > 0
            assert os.path.exists(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            assert content == "Test content"
    
    async def test_write_file_creates_directory(self):
        """测试写入文件时自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "subdir", "test.txt")
            
            await write_file(file_path, "Test content")
            
            assert os.path.exists(file_path)
    
    async def test_write_file_append(self):
        """测试追加写入文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Initial content\n")
            temp_file = f.name
        
        try:
            await write_file(temp_file, "Appended content", mode='a')
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            assert "Initial content" in content
            assert "Appended content" in content
        finally:
            os.unlink(temp_file)
    
    async def test_delete_file(self):
        """测试删除文件"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Test")
            temp_file = f.name
        
        assert os.path.exists(temp_file)
        
        result = await delete_file(temp_file)
        
        assert result is True
        assert not os.path.exists(temp_file)
    
    async def test_delete_file_not_found(self):
        """测试删除不存在的文件"""
        result = await delete_file("/nonexistent/file.txt")
        assert result is False
    
    async def test_copy_file(self):
        """测试复制文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "source.txt")
            dst_file = os.path.join(temp_dir, "dest.txt")
            
            # 创建源文件
            with open(src_file, 'w') as f:
                f.write("Source content")
            
            bytes_copied = await copy_file(src_file, dst_file)
            
            assert bytes_copied > 0
            assert os.path.exists(dst_file)
            
            with open(dst_file, 'r') as f:
                content = f.read()
            assert content == "Source content"
    
    async def test_copy_file_creates_directory(self):
        """测试复制文件时自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "source.txt")
            dst_file = os.path.join(temp_dir, "subdir", "dest.txt")
            
            # 创建源文件
            with open(src_file, 'w') as f:
                f.write("Source content")
            
            await copy_file(src_file, dst_file)
            
            assert os.path.exists(dst_file)
    
    async def test_move_file(self):
        """测试移动文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "source.txt")
            dst_file = os.path.join(temp_dir, "dest.txt")
            
            # 创建源文件
            with open(src_file, 'w') as f:
                f.write("Content to move")
            
            result = await move_file(src_file, dst_file)
            
            assert result is True
            assert not os.path.exists(src_file)
            assert os.path.exists(dst_file)
            
            with open(dst_file, 'r') as f:
                content = f.read()
            assert content == "Content to move"
    
    async def test_list_files(self):
        """测试列出文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一些测试文件
            for i in range(3):
                file_path = os.path.join(temp_dir, f"test{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Content {i}")
            
            files = await list_files(temp_dir, pattern="*.txt")
            
            assert len(files) == 3
            assert all(isinstance(f, Path) for f in files)
    
    async def test_list_files_recursive(self):
        """测试递归列出文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建子目录和文件
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            
            file1 = os.path.join(temp_dir, "test1.txt")
            file2 = os.path.join(subdir, "test2.txt")
            
            with open(file1, 'w') as f:
                f.write("Content 1")
            with open(file2, 'w') as f:
                f.write("Content 2")
            
            files = await list_files(temp_dir, pattern="*.txt", recursive=True)
            
            assert len(files) == 2
    
    async def test_create_directory(self):
        """测试创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new", "nested", "dir")
            
            result = await create_directory(new_dir)
            
            assert result is True
            assert os.path.exists(new_dir)
    
    async def test_delete_directory(self):
        """测试删除目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_to_delete = os.path.join(temp_dir, "to_delete")
            os.makedirs(dir_to_delete)
            
            # 添加一些文件
            file_path = os.path.join(dir_to_delete, "file.txt")
            with open(file_path, 'w') as f:
                f.write("Content")
            
            result = await delete_directory(dir_to_delete)
            
            assert result is True
            assert not os.path.exists(dir_to_delete)
    
    async def test_delete_directory_not_found(self):
        """测试删除不存在的目录"""
        result = await delete_directory("/nonexistent/directory")
        assert result is False
    
    async def test_get_file_info(self):
        """测试获取文件信息"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content for file info")
            temp_file = f.name
        
        try:
            info = await get_file_info(temp_file)
            
            assert info["name"] == os.path.basename(temp_file)
            assert info["extension"] == ".txt"
            assert info["size"] > 0
            assert info["is_file"] is True
            assert info["is_directory"] is False
            assert "created_at" in info
            assert "modified_at" in info
        finally:
            os.unlink(temp_file)
    
    async def test_file_exists_true(self):
        """测试文件存在检查 - 存在"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Test")
            temp_file = f.name
        
        try:
            exists = await file_exists(temp_file)
            assert exists is True
        finally:
            os.unlink(temp_file)
    
    async def test_file_exists_false(self):
        """测试文件存在检查 - 不存在"""
        exists = await file_exists("/nonexistent/file.txt")
        assert exists is False
    
    async def test_file_operations_with_path_object(self):
        """测试使用Path对象的操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            # 写入
            await write_file(file_path, "Test content")
            
            # 读取
            content = await read_file(file_path)
            assert content == "Test content"
            
            # 检查存在
            exists = await file_exists(file_path)
            assert exists is True
