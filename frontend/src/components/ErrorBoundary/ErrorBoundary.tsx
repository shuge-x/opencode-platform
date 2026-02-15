import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography } from 'antd'
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons'

const { Paragraph, Text } = Typography

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string | null
}

/**
 * Global Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error caught by ErrorBoundary')
      console.error('Error:', error)
      console.error('Component Stack:', errorInfo.componentStack)
      console.groupEnd()
    }

    this.setState({ errorInfo })

    // Call optional error handler
    this.props.onError?.(error, errorInfo)

    // TODO: Send error to error reporting service
    // errorReportingService.captureException(error, { extra: errorInfo })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleGoHome = (): void => {
    window.location.href = '/'
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    })
  }

  render(): ReactNode {
    const { hasError, error, errorInfo, errorId } = this.state
    const { children, fallback, showDetails = process.env.NODE_ENV === 'development' } = this.props

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback
      }

      // Default error UI
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          background: '#f5f5f5'
        }}>
          <Result
            status="error"
            icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
            title="页面出错了"
            subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面或返回首页。"
            extra={[
              <Button
                key="retry"
                type="primary"
                icon={<ReloadOutlined />}
                onClick={this.handleRetry}
              >
                重试
              </Button>,
              <Button
                key="reload"
                icon={<ReloadOutlined />}
                onClick={this.handleReload}
              >
                刷新页面
              </Button>,
              <Button
                key="home"
                icon={<HomeOutlined />}
                onClick={this.handleGoHome}
              >
                返回首页
              </Button>
            ]}
          >
            {showDetails && error && (
              <div style={{ textAlign: 'left', marginTop: 24 }}>
                <Paragraph>
                  <Text strong style={{ fontSize: 16 }}>
                    错误详情：
                  </Text>
                </Paragraph>
                <Paragraph>
                  <Text type="danger">{error.toString()}</Text>
                </Paragraph>
                {errorId && (
                  <Paragraph>
                    <Text type="secondary">错误ID: {errorId}</Text>
                  </Paragraph>
                )}
                {errorInfo?.componentStack && (
                  <details style={{ marginTop: 16 }}>
                    <summary style={{ cursor: 'pointer', marginBottom: 8 }}>
                      <Text>组件堆栈</Text>
                    </summary>
                    <pre style={{
                      fontSize: 12,
                      overflow: 'auto',
                      maxHeight: 200,
                      background: '#fafafa',
                      padding: 12,
                      borderRadius: 4
                    }}>
                      {errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </Result>
        </div>
      )
    }

    return children
  }
}

/**
 * HOC to wrap components with error boundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WithErrorBoundary = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  )

  WithErrorBoundary.displayName = `WithErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`

  return WithErrorBoundary
}

export default ErrorBoundary
