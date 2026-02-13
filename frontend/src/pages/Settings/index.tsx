import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Card, message, Statistic, Row, Col } from 'antd'
import { UserOutlined, MailOutlined } from '@ant-design/icons'
import client from '@/api/client'
import { useAuthStore } from '@/stores/authStore'

export default function SettingsPage() {
  const [form] = Form.useForm()
  const user = useAuthStore((state) => state.user)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadUserInfo()
  }, [])

  const loadUserInfo = async () => {
    try {
      const response = await client.get('/users/me')
      form.setFieldsValue(response.data)
    } catch (error: any) {
      message.error('加载用户信息失败')
    }
  }

  const updateUserInfo = async (values: any) => {
    setLoading(true)
    try {
      await client.put('/users/me', values)
      message.success('更新成功')
      loadUserInfo()
    } catch (error: any) {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>用户设置</h2>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="个人信息" style={{ marginBottom: '20px' }}>
            <Form
              form={form}
              layout="vertical"
              onFinish={updateUserInfo}
            >
              <Form.Item name="email" label="邮箱">
                <Input prefix={<MailOutlined />} disabled />
              </Form.Item>

              <Form.Item name="username" label="用户名">
                <Input prefix={<UserOutlined />} />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  保存
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="API配额" style={{ marginBottom: '20px' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="今日已使用"
                  value={user?.api_usage_today || 0}
                  suffix="次"
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="每日配额"
                  value={user?.api_quota_daily || 100}
                  suffix="次"
                />
              </Col>
            </Row>
          </Card>

          <Card title="账户信息">
            <p><strong>角色：</strong>{user?.role || 'user'}</p>
            <p><strong>状态：</strong>{user?.is_active ? '正常' : '已禁用'}</p>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
