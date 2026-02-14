import React, { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, Switch, message } from 'antd'
import { skillsDevApi, SkillTemplate } from '@/api/skills-dev'

interface CreateSkillModalProps {
  open: boolean
  onCancel: () => void
  onSuccess: (skillId: number) => void
}

export default function CreateSkillModal({ open, onCancel, onSuccess }: CreateSkillModalProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<SkillTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>()

  useEffect(() => {
    if (open) {
      loadTemplates()
    }
  }, [open])

  const loadTemplates = async () => {
    try {
      const data = await skillsDevApi.listTemplates()
      setTemplates(data)
    } catch (error) {
      console.error('加载模板失败', error)
    }
  }

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      const skill = await skillsDevApi.create(
        {
          name: values.name,
          description: values.description,
          skill_type: values.skill_type || 'custom',
          is_public: values.is_public || false
        },
        selectedTemplate
      )

      message.success('技能创建成功')
      form.resetFields()
      onSuccess(skill.id)
    } catch (error) {
      message.error('创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="创建技能"
      open={open}
      onOk={handleOk}
      onCancel={() => {
        form.resetFields()
        onCancel()
      }}
      confirmLoading={loading}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          skill_type: 'custom',
          is_public: false
        }}
      >
        <Form.Item
          name="name"
          label="技能名称"
          rules={[{ required: true, message: '请输入技能名称' }]}
        >
          <Input placeholder="例如：我的第一个技能" />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
        >
          <Input.TextArea
            placeholder="技能的简要描述"
            rows={3}
          />
        </Form.Item>

        <Form.Item
          label="选择模板"
        >
          <Select
            placeholder="选择一个模板（可选）"
            allowClear
            value={selectedTemplate}
            onChange={setSelectedTemplate}
          >
            {templates.map((template, index) => (
              <Select.Option key={index} value={Object.keys(templates)[index]}>
                {template.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="skill_type"
          label="技能类型"
        >
          <Select>
            <Select.Option value="custom">自定义</Select.Option>
            <Select.Option value="template">模板</Select.Option>
            <Select.Option value="imported">导入</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="is_public"
          label="公开"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}
