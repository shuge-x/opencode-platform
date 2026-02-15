import React, { useState, useRef, useEffect } from 'react'
import {
  Card,
  Form,
  Select,
  Button,
  Upload,
  Progress,
  Alert,
  Space,
  message,
  Divider,
  Input,
  Modal,
  List,
  Tag
} from 'antd'
import {
  InboxOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  FileZipOutlined,
  DownloadOutlined,
  DeleteOutlined
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Skill } from '@/api/skills-dev'
import { skillPublishApi, SkillVersion } from '@/api/skillPublish'
import styles from './PackageUpload.module.css'

const { Dragger } = Upload

interface PackageUploadProps {
  skill: Skill
  versions: SkillVersion[]
}

type PackageStage = 'idle' | 'packaging' | 'uploading' | 'success' | 'error'

interface PackageProgress {
  stage: 'preparing' | 'packing' | 'compressing' | 'completed' | 'failed'
  progress: number
  message: string
  files_total?: number
  files_processed?: number
}

export default function PackageUpload({ skill, versions }: PackageUploadProps) {
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [packageStage, setPackageStage] = useState<PackageStage>('idle')
  const [packageProgress, setPackageProgress] = useState<0 | number>(0)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [packageId, setPackageId] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [newVersion, setNewVersion] = useState('')
  const [newVersionDesc, setNewVersionDesc] = useState('')
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // 创建打包任务
  const packageMutation = useMutation({
    mutationFn: (version: string) => skillPublishApi.packageSkill(skill.id, version),
    onSuccess: (result) => {
      setPackageId(result.package_id)
      startPackagePolling(result.package_id)
    },
    onError: () => {
      setPackageStage('error')
      setStatusMessage('创建打包任务失败')
    }
  })

  // 上传技能包
  const uploadMutation = useMutation({
    mutationFn: ({ file, version }: { file: File; version: string }) =>
      skillPublishApi.uploadPackage(skill.id, file, (progress) => {
        setUploadProgress(progress)
      }),
    onSuccess: () => {
      setPackageStage('success')
      setStatusMessage('技能包上传成功')
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
    },
    onError: () => {
      setPackageStage('error')
      setStatusMessage('技能包上传失败')
    }
  })

  // 创建新版本
  const createVersionMutation = useMutation({
    mutationFn: () =>
      skillPublishApi.createVersion(skill.id, {
        version: newVersion,
        description: newVersionDesc
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill-versions', skill.id] })
      setShowVersionModal(false)
      setNewVersion('')
      setNewVersionDesc('')
      message.success('版本创建成功')
    },
    onError: () => {
      message.error('创建版本失败')
    }
  })

  // 开始打包进度轮询
  const startPackagePolling = (id: string) => {
    pollingRef.current = setInterval(async () => {
      try {
        const progress: PackageProgress = await skillPublishApi.getPackageProgress(id)
        setPackageProgress(progress.progress)
        setStatusMessage(progress.message)

        if (progress.stage === 'completed') {
          stopPolling()
          // 打包完成，开始上传
          // 这里假设打包完成后会自动下载或获取文件
          setPackageStage('uploading')
          setStatusMessage('准备上传...')
        } else if (progress.stage === 'failed') {
          stopPolling()
          setPackageStage('error')
          setStatusMessage(progress.message || '打包失败')
        }
      } catch (error) {
        stopPolling()
        setPackageStage('error')
        setStatusMessage('获取打包进度失败')
      }
    }, 1000)
  }

  // 停止轮询
  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  // 清理
  useEffect(() => {
    return () => stopPolling()
  }, [])

  // 开始打包
  const handlePackage = async () => {
    try {
      const values = await form.validateFields()
      setPackageStage('packaging')
      setPackageProgress(0)
      setStatusMessage('准备打包...')
      packageMutation.mutate(values.version)
    } catch (error) {
      message.error('请选择版本')
    }
  }

  // 处理文件选择
  const handleFileSelect = (file: File) => {
    const isValidType = file.name.endsWith('.zip') || file.name.endsWith('.tar.gz')
    if (!isValidType) {
      message.error('只支持 .zip 或 .tar.gz 格式的文件')
      return false
    }
    if (file.size > 100 * 1024 * 1024) {
      message.error('文件大小不能超过100MB')
      return false
    }
    setSelectedFile(file)
    return false // 阻止自动上传
  }

  // 手动上传
  const handleUpload = async () => {
    if (!selectedFile) {
      message.warning('请先选择要上传的文件')
      return
    }

    try {
      const values = await form.validateFields()
      setPackageStage('uploading')
      setUploadProgress(0)
      uploadMutation.mutate({ file: selectedFile, version: values.version })
    } catch (error) {
      message.error('请选择版本')
    }
  }

  // 下载版本包
  const handleDownload = async (versionId: number) => {
    try {
      const blob = await skillPublishApi.downloadVersion(skill.id, versionId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `skill-${skill.id}-v${versions.find(v => v.id === versionId)?.version}.zip`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载失败')
    }
  }

  // 重置状态
  const handleReset = () => {
    setPackageStage('idle')
    setPackageProgress(0)
    setUploadProgress(0)
    setStatusMessage('')
    setSelectedFile(null)
    setPackageId(null)
    stopPolling()
  }

  // 获取状态图标
  const getStatusIcon = () => {
    switch (packageStage) {
      case 'packaging':
      case 'uploading':
        return <SyncOutlined spin className={`${styles.statusIcon} ${styles.processing}`} />
      case 'success':
        return <CheckCircleOutlined className={`${styles.statusIcon} ${styles.success}`} />
      case 'error':
        return <CloseCircleOutlined className={`${styles.statusIcon} ${styles.error}`} />
      default:
        return <FileZipOutlined className={styles.statusIcon} />
    }
  }

  return (
    <div className={styles.packageUpload}>
      <div className={styles.uploadSection}>
        <Card title="打包技能" className={styles.packageCard}>
          <Form form={form} layout="vertical">
            <Form.Item
              name="version"
              label="选择版本"
              rules={[{ required: true, message: '请选择版本' }]}
            >
              <Select 
                placeholder="选择要打包的版本"
                dropdownRender={(menu) => (
                  <>
                    {menu}
                    <Divider style={{ margin: '8px 0' }} />
                    <Button
                      type="text"
                      icon={<span>+</span>}
                      onClick={() => setShowVersionModal(true)}
                      style={{ width: '100%', textAlign: 'left' }}
                    >
                      创建新版本
                    </Button>
                  </>
                )}
              >
                {versions.filter(v => v.status !== 'archived').map(v => (
                  <Select.Option key={v.id} value={v.version}>
                    v{v.version} 
                    <Tag 
                      color={v.status === 'published' ? 'green' : 'blue'}
                      style={{ marginLeft: 8 }}
                    >
                      {v.status === 'published' ? '已发布' : '草稿'}
                    </Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Button
              type="primary"
              icon={<FileZipOutlined />}
              onClick={handlePackage}
              loading={packageStage === 'packaging'}
              disabled={packageStage === 'packaging' || packageStage === 'uploading'}
              block
            >
              打包当前版本
            </Button>
          </Form>
        </Card>

        <Card title="或上传技能包" className={styles.uploadCard}>
          <Dragger
            accept=".zip,.tar.gz"
            beforeUpload={handleFileSelect}
            showUploadList={false}
            className={styles.dragger}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域</p>
            <p className="ant-upload-hint">
              支持 .zip 或 .tar.gz 格式，最大 100MB
            </p>
            {selectedFile && (
              <div className={styles.selectedFile}>
                <FileZipOutlined /> {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}
          </Dragger>

          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={handleUpload}
            loading={packageStage === 'uploading'}
            disabled={!selectedFile || packageStage === 'packaging' || packageStage === 'uploading'}
            block
            style={{ marginTop: 16 }}
          >
            上传技能包
          </Button>
        </Card>
      </div>

      {/* 进度显示 */}
      {packageStage !== 'idle' && (
        <Card className={styles.progressCard}>
          <div className={styles.progressHeader}>
            {getStatusIcon()}
            <span className={styles.progressTitle}>
              {packageStage === 'packaging' && '打包中'}
              {packageStage === 'uploading' && '上传中'}
              {packageStage === 'success' && '完成'}
              {packageStage === 'error' && '失败'}
            </span>
          </div>

          {(packageStage === 'packaging' || packageStage === 'uploading') && (
            <Progress
              percent={packageStage === 'packaging' ? packageProgress : uploadProgress}
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068'
              }}
            />
          )}

          <Alert
            type={packageStage === 'error' ? 'error' : packageStage === 'success' ? 'success' : 'info'}
            message={statusMessage}
            showIcon
            style={{ marginTop: 12 }}
          />

          {(packageStage === 'success' || packageStage === 'error') && (
            <Button onClick={handleReset} style={{ marginTop: 12 }}>
              重新开始
            </Button>
          )}
        </Card>
      )}

      {/* 版本列表 */}
      <Card title="已打包版本" className={styles.versionsCard}>
        <List
          dataSource={versions.filter(v => v.package_url)}
          renderItem={(version) => (
            <List.Item
              actions={[
                <Button
                  key="download"
                  type="link"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(version.id)}
                >
                  下载
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<FileZipOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={`v${version.version}`}
                description={
                  <Space>
                    <span>{version.description || '无描述'}</span>
                    <span>{version.package_size ? `${(version.package_size / 1024).toFixed(2)} KB` : ''}</span>
                    <Tag color={version.status === 'published' ? 'green' : 'blue'}>
                      {version.status === 'published' ? '已发布' : version.status}
                    </Tag>
                  </Space>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无已打包的版本' }}
        />
      </Card>

      {/* 创建新版本弹窗 */}
      <Modal
        title="创建新版本"
        open={showVersionModal}
        onOk={() => createVersionMutation.mutate()}
        onCancel={() => setShowVersionModal(false)}
        confirmLoading={createVersionMutation.isPending}
      >
        <Form layout="vertical">
          <Form.Item label="版本号" required>
            <Input
              placeholder="例如: 1.0.0"
              value={newVersion}
              onChange={(e) => setNewVersion(e.target.value)}
            />
          </Form.Item>
          <Form.Item label="版本描述">
            <Input.TextArea
              placeholder="描述此版本的更新内容..."
              value={newVersionDesc}
              onChange={(e) => setNewVersionDesc(e.target.value)}
              rows={4}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
