import React, { useState } from 'react'
import { Modal, Input, Checkbox, Space, Typography, Alert, List, Tag, Progress, Button } from 'antd'
import {
  WarningOutlined,
  RollbackOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import type { VersionInfo } from '@/types/version'
import styles from './RevertDialog.module.css'

const { Text, Paragraph } = Typography

interface RevertDialogProps {
  open: boolean
  version: VersionInfo | null
  skillId: number
  onConfirm: (options: { message: string; createNewVersion: boolean }) => Promise<boolean>
  onCancel: () => void
}

type RevertStatus = 'confirming' | 'reverting' | 'success' | 'error'

export default function RevertDialog({
  open,
  version,
  skillId,
  onConfirm,
  onCancel
}: RevertDialogProps) {
  const [message, setMessage] = useState('')
  const [createNewVersion, setCreateNewVersion] = useState(true)
  const [status, setStatus] = useState<RevertStatus>('confirming')
  const [progress, setProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')

  // 重置状态
  const resetState = () => {
    setMessage('')
    setCreateNewVersion(true)
    setStatus('confirming')
    setProgress(0)
    setErrorMessage('')
  }

  // 处理取消
  const handleCancel = () => {
    if (status === 'reverting') return // 回退中不允许取消
    resetState()
    onCancel()
  }

  // 处理确认
  const handleConfirm = async () => {
    if (!version) return

    setStatus('reverting')
    setProgress(10)

    try {
      // 模拟进度
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 10
        })
      }, 200)

      const success = await onConfirm({
        message: message || `回退到版本 ${version.version_number}`,
        createNewVersion
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (success) {
        setStatus('success')
        setTimeout(() => {
          resetState()
          onCancel()
        }, 1500)
      } else {
        setStatus('error')
        setErrorMessage('回退失败，请稍后重试')
      }
    } catch (error: any) {
      setStatus('error')
      setErrorMessage(error.message || '回退过程中发生错误')
    }
  }

  // 处理关闭后重试
  const handleRetry = () => {
    setStatus('confirming')
    setProgress(0)
    setErrorMessage('')
  }

  if (!version) return null

  // 文件变更统计
  const stats = {
    added: version.file_changes.filter(fc => fc.change_type === 'added').length,
    modified: version.file_changes.filter(fc => fc.change_type === 'modified').length,
    deleted: version.file_changes.filter(fc => fc.change_type === 'deleted').length
  }

  return (
    <Modal
      title={
        <Space>
          <RollbackOutlined />
          <span>版本回退确认</span>
        </Space>
      }
      open={open}
      onCancel={status === 'reverting' ? undefined : handleCancel}
      footer={
        status === 'confirming' ? (
          <>
            <Button onClick={handleCancel}>取消</Button>
            <Button type="primary" danger onClick={handleConfirm}>
              确认回退
            </Button>
          </>
        ) : status === 'error' ? (
          <>
            <Button onClick={handleCancel}>关闭</Button>
            <Button type="primary" onClick={handleRetry}>
              重试
            </Button>
          </>
        ) : null
      }
      width={520}
      maskClosable={false}
      closable={status !== 'reverting'}
      className={styles.revertDialog}
    >
      {status === 'confirming' && (
        <>
          <Alert
            type="warning"
            showIcon
            icon={<WarningOutlined />}
            message="回退警告"
            description="回退操作将覆盖当前文件内容。建议在回退前先保存当前版本。"
            className={styles.warningAlert}
          />

          <div className={styles.versionInfo}>
            <Paragraph>
              <Text strong>目标版本：</Text>
              <Text code>{version.version_number}</Text>
              <Text type="secondary"> ({version.commit_hash.substring(0, 7)})</Text>
            </Paragraph>
            <Paragraph>
              <Text strong>提交信息：</Text>
              <Text>{version.commit_message}</Text>
            </Paragraph>
            <Paragraph>
              <Text strong>影响文件：</Text>
              <Space size={4}>
                {stats.added > 0 && <Tag color="green">+{stats.added} 新增</Tag>}
                {stats.modified > 0 && <Tag color="blue">~{stats.modified} 修改</Tag>}
                {stats.deleted > 0 && <Tag color="red">-{stats.deleted} 删除</Tag>}
              </Space>
            </Paragraph>
          </div>

          <div className={styles.fileList}>
            <Text strong>受影响的文件：</Text>
            <List
              size="small"
              dataSource={version.file_changes}
              renderItem={(file) => (
                <List.Item className={styles.fileItem}>
                  <Space>
                    {file.change_type === 'added' && <Tag color="green">新增</Tag>}
                    {file.change_type === 'modified' && <Tag color="blue">修改</Tag>}
                    {file.change_type === 'deleted' && <Tag color="red">删除</Tag>}
                    <Text className={styles.filename}>{file.filename}</Text>
                    {file.additions > 0 && (
                      <Text type="success">+{file.additions}</Text>
                    )}
                    {file.deletions > 0 && (
                      <Text type="danger">-{file.deletions}</Text>
                    )}
                  </Space>
                </List.Item>
              )}
            />
          </div>

          <div className={styles.options}>
            <Input.TextArea
              placeholder="回退说明（可选）"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={2}
              className={styles.messageInput}
            />
            <Checkbox
              checked={createNewVersion}
              onChange={(e) => setCreateNewVersion(e.target.checked)}
            >
              回退后创建新版本记录
            </Checkbox>
          </div>
        </>
      )}

      {status === 'reverting' && (
        <div className={styles.statusContent}>
          <LoadingOutlined className={styles.statusIcon} spin />
          <Text>正在回退到版本 {version.version_number}...</Text>
          <Progress percent={progress} status="active" />
        </div>
      )}

      {status === 'success' && (
        <div className={styles.statusContent}>
          <CheckCircleOutlined className={styles.successIcon} />
          <Text>回退成功！</Text>
          <Text type="secondary">文件已更新，正在刷新...</Text>
        </div>
      )}

      {status === 'error' && (
        <div className={styles.statusContent}>
          <CloseCircleOutlined className={styles.errorIcon} />
          <Text type="danger">回退失败</Text>
          <Text type="secondary">{errorMessage}</Text>
        </div>
      )}
    </Modal>
  )
}
