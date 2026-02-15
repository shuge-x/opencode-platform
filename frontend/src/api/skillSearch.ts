import client from './client'

export interface PublishedSkill {
  id: number
  skill_id: number
  publisher_id: number
  name: string
  slug: string
  description?: string
  version: string
  category?: string
  tags?: string[]
  price: string
  currency: string
  status: string
  is_public: boolean
  is_featured: boolean
  download_count: number
  install_count: number
  rating: string
  rating_count: number
  homepage_url?: string
  repository_url?: string
  documentation_url?: string
  license: string
  published_at?: string
  created_at: string
  updated_at: string
}

export interface SkillSearchRequest {
  search?: string
  category?: string
  min_rating?: number
  price_filter?: 'free' | 'paid' | 'all'
  sort_by?: 'latest' | 'popular' | 'rating'
  page?: number
  page_size?: number
}

export interface SkillSearchResponse {
  items: PublishedSkill[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface Category {
  name: string
  icon?: string
  count: number
}

export const skillSearchApi = {
  // 搜索技能
  search: async (params: SkillSearchRequest): Promise<SkillSearchResponse> => {
    const queryParams: any = {}
    
    if (params.search) queryParams.search = params.search
    if (params.category) queryParams.category = params.category
    if (params.min_rating !== undefined) queryParams.min_rating = params.min_rating
    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    
    // 排序参数映射
    const sortMapping: { [key: string]: string } = {
      latest: 'created_at',
      popular: 'download_count',
      rating: 'rating'
    }
    
    if (params.sort_by) {
      queryParams.sort_by = sortMapping[params.sort_by] || 'download_count'
      queryParams.sort_order = params.sort_by === 'latest' ? 'desc' : 'desc'
    }
    
    const response = await client.get('/skills-hub', { params: queryParams })
    return response.data
  },

  // 获取分类列表
  getCategories: async (): Promise<Category[]> => {
    // 临时实现：从搜索结果中提取分类
    // TODO: 后端应该提供专门的分类列表API
    const response = await client.get<SkillSearchResponse>('/skills-hub', {
      params: { page_size: 100 }
    })
    
    const categoryMap = new Map<string, number>()
    response.data.items.forEach(skill => {
      if (skill.category) {
        categoryMap.set(skill.category, (categoryMap.get(skill.category) || 0) + 1)
      }
    })
    
    const categories: Category[] = Array.from(categoryMap.entries()).map(([name, count]) => ({
      name,
      count
    }))
    
    // 添加默认分类
    categories.unshift({ name: '全部', count: response.data.total })
    
    return categories
  },

  // 获取技能详情
  getSkill: async (skillId: number): Promise<PublishedSkill> => {
    const response = await client.get(`/skills-hub/${skillId}`)
    return response.data
  },

  // 获取搜索建议
  getSuggestions: async (query: string): Promise<string[]> => {
    // 临时实现：通过搜索获取技能名称作为建议
    // TODO: 后端应该提供专门的搜索建议API
    if (!query || query.length < 2) return []
    
    const response = await client.get<SkillSearchResponse>('/skills-hub', {
      params: { search: query, page_size: 5 }
    })
    
    return response.data.items
      .map(skill => skill.name)
      .filter((name, index, self) => self.indexOf(name) === index)
  },

  // 安装技能
  installSkill: async (skillId: number): Promise<void> => {
    await client.post(`/skills-hub/${skillId}/install`)
  }
}
