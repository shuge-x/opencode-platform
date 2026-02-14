"""
技能执行沙箱 - 使用 Docker 容器隔离执行
"""
import docker
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SkillExecutionSandbox:
    """技能执行沙箱"""

    def __init__(self):
        self.client = docker.from_env()
        self.container_timeout = 30  # 容器超时时间（秒）
        self.memory_limit = "128m"  # 内存限制
        self.cpu_quota = 50000  # CPU限制（50%）

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

                # 创建 Docker 容器
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
                    mem_limit=self.memory_limit,
                    cpu_quota=self.cpu_quota,
                    network_disabled=True,  # 禁用网络
                    remove=False,
                    detach=True,
                    environment={
                        "SKILL_ID": str(skill_id),
                        "USER_ID": str(user_id)
                    }
                )

                # 等待容器执行完成
                start_time = datetime.utcnow()

                try:
                    result = container.wait(timeout=self.container_timeout)
                    exit_code = result['StatusCode']
                except Exception as e:
                    logger.error(f"Container timeout: {e}")
                    container.kill()
                    exit_code = -1

                end_time = datetime.utcnow()
                execution_time = int((end_time - start_time).total_seconds() * 1000)

                # 获取日志
                logs = container.logs().decode('utf-8')

                # 构建结果
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": logs,
                        "execution_time": execution_time,
                        "container_id": container.id
                    }
                else:
                    return {
                        "success": False,
                        "error": logs,
                        "execution_time": execution_time,
                        "container_id": container.id,
                        "exit_code": exit_code
                    }

        except docker.errors.DockerException as e:
            logger.error(f"Docker error: {e}")
            return {
                "success": False,
                "error": f"Docker error: {str(e)}",
                "execution_time": 0
            }
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
        finally:
            # 清理容器
            if container:
                try:
                    container.remove()
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")


# 全局沙箱实例
skill_sandbox = SkillExecutionSandbox()
