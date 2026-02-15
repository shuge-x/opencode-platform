import React, { useState } from 'react'
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Typography,
  Popconfirm,
  Tooltip,
  Tag,
  message,
  Alert,
  Steps,
  Card,
  Switch,
  Divider,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  LinkOutlined,
  SafetyCertificateOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { DomainConfig } from '@/types/deployment'
import styles from './DomainBinding.module.css'

const { Text, Paragraph } = Typography

interface DomainBindingProps {
  deploymentId: string
  domains: DomainConfig[]
  defaultDomain?: string
  onAddDomain: (domain: string, sslEnabled?: boolean) => Promise<void>
  onVerifyDomain: (domainId: string) => Promise<void>
  onRemoveDomain: (domainId: string) => Promise<void>
  loading?: boolean
}

export const DomainBinding: React.FC<DomainBindingProps> = ({
  deploymentId,
  domains,
  defaultDomain,
  onAddDomain,
  onVerifyDomain,
  onRemoveDomain,
  loading = false,
}) => {
  const [modalVisible, setModalVisible] = useState(false)
  const [verifyingDomain, setVerifyingDomain] = useState<string | null>(null)
  const [form] = Form.useForm()
  const [useCustomSSL, setUseCustomSSL] = useState(false)

  // 添加域名
  const handleAddDomain = async () => {
    try {
      const values = await form.validateFields()
      await onAddDomain(values.domain, values.sslEnabled)
      setModalVisible(false)
      form.resetFields()
    } catch (error) {
      console.error('Failed to add domain:', error)
    }
  }

  // 验证域名
  const handleVerify = async (domainId: string) => {
    setVerifyingDomain(domainId)
    try {
      await onVerifyDomain(domainId)
    } finally {
      setVerifyingDomain(null)
    }
  }

  // 删除域名
  const handleDelete = async (domainId: string) => {
    await onRemoveDomain(domainId)
  }

  // 复制 DNS 记录值
  const copyDNSRecord = (value: string) => {
    navigator.clipboard.writeText(value)
    message.success('已复制到剪贴板')
  }

  // 表格列定义
  const columns: ColumnsType<DomainConfig> = [
    {
      title: '域名',
      dataIndex: 'domain',
      key: 'domain',
      render: (domain: string, record) => (
        <Space>
          <LinkOutlined />
          <Text strong>{domain}</Text>
          {record.sslEnabled && (
            <Tooltip title="SSL 已启用">
              <SafetyCertificateOutlined style={{ color: '#52c41a' }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'isVerified',
      key: 'status',
      render: (isVerified: boolean) => (
        <Tag color={isVerified ? 'success' : 'warning'} icon={isVerified ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {isVerified ? '已验证' : '待验证'}
        </Tag>
      ),
    },
    {
      title: 'SSL',
      dataIndex: 'sslEnabled',
      key: 'ssl',
      render: (sslEnabled: boolean, record) => (
        <Space>
          <Tag color={sslEnabled ? 'blue' : 'default'}>
            {sslEnabled ? (record.sslProvider === 'letsencrypt' ? 'Let\'s Encrypt' : '自定义') : '未启用'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '添加时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          {!record.isVerified && (
            <Tooltip title="验证域名">
              <Button
                type="link"
                size="small"
                icon={<SyncOutlined spin={verifyingDomain === record.id} />}
                onClick={() => handleVerify(record.id)}
                loading={verifyingDomain === record.id}
              >
                验证
              </Button>
            </Tooltip>
          )}
          <Popconfirm
            title="确定删除此域名？"
            description="删除后该域名将无法访问"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // DNS 验证说明
  const renderDNSInstructions = () => {
    const verificationDomain = defaultDomain || 'verify.opencode.local'
    
    return (
      <Card className={styles.dnsCard} title="DNS 验证说明">
        <Steps
          direction="vertical"
          size="small"
          current={-1}
          items={[
            {
              title: '添加 DNS 记录',
              description: (
                <div>
                  <Paragraph>
                    在您的域名 DNS 管理页面添加以下记录：
                  </Paragraph>
                  <div className={styles.dnsRecord}>
                    <div>
                      <Text type="secondary">类型：</Text>
                      <Text code>CNAME</Text>
                    </div>
                    <div>
                      <Text type="secondary">主机：</Text>
                      <Text code>@</Text>
                      <Button
                        type="text"
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => copyDNSRecord('@')}
                      />
                    </div>
                    <div>
                      <Text type="secondary">值：</Text>
                      <Text code>{verificationDomain}</Text>
                      <Button
                        type="text"
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => copyDNSRecord(verificationDomain)}
                      />
                    </div>
                  </div>
                </div>
              ),
            },
            {
              title: '等待生效',
              description: 'DNS 记录生效通常需要几分钟到几小时不等',
            },
            {
              title: '点击验证',
              description: 'DNS 生效后，点击"验证"按钮完成域名绑定',
            },
          ]}
        />
      </Card>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h3>域名绑定</h3>
          <Text type="secondary">
            为您的技能配置自定义域名，支持 SSL 证书自动配置
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          添加域名
        </Button>
      </div>

      {defaultDomain && (
        <Alert
          type="info"
          showIcon
          message="默认域名"
          description={
            <Space>
              <Text>您的技能默认访问地址：</Text>
              <Text code strong>
                https://{defaultDomain}
              </Text>
            </Space>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Table
        columns={columns}
        dataSource={domains}
        rowKey="id"
        size="small"
        pagination={false}
        locale={{ emptyText: '暂无自定义域名' }}
      />

      {domains.some((d) => !d.isVerified) && renderDNSInstructions()}

      <Modal
        title="添加自定义域名"
        open={modalVisible}
        onOk={handleAddDomain}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        okText="添加"
        cancelText="取消"
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" initialValues={{ sslEnabled: true }}>
          <Form.Item
            name="domain"
            label="域名"
            rules={[
              { required: true, message: '请输入域名' },
              {
                pattern: /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/,
                message: '请输入有效的域名',
              },
            ]}
          >
            <Input placeholder="例如: api.example.com" />
          </Form.Item>
          
          <Form.Item
            name="sslEnabled"
            label="启用 SSL"
            valuePropName="checked"
            tooltip="自动使用 Let's Encrypt 配置免费 SSL 证书"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Alert
            type="warning"
            showIcon
            message="请确保您已拥有该域名，并能够修改其 DNS 记录"
            style={{ marginTop: 8 }}
          />
        </Form>
      </Modal>
    </div>
  )
}

export default DomainBinding
