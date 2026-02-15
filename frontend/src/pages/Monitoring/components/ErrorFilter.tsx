import { Form, Input, Select, Button, Space, Card } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { useState } from 'react'

interface ErrorFilterProps {
  onFilter: (filters: {
    skillName?: string
    errorType?: string
    timeRange?: string
  }) => void
  loading?: boolean
}

export default function ErrorFilter({ onFilter, loading = false }: ErrorFilterProps) {
  const [form] = Form.useForm()

  const handleSearch = () => {
    const values = form.getFieldsValue()
    onFilter(values)
  }

  const handleReset = () => {
    form.resetFields()
    onFilter({})
  }

  return (
    <Card style={{ marginBottom: 16 }}>
      <Form
        form={form}
        layout="inline"
        style={{ gap: '16px' }}
      >
        <Form.Item name="skillName" label="技能名称">
          <Input
            placeholder="搜索技能名称"
            style={{ width: 200 }}
            onPressEnter={handleSearch}
          />
        </Form.Item>

        <Form.Item name="errorType" label="错误类型">
          <Select
            placeholder="选择错误类型"
            style={{ width: 200 }}
            allowClear
            options={[
              { label: 'TimeoutError', value: 'TimeoutError' },
              { label: 'ValidationError', value: 'ValidationError' },
              { label: 'NetworkError', value: 'NetworkError' },
              { label: 'AuthError', value: 'AuthError' },
              { label: 'RateLimitError', value: 'RateLimitError' },
              { label: 'InternalError', value: 'InternalError' },
            ]}
          />
        </Form.Item>

        <Form.Item name="timeRange" label="时间范围">
          <Select
            placeholder="选择时间范围"
            style={{ width: 150 }}
            allowClear
            options={[
              { label: '最近 1 小时', value: '1h' },
              { label: '最近 6 小时', value: '6h' },
              { label: '最近 24 小时', value: '24h' },
              { label: '最近 7 天', value: '7d' },
              { label: '最近 30 天', value: '30d' },
            ]}
          />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              loading={loading}
            >
              搜索
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}
