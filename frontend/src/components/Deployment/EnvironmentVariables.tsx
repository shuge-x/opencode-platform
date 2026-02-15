import React, { useState } from 'react'
import {
  Table,
  Button,
  Input,
  Switch,
  Space,
  Modal,
  Form,
  Select,
  Typography,
  Popconfirm,
  Tooltip,
  Dropdown,
  message,
  Tag,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CopyOutlined,
  DownOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { EnvironmentVariable, EnvTemplate } from '@/types/deployment'
import { ENV_TEMPLATES } from '@/types/deployment'
import styles from './EnvironmentVariables.module.css'

const { Text } = Typography
const { Option } = Select

interface EnvironmentVariablesProps {
  value: EnvironmentVariable[]
  onChange: (variables: EnvironmentVariable[]) => void
  readOnly?: boolean
}

const generateId = () => `env_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

export const EnvironmentVariables: React.FC<EnvironmentVariablesProps> = ({
  value,
  onChange,
  readOnly = false,
}) => {
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editingVar, setEditingVar] = useState<Partial<EnvironmentVariable>>({})
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set())

  // 添加环境变量
  const handleAdd = () => {
    form.resetFields()
    setEditingKey(null)
    setEditingVar({})
    setModalVisible(true)
  }

  // 编辑环境变量
  const handleEdit = (record: EnvironmentVariable) => {
    setEditingKey(record.id)
    setEditingVar(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  // 删除环境变量
  const handleDelete = (id: string) => {
    onChange(value.filter((v) => v.id !== id))
  }

  // 保存环境变量
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingKey) {
        // 更新
        onChange(
          value.map((v) =>
            v.id === editingKey ? { ...v, ...values } : v
          )
        )
      } else {
        // 新增
        onChange([...value, { ...values, id: generateId() }])
      }
      
      setModalVisible(false)
      setEditingKey(null)
      setEditingVar({})
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  // 从模板添加
  const handleAddFromTemplate = (template: EnvTemplate) => {
    const newVars: EnvironmentVariable[] = template.variables.map((v) => ({
      ...v,
      id: generateId(),
    }))
    
    // 检查是否有重复的 key
    const existingKeys = new Set(value.map((v) => v.key))
    const uniqueNewVars = newVars.filter((v) => !existingKeys.has(v.key))
    
    if (uniqueNewVars.length < newVars.length) {
      message.warning(`${newVars.length - uniqueNewVars.length} 个变量因键名重复被跳过`)
    }
    
    onChange([...value, ...uniqueNewVars])
  }

  // 复制值
  const handleCopyValue = (value: string) => {
    navigator.clipboard.writeText(value)
    message.success('已复制到剪贴板')
  }

  // 切换敏感信息可见性
  const toggleSecretVisibility = (id: string) => {
    setVisibleSecrets((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // 表格列定义
  const columns: ColumnsType<EnvironmentVariable> = [
    {
      title: '键名',
      dataIndex: 'key',
      key: 'key',
      width: '25%',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '值',
      dataIndex: 'value',
      key: 'value',
      width: '35%',
      render: (text: string, record) => {
        if (record.isSecret) {
          const isVisible = visibleSecrets.has(record.id)
          return (
            <Space>
              <Text type={isVisible ? undefined : 'secondary'}>
                {isVisible ? text : '••••••••'}
              </Text>
              <Button
                type="text"
                size="small"
                icon={isVisible ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                onClick={() => toggleSecretVisibility(record.id)}
              />
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyValue(text)}
              />
            </Space>
          )
        }
        return (
          <Space>
            <Text>{text || <Text type="secondary">未设置</Text>}</Text>
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopyValue(text)}
            />
          </Space>
        )
      },
    },
    {
      title: '敏感',
      dataIndex: 'isSecret',
      key: 'isSecret',
      width: 80,
      render: (isSecret: boolean) => (
        <Tag color={isSecret ? 'red' : 'default'}>{isSecret ? '是' : '否'}</Tag>
      ),
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description',
      width: '25%',
      render: (text: string) => (
        <Text type="secondary">{text || '-'}</Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) =>
        !readOnly && (
          <Space>
            <Tooltip title="编辑">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
            </Tooltip>
            <Popconfirm
              title="确定删除此环境变量？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          </Space>
        ),
    },
  ]

  // 模板菜单
  const templateMenu = {
    items: ENV_TEMPLATES.map((template) => ({
      key: template.id,
      label: (
        <div>
          <div>{template.name}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {template.description}
          </Text>
        </div>
      ),
      onClick: () => handleAddFromTemplate(template),
    })),
  }

  return (
    <div className={styles.container}>
      {!readOnly && (
        <div className={styles.toolbar}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加变量
            </Button>
            <Dropdown menu={templateMenu}>
              <Button>
                从模板添加 <DownOutlined />
              </Button>
            </Dropdown>
          </Space>
          <Text type="secondary">
            共 {value.length} 个环境变量
          </Text>
        </div>
      )}

      <Table
        columns={columns}
        dataSource={value}
        rowKey="id"
        size="small"
        pagination={false}
        locale={{ emptyText: '暂无环境变量' }}
      />

      <Modal
        title={editingKey ? '编辑环境变量' : '添加环境变量'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="key"
            label="键名"
            rules={[
              { required: true, message: '请输入键名' },
              { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: '键名必须以字母或下划线开头' },
            ]}
          >
            <Input placeholder="例如: DATABASE_URL" />
          </Form.Item>
          <Form.Item
            name="value"
            label="值"
          >
            <Input.TextArea
              placeholder="输入变量值"
              rows={3}
            />
          </Form.Item>
          <Form.Item
            name="isSecret"
            label="敏感信息"
            valuePropName="checked"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
          <Form.Item
            name="description"
            label="说明"
          >
            <Input placeholder="可选的变量描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default EnvironmentVariables
