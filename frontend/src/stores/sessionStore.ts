import { create } from 'zustand'

export interface Session {
  id: string
  user_id: string
  messages: any[]
  context: any
  created_at: string
  updated_at: string
}

interface SessionState {
  sessions: Session[]
  currentSession: Session | null
  loading: boolean

  setSessions: (sessions: Session[]) => void
  setCurrentSession: (session: Session | null) => void
  addSession: (session: Session) => void
  removeSession: (sessionId: string) => void
  updateSession: (sessionId: string, updates: Partial<Session>) => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  currentSession: null,
  loading: false,

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session }),
  addSession: (session) => set((state) => ({
    sessions: [session, ...state.sessions]
  })),
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter((s) => s.id !== sessionId),
    currentSession: state.currentSession?.id === sessionId ? null : state.currentSession
  })),
  updateSession: (sessionId, updates) => set((state) => ({
    sessions: state.sessions.map((s) =>
      s.id === sessionId ? { ...s, ...updates } : s
    )
  }))
}))
