import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Alert,
  Descriptions,
  Tag,
  Typography,
  Collapse,
  Divider,
  Spin,
  Empty,
  message,
} from 'antd'
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SendOutlined,
  ClearOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { routeApi } from '@/api/gateway'
import type { HttpMethod, RouteTestResult } from '@/types/gateway'
import type { RouteRule } from '@/types/gateway'

const { TextArea } = Input
const { Text, Paragraph } = Typography
const { Panel } = Collapse

const httpMethods: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const methodColors: Record<HttpMethod, string> = {
  GET: 'green',
  POST: 'blue',
  PUT: 'orange',
  DELETE: 'red',
  PATCH: 'cyan',
  HEAD: 'purple',
  OPTIONS: 'default',
}

interface RouteTesterProps {
  initialRoute?: RouteRule
}

export default function RouteTester({ initialRoute }: RouteTesterProps) {
  const [form] = Form.useForm()
  const [headers, setHeaders] = useState<{ key: string; value: string }[]>([])
  const [queryParams, setQueryParams] = useState<{ key: string; value: string }[]>([])
  const [testResult, setTestResult] = useState<RouteTestResult | null>(null)

  // 测试路由
  const testMutation = useMutation({
    mutationFn: async () => {
      const values = await form.validateFields()
      const headerMap: Record<string, string> = {}
      headers.forEach((h) => {
        if (h.key) headerMap[h.key] = h.value
      })
      const queryMap: Record<string, string> = {}
      queryParams.forEach((q) => {
        if (q.key) queryMap[q.key] = q.value
      })
      return routeApi.test({
        path: values.path,
        method: values.method,
        headers: headerMap,
        body: values.body,
        queryParams: queryMap,
      })
    },
    onSuccess: (data) => {
      setTestResult(data)
    },
    onError: (error) => {
      message.error('路由测试失败')
      console.error('Test failed:', error)
    },
  })

  React.useEffect(() => {
    if (initialRoute) {
      form.setFieldsValue({
        path: initialRoute.path,
        method: initialRoute.methods[0] || 'GET',
      })
    }
  }, [initialRoute, form])

  const handleTest = () => {
    testMutation.mutate()
  }

  const handleReset = () => {
    form.resetFields()
    setHeaders([])
    setQueryParams([])
    setTestResult(null)
  }

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }])
  }

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index))
  }

  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers]
    newHeaders[index][field] = value
    setHeaders(newHeaders)
  }

  const addQueryParam = () => {
    setQueryParams([...queryParams, { key: '', value: '' }])
  }

  const removeQueryParam = (index: number) => {
    setQueryParams(queryParams.filter((_, i) => i !== index))
  }

  const updateQueryParam = (index: number, field: 'key' | 'value', value: string) => {
    const newParams = [...queryParams]
    newParams[index][field] = value
    setQueryParams(newParams)
  }

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'green'
    if (status >= 300 && status < 400) return 'blue'
    if (status >= 400 && status < 500) return 'orange'
    return 'red'
  }

  const formatJson = (str: string) => {
    try {
      return JSON.stringify(JSON.parse(str), null, 2)
    } catch {
      return str
    }
  }

  return (
    <Card
      title={
        <Space>
          <ThunderboltOutlined />
          路由测试工具
        </Space>
      }
      extra={
        <Space>
          <Button icon={<ClearOutlined />} onClick={handleReset}>
            清空
          </Button>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleTest}
            loading={testMutation.isPending}
          >
            发送请求
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item label="请求路径" required>
          <Input.Group compact>
            <Form.Item name="method" noStyle initialValue="GET">
              <Select style={{ width: 100 }}>
                {httpMethods.map((method) => (
                  <Select.Option key={method} value={method}>
                    <Tag color={methodColors[method]} style={{ margin: 0 }}>
                      {method}
                    </Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item
              name="path"
              noStyle
              rules={[{ required: true, message: '请输入请求路径' }]}
            >
              <Input style={{ width: 'calc(100% - 100px)' }} placeholder="/api/v1/users/123" />
            </Form.Item>
          </Input.Group>
        </Form.Item>

        <Collapse ghost>
          <Panel header="查询参数" key="queryParams">
            {queryParams.map((param, index) => (
              <Input.Group key={index} compact style={{ marginBottom: 8 }}>
                <Input
                  style={{ width: '40%' }}
                  placeholder="参数名"
                  value={param.key}
                  onChange={(e) => updateQueryParam(index, 'key', e.target.value)}
                />
                <Input
                  style={{ width: '50%' }}
                  placeholder="参数值"
                  value={param.value}
                  onChange={(e) => updateQueryParam(index, 'value', e.target.value)}
                />
                <Button danger onClick={() => removeQueryParam(index)}>
                  删除
                </Button>
              </Input.Group>
            ))}
            <Button type="dashed" onClick={addQueryParam} block>
              + 添加查询参数
            </Button>
          </Panel>

          <Panel header="请求头" key="headers">
            {headers.map((header, index) => (
              <Input.Group key={index} compact style={{ marginBottom: 8 }}>
                <Input
                  style={{ width: '40%' }}
                  placeholder="Header Name"
                  value={header.key}
                  onChange={(e) => updateHeader(index, 'key', e.target.value)}
                />
                <Input
                  style={{ width: '50%' }}
                  placeholder="Header Value"
                  value={header.value}
                  onChange={(e) => updateHeader(index, 'value', e.target.value)}
                />
                <Button danger onClick={() => removeHeader(index)}>
                  删除
                </Button>
              </Input.Group>
            ))}
            <Button type="dashed" onClick={addHeader} block>
              + 添加请求头
            </Button>
          </Panel>

          <Panel header="请求体" key="body">
            <Form.Item name="body">
              <TextArea
                rows={6}
                placeholder='{"key": "value"}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>
          </Panel>
        </Collapse>
      </Form>

      <Divider>测试结果</Divider>

      {testMutation.isPending && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在发送请求...</div>
        </div>
      )}

      {!testMutation.isPending && !testResult && (
        <Empty description="发送请求后在此查看结果" />
      )}

      {testResult && (
        <div>
          <Alert
            message={
              testResult.matched ? (
                <Space>
                  <CheckCircleOutlined />
                  路由匹配成功
                </Space>
              ) : (
                <Space>
                  <CloseCircleOutlined />
                  路由匹配失败
                </Space>
              )
            }
            description={
              testResult.matched
                ? `匹配到路由: ${testResult.routeName} (${testResult.routeId})`
                : '未找到匹配的路由规则，请检查路径和方法是否正确'
            }
            type={testResult.matched ? 'success' : 'error'}
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="HTTP 状态码">
              <Tag color={getStatusColor(testResult.statusCode)}>
                {testResult.statusCode}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="响应时间">
              <Text strong>{testResult.responseTime}ms</Text>
            </Descriptions.Item>
          </Descriptions>

          {testResult.errors && testResult.errors.length > 0 && (
            <Alert
              type="error"
              style={{ marginTop: 16 }}
              message="错误信息"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {testResult.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              }
            />
          )}

          <Card title="响应头" size="small" style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              {Object.entries(testResult.responseHeaders).map(([key, value]) => (
                <Descriptions.Item key={key} label={key}>
                  <Text code>{value}</Text>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>

          <Card title="响应体" size="small" style={{ marginTop: 16 }}>
            <Paragraph>
              <pre
                style={{
                  background: '#f5f5f5',
                  padding: 16,
                  borderRadius: 4,
                  maxHeight: 400,
                  overflow: 'auto',
                }}
              >
                {formatJson(testResult.responseBody)}
              </pre>
            </Paragraph>
          </Card>
        </div>
      )}
    </Card>
  )
}
