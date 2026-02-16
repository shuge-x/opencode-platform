import React from 'react'
import { render, screen } from '@testing-library/react'
import HomePage from '../index'

describe('HomePage', () => {
  it('should render welcome title', () => {
    render(<HomePage />)
    
    expect(screen.getByText('OpenCode Web 平台')).toBeInTheDocument()
  })

  it('should render welcome message', () => {
    render(<HomePage />)
    
    expect(screen.getByText('欢迎使用 OpenCode Web 管理平台')).toBeInTheDocument()
  })

  it('should render description', () => {
    render(<HomePage />)
    
    expect(screen.getByText('基于 opencode 的可视化管理系统')).toBeInTheDocument()
  })

  it('should have centered layout', () => {
    const { container } = render(<HomePage />)
    
    const mainDiv = container.firstChild as HTMLElement
    expect(mainDiv.style.textAlign).toBe('center')
  })

  it('should have padding', () => {
    const { container } = render(<HomePage />)
    
    const mainDiv = container.firstChild as HTMLElement
    expect(mainDiv.style.padding).toBe('40px')
  })
})
