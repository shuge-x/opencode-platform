"""
Docker 服务 - 处理 Docker 镜像构建和容器管理
"""
import docker
from docker.errors import DockerException, ImageNotFound, APIError, BuildError
from docker.models.containers import Container
from docker.models.images import Image
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
import logging
import json
import os
import tempfile
from datetime import datetime
import aiofiles
from app.config import settings

logger = logging.getLogger(__name__)


class DockerService:
    """Docker 服务类"""
    
    def __init__(self):
        self._client: Optional[docker.DockerClient] = None
    
    @property
    def client(self) -> docker.DockerClient:
        """获取 Docker 客户端（延迟初始化）"""
        if self._client is None:
            try:
                self._client = docker.from_env()
                # 测试连接
                self._client.ping()
            except DockerException as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise
        return self._client
    
    async def close(self):
        """关闭 Docker 客户端"""
        if self._client:
            self._client.close()
            self._client = None
    
    # ============= 镜像操作 =============
    
    async def build_image(
        self,
        path: str,
        tag: str,
        dockerfile: str = "Dockerfile",
        buildargs: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        构建 Docker 镜像
        
        Args:
            path: 构建上下文路径
            tag: 镜像标签
            dockerfile: Dockerfile 路径
            buildargs: 构建参数
            labels: 镜像标签
            
        Yields:
            构建进度事件
        """
        try:
            # 在线程池中运行同步的 Docker 操作
            loop = asyncio.get_event_loop()
            
            def _build():
                return self.client.api.build(
                    path=path,
                    tag=tag,
                    dockerfile=dockerfile,
                    buildargs=buildargs,
                    labels=labels,
                    decode=True,
                    rm=True,
                )
            
            build_stream = await loop.run_in_executor(None, _build)
            
            image_id = None
            for event in build_stream:
                # 解析构建事件
                if 'stream' in event:
                    yield {
                        'type': 'stream',
                        'message': event['stream'],
                        'step': self._extract_step(event['stream'])
                    }
                elif 'status' in event:
                    yield {
                        'type': 'status',
                        'status': event['status'],
                        'id': event.get('id')
                    }
                elif 'error' in event:
                    yield {
                        'type': 'error',
                        'error': event['error'],
                        'error_detail': event.get('errorDetail', {})
                    }
                    return
                elif 'aux' in event:
                    image_id = event['aux'].get('ID')
                    yield {
                        'type': 'aux',
                        'image_id': image_id
                    }
            
            # 构建完成
            yield {
                'type': 'complete',
                'image_id': image_id,
                'tag': tag
            }
            
        except BuildError as e:
            logger.error(f"Build error: {e}")
            yield {
                'type': 'error',
                'error': str(e),
                'build_log': e.build_log
            }
        except Exception as e:
            logger.error(f"Unexpected build error: {e}")
            yield {
                'type': 'error',
                'error': str(e)
            }
    
    async def build_image_from_dockerfile(
        self,
        dockerfile_content: str,
        tag: str,
        context_files: Optional[Dict[str, bytes]] = None,
        buildargs: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        从 Dockerfile 内容构建镜像
        
        Args:
            dockerfile_content: Dockerfile 内容
            tag: 镜像标签
            context_files: 上下文文件 {filename: content}
            buildargs: 构建参数
            labels: 镜像标签
            
        Returns:
            构建结果
        """
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入 Dockerfile
            dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            async with aiofiles.open(dockerfile_path, 'w') as f:
                await f.write(dockerfile_content)
            
            # 写入上下文文件
            if context_files:
                for filename, content in context_files.items():
                    filepath = os.path.join(tmpdir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(content)
            
            # 收集构建输出
            events = []
            result = {'success': False, 'image_id': None, 'error': None}
            
            async for event in self.build_image(
                path=tmpdir,
                tag=tag,
                buildargs=buildargs,
                labels=labels
            ):
                events.append(event)
                if event['type'] == 'error':
                    result['error'] = event.get('error')
                elif event['type'] == 'complete':
                    result['success'] = True
                    result['image_id'] = event.get('image_id')
            
            result['events'] = events
            return result
    
    async def get_image(self, image_name: str) -> Optional[Image]:
        """获取镜像"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.images.get(image_name)
            )
        except ImageNotFound:
            return None
    
    async def list_images(
        self,
        name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Image]:
        """列出镜像"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.images.list(name=name, filters=filters)
        )
    
    async def remove_image(
        self,
        image_id: str,
        force: bool = False,
        noprune: bool = False
    ) -> Dict[str, Any]:
        """删除镜像"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.images.remove(
                image_id,
                force=force,
                noprune=noprune
            )
        )
    
    async def tag_image(
        self,
        image_id: str,
        repository: str,
        tag: str = "latest"
    ) -> bool:
        """给镜像打标签"""
        try:
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                None,
                lambda: self.client.images.get(image_id)
            )
            await loop.run_in_executor(
                None,
                lambda: image.tag(repository, tag)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to tag image: {e}")
            return False
    
    async def push_image(
        self,
        repository: str,
        tag: str = "latest",
        auth_config: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """推送镜像到仓库"""
        try:
            loop = asyncio.get_event_loop()
            
            def _push():
                return self.client.images.push(
                    repository,
                    tag=tag,
                    auth_config=auth_config,
                    decode=True
                )
            
            push_stream = await loop.run_in_executor(None, _push)
            
            for event in push_stream:
                yield event
                
        except Exception as e:
            logger.error(f"Failed to push image: {e}")
            yield {'error': str(e)}
    
    # ============= 容器操作 =============
    
    async def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, Any]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        networks: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        resource_limits: Optional[Dict[str, Any]] = None,
    ) -> Container:
        """
        创建容器
        
        Args:
            image: 镜像名称
            name: 容器名称
            command: 启动命令
            environment: 环境变量
            ports: 端口映射
            volumes: 卷挂载
            networks: 网络
            labels: 标签
            resource_limits: 资源限制
            
        Returns:
            容器对象
        """
        loop = asyncio.get_event_loop()
        
        # 准备环境变量
        env_list = [f"{k}={v}" for k, v in (environment or {}).items()]
        
        # 准备端口绑定
        port_bindings = {}
        if ports:
            for container_port, host_port in ports.items():
                port_bindings[container_port] = [{'HostPort': str(host_port)}]
        
        # 准备卷挂载
        volume_bindings = {}
        if volumes:
            for host_path, container_config in volumes.items():
                volume_bindings[host_path] = container_config
        
        # 准备资源限制
        host_config = {}
        if resource_limits:
            if 'cpu' in resource_limits:
                # CPU 配额 (单位: 100000 = 1 CPU)
                cpu_quota = int(float(resource_limits['cpu']) * 100000)
                host_config['CpuQuota'] = cpu_quota
            if 'memory' in resource_limits:
                host_config['Memory'] = self._parse_memory(resource_limits['memory'])
        
        if port_bindings:
            host_config['PortBindings'] = port_bindings
        if volume_bindings:
            host_config['Binds'] = [
                f"{host}:{container['bind']}:{container.get('mode', 'rw')}"
                for host, container in volume_bindings.items()
            ]
        
        # 创建容器
        def _create():
            return self.client.containers.create(
                image=image,
                name=name,
                command=command,
                environment=env_list,
                labels=labels,
                host_config=host_config if host_config else None,
                ports=list(ports.keys()) if ports else None,
            )
        
        container = await loop.run_in_executor(None, _create)
        
        # 连接网络
        if networks:
            for network_name in networks:
                try:
                    network = await loop.run_in_executor(
                        None,
                        lambda n=network_name: self.client.networks.get(n)
                    )
                    await loop.run_in_executor(
                        None,
                        lambda n=network, c=container: n.connect(c)
                    )
                except Exception as e:
                    logger.warning(f"Failed to connect to network {network_name}: {e}")
        
        return container
    
    async def start_container(self, container_id: str) -> bool:
        """启动容器"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            await loop.run_in_executor(None, container.start)
            return True
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            return False
    
    async def stop_container(
        self,
        container_id: str,
        timeout: int = 10
    ) -> bool:
        """停止容器"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            await loop.run_in_executor(None, lambda: container.stop(timeout=timeout))
            return True
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    async def restart_container(
        self,
        container_id: str,
        timeout: int = 10
    ) -> bool:
        """重启容器"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            await loop.run_in_executor(None, lambda: container.restart(timeout=timeout))
            return True
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            return False
    
    async def remove_container(
        self,
        container_id: str,
        force: bool = False,
        remove_volumes: bool = False
    ) -> bool:
        """删除容器"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            await loop.run_in_executor(
                None,
                lambda: container.remove(
                    force=force,
                    v=remove_volumes
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to remove container: {e}")
            return False
    
    async def get_container(self, container_id: str) -> Optional[Container]:
        """获取容器"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
        except Exception:
            return None
    
    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: Optional[datetime] = None,
        timestamps: bool = True
    ) -> str:
        """获取容器日志"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            
            logs = await loop.run_in_executor(
                None,
                lambda: container.logs(
                    tail=tail,
                    since=since,
                    timestamps=timestamps,
                    stdout=True,
                    stderr=True
                )
            )
            
            return logs.decode('utf-8') if logs else ""
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            return ""
    
    async def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """获取容器统计信息"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.get(container_id)
            )
            
            stats = await loop.run_in_executor(
                None,
                lambda: container.stats(stream=False)
            )
            
            return stats[0] if stats else None
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            return None
    
    async def list_containers(
        self,
        all: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Container]:
        """列出容器"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.containers.list(all=all, filters=filters)
        )
    
    # ============= 网络操作 =============
    
    async def create_network(
        self,
        name: str,
        driver: str = "bridge",
        labels: Optional[Dict[str, str]] = None
    ) -> Any:
        """创建网络"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.networks.create(
                name,
                driver=driver,
                labels=labels
            )
        )
    
    async def get_network(self, network_id: str) -> Any:
        """获取网络"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.networks.get(network_id)
        )
    
    async def remove_network(self, network_id: str) -> bool:
        """删除网络"""
        try:
            loop = asyncio.get_event_loop()
            network = await loop.run_in_executor(
                None,
                lambda: self.client.networks.get(network_id)
            )
            await loop.run_in_executor(None, network.remove)
            return True
        except Exception as e:
            logger.error(f"Failed to remove network: {e}")
            return False
    
    # ============= 辅助方法 =============
    
    def _extract_step(self, stream_line: str) -> Optional[str]:
        """从日志中提取步骤信息"""
        if 'Step' in stream_line and '/' in stream_line:
            # 例如: "Step 1/5 : FROM python:3.9"
            try:
                step_part = stream_line.split(':')[0].strip()
                return step_part
            except Exception:
                pass
        return None
    
    def _parse_memory(self, memory_str: str) -> int:
        """解析内存字符串为字节数"""
        units = {
            'b': 1,
            'k': 1024,
            'kb': 1024,
            'm': 1024 * 1024,
            'mb': 1024 * 1024,
            'g': 1024 * 1024 * 1024,
            'gb': 1024 * 1024 * 1024,
        }
        
        memory_str = memory_str.lower().strip()
        for unit, multiplier in units.items():
            if memory_str.endswith(unit):
                try:
                    value = int(memory_str[:-len(unit)])
                    return value * multiplier
                except ValueError:
                    pass
        
        try:
            return int(memory_str)
        except ValueError:
            return 0


# 全局 Docker 服务实例
docker_service = DockerService()
