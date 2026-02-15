import React, { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Dropdown,
  Empty
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RollbackOutlined,
  CloudUploadOutlined,
  DownloadOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ArchiveOutlined,
  EyeOutlined,
  HistoryOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { Skill } from '@/api/skills-dev'
import { skillPublishApi, SkillVersion } from '@/api/skillPublish'
import styles from './VersionManager.module.css'

const { TextArea } = Input

interface VersionManagerProps {
  skill: Skill
}

export default function VersionManager({ skill }: VersionManagerProps) {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingVersion, setEditingVersion] = useState<SkillVersion | null>(null)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  // 获取版本列表
  const { data: versions, isLoading } = useQuery({
    queryKey: ['skill-versions', skill.id],
    queryFn: () => skillPublishApi.listVersions(skill.id)
  })

  // 创建版本
  const createMutation = useMutation({
    mutationFn: (data: { version: string; description?: string; changelog?: string }) =>
      skillPublishApi.createVersion(skill.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      setShowCreateModal(false)
      createForm.resetFields()
      message.success('版本创建成功')
    },
    onError: () => {
      message.error('创建版本失败')
    }
  })

  // 更新版本
  const updateMutation = useMutation({
    mutationFn: (data: { versionId: number; description?: string; changelog?: string }) =>
      skillPublishApi.updateVersion(skill.id, data.versionId, {
        description: data.description,
        changelog: data.changelog
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      setShowEditModal(false)
      setEditingVersion(null)
      editForm.resetFields()
      message.success('版本更新成功')
    },
    onError: () => {
      message.error('更新版本失败')
    }
  })

  // 发布版本
  const publishMutation = useMutation({
    mutationFn: (versionId: number) => skillPublishApi.publishVersion(skill.id, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      message.success('版本已发布')
    },
    onError: () => {
      message.error('发布失败')
    }
  })

  // 归档版本
  const archiveMutation = useMutation({
    mutationFn: (versionId: number) => skillPublishApi.archiveVersion(skill.id, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      message.success('版本已归档')
    },
    onError: () => {
      message.error('归档失败')
    }
  })

  // 回退版本
  const rollbackMutation = useMutation({
    mutationFn: (versionId: number) => skillPublishApi.rollbackVersion(skill.id, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      message.success('已回退到指定版本')
    },
    onError: () => {
      message.error('回退失败')
    }
  })

  // 下载版本
  const handleDownload = async (version: SkillVersion) => {
    try {
      const blob = await skillPublishApi.downloadVersion(skill.id, version.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `skill-${skill.name}-v${version.version}.zip`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载失败')
    }
  }

  // 打开编辑弹窗
  const openEditModal = (version: SkillVersion) => {
    setEditingVersion(version)
    editForm.setFieldsValue({
      description: version.description,
      changelog: version.changelog
    })
    setShowEditModal(true)
  }

  // 处理创建
  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields()
      createMutation.mutate(values)
    } catch (error) {
      // 表单验证失败
    }
  }

  // 处理编辑
  const handleEdit = async () => {
    if (!editingVersion) return
    try {
      const values = await editForm.validateFields()
      updateMutation.mutate({
        versionId: editingVersion.id,
        ...values
      })
    } catch (error) {
      // 表单验证失败
    }
  }

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const config: { [key: string]: { color: string; icon: React.ReactNode; text: string } } = {
      draft: { color: 'default', icon: <EditOutlined />, text: '草稿' },
      published: { color: 'success', icon: <CheckCircleOutlined />, text: '已发布' },
      archived: { color: 'warning', icon: <ArchiveOutlined />, text: '已归档' }
    }
    const { color, icon, text } = config[status] || config.draft
    return <Tag color={color} icon={icon}>{text}</Tag>
  }

  // 表格列定义
  const columns: ColumnsType<SkillVersion> = [
    {
      title: '版本号',
      dataIndex: 'version',
      key: 'version',
      width: 120,
      render: (version: string, record: SkillVersion) => (
        <Space>
          <span style={{ fontWeight: 600 }}>v{version}</span>
          {record.status === 'published' && record.published_at === versions?.[0]?.published_at && (
            <Badge status="processing" text="最新" />
          )}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (desc: string) => desc || '-'
    },
    {
      title: '更新日志',
      dataIndex: 'changelog',
      key: 'changelog',
      ellipsis: true,
      width: 200,
      render: (changelog: string) => (
        <Tooltip title={changelog}>
          <span>{changelog || '-'}</span>
        </Tooltip>
      )
    },
    {
      title: '包大小',
      dataIndex: 'package_size',
      key: 'package_size',
      width: 100,
      render: (size?: number) => size ? `${(size / 1024).toFixed(2)} KB` : '-'
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      key: 'published_at',
      width: 160,
      render: (date?: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => {
        const items = [
          {
            key: 'edit',
            icon: <EditOutlined />,
            label: '编辑',
            onClick: () => openEditModal(record)
          },
          {
            key: 'download',
            icon: <DownloadOutlined />,
            label: '下载',
            onClick: () => handleDownload(record),
            disabled: !record.package_url
          }
        ]

        if (record.status === 'draft') {
          items.push({
            key: 'publish',
            icon: <CloudUploadOutlined />,
            label: '发布',
            onClick: () => {
              Modal.confirm({
                title: '确认发布',
                content: `确定要发布版本 v${record.version} 吗？`,
                onOk: () => publishMutation.mutate(record.id)
              })
            }
          })
        }

        if (record.status === 'published') {
          items.push({
            key: 'archive',
            icon: <ArchiveOutlined />,
            label: '归档',
            danger: true,
            onClick: () => {
              Modal.confirm({
                title: '确认归档',
                content: `归档后版本 v${record.version} 将不再可用，确定要归档吗？`,
                onOk: () => archiveMutation.mutate(record.id)
              })
            }
          })
        }

        if (record.status === 'archived') {
          items.push({
            key: 'rollback',
            icon: <RollbackOutlined />,
            label: '回退到此版本',
            onClick: () => {
              Modal.confirm({
                title: '确认回退',
                content: `确定要回退到版本 v${record.version} 吗？`,
                onOk: () => rollbackMutation.mutate(record.id)
              })
            }
          })
        }

        return (
          <Space>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => openEditModal(record)}
            >
              查看
            </Button>
            <Dropdown menu={{ items }} trigger={['click']}>
              <Button type="link" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        )
      }
    }
  ]

  return (
    <div className={styles.versionManager}>
      <Card
        title={
          <Space>
            <HistoryOutlined />
            <span>版本历史</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateModal(true)}
          >
            发布新版本
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={versions}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个版本`
          }}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty
                description="暂无版本记录"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={() => setShowCreateModal(true)}>
                  创建第一个版本
                </Button>
              </Empty>
            )
          }}
        />
      </Card>

      {/* 创建版本弹窗 */}
      <Modal
        title="发布新版本"
        open={showCreateModal}
        onOk={handleCreate}
        onCancel={() => {
          setShowCreateModal(false)
          createForm.resetFields()
        }}
        confirmLoading={createMutation.isPending}
        width={600}
      >
        <Form
          form={createForm}
          layout="vertical"
          initialValues={{ version: skill.version }}
        >
          <Form.Item
            name="version"
            label="版本号"
            rules={[
              { required: true, message: '请输入版本号' },
              { pattern: /^\d+\.\d+\.\d+$/, message: '版本号格式: x.x.x (如 1.0.0)' }
            ]}
          >
            <Input placeholder="例如: 1.0.0" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="版本描述"
          >
            <Input placeholder="简短描述此版本" />
          </Form.Item>
          
          <Form.Item
            name="changelog"
            label="更新日志"
          >
            <TextArea
              placeholder="详细描述此版本的更新内容..."
              rows={6}
              maxLength={5000}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑版本弹窗 */}
      <Modal
        title={`编辑版本 v${editingVersion?.version}`}
        open={showEditModal}
        onOk={handleEdit}
        onCancel={() => {
          setShowEditModal(false)
          setEditingVersion(null)
          editForm.resetFields()
        }}
        confirmLoading={updateMutation.isPending}
        width={600}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="description"
            label="版本描述"
          >
            <Input placeholder="简短描述此版本" />
          </Form.Item>
          
          <Form.Item
            name="changelog"
            label="更新日志"
          >
            <TextArea
              placeholder="详细描述此版本的更新内容..."
              rows={6}
              maxLength={5000}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
