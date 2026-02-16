import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography, Space, Divider, Alert } from 'antd'
import { 
  BugOutlined, 
  ReloadOutlined, 
  HomeOutlined, 
  WifiOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'

const { Paragraph, Text } = Typography

export enum ErrorType {
  NETWORK = 'network',
  PERMISSION = 'permission',
  DATA = 'data',
  COMPONENT = 'component',
  UNKNOWN = 'unknown'
}

interface ErrorClassification {
  type: ErrorType
  title: string
  description: string
  icon: React.ReactNode
  suggestions: string[]
}

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
  onRetry?: () => void
  resetKeys?: any[]
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string | null
  errorClassification: ErrorClassification | null
  copied: boolean
}

function classifyError(error: Error): ErrorClassification {
  const message = error.message.toLowerCase()
  const stack = error.stack?.toLowerCase() || ''

  if (
    message.includes('network') ||
    message.includes('fetch') ||
    message.includes('timeout') ||
    message.includes('failed to fetch')
  ) {
    return {
      type: ErrorType.NETWORK,
      title: '网络连接失败',
      description: '无法连接到服务器，请检查您的网络连接',
      icon: <WifiOutlined style={{ color: '#faad14' }} />,
      suggestions: ['检查网络连接', '刷新页面', '稍后重试']
    }
  }

  if (message.includes('401') || message.includes('403') || message.includes('unauthorized')) {
    return {
      type: ErrorType.PERMISSION,
      title: '权限不足',
      description: '您没有权限访问此资源',
      icon: <SecurityScanOutlined style={{ color: '#ff4d4f' }} />,
      suggestions: ['确认已登录', '联系管理员', '重新登录']
    }
  }

  if (message.includes('undefined') || message.includes('null') || message.includes('typeerror')) {
    return {
      type: ErrorType.DATA,
      title: '数据处理错误',
      description: '数据加载或处理时出现问题',
      icon: <DatabaseOutlined style={{ color: '#ff4d4f' }} />,
      suggestions: ['刷新页面', '清除缓存', '联系技术支持']
    }
  }

  if (stack.includes('react') || message.includes('render')) {
    return {
      type: ErrorType.COMPONENT,
      title: '页面渲染错误',
      description: '页面组件渲染时出现问题',
      icon: <BugOutlined style={{ color: '#ff4d4f' }} />,
      suggestions: ['刷新页面', '返回首页', '联系技术支持']
    }
  }

  return {
    type: ErrorType.UNKNOWN,
    title: '未知错误',
    description: '发生了未预期的错误',
    icon: <BugOutlined style={{ color: '#ff4d4f' }} />,
    suggestions: ['刷新页面', '返回首页', '联系技术支持']
  }
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      errorClassification: null,
      copied: false
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      errorClassification: classifyError(error)
    }
  }

  componentDidUpdate(prevProps: Props): void {
    if (this.state.hasError && this.props.resetKeys && prevProps.resetKeys) {
      const hasKeyChanged = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      )
      if (hasKeyChanged) this.handleRetry()
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught:', error, errorInfo)
    }
    this.setState({ errorInfo })
    this.props.onError?.(error, errorInfo)
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null, errorId: null, errorClassification: null, copied: false })
    this.props.onRetry?.()
  }

  handleCopyError = (): void => {
    const { error, errorInfo, errorId, errorClassification } = this.state
    const text = `Type: ${errorClassification?.type}\nID: ${errorId}\nMessage: ${error?.message}\nStack: ${error?.stack}\nComponent: ${errorInfo?.componentStack}`
    navigator.clipboard.writeText(text).then(() => {
      this.setState({ copied: true })
      setTimeout(() => this.setState({ copied: false }), 2000)
    })
  }

  render(): ReactNode {
    const { hasError, error, errorInfo, errorId, errorClassification, copied } = this.state
    const { children, fallback, showDetails = process.env.NODE_ENV === 'development' } = this.props

    if (hasError) {
      if (fallback) return fallback

      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: '#f5f5f5' }}>
          <div style={{ maxWidth: 800, width: '100%' }}>
            <Result
              status="error"
              icon={errorClassification?.icon}
              title={errorClassification?.title || '页面出错了'}
              subTitle={errorClassification?.description || '抱歉，页面遇到了一些问题'}
              extra={[
                <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={this.handleRetry}>重试</Button>,
                <Button key="reload" icon={<ReloadOutlined />} onClick={() => window.location.reload()}>刷新</Button>,
                <Button key="home" icon={<HomeOutlined />} onClick={() => window.location.href = '/'}>首页</Button>
              ]}
            >
              {errorClassification?.suggestions && (
                <Alert type="info" showIcon style={{ marginTop: 24, textAlign: 'left' }} message="建议操作：" description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {errorClassification.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                } />
              )}
              {showDetails && error && (
                <div style={{ textAlign: 'left', marginTop: 24 }}>
                  <Divider>错误详情</Divider>
                  <Paragraph><Text strong>类型：</Text><Text code>{errorClassification?.type}</Text></Paragraph>
                  <Paragraph><Text type="danger">{error.toString()}</Text></Paragraph>
                  {errorId && <Paragraph><Text type="secondary">ID: {errorId}</Text></Paragraph>}
                  <Button size="small" icon={copied ? <CheckCircleOutlined /> : <CopyOutlined />} onClick={this.handleCopyError}>{copied ? '已复制' : '复制'}</Button>
                  {errorInfo?.componentStack && (
                    <details style={{ marginTop: 16 }}>
                      <summary style={{ cursor: 'pointer' }}><Text strong>组件堆栈</Text></summary>
                      <pre style={{ fontSize: 12, overflow: 'auto', maxHeight: 200, background: '#fafafa', padding: 12, borderRadius: 4 }}>{errorInfo.componentStack}</pre>
                    </details>
                  )}
                </div>
              )}
            </Result>
          </div>
        </div>
      )
    }

    return children
  }
}

export function withErrorBoundary<P extends object>(WrappedComponent: React.ComponentType<P>, props?: Omit<Props, 'children'>) {
  const WithErrorBoundary = (p: P) => <ErrorBoundary {...props}><WrappedComponent {...p} /></ErrorBoundary>
  WithErrorBoundary.displayName = `WithErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`
  return WithErrorBoundary
}

export default ErrorBoundary
