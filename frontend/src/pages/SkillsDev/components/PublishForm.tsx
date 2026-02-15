import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  Button,
  Select,
  Upload,
  message,
  Space,
  Tag,
  Progress,
  Alert,
  Divider,
  Row,
  Col
} from 'antd'
import {
  PlusOutlined,
  InboxOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Skill } from '@/api/skills-dev'
import { skillPublishApi, SkillPublishData, PublishProgress } from '@/api/skillPublish'
import styles from './PublishForm.module.css'

const { TextArea } = Input
const { Dragger } = Upload

interface PublishFormProps {
  skill: Skill
  onSuccess: () => void
}

export default function PublishForm({ skill, onSuccess }: PublishFormProps) {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [tags, setTags] = useState<string[]>(skill.tags || [])
  const [inputTagVisible, setInputTagVisible] = useState(false)
  const [inputTagValue, setInputTagValue] = useState('')
  const [iconUrl, setIconUrl] = useState<string | undefined>(skill.config?.icon_url)
  const [isPublishing, setIsPublishing] = useState(false)
  const [publishProgress, setPublishProgress] = useState<PublishProgress | null>(null)
  const [publishId, setPublishId] = useState<string | null>(null)

  // 获取分类列表
  const { data: categories } = useQuery({
    queryKey: ['skill-categories'],
    queryFn: () => skillPublishApi.listCategories()
  })

  // 获取热门标签
  const { data: popularTags } = useQuery({
    queryKey: ['popular-tags'],
    queryFn: () => skillPublishApi.listPopularTags(20)
  })

  // 发布技能
  const publishMutation = useMutation({
    mutationFn: (data: SkillPublishData) => skillPublishApi.publish(skill.id, data),
    onSuccess: (result) => {
      setPublishId(result.publish_id)
      startProgressPolling(result.publish_id)
    },
    onError: () => {
      setIsPublishing(false)
      message.error('发布失败，请重试')
    }
  })

  // 轮询发布进度
  const startProgressPolling = (id: string) => {
    const interval = setInterval(async () => {
      try {
        const progress = await skillPublishApi.getPublishProgress(id)
        setPublishProgress(progress)

        if (progress.stage === 'completed') {
          clearInterval(interval)
          setIsPublishing(false)
          queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
          onSuccess()
        } else if (progress.stage === 'failed') {
          clearInterval(interval)
          setIsPublishing(false)
          message.error(progress.error || '发布失败')
        }
      } catch (error) {
        clearInterval(interval)
        setIsPublishing(false)
        message.error('获取发布进度失败')
      }
    }, 1000)
  }

  // 处理图标上传
  const handleIconUpload = async (file: File) => {
    try {
      const result = await skillPublishApi.uploadIcon(skill.id, file)
      setIconUrl(result.icon_url)
      message.success('图标上传成功')
      return false // 阻止默认上传行为
    } catch (error) {
      message.error('图标上传失败')
      return false
    }
  }

  // 添加标签
  const addTag = () => {
    if (inputTagValue && !tags.includes(inputTagValue)) {
      setTags([...tags, inputTagValue])
      setInputTagValue('')
    }
    setInputTagVisible(false)
  }

  // 移除标签
  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  // 提交表单
  const handleSubmit = async (values: any) => {
    setIsPublishing(true)
    setPublishProgress(null)

    const publishData: SkillPublishData = {
      name: values.name,
      description: values.description,
      icon: iconUrl,
      tags: tags,
      category: values.category,
      version: values.version,
      changelog: values.changelog,
      permissions: {
        is_public: values.is_public ?? false,
        access_level: values.access_level || 'private',
        require_approval: values.require_approval ?? false
      }
    }

    publishMutation.mutate(publishData)
  }

  // 取消发布
  const cancelPublish = async () => {
    if (publishId) {
      try {
        await skillPublishApi.cancelPublish(publishId)
        setIsPublishing(false)
        setPublishProgress(null)
        setPublishId(null)
        message.info('发布已取消')
      } catch (error) {
        message.error('取消发布失败')
      }
    }
  }

  // 获取进度条状态
  const getProgressStatus = (): 'success' | 'exception' | 'active' | 'normal' => {
    if (!publishProgress) return 'normal'
    switch (publishProgress.stage) {
      case 'completed': return 'success'
      case 'failed': return 'exception'
      default: return 'active'
    }
  }

  // 获取进度条颜色
  const getProgressColor = () => {
    if (!publishProgress) return '#1890ff'
    switch (publishProgress.stage) {
      case 'completed': return '#52c41a'
      case 'failed': return '#ff4d4f'
      default: return '#1890ff'
    }
  }

  return (
    <div className={styles.publishForm}>
      {/* 发布进度显示 */}
      {isPublishing && publishProgress && (
        <Alert
          type={publishProgress.stage === 'failed' ? 'error' : 'info'}
          className={styles.progressAlert}
          message={
            <div className={styles.progressContent}>
              <div className={styles.progressHeader}>
                {publishProgress.stage === 'completed' ? (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                ) : publishProgress.stage === 'failed' ? (
                  <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                ) : (
                  <LoadingOutlined spin />
                )}
                <span className={styles.progressStage}>
                  {publishProgress.stage === 'packaging' && '打包中...'}
                  {publishProgress.stage === 'uploading' && '上传中...'}
                  {publishProgress.stage === 'validating' && '验证中...'}
                  {publishProgress.stage === 'publishing' && '发布中...'}
                  {publishProgress.stage === 'completed' && '发布完成'}
                  {publishProgress.stage === 'failed' && '发布失败'}
                </span>
              </div>
              <Progress
                percent={publishProgress.progress}
                status={getProgressStatus()}
                strokeColor={getProgressColor()}
              />
              <div className={styles.progressMessage}>{publishProgress.message}</div>
              {publishProgress.stage !== 'completed' && publishProgress.stage !== 'failed' && (
                <Button size="small" danger onClick={cancelPublish}>
                  取消发布
                </Button>
              )}
            </div>
          }
        />
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          name: skill.name,
          description: skill.description,
          category: skill.skill_type,
          version: skill.version,
          is_public: skill.is_public,
          access_level: skill.is_public ? 'public' : 'private',
          require_approval: false
        }}
        onFinish={handleSubmit}
        disabled={isPublishing}
      >
        <Row gutter={24}>
          <Col span={16}>
            {/* 基本信息 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>基本信息</h3>
              
              <Form.Item
                name="name"
                label="技能名称"
                rules={[{ required: true, message: '请输入技能名称' }]}
              >
                <Input placeholder="输入技能名称" maxLength={100} />
              </Form.Item>

              <Form.Item
                name="description"
                label="技能描述"
                rules={[{ required: true, message: '请输入技能描述' }]}
              >
                <TextArea
                  placeholder="详细描述您的技能功能、用途和使用场景"
                  rows={4}
                  maxLength={2000}
                  showCount
                />
              </Form.Item>

              <Form.Item
                name="category"
                label="技能分类"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="选择技能分类">
                  {categories?.map(cat => (
                    <Select.Option key={cat} value={cat}>{cat}</Select.Option>
                  ))}
                  <Select.Option value="custom">自定义</Select.Option>
                  <Select.Option value="development">开发工具</Select.Option>
                  <Select.Option value="automation">自动化</Select.Option>
                  <Select.Option value="data">数据处理</Select.Option>
                  <Select.Option value="ai">AI助手</Select.Option>
                  <Select.Option value="integration">集成工具</Select.Option>
                </Select>
              </Form.Item>
            </div>

            {/* 版本信息 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>版本信息</h3>
              
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
                name="changelog"
                label="更新日志"
              >
                <TextArea
                  placeholder="描述此版本的更新内容..."
                  rows={4}
                  maxLength={5000}
                  showCount
                />
              </Form.Item>
            </div>
          </Col>

          <Col span={8}>
            {/* 图标上传 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>技能图标</h3>
              
              <div className={styles.iconUploadWrapper}>
                {iconUrl ? (
                  <div className={styles.iconPreview}>
                    <img src={iconUrl} alt="技能图标" />
                    <Button
                      size="small"
                      danger
                      className={styles.removeIcon}
                      onClick={() => setIconUrl(undefined)}
                    >
                      移除
                    </Button>
                  </div>
                ) : (
                  <Dragger
                    accept="image/*"
                    showUploadList={false}
                    beforeUpload={(file) => {
                      if (file.size > 2 * 1024 * 1024) {
                        message.error('图标大小不能超过2MB')
                        return false
                      }
                      handleIconUpload(file)
                      return false
                    }}
                    className={styles.iconDragger}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽上传图标</p>
                    <p className="ant-upload-hint">支持 JPG、PNG、SVG，建议 256x256px</p>
                  </Dragger>
                )}
              </div>
            </div>

            {/* 标签 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>标签</h3>
              
              <div className={styles.tagsContainer}>
                {tags.map(tag => (
                  <Tag
                    key={tag}
                    closable
                    onClose={() => removeTag(tag)}
                    className={styles.skillTag}
                  >
                    {tag}
                  </Tag>
                ))}
                {inputTagVisible ? (
                  <Input
                    type="text"
                    size="small"
                    className={styles.tagInput}
                    value={inputTagValue}
                    onChange={e => setInputTagValue(e.target.value)}
                    onBlur={addTag}
                    onPressEnter={addTag}
                    autoFocus
                  />
                ) : (
                  <Tag
                    className={styles.addTag}
                    onClick={() => setInputTagVisible(true)}
                  >
                    <PlusOutlined /> 添加标签
                  </Tag>
                )}
              </div>

              {popularTags && popularTags.length > 0 && (
                <div className={styles.popularTags}>
                  <span className={styles.popularTagsLabel}>热门标签:</span>
                  <div className={styles.popularTagsList}>
                    {popularTags.slice(0, 10).map(tag => (
                      <Tag
                        key={tag}
                        className={styles.popularTag}
                        onClick={() => {
                          if (!tags.includes(tag)) {
                            setTags([...tags, tag])
                          }
                        }}
                      >
                        {tag}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 权限设置 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>访问权限</h3>
              
              <Form.Item
                name="access_level"
                label="可见性"
              >
                <Select>
                  <Select.Option value="private">私有 - 仅自己可见</Select.Option>
                  <Select.Option value="public">公开 - 所有人可见</Select.Option>
                  <Select.Option value="restricted">受限 - 指定用户可见</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="require_approval"
                label="安装审批"
                valuePropName="checked"
                extra="开启后，用户安装此技能需要您的审批"
              >
                <Input type="checkbox" />
              </Form.Item>
            </div>
          </Col>
        </Row>

        <Divider />

        <Form.Item className={styles.formActions}>
          <Space>
            <Button onClick={() => form.resetFields()}>
              重置
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={isPublishing}
              disabled={isPublishing}
              size="large"
            >
              {isPublishing ? '发布中...' : '发布技能'}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}
