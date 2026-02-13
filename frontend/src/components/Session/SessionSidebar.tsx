import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  List,
  Button,
  Input,
  Empty,
  Modal,
  message,
  Popconfirm,
  Typography,
  Tooltip,
  Badge
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  DeleteOutlined,
  MessageOutlined,
  EditOutlined
} from '@ant-design/icons'
import { useSessionStore, Session } from '@/stores/sessionStore'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Title } = Typography

export default function SessionSidebar() {
  const navigate = useNavigate()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')

  const {
    sessions,
    currentSessionId,
    searchQuery,
    addSession,
    updateSession,
    deleteSession,
    setCurrentSession,
    setSearchQuery
  } = useSessionStore()

  const handleCreateSession = () => {
    if (!newSessionTitle.trim()) {
      message.warning('请输入会话标题')
      return
    }

    const newSession: Session = {
      id: Date.now().toString(),
      title: newSessionTitle,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 0
    }

    addSession(newSession)
    setNewSessionTitle('')
    setCreateModalVisible(false)
    message.success('会话创建成功')
    
    // Navigate to new session
    setCurrentSession(newSession.id)
    navigate(`/chat/${newSession.id}`)
  }

  const handleSelectSession = (sessionId: string) => {
    setCurrentSession(sessionId)
    navigate(`/chat/${sessionId}`)
  }

  const handleDeleteSession = (sessionId: string) => {
    deleteSession(sessionId)
    message.success('会话已删除')
  }

  const handleEditSession = (session: Session) => {
    setEditingId(session.id)
    setEditingTitle(session.title)
  }

  const handleSaveEdit = () => {
    if (!editingId || !editingTitle.trim()) return
    
    updateSession(editingId, {
      title: editingTitle,
      updatedAt: new Date().toISOString()
    })
    
    setEditingId(null)
    setEditingTitle('')
    message.success('会话标题已更新')
  }

  const filteredSessions = sessions.filter(s =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#fff',
      borderRight: '1px solid #f0f0f0'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <Title level={4} style={{ margin: 0, marginBottom: 12 }}>
          会话列表
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={() => setCreateModalVisible(true)}
        >
          新建会话
        </Button>
      </div>

      {/* Search */}
      <div style={{ padding: '12px 16px' }}>
        <Input
          placeholder="搜索会话..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
        />
      </div>

      {/* Session List */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 8px' }}>
        {filteredSessions.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={searchQuery ? "未找到匹配的会话" : "暂无会话"}
            style={{ marginTop: 40 }}
          />
        ) : (
          <List
            dataSource={filteredSessions}
            renderItem={(session) => (
              <List.Item
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
                style={{
                  cursor: 'pointer',
                  padding: '12px',
                  borderRadius: '8px',
                  marginBottom: '4px',
                  background: currentSessionId === session.id ? '#e6f4ff' : 'transparent',
                  border: currentSessionId === session.id ? '1px solid #1890ff' : '1px solid transparent',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  if (currentSessionId !== session.id) {
                    e.currentTarget.style.background = '#f5f5f5'
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentSessionId !== session.id) {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  {editingId === session.id ? (
                    <Input
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={handleSaveEdit}
                      onPressEnter={handleSaveEdit}
                      onClick={(e) => e.stopPropagation()}
                      size="small"
                    />
                  ) : (
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                        <MessageOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                        <Text strong ellipsis style={{ flex: 1 }}>
                          {session.title}
                        </Text>
                        <Badge
                          count={session.messageCount}
                          style={{ backgroundColor: '#52c41a' }}
                        />
                      </div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dayjs(session.updatedAt).fromNow()}
                      </Text>
                      {session.lastMessage && (
                        <Text
                          type="secondary"
                          ellipsis
                          style={{ fontSize: 12, display: 'block', marginTop: 4 }}
                        >
                          {session.lastMessage}
                        </Text>
                      )}
                    </>
                  )}
                </div>

                {/* Actions */}
                {editingId !== session.id && (
                  <div style={{ marginLeft: 8, display: 'flex', gap: 4 }}>
                    <Tooltip title="编辑">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleEditSession(session)
                        }}
                      />
                    </Tooltip>
                    <Popconfirm
                      title="确定要删除这个会话吗？"
                      onConfirm={(e) => {
                        e?.stopPropagation()
                        handleDeleteSession(session.id)
                      }}
                      onCancel={(e) => e?.stopPropagation()}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Tooltip title="删除">
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </Tooltip>
                    </Popconfirm>
                  </div>
                )}
              </List.Item>
            )}
          />
        )}
      </div>

      {/* Create Modal */}
      <Modal
        title="创建新会话"
        open={createModalVisible}
        onOk={handleCreateSession}
        onCancel={() => {
          setCreateModalVisible(false)
          setNewSessionTitle('')
        }}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="请输入会话标题"
          value={newSessionTitle}
          onChange={(e) => setNewSessionTitle(e.target.value)}
          onPressEnter={handleCreateSession}
          autoFocus
        />
      </Modal>
    </div>
  )
}
