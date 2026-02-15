import React from 'react'
import { Alert, Collapse, Empty, Button, Tooltip } from 'antd'
import {
  BugOutlined,
  CopyOutlined,
  FileTextOutlined,
  RightOutlined
} from '@ant-design/icons'
import type { DebugError, StackFrame } from '@/types/debug'
import styles from './ErrorStack.module.css'

interface ErrorStackProps {
  error: DebugError | null
  onStackFrameClick?: (frame: StackFrame) => void
  onDismiss?: () => void
}

// 格式化时间戳
const formatTimestamp = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

export default function ErrorStack({
  error,
  onStackFrameClick,
  onDismiss
}: ErrorStackProps) {
  if (!error) {
    return (
      <div className={styles.errorStack}>
        <Empty
          description="暂无错误"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          className={styles.emptyError}
        />
      </div>
    )
  }

  // 复制错误信息
  const copyError = () => {
    const text = `${error.name}: ${error.message}\n\nStack trace:\n${error.stack?.map(f =>
      `  at ${f.name} (${f.file}:${f.line}${f.column ? `:${f.column}` : ''})`
    ).join('\n') || 'No stack trace available'}`

    navigator.clipboard.writeText(text)
  }

  // 渲染堆栈帧
  const renderStackFrame = (frame: StackFrame, index: number) => (
    <div
      key={frame.id || index}
      className={`${styles.stackFrame} ${frame.isNative ? styles.nativeFrame : ''}`}
      onClick={() => !frame.isNative && onStackFrameClick?.(frame)}
    >
      <div className={styles.frameHeader}>
        <RightOutlined className={styles.frameIcon} />
        <span className={styles.frameName}>{frame.name}</span>
        {frame.isNative && (
          <span className={styles.nativeBadge}>native</span>
        )}
      </div>
      <div className={styles.frameLocation}>
        <FileTextOutlined className={styles.fileIcon} />
        <span className={styles.fileName}>{frame.file}</span>
        <span className={styles.lineNumber}>:{frame.line}</span>
        {frame.column && (
          <span className={styles.columnNumber}>:{frame.column}</span>
        )}
      </div>
    </div>
  )

  return (
    <div className={styles.errorStack}>
      <div className={styles.errorHeader}>
        <Alert
          type="error"
          message={
            <div className={styles.errorMessage}>
              <BugOutlined className={styles.errorIcon} />
              <span className={styles.errorName}>{error.name}:</span>
              <span className={styles.errorText}>{error.message}</span>
            </div>
          }
          description={
            <div className={styles.errorMeta}>
              <span>发生时间: {formatTimestamp(error.timestamp)}</span>
              <Tooltip title="复制错误信息">
                <Button
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={copyError}
                  type="text"
                />
              </Tooltip>
            </div>
          }
          showIcon={false}
          className={styles.errorAlert}
        />
      </div>

      {error.stack && error.stack.length > 0 && (
        <div className={styles.stackTrace}>
          <div className={styles.stackHeader}>
            <span>调用堆栈</span>
            <span className={styles.stackCount}>{error.stack.length} 帧</span>
          </div>
          <Collapse
            defaultActiveKey={['0', '1', '2']}
            ghost
            className={styles.stackCollapse}
          >
            {error.stack.slice(0, 50).map((frame, index) => (
              <Collapse.Panel
                key={index.toString()}
                header={renderStackFrame(frame, index)}
                className={styles.stackPanel}
              >
                {/* 可以在这里显示更多信息，如局部变量等 */}
                <div className={styles.frameDetails}>
                  <p>函数: {frame.name}</p>
                  <p>文件: {frame.file}</p>
                  <p>行号: {frame.line}</p>
                  {frame.column && <p>列号: {frame.column}</p>}
                  <Button
                    size="small"
                    type="link"
                    onClick={() => onStackFrameClick?.(frame)}
                  >
                    跳转到代码位置
                  </Button>
                </div>
              </Collapse.Panel>
            ))}
          </Collapse>
          {error.stack.length > 50 && (
            <div className={styles.stackTruncated}>
              还有 {error.stack.length - 50} 帧未显示...
            </div>
          )}
        </div>
      )}
    </div>
  )
}
