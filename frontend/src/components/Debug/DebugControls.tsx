import React from 'react'
import { Button, Tooltip, Space, Divider, Tag } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StepForwardOutlined,
  StepIntoOutlined,
  StepBackwardOutlined,
  RedoOutlined,
  StopOutlined,
  BugOutlined
} from '@ant-design/icons'
import type { DebugState } from '@/types/debug'
import styles from './DebugControls.module.css'

interface DebugControlsProps {
  state: DebugState
  isConnected: boolean
  onStart: () => void
  onPause: () => void
  onContinue: () => void
  onStepOver: () => void
  onStepInto: () => void
  onStepOut: () => void
  onRestart: () => void
  onStop: () => void
}

const STATUS_CONFIG: Record<DebugState['status'], { color: string; label: string; pulse?: boolean }> = {
  idle: { color: 'default', label: '空闲' },
  running: { color: 'processing', label: '运行中', pulse: true },
  paused: { color: 'warning', label: '已暂停' },
  error: { color: 'error', label: '错误' }
}

export default function DebugControls({
  state,
  isConnected,
  onStart,
  onPause,
  onContinue,
  onStepOver,
  onStepInto,
  onStepOut,
  onRestart,
  onStop
}: DebugControlsProps) {
  const statusConfig = STATUS_CONFIG[state.status]
  const isRunning = state.status === 'running'
  const isPaused = state.status === 'paused'
  const isIdle = state.status === 'idle'
  const hasError = state.status === 'error'

  return (
    <div className={styles.debugControls}>
      <div className={styles.controlsHeader}>
        <BugOutlined className={styles.debugIcon} />
        <span className={styles.controlsTitle}>调试控制</span>
        <Tag
          color={statusConfig.color}
          className={statusConfig.pulse ? styles.statusPulse : ''}
        >
          {statusConfig.label}
        </Tag>
        {!isConnected && (
          <Tag color="error">未连接</Tag>
        )}
      </div>

      <div className={styles.controlsBody}>
        {/* 主控制按钮组 */}
        <Space.Compact className={styles.buttonGroup}>
          {isIdle || hasError ? (
            <Tooltip title="开始调试 (F5)">
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onStart}
                disabled={!isConnected}
              >
                开始
              </Button>
            </Tooltip>
          ) : isRunning ? (
            <Tooltip title="暂停 (F6)">
              <Button
                type="primary"
                icon={<PauseCircleOutlined />}
                onClick={onPause}
                disabled={!isConnected}
              >
                暂停
              </Button>
            </Tooltip>
          ) : isPaused ? (
            <Tooltip title="继续 (F5)">
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onContinue}
                disabled={!isConnected}
              >
                继续
              </Button>
            </Tooltip>
          ) : null}
        </Space.Compact>

        <Divider type="vertical" className={styles.divider} />

        {/* 单步执行按钮组 */}
        <Space.Compact className={styles.buttonGroup}>
          <Tooltip title="单步跳过 (F10)">
            <Button
              icon={<StepForwardOutlined />}
              onClick={onStepOver}
              disabled={!isConnected || !isPaused}
            />
          </Tooltip>
          <Tooltip title="单步进入 (F11)">
            <Button
              icon={<StepIntoOutlined />}
              onClick={onStepInto}
              disabled={!isConnected || !isPaused}
            />
          </Tooltip>
          <Tooltip title="单步跳出 (Shift+F11)">
            <Button
              icon={<StepBackwardOutlined />}
              onClick={onStepOut}
              disabled={!isConnected || !isPaused}
            />
          </Tooltip>
        </Space.Compact>

        <Divider type="vertical" className={styles.divider} />

        {/* 重启和停止按钮组 */}
        <Space.Compact className={styles.buttonGroup}>
          <Tooltip title="重新运行 (Ctrl+Shift+F5)">
            <Button
              icon={<RedoOutlined />}
              onClick={onRestart}
              disabled={!isConnected || isIdle}
            />
          </Tooltip>
          <Tooltip title="停止 (Shift+F5)">
            <Button
              danger
              icon={<StopOutlined />}
              onClick={onStop}
              disabled={!isConnected || isIdle}
            />
          </Tooltip>
        </Space.Compact>
      </div>

      {/* 显示当前执行位置 */}
      {(isPaused || isRunning) && state.currentFile && (
        <div className={styles.currentLocation}>
          <span className={styles.locationLabel}>当前位置:</span>
          <span className={styles.locationFile}>{state.currentFile}</span>
          {state.currentLine && (
            <span className={styles.locationLine}>:{state.currentLine}</span>
          )}
        </div>
      )}

      {/* 快捷键提示 */}
      <div className={styles.shortcutsHint}>
        <span>F5: 开始/继续</span>
        <span>F6: 暂停</span>
        <span>F10: 单步跳过</span>
        <span>F11: 单步进入</span>
      </div>
    </div>
  )
}
