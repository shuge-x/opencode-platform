"""
技能执行沙箱 - 使用 Docker 容器隔离执行

提供安全的技能执行环境，包含完整的资源限制和监控
"""
import docker
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


# 资源限制常量
DEFAULT_TIMEOUT = settings.SKILL_EXECUTION_TIMEOUT
DEFAULT_MEMORY_LIMIT = settings.SKILL_MEMORY_LIMIT
DEFAULT_CPU_QUOTA = settings.SKILL_CPU_QUOTA
MAX_OUTPUT_SIZE = settings.SKILL_MAX_OUTPUT_SIZE
MAX_FILE_SIZE = 10 * 1024 * 1024  # 单文件最大10MB
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 总文件大小最大50MB


class SkillExecutionSandbox:
    """技能执行沙箱"""

    def __init__(self):
        self.client = docker.from_env()
        self.container_timeout = DEFAULT_TIMEOUT
        self.memory_limit = DEFAULT_MEMORY_LIMIT
        self.cpu_quota = DEFAULT_CPU_QUOTA
        self.pids_limit = 100  # 最大进程数
        self.max_output_size = MAX_OUTPUT_SIZE

    def _validate_files(self, files: Dict[str, str]) -> None:
        """验证上传的文件"""
        total_size = 0
        for filename, content in files.items():
            # 检查文件路径安全性
            if ".." in filename or filename.startswith("/"):
                raise ValueError(f"Invalid file path: {filename}")
            
            # 检查文件大小
            file_size = len(content.encode('utf-8'))
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File {filename} exceeds maximum size of {MAX_FILE_SIZE} bytes")
            total_size += file_size
        
        if total_size > MAX_TOTAL_SIZE:
            raise ValueError(f"Total file size exceeds maximum of {MAX_TOTAL_SIZE} bytes")

    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证并清理参数"""
        # 限制参数大小
        params_str = json.dumps(params)
        if len(params_str) > 64 * 1024:  # 64KB 参数限制
            raise ValueError("Parameters exceed maximum size")
        return params

    async def execute_skill(
        self,
        skill_id: int,
        files: Dict[str, str],
        main_file: str,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        执行技能

        Args:
            skill_id: 技能ID
            files: 文件内容字典 {filename: content}
            main_file: 主文件名
            params: 输入参数
            user_id: 用户ID

        Returns:
            执行结果
        """
        container = None
        try:
            # 验证输入
            self._validate_files(files)
            params = self._validate_params(params)

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 写入技能文件
                skill_dir = os.path.join(temp_dir, f"skill_{skill_id}")
                os.makedirs(skill_dir)

                for filename, content in files.items():
                    file_path = os.path.join(skill_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                # 写入参数文件
                params_file = os.path.join(skill_dir, "params.json")
                with open(params_file, 'w', encoding='utf-8') as f:
                    json.dump(params, f)

                # 创建 Docker 容器（带完整资源限制）
                container = self.client.containers.run(
                    image="python:3.11-slim",
                    command=f"python {main_file}",
                    volumes={
                        skill_dir: {
                            'bind': '/app/skill',
                            'mode': 'ro'
                        }
                    },
                    working_dir="/app/skill",
                    # 资源限制
                    mem_limit=self.memory_limit,
                    memswap_limit=self.memory_limit,  # 禁用swap
                    cpu_quota=self.cpu_quota,
                    cpu_period=100000,  # 100ms CPU周期
                    pids_limit=self.pids_limit,
                    # 安全限制
                    network_disabled=True,  # 禁用网络
                    read_only=True,  # 只读文件系统（除了/tmp）
                    security_opt=["no-new-privileges"],
                    cap_drop=["ALL"],  # 移除所有Linux能力
                    # 其他配置
                    remove=False,
                    detach=True,
                    environment={
                        "SKILL_ID": str(skill_id),
                        "USER_ID": str(user_id),
                        "PYTHONUNBUFFERED": "1",
                        "TMPDIR": "/tmp"
                    },
                    tmpfs={"/tmp": "size=10m,mode=1777"}  # 临时目录限制10MB
                )

                # 等待容器执行完成
                start_time = datetime.utcnow()

                try:
                    result = container.wait(timeout=self.container_timeout)
                    exit_code = result['StatusCode']
                except Exception as e:
                    logger.error(f"Container timeout for skill {skill_id}: {e}")
                    container.kill()
                    exit_code = -1
                    return {
                        "success": False,
                        "error": "Execution timeout exceeded",
                        "error_code": "TIMEOUT",
                        "execution_time": self.container_timeout * 1000
                    }

                end_time = datetime.utcnow()
                execution_time = int((end_time - start_time).total_seconds() * 1000)

                # 获取日志（限制大小）
                logs = container.logs().decode('utf-8')
                if len(logs) > self.max_output_size:
                    logs = logs[:self.max_output_size] + "\n... [output truncated]"

                # 获取容器资源使用统计
                stats = None
                try:
                    stats = container.stats(stream=False)
                except Exception:
                    pass

                # 构建结果
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": logs,
                        "execution_time": execution_time,
                        "container_id": container.id[:12],
                        "resource_usage": self._extract_resource_usage(stats)
                    }
                else:
                    return {
                        "success": False,
                        "error": logs,
                        "execution_time": execution_time,
                        "container_id": container.id[:12],
                        "exit_code": exit_code,
                        "resource_usage": self._extract_resource_usage(stats)
                    }

        except docker.errors.DockerException as e:
            logger.error(f"Docker error for skill {skill_id}: {e}")
            return {
                "success": False,
                "error": f"Container error: {str(e)}",
                "error_code": "CONTAINER_ERROR",
                "execution_time": 0
            }
        except ValueError as e:
            logger.warning(f"Validation error for skill {skill_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "VALIDATION_ERROR",
                "execution_time": 0
            }
        except Exception as e:
            logger.error(f"Execution error for skill {skill_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR",
                "execution_time": 0
            }
        finally:
            # 清理容器
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")

    def _extract_resource_usage(self, stats: Optional[dict]) -> dict:
        """提取资源使用统计"""
        if not stats:
            return {}
        
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            memory_stats = stats.get("memory_stats", {})
            
            return {
                "memory_used_mb": round(memory_stats.get("usage", 0) / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_stats.get("limit", 0) / (1024 * 1024), 2),
                "memory_percent": round(
                    memory_stats.get("usage", 0) / max(memory_stats.get("limit", 1), 1) * 100, 2
                )
            }
        except Exception:
            return {}


# 全局沙箱实例
skill_sandbox = SkillExecutionSandbox()
