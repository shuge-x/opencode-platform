import React, { useState, useCallback, useEffect } from 'react'
import { Tabs, Empty, message } from 'antd'
import {
  FileTextOutlined,
  CodeOutlined,
  BugOutlined,
  WarningOutlined
} from '@ant-design/icons'
import LogPanel from './LogPanel'
import VariableViewer from './VariableViewer'
import DebugControls from './DebugControls'
import ErrorStack from './ErrorStack'
import { useDebugWebSocket } from '@/hooks/useDebugWebSocket'
import type { LogEntry, DebugVariable, DebugState, DebugError, StackFrame } from '@/types/debug'
import styles from './DebugPanel.module.css'

interface DebugPanelProps {
  skillId: number
  onCodeLocationClick?: (file: string, line: number, column?: number) => void
  onStateChange?: (state: DebugState) => void
}

// 生成唯一 ID
const generateId = () => Math.random().toString(36).substring(2, 15)

export default function DebugPanel({
  skillId,
  onCodeLocationClick,
  onStateChange
}: DebugPanelProps) {
  // 状态
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [variables, setVariables] = useState<DebugVariable[]>([])
  const [debugState, setDebugState] = useState<DebugState>({ status: 'idle' })
  const [currentError, setCurrentError] = useState<DebugError | null>(null)
  const [activeTab, setActiveTab] = useState('logs')

  // WebSocket 连接
  const {
    isConnected,
    connectionError,
    startDebug,
    pauseExecution,
    continueExecution,
    stepOver,
    stepInto,
    stepOut,
    restart,
    stop
  } = useDebugWebSocket({
    skillId,
    onLog: (log) => {
      setLogs(prev => [...prev, { ...log, id: log.id || generateId() }])
    },
    onVariables: (vars) => {
      setVariables(vars)
    },
    onStateChange: (state) => {
      setDebugState(state)
      onStateChange?.(state)
    },
    onError: (error) => {
      setCurrentError(error)
      setActiveTab('error')
    },
    onConnect: () => {
      message.success('调试连接已建立')
    },
    onDisconnect: () => {
      message.warning('调试连接已断开')
    }
  })

  // 连接错误处理
  useEffect(() => {
    if (connectionError) {
      message.error(connectionError)
    }
  }, [connectionError])

  // 清空日志
  const handleClearLogs = useCallback(() => {
    setLogs([])
  }, [])

  // 点击日志
  const handleLogClick = useCallback((log: LogEntry) => {
    if (log.source && log.line) {
      onCodeLocationClick?.(log.source, log.line)
    }
  }, [onCodeLocationClick])

  // 刷新变量
  const handleRefreshVariables = useCallback(() => {
    // 可以通过 WebSocket 请求刷新变量
    message.info('刷新变量...')
  }, [])

  // 点击变量
  const handleVariableClick = useCallback((variable: DebugVariable) => {
    console.log('Variable clicked:', variable)
  }, [])

  // 点击堆栈帧
  const handleStackFrameClick = useCallback((frame: StackFrame) => {
    if (!frame.isNative) {
      onCodeLocationClick?.(frame.file, frame.line, frame.column)
    }
  }, [onCodeLocationClick])

  // 清除错误
  const handleDismissError = useCallback(() => {
    setCurrentError(null)
  }, [])

  // 开始调试
  const handleStart = useCallback(() => {
    setCurrentError(null)
    startDebug()
  }, [startDebug])

  // Tabs 配置
  const tabItems = [
    {
      key: 'logs',
      label: (
        <span>
          <FileTextOutlined />
          日志 {logs.length > 0 && <span className={styles.tabBadge}>{logs.length}</span>}
        </span>
      ),
      children: (
        <LogPanel
          logs={logs}
          onClear={handleClearLogs}
          onLogClick={handleLogClick}
        />
      )
    },
    {
      key: 'variables',
      label: (
        <span>
          <CodeOutlined />
          变量 {variables.length > 0 && <span className={styles.tabBadge}>{variables.length}</span>}
        </span>
      ),
      children: (
        <VariableViewer
          variables={variables}
          onRefresh={handleRefreshVariables}
          onVariableClick={handleVariableClick}
        />
      )
    },
    {
      key: 'error',
      label: (
        <span>
          <WarningOutlined />
          错误 {currentError && <span className={styles.errorBadge}>!</span>}
        </span>
      ),
      children: (
        <ErrorStack
          error={currentError}
          onStackFrameClick={handleStackFrameClick}
          onDismiss={handleDismissError}
        />
      )
    }
  ]

  // 计算日志和错误计数
  const errorCount = logs.filter(l => l.level === 'error').length
  const warnCount = logs.filter(l => l.level === 'warn').length

  return (
    <div className={styles.debugPanel}>
      <DebugControls
        state={debugState}
        isConnected={isConnected}
        onStart={handleStart}
        onPause={pauseExecution}
        onContinue={continueExecution}
        onStepOver={stepOver}
        onStepInto={stepInto}
        onStepOut={stepOut}
        onRestart={restart}
        onStop={stop}
      />

      {/* 状态栏 */}
      <div className={styles.statusBar}>
        {errorCount > 0 && (
          <span className={styles.errorCount}>
            <WarningOutlined /> {errorCount} 错误
          </span>
        )}
        {warnCount > 0 && (
          <span className={styles.warnCount}>
            <WarningOutlined /> {warnCount} 警告
          </span>
        )}
      </div>

      <div className={styles.panelContent}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          className={styles.debugTabs}
          size="small"
        />
      </div>
    </div>
  )
}
