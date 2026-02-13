import React, { useState, useEffect, useRef } from 'react'
import { Input, Button, message as antdMessage, Spin } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { useWebSocket } from '@/hooks/useWebSocket'
import MessageList from './MessageList'
import './ChatWindow.css'

const { TextArea } = Input

interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: any
}

interface ChatWindowProps {
  sessionId: string
  token: string
}

export default function ChatWindow({ sessionId, token }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // WebSocket连接
  const wsUrl = `ws://localhost:8000/ws/session/${sessionId}?token=${token}`
  const { isConnected, send, error } = useWebSocket(wsUrl, {
    onMessage: (data) => {
      console.log('Received message:', data)

      if (data.type === 'task_received') {
        // 任务已接收
        setIsLoading(true)
        const systemMessage: Message = {
          id: Date.now().toString(),
          type: 'system',
          content: 'AI正在思考...',
          timestamp: data.timestamp
        }
        setMessages(prev => [...prev, systemMessage])
      } else if (data.type === 'thinking') {
        // AI思考过程
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.type === 'system') {
            return [...prev.slice(0, -1), { ...last, content: data.thought }]
          }
          return prev
        })
      } else if (data.type === 'tool_call') {
        // 工具调用
        const toolMessage: Message = {
          id: Date.now().toString(),
          type: 'system',
          content: `执行工具: ${data.tool}`,
          timestamp: new Date().toISOString(),
          metadata: data
        }
        setMessages(prev => [...prev, toolMessage])
      } else if (data.type === 'response') {
        // AI响应
        setIsLoading(false)
        const assistantMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: data.content,
          timestamp: data.timestamp || new Date().toISOString()
        }
        setMessages(prev => [...prev, assistantMessage])
      } else if (data.type === 'error') {
        // 错误
        setIsLoading(false)
        antdMessage.error(data.message)
      }
    },
    onError: () => {
      antdMessage.error('WebSocket连接失败')
    }
  })

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 发送消息
  const handleSend = () => {
    if (!inputValue.trim()) {
      return
    }

    if (!isConnected) {
      antdMessage.error('WebSocket未连接')
      return
    }

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    // 发送到WebSocket
    send({
      type: 'chat',
      content: inputValue
    })

    setInputValue('')
    setIsLoading(true)
  }

  // 处理Enter键
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-window">
      {/* 连接状态 */}
      <div className="connection-status">
        {isConnected ? (
          <span style={{ color: '#52c41a' }}>● 已连接</span>
        ) : (
          <span style={{ color: '#ff4d4f' }}>● 未连接</span>
        )}
      </div>

      {/* 消息列表 */}
      <div className="messages-container">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="input-area">
        <TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息... (Shift+Enter换行)"
          autoSize={{ minRows: 2, maxRows: 4 }}
          disabled={isLoading}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={isLoading}
          disabled={!inputValue.trim() || !isConnected}
        >
          发送
        </Button>
      </div>

      {error && (
        <div className="error-message">
          错误: {error}
        </div>
      )}
    </div>
  )
}
