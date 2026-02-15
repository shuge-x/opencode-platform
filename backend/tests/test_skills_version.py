"""
技能版本管理 API 测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
import json


@pytest.fixture
def mock_git_service():
    """Mock git service"""
    with patch('app.api.skills_version.git_service') as mock:
        mock.get_status = AsyncMock(return_value={
            "initialized": True,
            "current_branch": "main",
            "current_commit": "abc1234567890",
            "is_dirty": False,
            "untracked_files": [],
            "modified_files": [],
            "staged_files": []
        })
        mock.init_repo = AsyncMock(return_value="/tmp/skill_repos/skill_1")
        mock.get_history = AsyncMock(return_value=[
            {
                "commit_hash": "abc1234567890abcdef1234567890abcdef1234",
                "short_hash": "abc1234",
                "message": "Initial commit",
                "author": {"name": "Test User", "email": "test@example.com"},
                "timestamp": "2024-02-15T10:00:00",
                "parents": []
            }
        ])
        mock.get_commit = AsyncMock(return_value={
            "commit_hash": "abc1234567890abcdef1234567890abcdef1234",
            "short_hash": "abc1234",
            "message": "Initial commit",
            "author": {"name": "Test User", "email": "test@example.com"},
            "timestamp": "2024-02-15T10:00:00",
            "parents": [],
            "file_changes": [{"file_path": "main.py", "change_type": "A"}]
        })
        mock.commit = AsyncMock(return_value={
            "success": True,
            "commit_hash": "def4567890abcdef1234567890abcdef123456",
            "message": "Add new feature",
            "author": "Test User",
            "timestamp": "2024-02-15T11:00:00"
        })
        mock.restore_to_commit = AsyncMock(return_value={
            "success": True,
            "restored_to": "abc1234567890abcdef1234567890abcdef1234",
            "previous_commit": "def4567890abcdef1234567890abcdef123456",
            "message": "Restored to commit abc1234"
        })
        mock.compare_commits = AsyncMock(return_value={
            "from_commit": {
                "hash": "abc1234567890abcdef1234567890abcdef1234",
                "short_hash": "abc1234",
                "message": "Initial commit",
                "timestamp": "2024-02-15T10:00:00"
            },
            "to_commit": {
                "hash": "def4567890abcdef1234567890abcdef123456",
                "short_hash": "def4567",
                "message": "Add new feature",
                "timestamp": "2024-02-15T11:00:00"
            },
            "files_changed": 1,
            "diffs": [{
                "file_path": "main.py",
                "change_type": "M",
                "old_file": "main.py",
                "new_file": "main.py",
                "diff": "--- main.py\n+++ main.py\n@@ -1,3 +1,5 @@\n+new line"
            }]
        })
        mock.create_branch = AsyncMock(return_value={
            "success": True,
            "message": "Branch 'feature-1' created"
        })
        mock.list_branches = AsyncMock(return_value=[
            {"name": "main", "commit_hash": "abc1234567890abcdef1234567890abcdef1234", "is_current": True}
        ])
        mock.switch_branch = AsyncMock(return_value={
            "success": True,
            "message": "Switched to branch 'main'",
            "commit_hash": "abc1234567890abcdef1234567890abcdef1234"
        })
        mock.get_file_at_commit = AsyncMock(return_value="# Main file\nprint('hello')")
        yield mock


class TestRepoStatus:
    """测试仓库状态 API"""
    
    @pytest.mark.asyncio
    async def test_get_repo_status_initialized(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取已初始化仓库状态"""
        response = await client.get(
            "/api/skills/1/repo/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["initialized"] is True
        assert data["current_branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_get_repo_status_skill_not_found(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取不存在技能的仓库状态"""
        response = await client.get(
            "/api/skills/999/repo/status",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestInitRepo:
    """测试仓库初始化 API"""
    
    @pytest.mark.asyncio
    async def test_init_repo(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试初始化仓库"""
        response = await client.post(
            "/api/skills/1/repo/init",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "repo_path" in data
        mock_git_service.init_repo.assert_called_once()


class TestVersionList:
    """测试版本列表 API"""
    
    @pytest.mark.asyncio
    async def test_list_versions(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取版本列表"""
        response = await client.get(
            "/api/skills/1/versions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    @pytest.mark.asyncio
    async def test_list_versions_with_pagination(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试分页获取版本列表"""
        response = await client.get(
            "/api/skills/1/versions?page=2&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestVersionDetail:
    """测试版本详情 API"""
    
    @pytest.mark.asyncio
    async def test_get_version(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取版本详情"""
        response = await client.get(
            "/api/skills/1/versions/abc1234",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["commit_hash"] == "abc1234567890abcdef1234567890abcdef1234"
        assert data["short_hash"] == "abc1234"
        assert "file_changes" in data


class TestCreateVersion:
    """测试创建版本 API"""
    
    @pytest.mark.asyncio
    async def test_create_version(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试创建新版本"""
        response = await client.post(
            "/api/skills/1/versions",
            headers=auth_headers,
            json={
                "message": "Add new feature",
                "files": {"main.py": "print('hello')"},
                "version_name": "v1.0.0",
                "is_release": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["commit_message"] == "Add new feature"
        mock_git_service.commit.assert_called_once()


class TestRestoreVersion:
    """测试版本回退 API"""
    
    @pytest.mark.asyncio
    async def test_restore_version(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试版本回退"""
        response = await client.post(
            "/api/skills/1/versions/abc1234/restore",
            headers=auth_headers,
            json={"create_backup": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "restored_to" in data
        mock_git_service.restore_to_commit.assert_called_once()


class TestCompareVersions:
    """测试版本对比 API"""
    
    @pytest.mark.asyncio
    async def test_compare_versions(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试对比两个版本"""
        response = await client.post(
            "/api/skills/1/versions/compare",
            headers=auth_headers,
            json={
                "from_commit": "abc1234",
                "to_commit": "def4567"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "from_commit" in data
        assert "to_commit" in data
        assert "diffs" in data
        mock_git_service.compare_commits.assert_called_once()


class TestBranchManagement:
    """测试分支管理 API"""
    
    @pytest.mark.asyncio
    async def test_list_branches(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取分支列表"""
        response = await client.get(
            "/api/skills/1/branches",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_create_branch(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试创建分支"""
        response = await client.post(
            "/api/skills/1/branches",
            headers=auth_headers,
            json={"branch_name": "feature-1"}
        )
        
        assert response.status_code == 201
        mock_git_service.create_branch.assert_called_once()


class TestFileAtVersion:
    """测试获取指定版本文件 API"""
    
    @pytest.mark.asyncio
    async def test_get_file_at_version(self, client: AsyncClient, auth_headers, mock_git_service):
        """测试获取指定版本的文件内容"""
        response = await client.get(
            "/api/skills/1/versions/abc1234/files/main.py",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["file_path"] == "main.py"
