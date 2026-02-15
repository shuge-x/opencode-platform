import client from './client'
import type {
  OverviewStats,
  SkillRanking,
  TrendData,
  CategoryDistribution,
  RatingDistribution,
  StatisticsQueryParams,
  PaginatedResponse,
} from '@/types/statistics'

// 获取总览统计数据
export const getOverviewStats = async (): Promise<OverviewStats> => {
  const response = await client.get<OverviewStats>('/statistics/overview')
  return response.data
}

// 获取技能排行（热门）
export const getPopularSkills = async (params?: StatisticsQueryParams): Promise<SkillRanking[]> => {
  const response = await client.get<SkillRanking[]>('/statistics/rankings/popular', { params })
  return response.data
}

// 获取技能排行（最新）
export const getLatestSkills = async (params?: StatisticsQueryParams): Promise<SkillRanking[]> => {
  const response = await client.get<SkillRanking[]>('/statistics/rankings/latest', { params })
  return response.data
}

// 获取技能排行（高评分）
export const getTopRatedSkills = async (params?: StatisticsQueryParams): Promise<SkillRanking[]> => {
  const response = await client.get<SkillRanking[]>('/statistics/rankings/top-rated', { params })
  return response.data
}

// 获取趋势数据
export const getTrendData = async (params?: StatisticsQueryParams): Promise<TrendData[]> => {
  const response = await client.get<TrendData[]>('/statistics/trends', { params })
  return response.data
}

// 获取分类分布
export const getCategoryDistribution = async (): Promise<CategoryDistribution[]> => {
  const response = await client.get<CategoryDistribution[]>('/statistics/categories')
  return response.data
}

// 获取评分分布
export const getRatingDistribution = async (): Promise<RatingDistribution[]> => {
  const response = await client.get<RatingDistribution[]>('/statistics/ratings')
  return response.data
}

// 获取分页数据
export const getPaginatedSkills = async (
  params?: StatisticsQueryParams
): Promise<PaginatedResponse<SkillRanking>> => {
  const response = await client.get<PaginatedResponse<SkillRanking>>('/statistics/skills', { params })
  return response.data
}

// 导出数据
export const exportStatisticsData = async (
  endpoint: string,
  format: 'csv' | 'json',
  params?: StatisticsQueryParams
): Promise<Blob> => {
  const response = await client.get(`/statistics/export/${endpoint}`, {
    params: { ...params, format },
    responseType: 'blob',
  })
  return response.data
}
