import client from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await client.post('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<void> => {
    await client.post('/auth/register', data)
  },

  getCurrentUser: async () => {
    const response = await client.get('/users/me')
    return response.data
  },
}
