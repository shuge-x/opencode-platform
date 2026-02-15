"""
部署服务 - 管理技能部署的生命周期
"""
import logging
import os
import uuid
import json
import slugify
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.deployment import (
    Deployment,
    DeploymentHealthCheck,
    DeploymentLog,
    DockerfileTemplate,
    DeploymentStatus,
    HealthStatus,
)
from app.models.published_skill import PublishedSkill, SkillPackage
from app.models.skill import Skill
from app.models.user import User
from app.services.docker_service import docker_service
from app.config import settings

logger = logging.getLogger(__name__)


class DeploymentService:
    """部署服务"""
    
    def __init__(self):
        self.deployment_base_path = os.path.join(settings.BASE_DIR, "deployments")
        os.makedirs(self.deployment_base_path, exist_ok=True)
    
    async def create_deployment(
        self,
        db: AsyncSession,
        user: User,
        skill_id: int,
        name: str,
        skill_package_id: Optional[int] = None,
        ports: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        auto_restart: bool = True,
        max_restart_attempts: int = 3,
    ) -> Deployment:
        """
        创建部署
        
        Args:
            db: 数据库会话
            user: 当前用户
            skill_id: 技能 ID
            name: 部署名称
            skill_package_id: 技能包 ID
            ports: 端口映射
            environment: 环境变量
            volumes: 卷挂载
            cpu_limit: CPU 限制
            memory_limit: 内存限制
            auto_restart: 自动重启
            max_restart_attempts: 最大重启次数
            
        Returns:
            部署对象
        """
        # 获取技能
        result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        # 获取技能包
        skill_package = None
        if skill_package_id:
            result = await db.execute(
                select(SkillPackage).where(SkillPackage.id == skill_package_id)
            )
            skill_package = result.scalar_one_or_none()
        else:
            # 获取最新版本
            result = await db.execute(
                select(SkillPackage)
                .where(SkillPackage.skill_id == skill_id)
                .where(SkillPackage.is_latest == True)
                .where(SkillPackage.is_active == True)
            )
            skill_package = result.scalar_one_or_none()
        
        if not skill_package:
            raise ValueError("No active skill package found")
        
        # 生成唯一 slug
        slug = f"{slugify.slugify(name)}-{uuid.uuid4().hex[:8]}"
        
        # 生成镜像名称
        image_name = f"skill-{slug}"
        image_tag = skill_package.version
        
        # 准备资源限制
        resource_limits = {}
        if cpu_limit:
            resource_limits['cpu'] = cpu_limit
        if memory_limit:
            resource_limits['memory'] = memory_limit
        
        # 创建部署记录
        deployment = Deployment(
            skill_id=skill_id,
            skill_package_id=skill_package.id,
            user_id=user.id,
            name=name,
            slug=slug,
            image_name=image_name,
            image_tag=image_tag,
            ports=ports,
            environment=environment,
            volumes=volumes,
            resource_limits=resource_limits if resource_limits else None,
            status=DeploymentStatus.PENDING,
            health_status=HealthStatus.UNKNOWN,
            auto_restart=auto_restart,
            max_restart_attempts=max_restart_attempts,
        )
        
        db.add(deployment)
        await db.commit()
        await db.refresh(deployment)
        
        return deployment
    
    async def build_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
        dockerfile_template_id: Optional[int] = None,
        custom_dockerfile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建部署镜像
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            dockerfile_template_id: Dockerfile 模板 ID
            custom_dockerfile: 自定义 Dockerfile
            
        Returns:
            构建结果
        """
        # 更新状态为构建中
        deployment.status = DeploymentStatus.BUILDING
        await db.commit()
        
        try:
            # 获取 Dockerfile 内容
            if custom_dockerfile:
                dockerfile_content = custom_dockerfile
            else:
                dockerfile_content = await self._get_dockerfile(
                    db, deployment, dockerfile_template_id
                )
            
            # 获取技能包内容
            skill_package = await db.get(SkillPackage, deployment.skill_package_id)
            context_files = await self._get_skill_package_files(skill_package)
            
            # 构建镜像
            build_result = await docker_service.build_image_from_dockerfile(
                dockerfile_content=dockerfile_content,
                tag=f"{deployment.image_name}:{deployment.image_tag}",
                context_files=context_files,
            )
            
            if build_result['success']:
                deployment.image_id = build_result.get('image_id')
                deployment.status = DeploymentStatus.PENDING
                await db.commit()
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = build_result.get('error')
                await db.commit()
            
            return build_result
            
        except Exception as e:
            logger.error(f"Build failed for deployment {deployment.id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await db.commit()
            raise
    
    async def start_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
    ) -> bool:
        """
        启动部署
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            
        Returns:
            是否成功
        """
        if deployment.status == DeploymentStatus.RUNNING:
            return True
        
        try:
            # 更新状态
            deployment.status = DeploymentStatus.DEPLOYING
            await db.commit()
            
            # 准备容器名称
            container_name = f"skill-{deployment.slug}"
            
            # 创建容器
            container = await docker_service.create_container(
                image=f"{deployment.image_name}:{deployment.image_tag}",
                name=container_name,
                environment=deployment.environment,
                ports=deployment.ports,
                volumes=deployment.volumes,
                labels={
                    "skill.id": str(deployment.skill_id),
                    "deployment.id": str(deployment.id),
                    "deployment.slug": deployment.slug,
                    "managed-by": "opencode-platform"
                },
                resource_limits=deployment.resource_limits,
            )
            
            # 启动容器
            success = await docker_service.start_container(container.id)
            
            if success:
                deployment.container_id = container.id
                deployment.container_name = container_name
                deployment.status = DeploymentStatus.RUNNING
                deployment.started_at = datetime.utcnow()
                deployment.stopped_at = None
                await db.commit()
                return True
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Failed to start container"
                await db.commit()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start deployment {deployment.id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await db.commit()
            return False
    
    async def stop_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
        timeout: int = 10,
    ) -> bool:
        """
        停止部署
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        if not deployment.container_id:
            deployment.status = DeploymentStatus.STOPPED
            await db.commit()
            return True
        
        try:
            success = await docker_service.stop_container(
                deployment.container_id,
                timeout=timeout
            )
            
            if success:
                deployment.status = DeploymentStatus.STOPPED
                deployment.stopped_at = datetime.utcnow()
                await db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop deployment {deployment.id}: {e}")
            return False
    
    async def restart_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
        timeout: int = 10,
        force: bool = False,
    ) -> bool:
        """
        重启部署
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            timeout: 超时时间
            force: 是否强制重启
            
        Returns:
            是否成功
        """
        if not deployment.container_id:
            return await self.start_deployment(db, deployment)
        
        try:
            deployment.status = DeploymentStatus.RESTARTING
            deployment.restart_count += 1
            await db.commit()
            
            if force:
                await docker_service.stop_container(deployment.container_id, timeout=0)
                await docker_service.start_container(deployment.container_id)
            else:
                await docker_service.restart_container(deployment.container_id, timeout=timeout)
            
            deployment.status = DeploymentStatus.RUNNING
            deployment.started_at = datetime.utcnow()
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart deployment {deployment.id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await db.commit()
            return False
    
    async def remove_deployment(
        self,
        db: AsyncSession,
        deployment: Deployment,
        remove_volumes: bool = False,
    ) -> bool:
        """
        删除部署
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            remove_volumes: 是否删除卷
            
        Returns:
            是否成功
        """
        try:
            # 停止并删除容器
            if deployment.container_id:
                await docker_service.remove_container(
                    deployment.container_id,
                    force=True,
                    remove_volumes=remove_volumes
                )
            
            # 删除镜像
            if deployment.image_name:
                try:
                    await docker_service.remove_image(
                        f"{deployment.image_name}:{deployment.image_tag}",
                        force=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to remove image: {e}")
            
            # 删除数据库记录
            await db.delete(deployment)
            await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove deployment {deployment.id}: {e}")
            return False
    
    async def get_deployment_status(
        self,
        db: AsyncSession,
        deployment: Deployment,
    ) -> Dict[str, Any]:
        """
        获取部署状态
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            
        Returns:
            状态信息
        """
        if not deployment.container_id:
            return {
                'status': deployment.status.value,
                'health_status': deployment.health_status.value,
            }
        
        container = await docker_service.get_container(deployment.container_id)
        
        if container:
            container_state = container.attrs.get('State', {})
            status = container_state.get('Status', 'unknown')
            
            # 更新部署状态
            if status == 'running':
                deployment.status = DeploymentStatus.RUNNING
            elif status == 'exited':
                deployment.status = DeploymentStatus.STOPPED
            elif status == 'restarting':
                deployment.status = DeploymentStatus.RESTARTING
            
            await db.commit()
            
            return {
                'status': deployment.status.value,
                'health_status': deployment.health_status.value,
                'container_status': status,
                'started_at': deployment.started_at,
                'restart_count': deployment.restart_count,
            }
        
        return {
            'status': deployment.status.value,
            'health_status': deployment.health_status.value,
        }
    
    async def health_check(
        self,
        db: AsyncSession,
        deployment: Deployment,
        check_endpoint: str = "/health",
    ) -> DeploymentHealthCheck:
        """
        执行健康检查
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            check_endpoint: 健康检查端点
            
        Returns:
            健康检查记录
        """
        import time
        import httpx
        
        check_record = DeploymentHealthCheck(
            deployment_id=deployment.id,
            status=HealthStatus.UNKNOWN,
            check_type="http",
        )
        
        if deployment.status != DeploymentStatus.RUNNING:
            check_record.status = HealthStatus.UNKNOWN
            check_record.error_message = "Deployment not running"
            db.add(check_record)
            await db.commit()
            return check_record
        
        # 检查 HTTP 端点
        try:
            port = None
            if deployment.ports:
                # 获取第一个暴露的端口
                for container_port, host_port in deployment.ports.items():
                    port = host_port
                    break
            
            if port:
                url = f"http://localhost:{port}{check_endpoint}"
                start_time = time.time()
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                
                response_time = int((time.time() - start_time) * 1000)
                
                check_record.response_time_ms = response_time
                check_record.http_status = response.status_code
                
                if response.status_code == 200:
                    check_record.status = HealthStatus.HEALTHY
                    deployment.health_status = HealthStatus.HEALTHY
                else:
                    check_record.status = HealthStatus.UNHEALTHY
                    deployment.health_status = HealthStatus.UNHEALTHY
                    check_record.error_message = f"HTTP {response.status_code}"
            else:
                check_record.status = HealthStatus.UNKNOWN
                check_record.error_message = "No exposed port"
                
        except httpx.TimeoutException:
            check_record.status = HealthStatus.UNHEALTHY
            deployment.health_status = HealthStatus.UNHEALTHY
            check_record.error_message = "Health check timeout"
        except Exception as e:
            check_record.status = HealthStatus.UNHEALTHY
            deployment.health_status = HealthStatus.UNHEALTHY
            check_record.error_message = str(e)
        
        # 保存记录
        deployment.last_health_check = datetime.utcnow()
        db.add(check_record)
        await db.commit()
        
        # 检查是否需要自动重启
        if (check_record.status == HealthStatus.UNHEALTHY and 
            deployment.auto_restart and 
            deployment.restart_count < deployment.max_restart_attempts):
            await self.restart_deployment(db, deployment)
        
        return check_record
    
    async def collect_logs(
        self,
        db: AsyncSession,
        deployment: Deployment,
        tail: int = 100,
        since: Optional[datetime] = None,
    ) -> List[DeploymentLog]:
        """
        收集部署日志
        
        Args:
            db: 数据库会话
            deployment: 部署对象
            tail: 获取最后 N 条
            since: 从指定时间开始
            
        Returns:
            日志列表
        """
        if not deployment.container_id:
            return []
        
        logs = await docker_service.get_container_logs(
            deployment.container_id,
            tail=tail,
            since=since
        )
        
        # 解析日志
        log_entries = []
        for line in logs.split('\n'):
            if line.strip():
                log_entry = DeploymentLog(
                    deployment_id=deployment.id,
                    log_type="stdout",  # Docker 返回的日志混合了 stdout 和 stderr
                    content=line,
                )
                db.add(log_entry)
                log_entries.append(log_entry)
        
        await db.commit()
        return log_entries
    
    async def generate_compose_config(
        self,
        deployment: Deployment,
    ) -> Dict[str, Any]:
        """
        生成 Docker Compose 配置
        
        Args:
            deployment: 部署对象
            
        Returns:
            Compose 配置字典
        """
        compose = {
            'version': '3.8',
            'services': {
                deployment.slug: {
                    'image': f"{deployment.image_name}:{deployment.image_tag}",
                    'container_name': deployment.container_name,
                    'restart': 'unless-stopped' if deployment.auto_restart else 'no',
                    'labels': {
                        "skill.id": str(deployment.skill_id),
                        "deployment.id": str(deployment.id),
                        "managed-by": "opencode-platform"
                    }
                }
            }
        }
        
        service = compose['services'][deployment.slug]
        
        # 端口映射
        if deployment.ports:
            service['ports'] = [
                f"{host}:{container}"
                for container, host in deployment.ports.items()
            ]
        
        # 环境变量
        if deployment.environment:
            service['environment'] = deployment.environment
        
        # 卷挂载
        if deployment.volumes:
            service['volumes'] = [
                f"{host}:{container}"
                for host, container in deployment.volumes.items()
            ]
        
        # 资源限制
        if deployment.resource_limits:
            deploy = {}
            if 'cpu' in deployment.resource_limits:
                deploy['resources'] = {
                    'limits': {
                        'cpus': deployment.resource_limits['cpu']
                    }
                }
            if 'memory' in deployment.resource_limits:
                if 'resources' not in deploy:
                    deploy['resources'] = {'limits': {}}
                deploy['resources']['limits']['memory'] = deployment.resource_limits['memory']
            if deploy:
                service['deploy'] = deploy
        
        # 健康检查
        service['healthcheck'] = {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8080/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3,
            'start_period': '40s'
        }
        
        return compose
    
    # ============= 私有辅助方法 =============
    
    async def _get_dockerfile(
        self,
        db: AsyncSession,
        deployment: Deployment,
        template_id: Optional[int] = None,
    ) -> str:
        """获取 Dockerfile 内容"""
        if template_id:
            result = await db.execute(
                select(DockerfileTemplate).where(DockerfileTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            if template:
                return self._render_dockerfile(template.content, deployment)
        
        # 获取默认模板或使用基础模板
        result = await db.execute(
            select(DockerfileTemplate)
            .where(DockerfileTemplate.is_default == True)
            .where(DockerfileTemplate.is_active == True)
        )
        template = result.scalar_one_or_none()
        
        if template:
            return self._render_dockerfile(template.content, deployment)
        
        # 返回默认 Dockerfile
        return self._get_default_dockerfile(deployment)
    
    def _render_dockerfile(
        self,
        template: str,
        deployment: Deployment,
    ) -> str:
        """渲染 Dockerfile 模板"""
        variables = {
            'SKILL_NAME': deployment.name,
            'SKILL_SLUG': deployment.slug,
            'SKILL_VERSION': deployment.image_tag,
        }
        
        content = template
        for key, value in variables.items():
            content = content.replace(f'${{{key}}}', value)
            content = content.replace(f'${key}', value)
        
        return content
    
    def _get_default_dockerfile(self, deployment: Deployment) -> str:
        """获取默认 Dockerfile"""
        return f'''# Auto-generated Dockerfile for {deployment.name}
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "main.py"]
'''
    
    async def _get_skill_package_files(
        self,
        skill_package: SkillPackage,
    ) -> Dict[str, bytes]:
        """获取技能包文件"""
        # 这里应该从 MinIO 下载技能包并解压
        # 目前返回空字典，实际实现需要集成 MinIO
        return {}


# 全局部署服务实例
deployment_service = DeploymentService()
