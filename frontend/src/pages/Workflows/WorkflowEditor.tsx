import React, { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import WorkflowEditorComponent from '@/components/WorkflowEditor'
import { useWorkflowStore, Workflow } from '@/stores/workflowStore'
import { message } from 'antd'

// Mock 数据 - 后续替换为 API 调用
const mockWorkflow: Workflow = {
  id: '1',
  name: '示例工作流',
  description: '这是一个示例工作流',
  nodes: [
    {
      id: 'start_1',
      type: 'start',
      position: { x: 250, y: 50 },
      data: {
        label: '开始',
        type: 'start',
      },
    },
    {
      id: 'skill_1',
      type: 'skill',
      position: { x: 250, y: 200 },
      data: {
        label: '数据处理',
        type: 'skill',
        skillName: 'data_processor',
      },
    },
    {
      id: 'end_1',
      type: 'end',
      position: { x: 250, y: 350 },
      data: {
        label: '结束',
        type: 'end',
      },
    },
  ],
  edges: [
    {
      id: 'e1',
      source: 'start_1',
      target: 'skill_1',
    },
    {
      id: 'e2',
      source: 'skill_1',
      target: 'end_1',
    },
  ],
  variables: [],
  is_active: true,
  created_at: '2026-02-15 10:00:00',
  updated_at: '2026-02-16 14:30:00',
}

const WorkflowEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { setCurrentWorkflow, reset } = useWorkflowStore()
  
  useEffect(() => {
    // 如果是编辑模式，加载工作流数据
    if (id && id !== 'new') {
      // 这里后续替换为 API 调用
      setCurrentWorkflow(mockWorkflow)
      message.success('工作流已加载')
    } else {
      // 新建模式，重置状态
      reset()
    }
    
    // 清理函数
    return () => {
      reset()
    }
  }, [id, setCurrentWorkflow, reset, navigate])
  
  return <WorkflowEditorComponent />
}

export default WorkflowEditorPage
