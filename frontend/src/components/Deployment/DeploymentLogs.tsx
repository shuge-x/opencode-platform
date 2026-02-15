import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Button,
  Input,
  Space,
  Select,
  Tag,
  Tooltip,
  Empty,
  Spin,
  Typography,
  message,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  ClearOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import type { DeploymentLog } from '@/types/deployment'
import { DeploymentLogStream } from '@/api/deployment'
import styles from './DeploymentLogs.module.css'

const { Text } = Typography
const { Option } = Select

interface DeploymentLogsProps {
  deploymentId: string
  logs: DeploymentLog[]
  isConnected?: boolean
  onLoadMore?: (params: { level?: string; search?: string }) => void
  onDownload?: () => void
  onConnect?: () => void
  onDisconnect?: () => void
  onClear?: () => void
  loading?: boolean
}

const LogLevelColors: Record<string, string> = {
  info: '#1890ff',
  warn: '#faad14',
  error: '#ff4d4f',
  debug: '#8c8c8c',
}

export const DeploymentLogs: React.FC<DeploymentLogsProps> = ({
  deploymentId,
  logs,
  isConnected = false,
  onLoadMore,
  onDownload,
  onConnect,
  onDisconnect,
  onClear,
  loading = false,
}) => {
  const [searchText, setSearchText] = useState('')
  const [levelFilter, setLevelFilter] = useState<string | undefined>()
  const [autoScroll, setAutoScroll] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const logsContainerRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  // 检测用户滚动，禁用自动滚动
  const handleScroll = useCallback(() => {
    if (logsContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
      setAutoScroll(isAtBottom)
    }
  }, [])

  // 过滤日志
  const filteredLogs = logs.filter((log) => {
    const matchesSearch = !searchText || 
      log.message.toLowerCase().includes(searchText.toLowerCase()) ||
      (log.source?.toLowerCase().includes(searchText.toLowerCase()))
    
    const matchesLevel = !levelFilter || log.level === levelFilter
    
    return matchesSearch && matchesLevel
  })

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }) + '.' + String(date.getMilliseconds()).padStart(3, '0')
  }

  // 渲染单条日志
  const renderLog = (log: DeploymentLog) => {
    const levelColor = LogLevelColors[log.level] || '#8c8c8c'
    
    return (
      <div key={log.id} className={`${styles.logLine} ${styles[log.level]}`}>
        <span className={styles.logTime}>{formatTime(log.timestamp)}</span>
        <Tag 
          color={levelColor} 
          className={styles.logLevel}
          style={{ color: levelColor }}
        >
          {log.level.toUpperCase()}
        </Tag>
        {log.source && (
          <span className={styles.logSource}>[{log.source}]</span>
        )}
        <span className={styles.logMessage}>{log.message}</span>
      </div>
    )
  }

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value)
  }

  // 处理级别过滤
  const handleLevelFilter = (level: string | undefined) => {
    setLevelFilter(level)
  }

  // 下载日志
  const handleDownload = () => {
    if (onDownload) {
      onDownload()
    } else {
      // 默认下载逻辑
      const content = logs
        .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.source ? `[${log.source}] ` : ''}${log.message}`)
        .join('\n')
      
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `deployment-${deploymentId}-logs-${new Date().toISOString()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      message.success('日志下载完成')
    }
  }

  return (
    <Card 
      className={styles.container}
      title={
        <Space>
          <span>部署日志</span>
          {isConnected && (
            <Tag color="processing" icon={<span className={styles.pulse} />}>
              实时
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Input
            placeholder="搜索日志..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="日志级别"
            style={{ width: 100 }}
            value={levelFilter}
            onChange={handleLevelFilter}
            allowClear
          >
            <Option value="info">INFO</Option>
            <Option value="warn">WARN</Option>
            <Option value="error">ERROR</Option>
            <Option value="debug">DEBUG</Option>
          </Select>
          <Tooltip title={isConnected ? '暂停实时日志' : '开始实时日志'}>
            <Button
              type={isConnected ? 'default' : 'primary'}
              icon={isConnected ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={isConnected ? onDisconnect : onConnect}
            >
              {isConnected ? '暂停' : '实时'}
            </Button>
          </Tooltip>
          <Tooltip title="刷新">
            <Button
              icon={<ReloadOutlined />}
              onClick={() => onLoadMore?.({ level: levelFilter, search: searchText })}
              loading={loading}
            />
          </Tooltip>
          <Tooltip title="清空">
            <Button
              icon={<ClearOutlined />}
              onClick={onClear}
              disabled={logs.length === 0}
            />
          </Tooltip>
          <Tooltip title="下载日志">
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              disabled={logs.length === 0}
            />
          </Tooltip>
        </Space>
      }
    >
      <div
        ref={logsContainerRef}
        className={styles.logsContainer}
        onScroll={handleScroll}
      >
        {loading && logs.length === 0 ? (
          <div className={styles.loadingContainer}>
            <Spin />
          </div>
        ) : filteredLogs.length === 0 ? (
          <Empty
            description={logs.length === 0 ? '暂无日志' : '没有匹配的日志'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <>
            {filteredLogs.map(renderLog)}
            <div ref={logsEndRef} />
          </>
        )}
      </div>
      
      <div className={styles.footer}>
        <Text type="secondary">
          共 {logs.length} 条日志，显示 {filteredLogs.length} 条
          {autoScroll && ' · 自动滚动'}
        </Text>
      </div>
    </Card>
  )
}

export default DeploymentLogs
