import React from 'react'
import { Avatar, Tag } from 'antd'
import { UserOutlined, RobotOutlined, ToolOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import './MessageList.css'

interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: any
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <UserOutlined />
      case 'assistant':
        return <RobotOutlined />
      case 'system':
        return <ToolOutlined />
      default:
        return <UserOutlined />
    }
  }

  const getMessageColor = (type: string) => {
    switch (type) {
      case 'user':
        return '#1890ff'
      case 'assistant':
        return '#52c41a'
      case 'system':
        return '#faad14'
      default:
        return '#8c8c8c'
    }
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message-item message-${msg.type}`}>
          <div className="message-avatar">
            <Avatar
              icon={getMessageIcon(msg.type)}
              style={{ backgroundColor: getMessageColor(msg.type) }}
            />
          </div>

          <div className="message-content">
            <div className="message-header">
              <Tag color={getMessageColor(msg.type)}>
                {msg.type === 'user' ? '用户' :
                 msg.type === 'assistant' ? 'AI助手' : '系统'}
              </Tag>
              <span className="message-time">{formatTime(msg.timestamp)}</span>
            </div>

            <div className="message-text">
              {msg.type === 'assistant' ? (
                // AI消息使用Markdown渲染
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>

            {/* 工具调用信息 */}
            {msg.metadata && msg.metadata.tool && (
              <div className="tool-call-info">
                <Tag icon={<ToolOutlined />} color="blue">
                  {msg.metadata.tool}
                </Tag>
                {msg.metadata.args && (
                  <pre className="tool-args">
                    {JSON.stringify(msg.metadata.args, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
