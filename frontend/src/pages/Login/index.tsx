import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useNavigate, Link } from 'react-router-dom'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const login = useAuthStore((state) => state.login)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const onFinish = async (values: LoginForm) => {
    try {
      const response = await authApi.login(values)
      login({ id: '', email: values.email, username: '', role: 'user' }, response.access_token)
      message.success('登录成功')
      navigate('/')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败')
    }
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: '#f0f2f5'
    }}>
      <Card title="登录" style={{ width: 400 }}>
        <Form form={form} onFinish={onFinish}>
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="邮箱" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            还没有账号？ <Link to="/register">立即注册</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}
