import { create } from 'zustand'

export interface Skill {
  id: string
  name: string
  description: string
  category: string
  version: string
  author: string
  downloads: number
  rating: number
  tags: string[]
  icon?: string
  installed: boolean
  createdAt: string
  updatedAt: string
  readme?: string
}

interface SkillState {
  skills: Skill[]
  installedSkills: Skill[]
  searchQuery: string
  selectedCategory: string
  loading: boolean
  
  // Actions
  setSkills: (skills: Skill[]) => void
  installSkill: (id: string) => void
  uninstallSkill: (id: string) => void
  setSearchQuery: (query: string) => void
  setSelectedCategory: (category: string) => void
  setLoading: (loading: boolean) => void
  getSkillById: (id: string) => Skill | undefined
}

const mockSkills: Skill[] = [
  {
    id: '1',
    name: '代码生成器',
    description: '智能生成高质量代码，支持多种编程语言和框架',
    category: '开发工具',
    version: '2.1.0',
    author: 'OpenCode Team',
    downloads: 12500,
    rating: 4.8,
    tags: ['代码生成', 'AI', '效率工具'],
    installed: true,
    createdAt: '2024-01-15T00:00:00Z',
    updatedAt: '2024-02-10T00:00:00Z',
    readme: '# 代码生成器\n\n这是一个强大的AI代码生成工具...\n\n## 功能特性\n\n- 支持多种语言\n- 智能代码补全\n- 代码优化建议'
  },
  {
    id: '2',
    name: '文档助手',
    description: '自动生成项目文档，支持Markdown和API文档',
    category: '文档工具',
    version: '1.5.2',
    author: 'DocMaster',
    downloads: 8900,
    rating: 4.5,
    tags: ['文档', 'Markdown', '自动化'],
    installed: false,
    createdAt: '2024-01-20T00:00:00Z',
    updatedAt: '2024-02-08T00:00:00Z'
  },
  {
    id: '3',
    name: '数据分析',
    description: '强大的数据分析工具，支持可视化图表生成',
    category: '数据分析',
    version: '3.0.1',
    author: 'DataViz Inc',
    downloads: 15600,
    rating: 4.9,
    tags: ['数据分析', '可视化', '图表'],
    installed: true,
    createdAt: '2024-01-10T00:00:00Z',
    updatedAt: '2024-02-12T00:00:00Z'
  },
  {
    id: '4',
    name: 'API测试工具',
    description: 'RESTful API测试和调试工具，支持自动化测试',
    category: '开发工具',
    version: '1.8.5',
    author: 'APITester',
    downloads: 7200,
    rating: 4.6,
    tags: ['API', '测试', '调试'],
    installed: false,
    createdAt: '2024-01-25T00:00:00Z',
    updatedAt: '2024-02-05T00:00:00Z'
  },
  {
    id: '5',
    name: 'Git助手',
    description: '智能Git操作助手，简化版本控制流程',
    category: '开发工具',
    version: '2.3.0',
    author: 'GitMaster',
    downloads: 11200,
    rating: 4.7,
    tags: ['Git', '版本控制', '协作'],
    installed: false,
    createdAt: '2024-01-18T00:00:00Z',
    updatedAt: '2024-02-11T00:00:00Z'
  },
  {
    id: '6',
    name: 'UI组件库',
    description: '丰富的UI组件集合，快速构建美观界面',
    category: 'UI设计',
    version: '4.2.1',
    author: 'UIComponents',
    downloads: 21000,
    rating: 4.8,
    tags: ['UI', '组件', '设计'],
    installed: false,
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-02-13T00:00:00Z'
  },
  {
    id: '7',
    name: 'SQL优化器',
    description: '自动分析和优化SQL查询性能',
    category: '数据库',
    version: '1.2.4',
    author: 'SQLOptimizer',
    downloads: 5400,
    rating: 4.4,
    tags: ['SQL', '性能优化', '数据库'],
    installed: false,
    createdAt: '2024-01-30T00:00:00Z',
    updatedAt: '2024-02-09T00:00:00Z'
  },
  {
    id: '8',
    name: '部署助手',
    description: '一键部署到多种云平台，支持Docker和K8s',
    category: 'DevOps',
    version: '3.1.0',
    author: 'DeployMaster',
    downloads: 9800,
    rating: 4.6,
    tags: ['部署', 'Docker', 'K8s', '云平台'],
    installed: false,
    createdAt: '2024-01-22T00:00:00Z',
    updatedAt: '2024-02-07T00:00:00Z'
  }
]

export const useSkillStore = create<SkillState>((set, get) => ({
  skills: mockSkills,
  installedSkills: mockSkills.filter(s => s.installed),
  searchQuery: '',
  selectedCategory: 'all',
  loading: false,

  setSkills: (skills) => set({ 
    skills,
    installedSkills: skills.filter(s => s.installed)
  }),
  
  installSkill: (id) => set((state) => {
    const skills = state.skills.map(s => 
      s.id === id ? { ...s, installed: true, downloads: s.downloads + 1 } : s
    )
    return {
      skills,
      installedSkills: skills.filter(s => s.installed)
    }
  }),
  
  uninstallSkill: (id) => set((state) => {
    const skills = state.skills.map(s => 
      s.id === id ? { ...s, installed: false } : s
    )
    return {
      skills,
      installedSkills: skills.filter(s => s.installed)
    }
  }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  
  setLoading: (loading) => set({ loading }),
  
  getSkillById: (id) => get().skills.find(s => s.id === id)
}))
