import client from './client'

export interface Skill {
  id: number
  user_id: number
  name: string
  description?: string
  version: string
  skill_type: string
  config?: any
  tags?: string[]
  git_repo_url?: string
  git_branch: string
  is_active: boolean
  is_public: boolean
  execution_count: number
  success_count: number
  failure_count: number
  created_at: string
  updated_at: string
  files: SkillFile[]
}

export interface SkillFile {
  id: number
  skill_id: number
  filename: string
  file_path: string
  file_type: string
  content?: string
  git_last_commit?: string
  git_last_modified?: string
  created_at: string
  updated_at: string
}

export interface SkillTemplate {
  name: string
  description: string
  file_structure: { [filename: string]: string }
  skill_type: string
}

export interface SkillListResponse {
  items: Skill[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export const skillsDevApi = {
  // 获取技能模板列表
  listTemplates: async (): Promise<SkillTemplate[]> => {
    const response = await client.get('/skills-dev/templates')
    return response.data
  },

  // 创建技能
  create: async (data: {
    name: string
    description?: string
    skill_type?: string
    config?: any
    tags?: string[]
    is_public?: boolean
  }, template?: string): Promise<Skill> => {
    const params = template ? { template } : {}
    const response = await client.post('/skills-dev', data, { params })
    return response.data
  },

  // 列出技能
  list: async (params?: {
    search?: string
    skill_type?: string
    is_public?: boolean
    page?: number
    page_size?: number
  }): Promise<SkillListResponse> => {
    const response = await client.get('/skills-dev', { params })
    return response.data
  },

  // 获取技能详情
  get: async (skillId: number): Promise<Skill> => {
    const response = await client.get(`/skills-dev/${skillId}`)
    return response.data
  },

  // 更新技能
  update: async (skillId: number, data: {
    name?: string
    description?: string
    config?: any
    tags?: string[]
    is_public?: boolean
  }): Promise<Skill> => {
    const response = await client.put(`/skills-dev/${skillId}`, data)
    return response.data
  },

  // 删除技能
  delete: async (skillId: number): Promise<void> => {
    await client.delete(`/skills-dev/${skillId}`)
  },

  // 创建文件
  createFile: async (skillId: number, data: {
    filename: string
    file_path: string
    file_type: string
    content?: string
  }): Promise<SkillFile> => {
    const response = await client.post(`/skills-dev/${skillId}/files`, data)
    return response.data
  },

  // 列出文件
  listFiles: async (skillId: number): Promise<SkillFile[]> => {
    const response = await client.get(`/skills-dev/${skillId}/files`)
    return response.data
  },

  // 获取文件详情
  getFile: async (skillId: number, fileId: number): Promise<SkillFile> => {
    const response = await client.get(`/skills-dev/${skillId}/files/${fileId}`)
    return response.data
  },

  // 更新文件（用于编辑器保存）
  updateFile: async (skillId: number, fileId: number, data: {
    content?: string
    filename?: string
  }): Promise<SkillFile> => {
    const response = await client.put(`/skills-dev/${skillId}/files/${fileId}`, data)
    return response.data
  },

  // 删除文件
  deleteFile: async (skillId: number, fileId: number): Promise<void> => {
    await client.delete(`/skills-dev/${skillId}/files/${fileId}`)
  },

  // 执行技能
  execute: async (data: {
    skill_id: number
    input_params?: any
  }): Promise<any> => {
    const response = await client.post('/skills-dev/execute', data)
    return response.data
  },

  // 获取执行结果
  getExecution: async (executionId: number): Promise<any> => {
    const response = await client.get(`/skills-dev/executions/${executionId}`)
    return response.data
  },

  // 获取执行日志
  getExecutionLogs: async (executionId: number): Promise<any[]> => {
    const response = await client.get(`/skills-dev/executions/${executionId}/logs`)
    return response.data
  }
}
