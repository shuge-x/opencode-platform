import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from '../index'
import { useAuthStore } from '@/stores/authStore'

// Mock auth API
jest.mock('@/api/auth', () => ({
  authApi: {
    login: jest.fn().mockResolvedValue({ access_token: 'mock-token' }),
  },
}))

// Mock useNavigate
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

// Mock useAuthStore
jest.mock('@/stores/authStore', () => ({
  useAuthStore: jest.fn(),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  )
}

describe('LoginPage', () => {
  const mockLogin = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useAuthStore as unknown as jest.Mock).mockImplementation((selector) => {
      return selector({ login: mockLogin })
    })
  })

  it('should render login form', () => {
    renderWithRouter(<LoginPage />)
    
    expect(screen.getByText('登录')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('邮箱')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument()
  })

  it('should render submit button', () => {
    renderWithRouter(<LoginPage />)
    
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument()
  })

  it('should render register link', () => {
    renderWithRouter(<LoginPage />)
    
    expect(screen.getByText('立即注册')).toBeInTheDocument()
  })

  it('should show validation error for empty email', async () => {
    renderWithRouter(<LoginPage />)
    
    const submitButton = screen.getByRole('button', { name: '登录' })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入邮箱')).toBeInTheDocument()
    })
  })

  it('should show validation error for empty password', async () => {
    renderWithRouter(<LoginPage />)
    
    const emailInput = screen.getByPlaceholderText('邮箱')
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    
    const submitButton = screen.getByRole('button', { name: '登录' })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入密码')).toBeInTheDocument()
    })
  })

  it('should show validation error for invalid email', async () => {
    renderWithRouter(<LoginPage />)
    
    const emailInput = screen.getByPlaceholderText('邮箱')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    
    const submitButton = screen.getByRole('button', { name: '登录' })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入有效的邮箱地址')).toBeInTheDocument()
    })
  })

  it('should have correct layout styles', () => {
    const { container } = renderWithRouter(<LoginPage />)
    
    const layoutDiv = container.firstChild as HTMLElement
    expect(layoutDiv.style.height).toBe('100vh')
    expect(layoutDiv.style.display).toBe('flex')
  })
})
