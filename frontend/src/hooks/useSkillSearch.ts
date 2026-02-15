import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillSearchApi, SkillSearchRequest } from '@/api/skillSearch'
import { message } from 'antd'

// 搜索技能
export function useSkillSearch(params: SkillSearchRequest) {
  return useQuery({
    queryKey: ['skillSearch', params],
    queryFn: () => skillSearchApi.search(params),
    staleTime: 30000, // 30秒内不重新请求
  })
}

// 获取分类列表
export function useSkillCategories() {
  return useQuery({
    queryKey: ['skillCategories'],
    queryFn: () => skillSearchApi.getCategories(),
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  })
}

// 获取搜索建议
export function useSkillSuggestions(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['skillSuggestions', query],
    queryFn: () => skillSearchApi.getSuggestions(query),
    enabled: enabled && query.length >= 2,
    staleTime: 60000, // 1分钟内不重新请求
  })
}

// 获取技能详情
export function useSkillDetail(skillId: number | null) {
  return useQuery({
    queryKey: ['skillDetail', skillId],
    queryFn: () => skillSearchApi.getSkill(skillId!),
    enabled: skillId !== null,
  })
}

// 安装技能
export function useInstallSkill() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (skillId: number) => skillSearchApi.installSkill(skillId),
    onSuccess: () => {
      message.success('安装成功')
      // 刷新搜索结果
      queryClient.invalidateQueries({ queryKey: ['skillSearch'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '安装失败')
    },
  })
}
