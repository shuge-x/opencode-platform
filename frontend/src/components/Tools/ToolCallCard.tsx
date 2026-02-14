import React, { useState } from 'react'
import { Card, Tag, Button, Collapse, Modal, Input, Space, message, Spin } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  CodeOutlined
} from '@ant-design/icons'
import type { ToolCallResponse } from '@/api/tools'

interface ToolCallCardProps {
  toolCall: ToolCallResponse
  onGrantPermission?: (granted: boolean, reason?: string) => void
}

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待执行' },
  running: { color: 'processing', icon: <LoadingOutlined />, text: '执行中' },
  success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  permission_required: { color: 'warning', icon: <ExclamationCircleOutlined />, text: '需要权限' },
  permission_denied: { color: 'error', icon: <CloseCircleOutlined />, text: '权限被拒绝' }
}

export default function ToolCallCard({ toolCall, onGrantPermission }: ToolCallCardProps) {
  const [showPermissionModal, setShowPermissionModal] = useState(false)
  const [permissionReason, setPermissionReason] = useState('')
  const [loading, setLoading] = useState(false)

  const config = statusConfig[toolCall.status]

  const handleGrantPermission = async (granted: boolean) => {
    if (!onGrantPermission) return

    setLoading(true)
    try {
      await onGrantPermission(granted, permissionReason)
      setShowPermissionModal(false)
      setPermissionReason('')
      message.success(granted ? '已授权' : '已拒绝')
    } catch (error) {
      message.error('操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Card
        size="small"
        title={
          <Space>
            <CodeOutlined />
            <span>{toolCall.tool_name}</span>
            <Tag color={config.color} icon={config.icon}>
              {config.text}
            </Tag>
          </Space>
        }
        extra={
          toolCall.status === 'permission_required' && (
            <Button
              type="primary"
              size="small"
              onClick={() => setShowPermissionModal(true)}
            >
              处理权限
            </Button>
          )
        }
        style={{ marginBottom: 12 }}
      >
        {toolCall.tool_description && (
          <p style={{ marginBottom: 8, color: '#666' }}>
            {toolCall.tool_description}
          </p>
        )}

        {toolCall.parameters && (
          <div style={{ marginBottom: 8 }}>
            <strong>参数：</strong>
            <pre style={{
              background: '#f5f5f5',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '12px',
              overflow: 'auto'
            }}>
              {JSON.stringify(JSON.parse(toolCall.parameters), null, 2)}
            </pre>
          </div>
        )}

        {toolCall.result && (
          <div style={{ marginBottom: 8 }}>
            <strong>结果：</strong>
            <pre style={{
              background: '#f0f5ff',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '12px',
              maxHeight: '200px',
              overflow: 'auto'
            }}>
              {toolCall.result}
            </pre>
          </div>
        )}

        {toolCall.error_message && (
          <div style={{ marginBottom: 8 }}>
            <strong style={{ color: '#ff4d4f' }}>错误：</strong>
            <pre style={{
              background: '#fff1f0',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '12px',
              color: '#ff4d4f'
            }}>
              {toolCall.error_message}
            </pre>
          </div>
        )}

        {toolCall.execution_logs && toolCall.execution_logs.length > 0 && (
          <Collapse
            size="small"
            items={[
              {
                key: '1',
                label: `执行日志 (${toolCall.execution_logs.length})`,
                children: (
                  <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                    {toolCall.execution_logs.map((log) => (
                      <div
                        key={log.id}
                        style={{
                          marginBottom: 8,
                          padding: '4px 8px',
                          background: log.log_level === 'ERROR' ? '#fff1f0' : '#f5f5f5',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      >
                        <Tag color={log.log_level === 'ERROR' ? 'error' : 'default'}>
                          {log.log_level}
                        </Tag>
                        <span style={{ marginLeft: 8 }}>{log.message}</span>
                      </div>
                    ))}
                  </div>
                )
              }
            ]}
          />
        )}

        <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
          {toolCall.started_at && `开始: ${new Date(toolCall.started_at).toLocaleString()}`}
          {toolCall.completed_at && ` | 完成: ${new Date(toolCall.completed_at).toLocaleString()}`}
        </div>
      </Card>

      <Modal
        title="权限确认"
        open={showPermissionModal}
        onCancel={() => setShowPermissionModal(false)}
        footer={[
          <Button key="cancel" onClick={() => setShowPermissionModal(false)}>
            取消
          </Button>,
          <Button
            key="deny"
            danger
            loading={loading}
            onClick={() => handleGrantPermission(false)}
          >
            拒绝
          </Button>,
          <Button
            key="grant"
            type="primary"
            loading={loading}
            onClick={() => handleGrantPermission(true)}
          >
            允许
          </Button>
        ]}
      >
        <p>
          工具 <strong>{toolCall.tool_name}</strong> 请求执行权限
        </p>

        {toolCall.permission_reason && (
          <p style={{ color: '#666' }}>原因: {toolCall.permission_reason}</p>
        )}

        <Input.TextArea
          placeholder="备注（可选）"
          value={permissionReason}
          onChange={(e) => setPermissionReason(e.target.value)}
          rows={3}
        />
      </Modal>
    </>
  )
}
