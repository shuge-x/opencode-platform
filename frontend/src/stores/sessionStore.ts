import { create } from 'zustand'

export interface Session {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messageCount: number
  lastMessage?: string
}

interface SessionState {
  sessions: Session[]
  currentSessionId: string | null
  searchQuery: string
  loading: boolean
  
  // Actions
  setSessions: (sessions: Session[]) => void
  addSession: (session: Session) => void
  updateSession: (id: string, updates: Partial<Session>) => void
  deleteSession: (id: string) => void
  setCurrentSession: (id: string | null) => void
  setSearchQuery: (query: string) => void
  setLoading: (loading: boolean) => void
  
  // Computed
  getFilteredSessions: () => Session[]
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [
    {
      id: '1',
      title: 'React项目开发讨论',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 15,
      lastMessage: '好的，我们继续完善组件...'
    },
    {
      id: '2',
      title: 'API接口设计',
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
      messageCount: 8,
      lastMessage: 'RESTful API已设计完成'
    },
    {
      id: '3',
      title: '数据库优化方案',
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
      messageCount: 22,
      lastMessage: '索引优化建议已提交'
    }
  ],
  currentSessionId: null,
  searchQuery: '',
  loading: false,

  setSessions: (sessions) => set({ sessions }),
  
  addSession: (session) => set((state) => ({
    sessions: [session, ...state.sessions]
  })),
  
  updateSession: (id, updates) => set((state) => ({
    sessions: state.sessions.map(s => s.id === id ? { ...s, ...updates } : s)
  })),
  
  deleteSession: (id) => set((state) => ({
    sessions: state.sessions.filter(s => s.id !== id),
    currentSessionId: state.currentSessionId === id ? null : state.currentSessionId
  })),
  
  setCurrentSession: (id) => set({ currentSessionId: id }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  setLoading: (loading) => set({ loading }),
  
  getFilteredSessions: () => {
    const { sessions, searchQuery } = get()
    if (!searchQuery) return sessions
    return sessions.filter(s => 
      s.title.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }
}))
