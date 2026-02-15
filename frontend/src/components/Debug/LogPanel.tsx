import React, { useEffect, useRef, useState, useMemo } from 'react'
import { Input, Select, Tag, Empty, Tooltip, Button } from 'antd'
import {
  SearchOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  BugOutlined
} from '@ant-design/icons'
import type { LogEntry, LogLevel } from '@/types/debug'
import styles from './LogPanel.module.css'

interface LogPanelProps {
  logs: LogEntry[]
  onClear?: () => void
  onLogClick?: (log: LogEntry) => void
  maxLogs?: number
}

const LOG_LEVEL_CONFIG: Record<LogLevel, { color: string; icon: React.ReactNode; label: string }> = {
  debug: { color: '#8c8c8c', icon: <BugOutlined />, label: 'DEBUG' },
  info: { color: '#1890ff', icon: <InfoCircleOutlined />, label: 'INFO' },
  warn: { color: '#faad14', icon: <WarningOutlined />, label: 'WARN' },
  error: { color: '#ff4d4f', icon: <CloseCircleOutlined />, label: 'ERROR' }
}

export default function LogPanel({ logs, onClear, onLogClick, maxLogs = 1000 }: LogPanelProps) {
  const [filterLevel, setFilterLevel] = useState<LogLevel | 'all'>('all')
  const [searchText, setSearchText] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const logContainerRef = useRef<HTMLDivElement>(null)

  // 过滤日志
  const filteredLogs = useMemo(() => {
    let result = logs

    // 按级别过滤
    if (filterLevel !== 'all') {
      result = result.filter(log => log.level === filterLevel)
    }

    // 按关键词搜索
    if (searchText) {
      const lowerSearch = searchText.toLowerCase()
      result = result.filter(log =>
        log.message.toLowerCase().includes(lowerSearch) ||
        log.source?.toLowerCase().includes(lowerSearch)
      )
    }

    // 限制最大日志数
    if (result.length > maxLogs) {
      result = result.slice(-maxLogs)
    }

    return result
  }, [logs, filterLevel, searchText, maxLogs])

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [filteredLogs, autoScroll])

  // 处理滚动
  const handleScroll = () => {
    if (!logContainerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
    setAutoScroll(isAtBottom)
  }

  // 格式化时间戳
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
  }

  // 渲染单条日志
  const renderLogEntry = (log: LogEntry) => {
    const config = LOG_LEVEL_CONFIG[log.level]

    return (
      <div
        key={log.id}
        className={`${styles.logEntry} ${styles[`logEntry_${log.level}`]}`}
        onClick={() => onLogClick?.(log)}
      >
        <span className={styles.logTime}>{formatTimestamp(log.timestamp)}</span>
        <Tag
          color={config.color}
          icon={config.icon}
          className={styles.logLevel}
        >
          {config.label}
        </Tag>
        {log.source && (
          <Tooltip title={log.source}>
            <span className={styles.logSource}>
              [{log.source}{log.line ? `:${log.line}` : ''}]
            </span>
          </Tooltip>
        )}
        <span className={styles.logMessage}>{log.message}</span>
      </div>
    )
  }

  return (
    <div className={styles.logPanel}>
      <div className={styles.logToolbar}>
        <div className={styles.filterSection}>
          <Select
            value={filterLevel}
            onChange={setFilterLevel}
            style={{ width: 100 }}
            size="small"
            options={[
              { value: 'all', label: '全部' },
              { value: 'debug', label: 'DEBUG' },
              { value: 'info', label: 'INFO' },
              { value: 'warn', label: 'WARN' },
              { value: 'error', label: 'ERROR' }
            ]}
          />
          <Input
            placeholder="搜索日志..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            allowClear
            size="small"
            style={{ width: 200 }}
          />
        </div>
        <div className={styles.actionSection}>
          <span className={styles.logCount}>
            {filteredLogs.length} / {logs.length} 条
          </span>
          <Button
            size="small"
            icon={<ClearOutlined />}
            onClick={onClear}
          >
            清空
          </Button>
        </div>
      </div>

      <div
        ref={logContainerRef}
        className={styles.logContainer}
        onScroll={handleScroll}
      >
        {filteredLogs.length > 0 ? (
          filteredLogs.map(renderLogEntry)
        ) : (
          <Empty
            description="暂无日志"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className={styles.emptyLogs}
          />
        )}
      </div>

      {!autoScroll && (
        <div className={styles.scrollHint}>
          <Button
            size="small"
            onClick={() => {
              setAutoScroll(true)
              if (logContainerRef.current) {
                logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
              }
            }}
          >
            滚动到底部
          </Button>
        </div>
      )}
    </div>
  )
}
