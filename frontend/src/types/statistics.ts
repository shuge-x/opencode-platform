// 统计相关类型定义

export interface OverviewStats {
  totalSkills: number
  totalDownloads: number
  totalUsers: number
  activeUsersToday: number
  growthRate: number
}

export interface SkillRanking {
  id: string
  name: string
  author: string
  downloads: number
  rating: number
  category: string
  createdAt: string
}

export interface TrendData {
  date: string
  downloads: number
  usage: number
}

export interface CategoryDistribution {
  category: string
  count: number
  percentage: number
}

export interface RatingDistribution {
  rating: number
  count: number
}

export interface ExportOptions {
  format: 'csv' | 'json'
  dateRange?: {
    start: string
    end: string
  }
  includeFields?: string[]
}

export interface StatisticsQueryParams {
  startDate?: string
  endDate?: string
  category?: string
  limit?: number
  offset?: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}
