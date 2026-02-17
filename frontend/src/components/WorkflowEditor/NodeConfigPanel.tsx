import { useMemo } from 'react'
import { Typography, Form, Input, Select, Button, Divider, Space, Empty } from 'antd'
import { useWorkflowStore } from '@/stores/workflowStore'
import type {
  SkillNodeData,
  ConditionNodeData,
  TransformNodeData,
  ConditionExpression,
  TransformExpression,
} from '@/types/workflow'
import './NodeConfigPanel.css'

const { Text } = Typography
const { Option } = Select
const { TextArea } = Input

export default function NodeConfigPanel() {
  const { nodes, selectedNode, updateNode, removeNode } = useWorkflowStore()

  const currentNode = useMemo(
    () => nodes.find((n) => n.id === selectedNode),
    [nodes, selectedNode]
  )

  if (!currentNode) {
    return (
      <div className="node-config-panel">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="选择节点以编辑属性"
        />
      </div>
    )
  }

  const { data, type } = currentNode

  const handleUpdate = (updates: Partial<typeof data>) => {
    updateNode(currentNode.id, updates)
  }

  const renderConfigByType = () => {
    switch (type) {
      case 'start':
      case 'end':
        return (
          <>
            <Form.Item label="标签">
              <Input
                value={data.label}
                onChange={(e) => handleUpdate({ label: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="描述">
              <TextArea
                value={data.description}
                onChange={(e) => handleUpdate({ description: e.target.value })}
                rows={2}
              />
            </Form.Item>
          </>
        )

      case 'skill':
        return <SkillConfig data={data as SkillNodeData} onUpdate={handleUpdate} />

      case 'condition':
        return <ConditionConfig data={data as ConditionNodeData} onUpdate={handleUpdate} />

      case 'transform':
        return <TransformConfig data={data as TransformNodeData} onUpdate={handleUpdate} />

      default:
        return <Text type="secondary">此节点类型没有可配置项</Text>
    }
  }

  return (
    <div className="node-config-panel">
      <div className="config-header">
        <Text strong>节点配置</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          类型: {type}
        </Text>
      </div>
      <Divider style={{ margin: '12px 0' }} />
      <Form layout="vertical" size="small">
        {renderConfigByType()}
      </Form>
      <Divider style={{ margin: '12px 0' }} />
      <Button danger block onClick={() => removeNode(currentNode.id)}>
        删除节点
      </Button>
    </div>
  )
}

// 技能节点配置
function SkillConfig({
  data,
  onUpdate,
}: {
  data: SkillNodeData
  onUpdate: (updates: Partial<SkillNodeData>) => void
}) {
  return (
    <>
      <Form.Item label="标签">
        <Input
          value={data.label}
          onChange={(e) => onUpdate({ label: e.target.value })}
        />
      </Form.Item>
      <Form.Item label="描述">
        <TextArea
          value={data.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          rows={2}
        />
      </Form.Item>
      <Form.Item label="技能ID">
        <Input
          value={data.skillId}
          onChange={(e) => onUpdate({ skillId: e.target.value, skillName: e.target.value })}
          placeholder="输入技能ID"
        />
      </Form.Item>
      <Form.Item label="输入映射">
        <TextArea
          value={JSON.stringify(data.inputMapping, null, 2)}
          onChange={(e) => {
            try {
              onUpdate({ inputMapping: JSON.parse(e.target.value) })
            } catch {
              // 忽略无效 JSON
            }
          }}
          rows={3}
          placeholder='{"参数名": "${变量名}"}'
        />
      </Form.Item>
      <Form.Item label="输出映射">
        <TextArea
          value={JSON.stringify(data.outputMapping, null, 2)}
          onChange={(e) => {
            try {
              onUpdate({ outputMapping: JSON.parse(e.target.value) })
            } catch {
              // 忽略无效 JSON
            }
          }}
          rows={3}
          placeholder='{"输出字段": "变量名"}'
        />
      </Form.Item>
    </>
  )
}

// 条件节点配置
function ConditionConfig({
  data,
  onUpdate,
}: {
  data: ConditionNodeData
  onUpdate: (updates: Partial<ConditionNodeData>) => void
}) {
  const addCondition = () => {
    const newExpression: ConditionExpression = {
      field: '',
      operator: 'equals',
      value: '',
    }
    onUpdate({
      conditions: {
        ...data.conditions,
        expressions: [...(data.conditions.expressions || []), newExpression],
      },
    })
  }

  const updateCondition = (index: number, updates: Partial<ConditionExpression>) => {
    const expressions = [...(data.conditions.expressions || [])]
    expressions[index] = { ...expressions[index], ...updates }
    onUpdate({
      conditions: { ...data.conditions, expressions },
    })
  }

  const removeCondition = (index: number) => {
    const expressions = (data.conditions.expressions || []).filter((_, i) => i !== index)
    onUpdate({
      conditions: { ...data.conditions, expressions },
    })
  }

  return (
    <>
      <Form.Item label="标签">
        <Input
          value={data.label}
          onChange={(e) => onUpdate({ label: e.target.value })}
        />
      </Form.Item>
      <Form.Item label="描述">
        <TextArea
          value={data.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          rows={2}
        />
      </Form.Item>
      <Form.Item label="条件逻辑">
        <Select
          value={data.conditions.logic}
          onChange={(logic) =>
            onUpdate({
              conditions: { ...data.conditions, logic },
            })
          }
        >
          <Option value="and">全部满足 (AND)</Option>
          <Option value="or">任一满足 (OR)</Option>
        </Select>
      </Form.Item>
      <Divider orientation="left" plain style={{ margin: '8px 0' }}>
        条件表达式
      </Divider>
      {(data.conditions.expressions || []).map((expr, index) => (
        <div key={index} className="condition-row">
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="字段名"
              value={expr.field}
              onChange={(e) => updateCondition(index, { field: e.target.value })}
              style={{ width: '30%' }}
            />
            <Select
              value={expr.operator}
              onChange={(operator) => updateCondition(index, { operator })}
              style={{ width: '35%' }}
            >
              <Option value="equals">等于</Option>
              <Option value="not_equals">不等于</Option>
              <Option value="contains">包含</Option>
              <Option value="greater_than">大于</Option>
              <Option value="less_than">小于</Option>
              <Option value="is_empty">为空</Option>
              <Option value="is_not_empty">不为空</Option>
            </Select>
            <Input
              placeholder="值"
              value={expr.value}
              onChange={(e) => updateCondition(index, { value: e.target.value })}
              style={{ width: '30%' }}
            />
            <Button danger onClick={() => removeCondition(index)}>
              ×
            </Button>
          </Space.Compact>
        </div>
      ))}
      <Button type="dashed" block onClick={addCondition}>
        + 添加条件
      </Button>
      <Form.Item label="True 标签" style={{ marginTop: 16 }}>
        <Input
          value={data.trueLabel}
          onChange={(e) => onUpdate({ trueLabel: e.target.value })}
          placeholder="是"
        />
      </Form.Item>
      <Form.Item label="False 标签">
        <Input
          value={data.falseLabel}
          onChange={(e) => onUpdate({ falseLabel: e.target.value })}
          placeholder="否"
        />
      </Form.Item>
    </>
  )
}

// 数据变换节点配置
function TransformConfig({
  data,
  onUpdate,
}: {
  data: TransformNodeData
  onUpdate: (updates: Partial<TransformNodeData>) => void
}) {
  const addExpression = () => {
    const newExpr: TransformExpression = {
      inputField: '',
      outputField: '',
      transform: 'copy',
    }
    onUpdate({ expressions: [...(data.expressions || []), newExpr] })
  }

  const updateExpression = (index: number, updates: Partial<TransformExpression>) => {
    const expressions = [...(data.expressions || [])]
    expressions[index] = { ...expressions[index], ...updates }
    onUpdate({ expressions })
  }

  const removeExpression = (index: number) => {
    const expressions = (data.expressions || []).filter((_, i) => i !== index)
    onUpdate({ expressions })
  }

  return (
    <>
      <Form.Item label="标签">
        <Input
          value={data.label}
          onChange={(e) => onUpdate({ label: e.target.value })}
        />
      </Form.Item>
      <Form.Item label="描述">
        <TextArea
          value={data.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          rows={2}
        />
      </Form.Item>
      <Divider orientation="left" plain style={{ margin: '8px 0' }}>
        转换表达式
      </Divider>
      {(data.expressions || []).map((expr, index) => (
        <div key={index} className="transform-row">
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            <Space.Compact style={{ width: '100%' }}>
              <Input
                placeholder="输入字段"
                value={expr.inputField}
                onChange={(e) => updateExpression(index, { inputField: e.target.value })}
                style={{ width: '45%' }}
              />
              <span className="transform-arrow">→</span>
              <Input
                placeholder="输出字段"
                value={expr.outputField}
                onChange={(e) => updateExpression(index, { outputField: e.target.value })}
                style={{ width: '45%' }}
              />
              <Button danger onClick={() => removeExpression(index)}>
                ×
              </Button>
            </Space.Compact>
            <Select
              value={expr.transform}
              onChange={(transform) => updateExpression(index, { transform })}
              style={{ width: '100%' }}
            >
              <Option value="copy">复制</Option>
              <Option value="rename">重命名</Option>
              <Option value="format">格式化</Option>
              <Option value="calculate">计算</Option>
              <Option value="custom">自定义</Option>
            </Select>
            {expr.transform === 'custom' && (
              <TextArea
                placeholder="自定义表达式"
                value={expr.customExpression}
                onChange={(e) => updateExpression(index, { customExpression: e.target.value })}
                rows={2}
              />
            )}
          </Space>
        </div>
      ))}
      <Button type="dashed" block onClick={addExpression}>
        + 添加转换
      </Button>
    </>
  )
}
