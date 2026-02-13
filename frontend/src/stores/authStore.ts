import { create } from 'zustand'

export interface User {
  id: string
  email: string
  username: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),

  login: (user, token) => {
    localStorage.setItem('token', token)
    set({ user, token, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  setUser: (user) => set({ user }),
}))
