import React, { useState } from 'react'
import { Tabs, Card, Button, Space } from 'antd'
import {
  ApiOutlined,
  ClockCircleOutlined,
  KeyOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import RouteList from './components/RouteList'
import RateLimitConfig from './components/RateLimitConfig'
import ApiKeyManager from './components/ApiKeyManager'
import RouteTester from './components/RouteTester'
import GatewayOverview from './components/GatewayOverview'
import type { RouteRule } from '@/types/gateway'

export default function GatewayPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [testRoute, setTestRoute] = useState<RouteRule | undefined>(undefined)

  const handleTestRoute = (route: RouteRule) => {
    setTestRoute(route)
    setActiveTab('test')
  }

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <DashboardOutlined />
          概览
        </span>
      ),
      children: <GatewayOverview />,
    },
    {
      key: 'routes',
      label: (
        <span>
          <ApiOutlined />
          路由规则
        </span>
      ),
      children: <RouteList onTestRoute={handleTestRoute} />,
    },
    {
      key: 'rate-limits',
      label: (
        <span>
          <ClockCircleOutlined />
          限流配置
        </span>
      ),
      children: <RateLimitConfig />,
    },
    {
      key: 'api-keys',
      label: (
        <span>
          <KeyOutlined />
          API 密钥
        </span>
      ),
      children: <ApiKeyManager />,
    },
    {
      key: 'test',
      label: (
        <span>
          <ThunderboltOutlined />
          路由测试
        </span>
      ),
      children: <RouteTester initialRoute={testRoute} />,
    },
  ]

  return (
    <div style={{ padding: '0 0 24px' }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>API 网关配置</h2>
        <p style={{ color: '#666', margin: '8px 0 0' }}>
          管理 API 路由规则、限流策略和密钥访问
        </p>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
        tabBarExtraContent={
          <Space>
            <Button type="link" onClick={() => setActiveTab('test')}>
              快速测试路由
            </Button>
          </Space>
        }
      />
    </div>
  )
}
