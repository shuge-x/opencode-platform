"""
Git 服务 - 技能版本管理
使用 GitPython 操作 Git 仓库
"""
import os
import shutil
import tempfile
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from git import Repo, GitCommandError, InvalidGitRepositoryError
from git.objects.commit import Commit
from git.diff import Diff

# 线程池用于异步执行 Git 操作
_executor = ThreadPoolExecutor(max_workers=4)


class GitService:
    """Git 操作服务"""
    
    def __init__(self, base_path: str = "/tmp/skill_repos"):
        """
        初始化 Git 服务
        
        Args:
            base_path: Git 仓库存储的基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_repo_path(self, skill_id: int) -> Path:
        """获取技能仓库路径"""
        return self.base_path / f"skill_{skill_id}"
    
    def _run_in_executor(self, func, *args, **kwargs):
        """在线程池中执行同步函数"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(_executor, func, *args, **kwargs)
    
    def _init_repo_sync(self, skill_id: int, initial_files: Optional[Dict[str, str]] = None) -> str:
        """同步初始化仓库"""
        repo_path = self._get_repo_path(skill_id)
        
        # 如果仓库已存在，直接返回
        if repo_path.exists():
            try:
                Repo(repo_path)
                return str(repo_path)
            except InvalidGitRepositoryError:
                shutil.rmtree(repo_path)
        
        # 创建仓库目录
        repo_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Git 仓库
        repo = Repo.init(repo_path)
        
        # 配置 Git 用户
        config = repo.config_writer()
        config.set_value("user", "name", "OpenCode Bot")
        config.set_value("user", "email", "bot@opencode.ai")
        config.release()
        
        # 创建初始文件
        if initial_files:
            for filename, content in initial_files.items():
                file_path = repo_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # 提交初始文件
            repo.index.add(list(initial_files.keys()))
            repo.index.commit("Initial commit")
        
        return str(repo_path)
    
    async def init_repo(self, skill_id: int, initial_files: Optional[Dict[str, str]] = None) -> str:
        """
        初始化技能的 Git 仓库
        
        Args:
            skill_id: 技能 ID
            initial_files: 初始文件 {filename: content}
        
        Returns:
            仓库路径
        """
        return await self._run_in_executor(
            self._init_repo_sync, skill_id, initial_files
        )
    
    def _commit_sync(
        self, 
        skill_id: int, 
        message: str, 
        files: Optional[Dict[str, str]] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """同步提交变更"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        # 更新或创建文件
        if files:
            for filename, content in files.items():
                file_path = repo_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                repo.index.add([filename])
        
        # 检查是否有变更
        if not repo.index.diff("HEAD"):
            # 检查未跟踪的文件
            untracked = repo.untracked_files
            if not untracked and not files:
                return {
                    "success": False,
                    "message": "No changes to commit"
                }
            if untracked:
                repo.index.add(untracked)
        
        # 设置作者信息
        if author_name and author_email:
            commit = repo.index.commit(
                message,
                author=f"{author_name} <{author_email}>",
                committer=f"{author_name} <{author_email}>"
            )
        else:
            commit = repo.index.commit(message)
        
        return {
            "success": True,
            "commit_hash": commit.hexsha,
            "message": message,
            "author": commit.author.name,
            "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat()
        }
    
    async def commit(
        self, 
        skill_id: int, 
        message: str, 
        files: Optional[Dict[str, str]] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交变更
        
        Args:
            skill_id: 技能 ID
            message: 提交信息
            files: 要提交的文件 {filename: content}
            author_name: 作者名称
            author_email: 作者邮箱
        
        Returns:
            提交结果
        """
        return await self._run_in_executor(
            self._commit_sync, skill_id, message, files, author_name, author_email
        )
    
    def _get_history_sync(
        self, 
        skill_id: int, 
        branch: str = "main",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """同步获取版本历史"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        commits = []
        try:
            # 获取提交历史
            for i, commit in enumerate(repo.iter_commits(branch)):
                if i < offset:
                    continue
                if i >= offset + limit:
                    break
                
                commits.append({
                    "commit_hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": {
                        "name": commit.author.name,
                        "email": commit.author.email
                    },
                    "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                    "parents": [p.hexsha for p in commit.parents]
                })
        except GitCommandError:
            pass
        
        return commits
    
    async def get_history(
        self, 
        skill_id: int, 
        branch: str = "main",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取版本历史
        
        Args:
            skill_id: 技能 ID
            branch: 分支名称
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            版本历史列表
        """
        return await self._run_in_executor(
            self._get_history_sync, skill_id, branch, limit, offset
        )
    
    def _get_commit_sync(self, skill_id: int, commit_hash: str) -> Optional[Dict[str, Any]]:
        """同步获取单个提交详情"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            commit = repo.commit(commit_hash)
            
            # 获取文件变更
            file_changes = []
            if commit.parents:
                # 与父提交对比
                parent = commit.parents[0]
                diffs = parent.diff(commit)
                
                for diff in diffs:
                    file_changes.append({
                        "file_path": diff.a_path or diff.b_path,
                        "change_type": diff.change_type,
                        "old_file": diff.a_path,
                        "new_file": diff.b_path
                    })
            else:
                # 初始提交，获取所有文件
                for blob in commit.tree.traverse():
                    if blob.type == 'blob':
                        file_changes.append({
                            "file_path": blob.path,
                            "change_type": "A",
                            "old_file": None,
                            "new_file": blob.path
                        })
            
            return {
                "commit_hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": {
                    "name": commit.author.name,
                    "email": commit.author.email
                },
                "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "parents": [p.hexsha for p in commit.parents],
                "file_changes": file_changes
            }
        except GitCommandError:
            return None
    
    async def get_commit(self, skill_id: int, commit_hash: str) -> Optional[Dict[str, Any]]:
        """
        获取单个提交详情
        
        Args:
            skill_id: 技能 ID
            commit_hash: 提交哈希
        
        Returns:
            提交详情
        """
        return await self._run_in_executor(
            self._get_commit_sync, skill_id, commit_hash
        )
    
    def _get_file_at_commit_sync(self, skill_id: int, commit_hash: str, file_path: str) -> Optional[str]:
        """同步获取指定版本的文件内容"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            commit = repo.commit(commit_hash)
            blob = commit.tree[file_path]
            return blob.data_stream.read().decode('utf-8')
        except (KeyError, GitCommandError):
            return None
    
    async def get_file_at_commit(self, skill_id: int, commit_hash: str, file_path: str) -> Optional[str]:
        """
        获取指定版本的文件内容
        
        Args:
            skill_id: 技能 ID
            commit_hash: 提交哈希
            file_path: 文件路径
        
        Returns:
            文件内容
        """
        return await self._run_in_executor(
            self._get_file_at_commit_sync, skill_id, commit_hash, file_path
        )
    
    def _compare_commits_sync(
        self, 
        skill_id: int, 
        from_commit: str, 
        to_commit: str
    ) -> Dict[str, Any]:
        """同步对比两个版本"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            from_c = repo.commit(from_commit)
            to_c = repo.commit(to_commit)
            
            # 获取差异
            diffs = from_c.diff(to_c)
            
            file_diffs = []
            for diff in diffs:
                diff_data = {
                    "file_path": diff.a_path or diff.b_path,
                    "change_type": diff.change_type,
                    "old_file": diff.a_path,
                    "new_file": diff.b_path,
                }
                
                # 生成 diff 格式
                try:
                    diff_data["diff"] = diff.diff.decode('utf-8') if diff.diff else ""
                except:
                    diff_data["diff"] = ""
                
                file_diffs.append(diff_data)
            
            return {
                "from_commit": {
                    "hash": from_c.hexsha,
                    "short_hash": from_c.hexsha[:7],
                    "message": from_c.message.strip(),
                    "timestamp": datetime.fromtimestamp(from_c.committed_date).isoformat()
                },
                "to_commit": {
                    "hash": to_c.hexsha,
                    "short_hash": to_c.hexsha[:7],
                    "message": to_c.message.strip(),
                    "timestamp": datetime.fromtimestamp(to_c.committed_date).isoformat()
                },
                "files_changed": len(file_diffs),
                "diffs": file_diffs
            }
        except GitCommandError as e:
            return {
                "error": str(e),
                "from_commit": from_commit,
                "to_commit": to_commit
            }
    
    async def compare_commits(
        self, 
        skill_id: int, 
        from_commit: str, 
        to_commit: str
    ) -> Dict[str, Any]:
        """
        对比两个版本
        
        Args:
            skill_id: 技能 ID
            from_commit: 源提交哈希
            to_commit: 目标提交哈希
        
        Returns:
            版本差异
        """
        return await self._run_in_executor(
            self._compare_commits_sync, skill_id, from_commit, to_commit
        )
    
    def _restore_to_commit_sync(self, skill_id: int, commit_hash: str) -> Dict[str, Any]:
        """同步恢复到指定版本"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            # 获取当前 HEAD
            current_commit = repo.head.commit
            
            # 硬重置到指定提交
            repo.git.reset('--hard', commit_hash)
            
            return {
                "success": True,
                "restored_to": commit_hash,
                "previous_commit": current_commit.hexsha,
                "message": f"Restored to commit {commit_hash[:7]}"
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_to_commit(self, skill_id: int, commit_hash: str) -> Dict[str, Any]:
        """
        恢复到指定版本
        
        Args:
            skill_id: 技能 ID
            commit_hash: 目标提交哈希
        
        Returns:
            恢复结果
        """
        return await self._run_in_executor(
            self._restore_to_commit_sync, skill_id, commit_hash
        )
    
    def _create_branch_sync(self, skill_id: int, branch_name: str, from_commit: Optional[str] = None) -> Dict[str, Any]:
        """同步创建分支"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            if from_commit:
                repo.create_head(branch_name, from_commit)
            else:
                repo.create_head(branch_name)
            
            return {
                "success": True,
                "branch_name": branch_name,
                "message": f"Branch '{branch_name}' created"
            }
        except GitCommandError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_branch(
        self, 
        skill_id: int, 
        branch_name: str, 
        from_commit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建分支
        
        Args:
            skill_id: 技能 ID
            branch_name: 分支名称
            from_commit: 从指定提交创建
        
        Returns:
            创建结果
        """
        return await self._run_in_executor(
            self._create_branch_sync, skill_id, branch_name, from_commit
        )
    
    def _list_branches_sync(self, skill_id: int) -> List[Dict[str, Any]]:
        """同步获取分支列表"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        branches = []
        for branch in repo.heads:
            branches.append({
                "name": branch.name,
                "commit_hash": branch.commit.hexsha,
                "is_current": branch == repo.active_branch
            })
        
        return branches
    
    async def list_branches(self, skill_id: int) -> List[Dict[str, Any]]:
        """
        获取分支列表
        
        Args:
            skill_id: 技能 ID
        
        Returns:
            分支列表
        """
        return await self._run_in_executor(
            self._list_branches_sync, skill_id
        )
    
    def _switch_branch_sync(self, skill_id: int, branch_name: str) -> Dict[str, Any]:
        """同步切换分支"""
        repo_path = self._get_repo_path(skill_id)
        repo = Repo(repo_path)
        
        try:
            repo.heads[branch_name].checkout()
            
            return {
                "success": True,
                "branch": branch_name,
                "commit_hash": repo.head.commit.hexsha,
                "message": f"Switched to branch '{branch_name}'"
            }
        except (GitCommandError, IndexError) as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def switch_branch(self, skill_id: int, branch_name: str) -> Dict[str, Any]:
        """
        切换分支
        
        Args:
            skill_id: 技能 ID
            branch_name: 分支名称
        
        Returns:
            切换结果
        """
        return await self._run_in_executor(
            self._switch_branch_sync, skill_id, branch_name
        )
    
    def _get_status_sync(self, skill_id: int) -> Dict[str, Any]:
        """同步获取仓库状态"""
        repo_path = self._get_repo_path(skill_id)
        
        try:
            repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            return {
                "initialized": False,
                "message": "Repository not initialized"
            }
        
        # 获取未跟踪的文件
        untracked = repo.untracked_files
        
        # 获取已修改的文件
        modified = []
        for item in repo.index.diff(None):
            modified.append(item.a_path)
        
        # 获取已暂存的文件
        staged = []
        if repo.head.is_valid():
            for item in repo.index.diff(repo.head.commit):
                staged.append(item.a_path)
        else:
            staged = [item.a_path for item in repo.index.diff(None)]
        
        return {
            "initialized": True,
            "current_branch": repo.active_branch.name if repo.head.is_valid() else None,
            "current_commit": repo.head.commit.hexsha if repo.head.is_valid() else None,
            "is_dirty": repo.is_dirty(),
            "untracked_files": untracked,
            "modified_files": modified,
            "staged_files": staged
        }
    
    async def get_status(self, skill_id: int) -> Dict[str, Any]:
        """
        获取仓库状态
        
        Args:
            skill_id: 技能 ID
        
        Returns:
            仓库状态
        """
        return await self._run_in_executor(
            self._get_status_sync, skill_id
        )
    
    def _delete_repo_sync(self, skill_id: int) -> bool:
        """同步删除仓库"""
        repo_path = self._get_repo_path(skill_id)
        
        if repo_path.exists():
            shutil.rmtree(repo_path)
            return True
        return False
    
    async def delete_repo(self, skill_id: int) -> bool:
        """
        删除仓库
        
        Args:
            skill_id: 技能 ID
        
        Returns:
            是否删除成功
        """
        return await self._run_in_executor(
            self._delete_repo_sync, skill_id
        )


# 单例实例
git_service = GitService()
