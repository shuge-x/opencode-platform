"""
调试执行器 - 扩展技能执行沙箱以支持调试
"""
import docker
import asyncio
import json
import tempfile
import os
import re
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from app.core.skill_executor import SkillExecutionSandbox
from app.core.debug_manager import debug_manager, DebugState

logger = logging.getLogger(__name__)


class DebugSkillExecutor(SkillExecutionSandbox):
    """调试技能执行器"""

    def __init__(self):
        super().__init__()
        self.debug_instrumentation = self._load_debug_instrumentation()

    def _load_debug_instrumentation(self) -> str:
        """加载调试插桩代码"""
        return '''
import sys
import json
import traceback as tb
from datetime import datetime

class DebugHook:
    """调试钩子"""
    
    def __init__(self, skill_id, execution_id):
        self.skill_id = skill_id
        self.execution_id = execution_id
        self.original_trace = None
        
    def trace_calls(self, frame, event, arg):
        """跟踪函数调用"""
        if event == 'call':
            code = frame.f_code
            func_name = code.co_name
            file_name = code.co_filename
            line_no = frame.f_lineno
            
            # 发送调试事件
            self._send_debug_event('call', {
                'function': func_name,
                'file': file_name,
                'line': line_no,
                'locals': {k: str(v) for k, v in frame.f_locals.items()}
            })
            
        return self.trace_calls
    
    def trace_lines(self, frame, event, arg):
        """跟踪行执行"""
        if event == 'line':
            code = frame.f_code
            file_name = code.co_filename
            line_no = frame.f_lineno
            
            # 发送调试事件
            self._send_debug_event('line', {
                'file': file_name,
                'line': line_no,
                'locals': {k: str(v) for k, v in frame.f_locals.items()}
            })
            
        return self.trace_lines
    
    def _send_debug_event(self, event_type, data):
        """发送调试事件到日志"""
        event = {
            'type': 'debug_event',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        print(f"DEBUG_EVENT: {json.dumps(event)}", file=sys.stderr)
    
    def install(self):
        """安装调试钩子"""
        self.original_trace = sys.gettrace()
        sys.settrace(self.trace_calls)
    
    def uninstall(self):
        """卸载调试钩子"""
        sys.settrace(self.original_trace)

# 全局调试钩子
_debug_hook = None

def start_debug(skill_id, execution_id):
    """启动调试"""
    global _debug_hook
    _debug_hook = DebugHook(skill_id, execution_id)
    _debug_hook.install()

def stop_debug():
    """停止调试"""
    global _debug_hook
    if _debug_hook:
        _debug_hook.uninstall()
        _debug_hook = None

def log_debug(message, level="INFO", **kwargs):
    """记录调试日志"""
    log_entry = {
        'type': 'log',
        'level': level,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': kwargs
    }
    print(f"DEBUG_LOG: {json.dumps(log_entry)}", file=sys.stderr)

def capture_error(error):
    """捕获错误"""
    error_info = {
        'type': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'stack_trace': tb.format_exc(),
        'timestamp': datetime.utcnow().isoformat()
    }
    print(f"DEBUG_ERROR: {json.dumps(error_info)}", file=sys.stderr)
'''

    async def execute_skill_with_debug(
        self,
        skill_id: int,
        execution_id: int,
        files: Dict[str, str],
        main_file: str,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        执行技能（带调试支持）

        Args:
            skill_id: 技能ID
            execution_id: 执行ID
            files: 文件内容字典
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
                skill_dir = os.path.join(temp_dir, f"skill_{skill_id}")
                os.makedirs(skill_dir)

                # 写入调试插桩代码
                debug_file = os.path.join(skill_dir, "__debug__.py")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.debug_instrumentation)

                # 写入技能文件
                for filename, content in files.items():
                    file_path = os.path.join(skill_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                # 修改主文件，添加调试钩子
                if main_file in files:
                    instrumented_code = self._instrument_code(
                        files[main_file],
                        skill_id,
                        execution_id
                    )
                    main_file_path = os.path.join(skill_dir, main_file)
                    with open(main_file_path, 'w', encoding='utf-8') as f:
                        f.write(instrumented_code)

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
                            'mode': 'rw'  # 允许写入调试信息
                        }
                    },
                    working_dir="/app/skill",
                    mem_limit=self.memory_limit,
                    cpu_quota=self.cpu_quota,
                    network_disabled=True,
                    remove=False,
                    detach=True,
                    environment={
                        "SKILL_ID": str(skill_id),
                        "EXECUTION_ID": str(execution_id),
                        "USER_ID": str(user_id),
                        "PYTHONPATH": "/app/skill"
                    }
                )

                # 启动日志流任务
                log_task = asyncio.create_task(
                    self._stream_logs(execution_id, container)
                )

                # 等待容器执行完成
                start_time = datetime.utcnow()

                try:
                    # 使用异步等待
                    while True:
                        container.reload()
                        if container.status == 'exited':
                            break
                        
                        # 检查调试会话状态
                        debug_session = debug_manager.get_debug_session(execution_id)
                        if debug_session and debug_session.state == DebugState.STOPPED:
                            logger.info(f"Debug session stopped by user: {execution_id}")
                            container.kill()
                            break
                        
                        await asyncio.sleep(0.1)

                    exit_code = container.attrs['State']['ExitCode']
                except Exception as e:
                    logger.error(f"Container execution error: {e}")
                    container.kill()
                    exit_code = -1
                finally:
                    log_task.cancel()

                end_time = datetime.utcnow()
                execution_time = int((end_time - start_time).total_seconds() * 1000)

                # 获取剩余日志
                logs = container.logs().decode('utf-8')

                # 解析日志中的调试事件
                await self._parse_and_send_debug_logs(execution_id, logs)

                # 构建结果
                if exit_code == 0:
                    # 过滤掉调试信息，只返回实际输出
                    output = self._filter_debug_output(logs)
                    
                    return {
                        "success": True,
                        "output": output,
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
            await debug_manager.send_error(
                execution_id,
                error_type="DockerError",
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
            return {
                "success": False,
                "error": f"Docker error: {str(e)}",
                "execution_time": 0
            }
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            await debug_manager.send_error(
                execution_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
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

    def _instrument_code(self, code: str, skill_id: int, execution_id: int) -> str:
        """插桩代码，添加调试钩子"""
        lines = code.split('\n')
        
        # 在文件开头插入调试初始化代码
        debug_init = f'''
from __debug__ import start_debug, stop_debug, log_debug, capture_error

# 启动调试
start_debug({skill_id}, {execution_id})

try:
'''
        
        # 在文件末尾插入调试清理代码
        debug_cleanup = '''
finally:
    # 停止调试
    stop_debug()
'''
        
        # 缩进原始代码
        indented_code = '\n'.join('    ' + line if line.strip() else line for line in lines)
        
        return debug_init + indented_code + debug_cleanup

    async def _stream_logs(self, execution_id: int, container):
        """流式传输容器日志"""
        try:
            for line in container.logs(stream=True, follow=True):
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    
                    # 解析调试事件
                    if decoded_line.startswith('DEBUG_EVENT:'):
                        event_data = json.loads(decoded_line[len('DEBUG_EVENT:'):])
                        await debug_manager.send_debug_event(
                            execution_id,
                            event_data['event_type'],
                            **event_data['data']
                        )
                    
                    elif decoded_line.startswith('DEBUG_LOG:'):
                        log_data = json.loads(decoded_line[len('DEBUG_LOG:'):])
                        await debug_manager.send_log(
                            execution_id,
                            log_data['level'],
                            log_data['message'],
                            log_data.get('metadata')
                        )
                    
                    elif decoded_line.startswith('DEBUG_ERROR:'):
                        error_data = json.loads(decoded_line[len('DEBUG_ERROR:'):])
                        await debug_manager.send_error(
                            execution_id,
                            error_data['error_type'],
                            error_data['error_message'],
                            error_data.get('stack_trace')
                        )
                    
                    else:
                        # 普通日志
                        await debug_manager.send_log(
                            execution_id,
                            'INFO',
                            decoded_line
                        )
                        
        except asyncio.CancelledError:
            logger.info(f"Log streaming cancelled for execution {execution_id}")
        except Exception as e:
            logger.error(f"Error streaming logs: {e}")

    async def _parse_and_send_debug_logs(self, execution_id: int, logs: str):
        """解析并发送日志中的调试事件"""
        for line in logs.split('\n'):
            line = line.strip()
            if not line:
                continue

            try:
                if line.startswith('DEBUG_EVENT:'):
                    event_data = json.loads(line[len('DEBUG_EVENT:'):])
                    await debug_manager.send_debug_event(
                        execution_id,
                        event_data['event_type'],
                        **event_data['data']
                    )

                elif line.startswith('DEBUG_LOG:'):
                    log_data = json.loads(line[len('DEBUG_LOG:'):])
                    await debug_manager.send_log(
                        execution_id,
                        log_data['level'],
                        log_data['message'],
                        log_data.get('metadata')
                    )

                elif line.startswith('DEBUG_ERROR:'):
                    error_data = json.loads(line[len('DEBUG_ERROR:'):])
                    await debug_manager.send_error(
                        execution_id,
                        error_data['error_type'],
                        error_data['error_message'],
                        error_data.get('stack_trace')
                    )

            except json.JSONDecodeError:
                # 忽略无效的JSON
                pass
            except Exception as e:
                logger.error(f"Error parsing debug log: {e}")

    def _filter_debug_output(self, logs: str) -> str:
        """过滤调试输出，只返回实际输出"""
        filtered_lines = []
        for line in logs.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 过滤掉调试相关的行
            if line.startswith(('DEBUG_EVENT:', 'DEBUG_LOG:', 'DEBUG_ERROR:')):
                continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)


# 全局调试执行器实例
debug_executor = DebugSkillExecutor()
