import React from 'react'
import { render, screen } from '@testing-library/react'
import MessageList from '../MessageList'

// Mock ReactMarkdown
jest.mock('react-markdown', () => {
  return ({ children }: { children: string }) => <div>{children}</div>
})

describe('MessageList', () => {
  const mockMessages = [
    {
      id: '1',
      type: 'user' as const,
      content: 'Hello, how are you?',
      timestamp: '2024-01-15T10:30:00Z',
    },
    {
      id: '2',
      type: 'assistant' as const,
      content: 'I am doing well, thank you!',
      timestamp: '2024-01-15T10:30:30Z',
    },
    {
      id: '3',
      type: 'system' as const,
      content: 'Processing your request...',
      timestamp: '2024-01-15T10:30:15Z',
    },
  ]

  it('should render all messages', () => {
    render(<MessageList messages={mockMessages} />)
    
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument()
    expect(screen.getByText('Processing your request...')).toBeInTheDocument()
  })

  it('should render empty list when no messages', () => {
    const { container } = render(<MessageList messages={[]} />)
    
    expect(container.querySelector('.message-list')).toBeInTheDocument()
    expect(container.querySelectorAll('.message-item').length).toBe(0)
  })

  it('should display user label for user messages', () => {
    render(<MessageList messages={[mockMessages[0]]} />)
    
    expect(screen.getByText('用户')).toBeInTheDocument()
  })

  it('should display AI assistant label for assistant messages', () => {
    render(<MessageList messages={[mockMessages[1]]} />)
    
    expect(screen.getByText('AI助手')).toBeInTheDocument()
  })

  it('should display system label for system messages', () => {
    render(<MessageList messages={[mockMessages[2]]} />)
    
    expect(screen.getByText('系统')).toBeInTheDocument()
  })

  it('should render message with metadata', () => {
    const messageWithMetadata = [
      {
        id: '4',
        type: 'system' as const,
        content: 'Tool executed',
        timestamp: '2024-01-15T10:31:00Z',
        metadata: {
          tool: 'CodeGenerator',
          args: { language: 'typescript' },
        },
      },
    ]
    
    render(<MessageList messages={messageWithMetadata} />)
    
    expect(screen.getByText('CodeGenerator')).toBeInTheDocument()
  })

  it('should apply correct message type class', () => {
    const { container } = render(<MessageList messages={[mockMessages[0]]} />)
    
    expect(container.querySelector('.message-user')).toBeInTheDocument()
  })

  it('should render timestamps', () => {
    render(<MessageList messages={mockMessages} />)
    
    // Check that timestamps are rendered (they will be formatted)
    const timeElements = document.querySelectorAll('.message-time')
    expect(timeElements.length).toBe(mockMessages.length)
  })
})
