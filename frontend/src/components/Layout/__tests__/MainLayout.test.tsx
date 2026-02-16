import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import MainLayout from '@/components/Layout/MainLayout'

// Mock useNavigate and useLocation
const mockNavigate = jest.fn()
const mockLocation = { pathname: '/' }

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => mockLocation,
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  )
}

describe('MainLayout', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('should render the layout', () => {
    renderWithRouter(<MainLayout />)
    
    expect(screen.getByText('OpenCode')).toBeInTheDocument()
  })

  it('should render header title', () => {
    renderWithRouter(<MainLayout />)
    
    expect(screen.getByText('OpenCode Web 平台')).toBeInTheDocument()
  })

  it('should render menu items', () => {
    renderWithRouter(<MainLayout />)
    
    expect(screen.getByText('首页')).toBeInTheDocument()
    expect(screen.getByText('对话')).toBeInTheDocument()
    expect(screen.getByText('技能')).toBeInTheDocument()
    expect(screen.getByText('设置')).toBeInTheDocument()
  })

  it('should have a collapsible sider', () => {
    const { container } = renderWithRouter(<MainLayout />)
    
    expect(container.querySelector('.ant-layout-sider')).toBeInTheDocument()
  })

  it('should render content area', () => {
    const { container } = renderWithRouter(<MainLayout />)
    
    expect(container.querySelector('.ant-layout-content')).toBeInTheDocument()
  })

  it('should highlight current route', () => {
    const { container } = renderWithRouter(<MainLayout />)
    
    const selectedMenu = container.querySelector('.ant-menu-item-selected')
    expect(selectedMenu).toBeInTheDocument()
  })

  it('should navigate when menu item is clicked', () => {
    renderWithRouter(<MainLayout />)
    
    const skillsMenu = screen.getByText('技能')
    fireEvent.click(skillsMenu)
    
    expect(mockNavigate).toHaveBeenCalledWith('/skills')
  })

  it('should navigate to chat when chat menu is clicked', () => {
    renderWithRouter(<MainLayout />)
    
    const chatMenu = screen.getByText('对话')
    fireEvent.click(chatMenu)
    
    expect(mockNavigate).toHaveBeenCalledWith('/chat')
  })

  it('should navigate to home when home menu is clicked', () => {
    renderWithRouter(<MainLayout />)
    
    const homeMenu = screen.getByText('首页')
    fireEvent.click(homeMenu)
    
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('should have favorites menu item', () => {
    renderWithRouter(<MainLayout />)
    
    expect(screen.getByText('收藏')).toBeInTheDocument()
  })

  it('should have monitoring menu item', () => {
    renderWithRouter(<MainLayout />)
    
    expect(screen.getByText('监控')).toBeInTheDocument()
  })
})
