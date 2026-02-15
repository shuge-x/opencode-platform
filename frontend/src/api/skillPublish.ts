import client from './client'

// 技能版本接口
export interface SkillVersion {
  id: number
  skill_id: number
  version: string
  description?: string
  changelog?: string
  status: 'draft' | 'published' | 'archived'
  package_url?: string
  package_size?: number
  published_at?: string
  created_at: string
  updated_at: string
}

// 协作者接口
export interface SkillCollaborator {
  id: number
  skill_id: number
  user_id: number
  username: string
  email: string
  role: 'owner' | 'admin' | 'editor' | 'viewer'
  added_at: string
}

// 发布进度接口
export interface PublishProgress {
  stage: 'packaging' | 'uploading' | 'validating' | 'publishing' | 'completed' | 'failed'
  progress: number
  message: string
  error?: string
}

// 权限设置接口
export interface PermissionSettings {
  is_public: boolean
  access_level: 'public' | 'private' | 'restricted'
  allowed_users?: number[]
  allowed_groups?: string[]
  require_approval: boolean
}

// 技能发布数据接口
export interface SkillPublishData {
  name: string
  description: string
  icon?: string
  tags: string[]
  category: string
  version: string
  changelog?: string
  permissions: PermissionSettings
}

// 技能发布 API
export const skillPublishApi = {
  // ============ 技能发布相关 ============
  
  // 发布技能
  publish: async (skillId: number, data: SkillPublishData): Promise<{ publish_id: string }> => {
    const response = await client.post(`/skills-dev/${skillId}/publish`, data)
    return response.data
  },

  // 获取发布进度
  getPublishProgress: async (publishId: string): Promise<PublishProgress> => {
    const response = await client.get(`/skills-dev/publish/${publishId}/progress`)
    return response.data
  },

  // 取消发布
  cancelPublish: async (publishId: string): Promise<void> => {
    await client.post(`/skills-dev/publish/${publishId}/cancel`)
  },

  // ============ 版本管理相关 ============
  
  // 获取版本列表
  listVersions: async (skillId: number): Promise<SkillVersion[]> => {
    const response = await client.get(`/skills-dev/${skillId}/versions`)
    return response.data
  },

  // 获取版本详情
  getVersion: async (skillId: number, versionId: number): Promise<SkillVersion> => {
    const response = await client.get(`/skills-dev/${skillId}/versions/${versionId}`)
    return response.data
  },

  // 创建新版本
  createVersion: async (skillId: number, data: {
    version: string
    description?: string
    changelog?: string
  }): Promise<SkillVersion> => {
    const response = await client.post(`/skills-dev/${skillId}/versions`, data)
    return response.data
  },

  // 更新版本信息
  updateVersion: async (skillId: number, versionId: number, data: {
    description?: string
    changelog?: string
  }): Promise<SkillVersion> => {
    const response = await client.put(`/skills-dev/${skillId}/versions/${versionId}`, data)
    return response.data
  },

  // 发布版本
  publishVersion: async (skillId: number, versionId: number): Promise<SkillVersion> => {
    const response = await client.post(`/skills-dev/${skillId}/versions/${versionId}/publish`)
    return response.data
  },

  // 归档版本（回退）
  archiveVersion: async (skillId: number, versionId: number): Promise<SkillVersion> => {
    const response = await client.post(`/skills-dev/${skillId}/versions/${versionId}/archive`)
    return response.data
  },

  // 回退到指定版本
  rollbackVersion: async (skillId: number, versionId: number): Promise<SkillVersion> => {
    const response = await client.post(`/skills-dev/${skillId}/versions/${versionId}/rollback`)
    return response.data
  },

  // 下载版本包
  downloadVersion: async (skillId: number, versionId: number): Promise<Blob> => {
    const response = await client.get(`/skills-dev/${skillId}/versions/${versionId}/download`, {
      responseType: 'blob'
    })
    return response.data
  },

  // ============ 打包上传相关 ============
  
  // 打包技能
  packageSkill: async (skillId: number, version: string): Promise<{ package_id: string }> => {
    const response = await client.post(`/skills-dev/${skillId}/package`, { version })
    return response.data
  },

  // 获取打包进度
  getPackageProgress: async (packageId: string): Promise<{
    stage: 'preparing' | 'packing' | 'compressing' | 'completed' | 'failed'
    progress: number
    message: string
    files_total?: number
    files_processed?: number
  }> => {
    const response = await client.get(`/skills-dev/package/${packageId}/progress`)
    return response.data
  },

  // 上传技能包
  uploadPackage: async (skillId: number, file: File, onProgress?: (progress: number) => void): Promise<{
    version_id: number
    package_url: string
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await client.post(`/skills-dev/${skillId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
    return response.data
  },

  // ============ 权限设置相关 ============
  
  // 获取权限设置
  getPermissions: async (skillId: number): Promise<PermissionSettings> => {
    const response = await client.get(`/skills-dev/${skillId}/permissions`)
    return response.data
  },

  // 更新权限设置
  updatePermissions: async (skillId: number, settings: PermissionSettings): Promise<PermissionSettings> => {
    const response = await client.put(`/skills-dev/${skillId}/permissions`, settings)
    return response.data
  },

  // ============ 协作者管理相关 ============
  
  // 获取协作者列表
  listCollaborators: async (skillId: number): Promise<SkillCollaborator[]> => {
    const response = await client.get(`/skills-dev/${skillId}/collaborators`)
    return response.data
  },

  // 添加协作者
  addCollaborator: async (skillId: number, data: {
    email: string
    role: 'admin' | 'editor' | 'viewer'
  }): Promise<SkillCollaborator> => {
    const response = await client.post(`/skills-dev/${skillId}/collaborators`, data)
    return response.data
  },

  // 更新协作者角色
  updateCollaborator: async (skillId: number, collaboratorId: number, role: string): Promise<SkillCollaborator> => {
    const response = await client.put(`/skills-dev/${skillId}/collaborators/${collaboratorId}`, { role })
    return response.data
  },

  // 移除协作者
  removeCollaborator: async (skillId: number, collaboratorId: number): Promise<void> => {
    await client.delete(`/skills-dev/${skillId}/collaborators/${collaboratorId}`)
  },

  // ============ 图标上传相关 ============
  
  // 上传技能图标
  uploadIcon: async (skillId: number, file: File): Promise<{ icon_url: string }> => {
    const formData = new FormData()
    formData.append('icon', file)

    const response = await client.post(`/skills-dev/${skillId}/icon`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // ============ 分类和标签相关 ============
  
  // 获取技能分类列表
  listCategories: async (): Promise<string[]> => {
    const response = await client.get('/skills-dev/categories')
    return response.data
  },

  // 获取热门标签
  listPopularTags: async (limit?: number): Promise<string[]> => {
    const response = await client.get('/skills-dev/tags/popular', {
      params: { limit }
    })
    return response.data
  }
}
