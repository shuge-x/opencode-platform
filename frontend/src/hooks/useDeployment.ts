import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { deploymentApi, DeploymentLogStream } from '@/api/deployment'
import type {
  CreateDeploymentRequest,
  UpdateDeploymentRequest,
  AddDomainRequest,
  DeploymentLog,
} from '@/types/deployment'
import { useState, useEffect, useCallback } from 'react'

// 获取部署列表
export function useDeployments() {
  return useQuery({
    queryKey: ['deployments'],
    queryFn: () => deploymentApi.listDeployments(),
  })
}

// 获取单个部署
export function useDeployment(deploymentId: string | null) {
  return useQuery({
    queryKey: ['deployment', deploymentId],
    queryFn: () => deploymentApi.getDeployment(deploymentId!),
    enabled: !!deploymentId,
  })
}

// 创建部署
export function useCreateDeployment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: CreateDeploymentRequest) => deploymentApi.createDeployment(request),
    onSuccess: () => {
      message.success('部署创建成功')
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建部署失败')
    },
  })
}

// 更新部署
export function useUpdateDeployment(deploymentId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: UpdateDeploymentRequest) => deploymentApi.updateDeployment(deploymentId, request),
    onSuccess: () => {
      message.success('部署更新成功')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '更新部署失败')
    },
  })
}

// 启动部署
export function useStartDeployment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (deploymentId: string) => deploymentApi.startDeployment(deploymentId),
    onSuccess: (_, deploymentId) => {
      message.success('部署已启动')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '启动失败')
    },
  })
}

// 停止部署
export function useStopDeployment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (deploymentId: string) => deploymentApi.stopDeployment(deploymentId),
    onSuccess: (_, deploymentId) => {
      message.success('部署已停止')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '停止失败')
    },
  })
}

// 重启部署
export function useRestartDeployment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (deploymentId: string) => deploymentApi.restartDeployment(deploymentId),
    onSuccess: (_, deploymentId) => {
      message.success('部署重启中...')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '重启失败')
    },
  })
}

// 删除部署
export function useDeleteDeployment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (deploymentId: string) => deploymentApi.deleteDeployment(deploymentId),
    onSuccess: () => {
      message.success('部署已删除')
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })
}

// 获取部署日志
export function useDeploymentLogs(
  deploymentId: string | null,
  params?: {
    level?: 'info' | 'warn' | 'error' | 'debug'
    search?: string
  }
) {
  return useQuery({
    queryKey: ['deploymentLogs', deploymentId, params],
    queryFn: () => deploymentApi.getDeploymentLogs(deploymentId!, params),
    enabled: !!deploymentId,
    refetchInterval: 5000, // 每 5 秒刷新一次
  })
}

// 添加域名
export function useAddDomain(deploymentId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: AddDomainRequest) => deploymentApi.addDomain(deploymentId, request),
    onSuccess: () => {
      message.success('域名添加成功')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '添加域名失败')
    },
  })
}

// 验证域名
export function useVerifyDomain(deploymentId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (domainId: string) => deploymentApi.verifyDomain(deploymentId, domainId),
    onSuccess: () => {
      message.success('域名验证成功')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '域名验证失败')
    },
  })
}

// 删除域名
export function useRemoveDomain(deploymentId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (domainId: string) => deploymentApi.removeDomain(deploymentId, domainId),
    onSuccess: () => {
      message.success('域名已删除')
      queryClient.invalidateQueries({ queryKey: ['deployment', deploymentId] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除域名失败')
    },
  })
}

// 获取技能版本
export function useSkillVersions(skillId: string | null) {
  return useQuery({
    queryKey: ['skillVersions', skillId],
    queryFn: () => deploymentApi.getSkillVersions(skillId!),
    enabled: !!skillId,
  })
}

// 实时日志流 Hook
export function useDeploymentLogStream(deploymentId: string | null) {
  const [logs, setLogs] = useState<DeploymentLog[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [stream, setStream] = useState<DeploymentLogStream | null>(null)

  const connect = useCallback(() => {
    if (!deploymentId) return

    const logStream = new DeploymentLogStream(
      deploymentId,
      (log) => {
        setLogs((prev) => [...prev, log].slice(-500)) // 保留最近 500 条日志
      },
      (status) => {
        console.log('Deployment status changed:', status)
      },
      (error) => {
        console.error('Log stream error:', error)
        setIsConnected(false)
      }
    )

    logStream.connect()
    setStream(logStream)
    setIsConnected(true)
  }, [deploymentId])

  const disconnect = useCallback(() => {
    stream?.disconnect()
    setStream(null)
    setIsConnected(false)
  }, [stream])

  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  useEffect(() => {
    return () => {
      stream?.disconnect()
    }
  }, [stream])

  return {
    logs,
    isConnected,
    connect,
    disconnect,
    clearLogs,
  }
}
