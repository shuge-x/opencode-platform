import { useParams, useNavigate } from 'react-router-dom'
import { Typography, Button, message } from 'antd'
import ChatWindow from '@/components/Chat/ChatWindow'
import { useAuthStore } from '@/stores/authStore'

const { Title } = Typography

export default function ChatPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const token = useAuthStore((state) => state.token)

  if (!sessionId) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <Title level={3}>请选择或创建会话</Title>
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    )
  }

  if (!token) {
    message.error('请先登录')
    navigate('/login')
    return null
  }

  return (
    <div style={{ height: 'calc(100vh - 64px - 40px)' }}>
      <ChatWindow sessionId={sessionId} token={token} />
    </div>
  )
}
