import React, { useEffect, useState } from 'react'
import { List, Button, Modal, Input, message, Empty, Spin } from 'antd'
import { PlusOutlined, DeleteOutlined, MessageOutlined } from '@ant-design/icons'
import client from '@/api/client'
import { useSessionStore } from '@/stores/sessionStore'
import './SessionSidebar.css'

export default function SessionSidebar() {
  const { sessions, currentSession, setSessions, setCurrentSession, addSession, removeSession } = useSessionStore()
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')

  // 加载会话列表
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const response = await client.get('/sessions')
      setSessions(response.data)
    } catch (error: any) {
      message.error('加载会话失败')
    } finally {
      setLoading(false)
    }
  }

  const createSession = async () => {
    if (!newSessionTitle.trim()) {
      message.warning('请输入会话标题')
      return
    }

    try {
      const response = await client.post('/sessions', {
        context: { title: newSessionTitle }
      })
      addSession(response.data)
      setCurrentSession(response.data)
      setCreateModalVisible(false)
      setNewSessionTitle('')
      message.success('创建成功')
    } catch (error: any) {
      message.error('创建会话失败')
    }
  }

  const deleteSession = async (sessionId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个会话吗？',
      onOk: async () => {
        try {
          await client.delete(`/sessions/${sessionId}`)
          removeSession(sessionId)
          message.success('删除成功')
        } catch (error: any) {
          message.error('删除失败')
        }
      }
    })
  }

  return (
    <div className="session-sidebar">
      <div className="sidebar-header">
        <h3>会话列表</h3>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          新建
        </Button>
      </div>

      <div className="session-list">
        {loading ? (
          <Spin />
        ) : sessions.length === 0 ? (
          <Empty description="暂无会话" />
        ) : (
          <List
            dataSource={sessions}
            renderItem={(session) => (
              <List.Item
                className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
                onClick={() => setCurrentSession(session)}
              >
                <div className="session-info">
                  <MessageOutlined className="session-icon" />
                  <div className="session-title">
                    {session.context?.title || '未命名会话'}
                  </div>
                </div>
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteSession(session.id)
                  }}
                />
              </List.Item>
            )}
          />
        )}
      </div>

      <Modal
        title="创建新会话"
        open={createModalVisible}
        onOk={createSession}
        onCancel={() => setCreateModalVisible(false)}
      >
        <Input
          placeholder="会话标题"
          value={newSessionTitle}
          onChange={(e) => setNewSessionTitle(e.target.value)}
          onPressEnter={createSession}
        />
      </Modal>
    </div>
  )
}
