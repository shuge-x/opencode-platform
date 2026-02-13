"""
OpenCode Sidecar模块

用于调用opencode CLI工具
"""
import asyncio
from typing import Dict, Any, Optional


class OpenCodeSidecar:
    """OpenCode Sidecar - 用于调用opencode CLI"""
    
    def __init__(self, opencode_path: str = "opencode"):
        """
        初始化OpenCode Sidecar
        
        Args:
            opencode_path: opencode CLI路径
        """
        self.opencode_path = opencode_path
    
    async def execute(
        self,
        message: str,
        session_id: str,
        user_id: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        执行opencode命令
        
        Args:
            message: 要发送的消息
            session_id: 会话ID
            user_id: 用户ID
            timeout: 超时时间（秒）
        
        Returns:
            Dict包含执行结果
        """
        try:
            # 构建命令
            cmd = [
                self.opencode_path,
                "--session", session_id,
                "--user", user_id,
                message
            ]
            
            # 异步执行命令
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                if proc.returncode == 0:
                    return {
                        "success": True,
                        "output": stdout.decode("utf-8"),
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "output": None,
                        "error": stderr.decode("utf-8")
                    }
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {
                    "success": False,
                    "output": None,
                    "error": "Timeout"
                }
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
    
    async def check_health(self) -> bool:
        """
        检查opencode CLI是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                self.opencode_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=5
            )
            
            return proc.returncode == 0
        except Exception:
            return False
