import React, { useState } from 'react'
import { Card, Form, Input, Button, message, Spin, Alert, Tabs, Empty, Tag } from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import Editor from '@monaco-editor/react'
import { skillsDevApi } from '@/api/skills-dev'
import styles from './SkillTester.module.css'

interface SkillTesterProps {
  skillId: number
  onExecutionComplete?: () => void
}

export default function SkillTester({ skillId, onExecutionComplete }: SkillTesterProps) {
  const [form] = Form.useForm()
  const [executing, setExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [polling, setPolling] = useState(false)

  const executeSkill = async (params: any) => {
    setExecuting(true)
    setExecutionResult(null)

    try {
      // 创建执行
      const execution = await skillsDevApi.execute({
        skill_id: skillId,
        input_params: params
      })

      message.success('技能已提交执行')

      // 轮询执行状态
      pollExecutionStatus(execution.id)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '执行失败')
      setExecuting(false)
    }
  }

  const pollExecutionStatus = async (executionId: number) => {
    setPolling(true)

    const maxAttempts = 60 // 最多轮询60次（2分钟）
    let attempts = 0

    const poll = async (): Promise<void> => {
      try {
        const execution = await skillsDevApi.getExecution(executionId)

        if (execution.status === 'success' || execution.status === 'failed') {
          setExecutionResult(execution)
          setExecuting(false)
          setPolling(false)

          if (execution.status === 'success') {
            message.success('执行成功')
          } else {
            message.error('执行失败')
          }

          onExecutionComplete?.()
          return
        }

        attempts++
        if (attempts >= maxAttempts) {
          message.warning('执行超时')
          setExecuting(false)
          setPolling(false)
          return
        }

        // 继续轮询
        setTimeout(poll, 2000)
      } catch (error) {
        message.error('获取执行状态失败')
        setExecuting(false)
        setPolling(false)
      }
    }

    poll()
  }

  const getStatusTag = (status: string) => {
    const statusConfig: any = {
      pending: { color: 'default', icon: <LoadingOutlined />, text: '等待中' },
      running: { color: 'processing', icon: <LoadingOutlined />, text: '执行中' },
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' }
    }

    const config = statusConfig[status] || statusConfig.pending
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  return (
    <div className={styles.testerContainer}>
      <Card title="测试参数" className={styles.paramCard}>
        <Form
          form={form}
          layout="vertical"
          onFinish={executeSkill}
        >
          <Form.Item
            name="params"
            label="输入参数（JSON格式）"
            help="请输入 JSON 格式的参数"
          >
            <Input.TextArea
              placeholder='{"param1": "value1", "param2": "value2"}'
              rows={6}
              className={styles.paramsInput}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlayCircleOutlined />}
              loading={executing}
              block
            >
              {executing ? '执行中...' : '执行技能'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {executing && (
        <Card className={styles.resultCard}>
          <div className={styles.executingStatus}>
            <Spin size="large" />
            <p>技能正在执行中...</p>
            {polling && <p className={styles.pollingHint}>正在等待执行结果...</p>}
          </div>
        </Card>
      )}

      {executionResult && !executing && (
        <Card
          title={
            <div className={styles.resultHeader}>
              <span>执行结果</span>
              {getStatusTag(executionResult.status)}
            </div>
          }
          className={styles.resultCard}
        >
          <div className={styles.resultDetails}>
            <div className={styles.detailItem}>
              <strong>执行时间：</strong>
              {executionResult.execution_time} ms
            </div>

            {executionResult.container_id && (
              <div className={styles.detailItem}>
                <strong>容器 ID：</strong>
                <code>{executionResult.container_id.substring(0, 12)}</code>
              </div>
            )}
          </div>

          <Tabs
            items={[
              {
                key: 'output',
                label: '输出',
                children: executionResult.output_result ? (
                  <Editor
                    height="300px"
                    language="plaintext"
                    value={executionResult.output_result}
                    theme="vs-dark"
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false
                    }}
                  />
                ) : (
                  <Empty description="无输出" />
                )
              },
              {
                key: 'error',
                label: '错误',
                children: executionResult.error_message ? (
                  <Alert
                    type="error"
                    message="执行错误"
                    description={executionResult.error_message}
                    showIcon
                  />
                ) : (
                  <Empty description="无错误" />
                )
              },
              {
                key: 'logs',
                label: '日志',
                children: executionResult.logs && executionResult.logs.length > 0 ? (
                  <div className={styles.logList}>
                    {executionResult.logs.map((log: any) => (
                      <div
                        key={log.id}
                        className={`${styles.logItem} ${styles[log.log_level.toLowerCase()]}`}
                      >
                        <Tag color={log.log_level === 'ERROR' ? 'error' : 'default'}>
                          {log.log_level}
                        </Tag>
                        <span className={styles.logMessage}>{log.message}</span>
                        <span className={styles.logTime}>
                          {new Date(log.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty description="无日志" />
                )
              }
            ]}
          />
        </Card>
      )}
    </div>
  )
}
