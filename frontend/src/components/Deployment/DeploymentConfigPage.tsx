import React, { useState, useEffect } from 'react'
import {
  Card,
  Steps,
  Button,
  Form,
  Select,
  InputNumber,
  Slider,
  Space,
  Typography,
  Alert,
  Spin,
  Divider,
  Row,
  Col,
  message,
  Progress,
  Modal,
  Switch,
} from 'antd'
import {
  CloudServerOutlined,
  SettingOutlined,
  LinkOutlined,
  FileTextOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import type { DeploymentConfig, ResourceLimits, PortConfig, EnvironmentVariable } from '@/types/deployment'
import { EnvironmentVariables } from './EnvironmentVariables'
import styles from './DeploymentConfig.module.css'

const { Text, Title } = Typography
const { Option } = Select
const { Step } = Steps

interface DeploymentConfigPageProps {
  skillId: string
  skillName: string
  versions: string[]
  defaultVersion?: string
  onDeploy: (config: DeploymentConfig) => Promise<void>
  loading?: boolean
  existingConfig?: DeploymentConfig
}

// 资源预设配置
const RESOURCE_PRESETS = [
  { name: '轻量', cpu: 0.5, memory: 256, description: '适合轻量级应用' },
  { name: '标准', cpu: 1, memory: 512, description: '适合标准应用' },
  { name: '高性能', cpu: 2, memory: 1024, description: '适合资源密集型应用' },
  { name: '自定义', cpu: 0, memory: 0, description: '自定义资源配置' },
]

export const DeploymentConfigPage: React.FC<DeploymentConfigPageProps> = ({
  skillId,
  skillName,
  versions,
  defaultVersion,
  onDeploy,
  loading = false,
  existingConfig,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()
  const [deployProgress, setDeployProgress] = useState(0)
  const [deployStatus, setDeployStatus] = useState<'idle' | 'deploying' | 'success' | 'error'>('idle')
  const [selectedPreset, setSelectedPreset] = useState(1) // 默认标准配置
  const [autoScaling, setAutoScaling] = useState(false)

  // 初始化表单
  useEffect(() => {
    if (existingConfig) {
      form.setFieldsValue({
        version: existingConfig.version,
        replicas: existingConfig.replicas || 1,
        resources: existingConfig.resources,
        ports: existingConfig.ports,
      })
    } else {
      form.setFieldsValue({
        version: defaultVersion || versions[0],
        replicas: 1,
        resources: RESOURCE_PRESETS[1], // 默认标准配置
        ports: [{ port: 8080, protocol: 'tcp' }],
      })
    }
  }, [existingConfig, defaultVersion, versions, form])

  // 版本选择步骤
  const renderVersionStep = () => (
    <div className={styles.stepContent}>
      <Title level={5}>选择技能版本</Title>
      <Text type="secondary">选择要部署的技能版本</Text>
      
      <Form.Item
        name="version"
        label="版本"
        rules={[{ required: true, message: '请选择版本' }]}
        style={{ marginTop: 16, maxWidth: 300 }}
      >
        <Select placeholder="选择版本">
          {versions.map((v) => (
            <Option key={v} value={v}>
              v{v}
            </Option>
          ))}
        </Select>
      </Form.Item>
    </div>
  )

  // 资源配置步骤
  const renderResourceStep = () => (
    <div className={styles.stepContent}>
      <Title level={5}>资源配置</Title>
      <Text type="secondary">配置部署的资源和端口</Text>

      <div className={styles.section}>
        <Text strong>资源预设</Text>
        <Row gutter={[16, 16]} style={{ marginTop: 12 }}>
          {RESOURCE_PRESETS.map((preset, index) => (
            <Col span={6} key={preset.name}>
              <Card
                hoverable
                className={`${styles.presetCard} ${selectedPreset === index ? styles.presetCardActive : ''}`}
                onClick={() => {
                  if (preset.name !== '自定义') {
                    setSelectedPreset(index)
                    form.setFieldsValue({
                      resources: { cpu: preset.cpu, memory: preset.memory }
                    })
                  } else {
                    setSelectedPreset(index)
                  }
                }}
              >
                <div className={styles.presetName}>{preset.name}</div>
                <div className={styles.presetSpec}>
                  {preset.cpu > 0 ? `${preset.cpu} CPU / ${preset.memory}MB` : '自定义'}
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {preset.description}
                </Text>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      <div className={styles.section}>
        <Form.Item label="CPU 核心" name={['resources', 'cpu']}>
          <Slider
            min={0.1}
            max={4}
            step={0.1}
            marks={{ 0.1: '0.1', 1: '1', 2: '2', 4: '4' }}
            tooltip={{ formatter: (v) => `${v} 核` }}
          />
        </Form.Item>
        
        <Form.Item label="内存 (MB)" name={['resources', 'memory']}>
          <Slider
            min={64}
            max={8192}
            step={64}
            marks={{ 64: '64', 1024: '1GB', 4096: '4GB', 8192: '8GB' }}
            tooltip={{ formatter: (v) => `${v} MB` }}
          />
        </Form.Item>
      </div>

      <Divider />

      <div className={styles.section}>
        <Text strong>实例配置</Text>
        <Row gutter={24} style={{ marginTop: 12 }}>
          <Col span={12}>
            <Form.Item label="实例数量" name="replicas" tooltip="同时运行的实例数量">
              <InputNumber min={1} max={10} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="自动扩缩容" tooltip="根据负载自动调整实例数量">
              <Switch
                checked={autoScaling}
                onChange={setAutoScaling}
                checkedChildren="启用"
                unCheckedChildren="禁用"
              />
            </Form.Item>
          </Col>
        </Row>
        
        {autoScaling && (
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item label="最小实例" name="minReplicas">
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="最大实例" name="maxReplicas">
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )}
      </div>

      <Divider />

      <div className={styles.section}>
        <Text strong>端口配置</Text>
        <Form.List name="ports">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }, index) => (
                <Row gutter={16} key={key} style={{ marginTop: 12 }}>
                  <Col span={8}>
                    <Form.Item
                      {...restField}
                      name={[name, 'port']}
                      label={index === 0 ? '端口号' : ''}
                      rules={[{ required: true }]}
                    >
                      <InputNumber min={1} max={65535} placeholder="8080" style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      {...restField}
                      name={[name, 'protocol']}
                      label={index === 0 ? '协议' : ''}
                      initialValue="tcp"
                    >
                      <Select>
                        <Option value="tcp">TCP</Option>
                        <Option value="udp">UDP</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  {fields.length > 1 && (
                    <Col span={4}>
                      <Form.Item label={index === 0 ? ' ' : ''}>
                        <Button danger onClick={() => remove(name)}>
                          删除
                        </Button>
                      </Form.Item>
                    </Col>
                  )}
                </Row>
              ))}
              <Button type="dashed" onClick={() => add({ port: 8080, protocol: 'tcp' })} style={{ marginTop: 8 }}>
                + 添加端口
              </Button>
            </>
          )}
        </Form.List>
      </div>
    </div>
  )

  // 环境变量步骤
  const renderEnvStep = () => (
    <div className={styles.stepContent}>
      <Title level={5}>环境变量</Title>
      <Text type="secondary">配置技能运行所需的环境变量</Text>
      
      <Alert
        type="info"
        showIcon
        message="安全提示"
        description="敏感信息（如密码、密钥）请标记为"敏感"，系统会自动加密存储"
        style={{ marginBottom: 16, marginTop: 16 }}
      />
      
      <Form.Item name="environmentVariables" noStyle>
        <EnvironmentVariables
          value={form.getFieldValue('environmentVariables') || []}
          onChange={(vars) => form.setFieldValue('environmentVariables', vars)}
        />
      </Form.Item>
    </div>
  )

  // 确认和部署步骤
  const renderConfirmStep = () => {
    const values = form.getFieldsValue()
    
    return (
      <div className={styles.stepContent}>
        <Title level={5}>确认部署</Title>
        <Text type="secondary">请确认以下部署配置</Text>

        <Card className={styles.confirmCard}>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Text type="secondary">技能名称</Text>
              <div><Text strong>{skillName}</Text></div>
            </Col>
            <Col span={12}>
              <Text type="secondary">版本</Text>
              <div><Text strong>v{values.version}</Text></div>
            </Col>
            <Col span={12}>
              <Text type="secondary">CPU</Text>
              <div><Text strong>{values.resources?.cpu || 1} 核</Text></div>
            </Col>
            <Col span={12}>
              <Text type="secondary">内存</Text>
              <div><Text strong>{values.resources?.memory || 512} MB</Text></div>
            </Col>
            <Col span={12}>
              <Text type="secondary">实例数量</Text>
              <div><Text strong>{values.replicas || 1}</Text></div>
            </Col>
            <Col span={12}>
              <Text type="secondary">自动扩缩容</Text>
              <div><Text strong>{autoScaling ? '已启用' : '未启用'}</Text></div>
            </Col>
            <Col span={24}>
              <Text type="secondary">端口</Text>
              <div>
                {values.ports?.map((p: PortConfig, i: number) => (
                  <Text key={i} strong style={{ marginRight: 8 }}>
                    {p.port}/{p.protocol.toUpperCase()}
                  </Text>
                ))}
              </div>
            </Col>
            <Col span={24}>
              <Text type="secondary">环境变量</Text>
              <div>
                <Text strong>{values.environmentVariables?.length || 0} 个变量</Text>
              </div>
            </Col>
          </Row>
        </Card>

        <Alert
          type="warning"
          showIcon
          message="部署确认"
          description="点击"开始部署"后将立即开始部署流程，这可能需要几分钟时间"
          style={{ marginTop: 16 }}
        />
      </div>
    )
  }

  // 部署进度步骤
  const renderDeployingStep = () => (
    <div className={styles.stepContent}>
      <div className={styles.deployingContainer}>
        {deployStatus === 'deploying' && (
          <>
            <LoadingOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <Title level={4} style={{ marginTop: 24 }}>正在部署...</Title>
            <Progress percent={deployProgress} status="active" style={{ width: '100%', maxWidth: 400 }} />
            <Text type="secondary">请稍候，部署可能需要几分钟时间</Text>
          </>
        )}
        
        {deployStatus === 'success' && (
          <>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <Title level={4} style={{ marginTop: 24 }}>部署成功！</Title>
            <Text>您的技能已成功部署并开始运行</Text>
            <Space style={{ marginTop: 24 }}>
              <Button type="primary">查看部署</Button>
              <Button>返回列表</Button>
            </Space>
          </>
        )}
        
        {deployStatus === 'error' && (
          <>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
            <Title level={4} style={{ marginTop: 24 }}>部署失败</Title>
            <Text type="danger">部署过程中出现错误，请检查配置后重试</Text>
            <Button type="primary" style={{ marginTop: 24 }} onClick={() => setCurrentStep(0)}>
              重新配置
            </Button>
          </>
        )}
      </div>
    </div>
  )

  // 步骤内容
  const steps = [
    { title: '选择版本', icon: <CloudServerOutlined />, content: renderVersionStep() },
    { title: '资源配置', icon: <SettingOutlined />, content: renderResourceStep() },
    { title: '环境变量', icon: <FileTextOutlined />, content: renderEnvStep() },
    { title: '确认部署', icon: <RocketOutlined />, content: renderConfirmStep() },
  ]

  // 下一步
  const handleNext = async () => {
    try {
      await form.validateFields()
      setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1))
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  // 上一步
  const handlePrev = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0))
  }

  // 开始部署
  const handleDeploy = async () => {
    try {
      const values = await form.validateFields()
      setDeployStatus('deploying')
      setDeployProgress(0)
      setCurrentStep(steps.length) // 进入部署进度步骤

      // 模拟部署进度
      const progressInterval = setInterval(() => {
        setDeployProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 10
        })
      }, 500)

      const config: DeploymentConfig = {
        skillId,
        skillName,
        version: values.version,
        environmentVariables: values.environmentVariables || [],
        ports: values.ports || [],
        resources: values.resources,
        domains: [],
        replicas: values.replicas || 1,
        autoScaling,
        minReplicas: values.minReplicas || 1,
        maxReplicas: values.maxReplicas || 5,
      }

      await onDeploy(config)
      
      clearInterval(progressInterval)
      setDeployProgress(100)
      
      setTimeout(() => {
        setDeployStatus('success')
      }, 500)
    } catch (error) {
      setDeployStatus('error')
      message.error('部署失败，请重试')
    }
  }

  return (
    <div className={styles.container}>
      <Steps current={currentStep} className={styles.steps}>
        {steps.map((step) => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      <Form form={form} layout="vertical" className={styles.form}>
        {currentStep < steps.length ? (
          steps[currentStep].content
        ) : (
          renderDeployingStep()
        )}
      </Form>

      {currentStep < steps.length && (
        <div className={styles.actions}>
          <Button
            disabled={currentStep === 0 || loading}
            onClick={handlePrev}
          >
            上一步
          </Button>
          {currentStep < steps.length - 1 ? (
            <Button type="primary" onClick={handleNext} loading={loading}>
              下一步
            </Button>
          ) : (
            <Button type="primary" onClick={handleDeploy} loading={loading}>
              <RocketOutlined /> 开始部署
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

export default DeploymentConfigPage
