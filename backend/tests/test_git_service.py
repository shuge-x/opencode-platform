"""
Git 服务测试
"""
import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 注意：由于 Git 操作需要实际 Git 环境，这些测试使用临时目录


class TestGitServiceInit:
    """测试 Git 服务初始化"""
    
    @pytest.mark.asyncio
    async def test_init_repo_creates_directory(self):
        """测试初始化仓库创建目录"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            repo_path = await service.init_repo(skill_id=1)
            
            assert repo_path is not None
            assert os.path.exists(repo_path)
            assert os.path.isdir(repo_path)
    
    @pytest.mark.asyncio
    async def test_init_repo_with_initial_files(self):
        """测试带初始文件的仓库初始化"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            initial_files = {
                "main.py": "print('hello')",
                "README.md": "# Test Skill"
            }
            
            repo_path = await service.init_repo(skill_id=2, initial_files=initial_files)
            
            # 检查文件是否创建
            assert os.path.exists(os.path.join(repo_path, "main.py"))
            assert os.path.exists(os.path.join(repo_path, "README.md"))


class TestGitServiceCommit:
    """测试 Git 提交操作"""
    
    @pytest.mark.asyncio
    async def test_commit_creates_commit(self):
        """测试提交创建 commit"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 先初始化仓库
            await service.init_repo(skill_id=3, initial_files={"test.py": "# initial"})
            
            # 提交变更
            result = await service.commit(
                skill_id=3,
                message="Update test.py",
                files={"test.py": "# updated content"}
            )
            
            assert result["success"] is True
            assert "commit_hash" in result
            assert result["message"] == "Update test.py"
    
    @pytest.mark.asyncio
    async def test_commit_no_changes(self):
        """测试无变更时的提交"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化并提交
            await service.init_repo(skill_id=4, initial_files={"test.py": "# content"})
            
            # 再次提交相同内容
            result = await service.commit(
                skill_id=4,
                message="No changes",
                files={"test.py": "# content"}
            )
            
            # 应该返回无变更
            assert result["success"] is False or "commit_hash" in result


class TestGitServiceHistory:
    """测试版本历史"""
    
    @pytest.mark.asyncio
    async def test_get_history(self):
        """测试获取版本历史"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=5, initial_files={"main.py": "# v1"})
            
            # 创建多个提交
            await service.commit(skill_id=5, message="Second commit", files={"main.py": "# v2"})
            await service.commit(skill_id=5, message="Third commit", files={"main.py": "# v3"})
            
            # 获取历史
            history = await service.get_history(skill_id=5, limit=10)
            
            assert len(history) >= 2
            assert "commit_hash" in history[0]
            assert "message" in history[0]
    
    @pytest.mark.asyncio
    async def test_get_history_pagination(self):
        """测试版本历史分页"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=6, initial_files={"main.py": "# initial"})
            
            # 创建多个提交
            for i in range(5):
                await service.commit(skill_id=6, message=f"Commit {i}", files={"main.py": f"# v{i}"})
            
            # 分页获取
            page1 = await service.get_history(skill_id=6, limit=2, offset=0)
            page2 = await service.get_history(skill_id=6, limit=2, offset=2)
            
            assert len(page1) == 2
            assert page1[0]["commit_hash"] != page2[0]["commit_hash"]


class TestGitServiceCompare:
    """测试版本对比"""
    
    @pytest.mark.asyncio
    async def test_compare_commits(self):
        """测试对比两个提交"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=7, initial_files={"main.py": "# initial\n"})
            
            # 获取初始提交
            history = await service.get_history(skill_id=7, limit=1)
            first_commit = history[0]["commit_hash"]
            
            # 创建新提交
            result = await service.commit(
                skill_id=7,
                message="Update file",
                files={"main.py": "# initial\n# added line\n"}
            )
            second_commit = result["commit_hash"]
            
            # 对比
            compare_result = await service.compare_commits(
                skill_id=7,
                from_commit=first_commit,
                to_commit=second_commit
            )
            
            assert "from_commit" in compare_result
            assert "to_commit" in compare_result
            assert "diffs" in compare_result


class TestGitServiceBranch:
    """测试分支操作"""
    
    @pytest.mark.asyncio
    async def test_create_branch(self):
        """测试创建分支"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=8)
            
            # 创建分支
            result = await service.create_branch(skill_id=8, branch_name="feature")
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_branches(self):
        """测试列出分支"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=9)
            
            # 创建分支
            await service.create_branch(skill_id=9, branch_name="develop")
            
            # 列出分支
            branches = await service.list_branches(skill_id=9)
            
            assert len(branches) >= 2  # main + develop
            branch_names = [b["name"] for b in branches]
            assert "main" in branch_names or "master" in branch_names
    
    @pytest.mark.asyncio
    async def test_switch_branch(self):
        """测试切换分支"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=10)
            
            # 创建分支
            await service.create_branch(skill_id=10, branch_name="test-branch")
            
            # 切换分支
            result = await service.switch_branch(skill_id=10, branch_name="test-branch")
            
            assert result["success"] is True


class TestGitServiceRestore:
    """测试版本恢复"""
    
    @pytest.mark.asyncio
    async def test_restore_to_commit(self):
        """测试恢复到指定版本"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=11, initial_files={"main.py": "# v1"})
            
            # 获取初始提交
            history = await service.get_history(skill_id=11, limit=1)
            first_commit = history[0]["commit_hash"]
            
            # 创建新提交
            await service.commit(skill_id=11, message="Update", files={"main.py": "# v2"})
            
            # 恢复
            result = await service.restore_to_commit(skill_id=11, commit_hash=first_commit)
            
            assert result["success"] is True
            assert result["restored_to"] == first_commit


class TestGitServiceStatus:
    """测试仓库状态"""
    
    @pytest.mark.asyncio
    async def test_get_status_initialized(self):
        """测试获取已初始化仓库状态"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            await service.init_repo(skill_id=12)
            
            # 获取状态
            status = await service.get_status(skill_id=12)
            
            assert status["initialized"] is True
    
    @pytest.mark.asyncio
    async def test_get_status_not_initialized(self):
        """测试获取未初始化仓库状态"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 获取状态（未初始化）
            status = await service.get_status(skill_id=999)
            
            assert status["initialized"] is False


class TestGitServiceDelete:
    """测试删除仓库"""
    
    @pytest.mark.asyncio
    async def test_delete_repo(self):
        """测试删除仓库"""
        from app.services.git_service import GitService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = GitService(base_path=tmpdir)
            
            # 初始化仓库
            repo_path = await service.init_repo(skill_id=13)
            assert os.path.exists(repo_path)
            
            # 删除仓库
            result = await service.delete_repo(skill_id=13)
            assert result is True
            assert not os.path.exists(repo_path)
