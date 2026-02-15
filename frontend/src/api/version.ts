import client from './client'
import type {
  VersionInfo,
  VersionDiff,
  VersionListResponse,
  VersionSearchParams,
  RevertResult
} from '@/types/version'

export const versionApi = {
  // 获取版本列表
  list: async (skillId: number, params?: VersionSearchParams): Promise<VersionListResponse> => {
    const response = await client.get(`/skills-dev/${skillId}/versions`, { params })
    return response.data
  },

  // 获取版本详情
  get: async (skillId: number, versionId: number): Promise<VersionInfo> => {
    const response = await client.get(`/skills-dev/${skillId}/versions/${versionId}`)
    return response.data
  },

  // 获取版本对比
  getDiff: async (
    skillId: number,
    versionId: number,
    fileId?: number,
    compareWith?: number
  ): Promise<VersionDiff> => {
    const params: Record<string, any> = {}
    if (fileId) params.file_id = fileId
    if (compareWith) params.compare_with = compareWith
    
    const response = await client.get(
      `/skills-dev/${skillId}/versions/${versionId}/diff`,
      { params }
    )
    return response.data
  },

  // 获取文件在特定版本的内容
  getFileAtVersion: async (
    skillId: number,
    versionId: number,
    fileId: number
  ): Promise<{ content: string; filename: string }> => {
    const response = await client.get(
      `/skills-dev/${skillId}/versions/${versionId}/files/${fileId}`
    )
    return response.data
  },

  // 回退到指定版本
  revert: async (
    skillId: number,
    versionId: number,
    options?: {
      message?: string
      create_new_version?: boolean
    }
  ): Promise<RevertResult> => {
    const response = await client.post(
      `/skills-dev/${skillId}/versions/${versionId}/revert`,
      options
    )
    return response.data
  },

  // 创建版本标签
  createTag: async (
    skillId: number,
    versionId: number,
    tag: string
  ): Promise<VersionInfo> => {
    const response = await client.post(
      `/skills-dev/${skillId}/versions/${versionId}/tags`,
      { tag }
    )
    return response.data
  },

  // 删除版本标签
  deleteTag: async (
    skillId: number,
    versionId: number,
    tag: string
  ): Promise<void> => {
    await client.delete(
      `/skills-dev/${skillId}/versions/${versionId}/tags/${tag}`
    )
  },

  // 比较两个版本
  compare: async (
    skillId: number,
    fromVersionId: number,
    toVersionId: number
  ): Promise<{
    from_version: VersionInfo
    to_version: VersionInfo
    file_diffs: VersionDiff[]
  }> => {
    const response = await client.get(
      `/skills-dev/${skillId}/versions/compare`,
      {
        params: {
          from: fromVersionId,
          to: toVersionId
        }
      }
    )
    return response.data
  },

  // 获取最新版本
  getLatest: async (skillId: number): Promise<VersionInfo> => {
    const response = await client.get(`/skills-dev/${skillId}/versions/latest`)
    return response.data
  }
}
