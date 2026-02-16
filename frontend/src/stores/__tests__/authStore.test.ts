import { useAuthStore } from '../authStore'

// Mock localStorage
const localStorageMock = {
  store: {} as Record<string, string>,
  getItem: jest.fn((key: string) => localStorageMock.store[key] || null),
  setItem: jest.fn((key: string, value: string) => {
    localStorageMock.store[key] = value
  }),
  removeItem: jest.fn((key: string) => {
    delete localStorageMock.store[key]
  }),
  clear: jest.fn(() => {
    localStorageMock.store = {}
  }),
  length: 0,
  key: jest.fn(),
}

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state and localStorage
    localStorageMock.store = {}
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  describe('initial state', () => {
    it('should have null user initially', () => {
      const { user } = useAuthStore.getState()
      expect(user).toBeNull()
    })

    it('should have null token initially', () => {
      const { token } = useAuthStore.getState()
      expect(token).toBeNull()
    })

    it('should not be authenticated initially', () => {
      const { isAuthenticated } = useAuthStore.getState()
      expect(isAuthenticated).toBe(false)
    })
  })

  describe('login', () => {
    it('should set user and token on login', () => {
      const { login } = useAuthStore.getState()
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }

      login(mockUser, 'mock-token')

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.token).toBe('mock-token')
      expect(state.isAuthenticated).toBe(true)
    })

    it('should store token in localStorage on login', () => {
      const { login } = useAuthStore.getState()
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }

      login(mockUser, 'mock-token')

      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'mock-token')
    })

    it('should update isAuthenticated to true on login', () => {
      const { login, isAuthenticated } = useAuthStore.getState()
      expect(isAuthenticated).toBe(false)

      login({
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }, 'token')

      expect(useAuthStore.getState().isAuthenticated).toBe(true)
    })
  })

  describe('logout', () => {
    it('should clear user and token on logout', () => {
      const { login, logout } = useAuthStore.getState()
      
      // First login
      login({
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }, 'mock-token')

      // Then logout
      logout()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })

    it('should remove token from localStorage on logout', () => {
      const { login, logout } = useAuthStore.getState()
      
      login({
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }, 'mock-token')

      logout()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })
  })

  describe('setUser', () => {
    it('should update user without affecting token', () => {
      const { login, setUser } = useAuthStore.getState()
      
      login({
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
      }, 'mock-token')

      const updatedUser = {
        id: '1',
        email: 'updated@example.com',
        username: 'updateduser',
        role: 'admin',
      }

      setUser(updatedUser)

      const state = useAuthStore.getState()
      expect(state.user).toEqual(updatedUser)
      expect(state.token).toBe('mock-token')
      expect(state.isAuthenticated).toBe(true)
    })
  })
})
