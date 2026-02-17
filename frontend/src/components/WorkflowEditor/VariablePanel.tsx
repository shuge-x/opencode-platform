import { useState, useCallback } from 'react'
import { Typography, Button, List, Tag, Modal, Form, Input, Select, Switch, Space, Collapse } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  VariableOutlined,
} from '@ant-design/icons'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { WorkflowVariable } from '@/types/workflow'
import './VariablePanel.css'

const { Text } = Typography
const { Panel } = Collapse
const { Option } = Select

const variableTypeColors: Record<WorkflowVariable['type'], string> = {
  string: 'blue',
  number: 'green',
  boolean: 'orange',
  object: 'purple',
  array: 'cyan',
}

const variableTypeLabels: Record<WorkflowVariable['type'], string> = {
  string: '字符串',
  number: '数字',
  boolean: '布尔值',
  object: '对象',
  array: '数组',
}

export default function VariablePanel() {
  const { variables, addVariable, updateVariable, removeVariable } = useWorkflowStore()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingVariable, setEditingVariable] = useState<WorkflowVariable | null>(null)
  const [form] = Form.useForm()

  const handleAdd = useCallback(() => {
    setEditingVariable(null)
    form.resetFields()
    form.setFieldsValue({
      type: 'string',
      required: false,
    })
    setModalVisible(true)
  }, [form])

  const handleEdit = useCallback(
    (variable: WorkflowVariable) => {
      setEditingVariable(variable)
      form.setFieldsValue({
        name: variable.name,
        type: variable.type,
        defaultValue:
          variable.type === 'object' || variable.type === 'array'
            ? JSON.stringify(variable.defaultValue, null, 2)
            : String(variable.defaultValue ?? ''),
        description: variable.description,
        required: variable.required,
      })
      setModalVisible(true)
    },
    [form]
  )

  const handleDelete = useCallback(
    (id: string) => {
      Modal.confirm({
        title: '确认删除',
        content: '确定要删除此变量吗？',
        onOk: () => removeVariable(id),
      })
    },
    [removeVariable]
  )

  const handleSave = useCallback(async () => {
    try {
      const values = await form.validateFields()
      let defaultValue: unknown = values.defaultValue

      // 解析对象和数组类型
      if (values.type === 'object' || values.type === 'array') {
        try {
          defaultValue = values.defaultValue ? JSON.parse(values.defaultValue) : undefined
        } catch {
          form.setFields([
            {
              name: 'defaultValue',
              errors: ['无效的 JSON 格式'],
            },
          ])
          return
        }
      } else if (values.type === 'number') {
        defaultValue = values.defaultValue ? Number(values.defaultValue) : undefined
      } else if (values.type === 'boolean') {
        defaultValue = values.defaultValue === 'true' || values.defaultValue === true
      }

      const variableData: Omit<WorkflowVariable, 'id'> = {
        name: values.name,
        type: values.type,
        defaultValue,
        description: values.description,
        required: values.required,
      }

      if (editingVariable) {
        updateVariable(editingVariable.id, variableData)
      } else {
        addVariable({
          ...variableData,
          id: `var-${Date.now()}`,
        })
      }

      setModalVisible(false)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }, [form, editingVariable, addVariable, updateVariable])

  return (
    <div className="variable-panel">
      <Collapse
        defaultActiveKey={['variables']}
        className="variable-collapse"
        expandIconPosition="start"
      >
        <Panel
          header={
            <Space>
              <VariableOutlined />
              <Text strong>工作流变量</Text>
              <Tag color="blue">{variables.length}</Tag>
            </Space>
          }
          key="variables"
          extra={
            <Button
              type="text"
              size="small"
              icon={<PlusOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                handleAdd()
              }}
            />
          }
        >
          <div className="variable-list">
            {variables.length === 0 ? (
              <div className="empty-variables">
                <Text type="secondary">暂无变量，点击 + 添加</Text>
              </div>
            ) : (
              <List
                dataSource={variables}
                renderItem={(variable) => (
                  <List.Item
                    className="variable-item"
                    actions={[
                      <Button
                        key="edit"
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(variable)}
                      />,
                      <Button
                        key="delete"
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDelete(variable.id)}
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text code>{variable.name}</Text>
                          <Tag color={variableTypeColors[variable.type]}>
                            {variableTypeLabels[variable.type]}
                          </Tag>
                          {variable.required && <Tag color="red">必填</Tag>}
                        </Space>
                      }
                      description={variable.description}
                    />
                  </List.Item>
                )}
              />
            )}
          </div>
        </Panel>
      </Collapse>

      <Modal
        title={editingVariable ? '编辑变量' : '添加变量'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label="变量名"
            rules={[
              { required: true, message: '请输入变量名' },
              { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '变量名只能包含字母、数字和下划线，且不能以数字开头' },
            ]}
          >
            <Input placeholder="例如: input_data" disabled={!!editingVariable} />
          </Form.Item>

          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select>
              <Option value="string">字符串</Option>
              <Option value="number">数字</Option>
              <Option value="boolean">布尔值</Option>
              <Option value="object">对象</Option>
              <Option value="array">数组</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="defaultValue"
            label="默认值"
            extra="对象和数组类型请输入 JSON 格式"
          >
            <Input.TextArea rows={3} placeholder="可选，输入默认值" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input placeholder="变量的用途说明" />
          </Form.Item>

          <Form.Item name="required" label="必填" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
