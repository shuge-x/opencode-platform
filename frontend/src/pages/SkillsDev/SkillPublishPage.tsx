import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Tabs, Card, Button, message, Result, Spin } from 'antd'
import {
  EditOutlined,
  UploadOutlined,
  HistoryOutlined,
  SettingOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { skillsDevApi, Skill } from '@/api/skills-dev'
import { skillPublishApi } from '@/api/skillPublish'
import PublishForm from './components/PublishForm'
import PackageUpload from './components/PackageUpload'
import VersionManager from './components/VersionManager'
import PermissionSettings from './components/PermissionSettings'
import styles from './SkillPublishPage.module.css'

export default function SkillPublishPage() {
  const { skillId } = useParams<{ skillId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('publish')

  // 获取技能详情
  const { data: skill, isLoading, error } = useQuery({
    queryKey: ['skill', skillId],
    queryFn: () => skillsDevApi.get(Number(skillId)),
    enabled: !!skillId
  })

  // 获取版本列表
  const { data: versions } = useQuery({
    queryKey: ['skill-versions', skillId],
    queryFn: () => skillPublishApi.listVersions(Number(skillId)),
    enabled: !!skillId
  })

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spin size="large" tip="加载技能信息..." />
      </div>
    )
  }

  if (error || !skill) {
    return (
      <div className={styles.errorContainer}>
        <Result
          status="error"
          title="加载失败"
          subTitle="无法加载技能信息，请检查技能是否存在"
          extra={[
            <Button type="primary" key="back" onClick={() => navigate(-1)}>
              返回
            </Button>
          ]}
        />
      </div>
    )
  }

  const tabItems = [
    {
      key: 'publish',
      label: (
        <span>
          <EditOutlined />
          发布技能
        </span>
      ),
      children: (
        <PublishForm 
          skill={skill} 
          onSuccess={() => {
            message.success('技能发布成功')
            setActiveTab('version')
          }} 
        />
      )
    },
    {
      key: 'upload',
      label: (
        <span>
          <UploadOutlined />
          打包上传
        </span>
      ),
      children: <PackageUpload skill={skill} versions={versions || []} />
    },
    {
      key: 'version',
      label: (
        <span>
          <HistoryOutlined />
          版本管理
        </span>
      ),
      children: <VersionManager skill={skill} />
    },
    {
      key: 'permission',
      label: (
        <span>
          <SettingOutlined />
          权限设置
        </span>
      ),
      children: <PermissionSettings skill={skill} />
    }
  ]

  return (
    <div className={styles.publishPage}>
      <div className={styles.pageHeader}>
        <Button 
          type="text" 
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
        >
          返回
        </Button>
        <h2 className={styles.pageTitle}>
          发布技能: {skill.name}
          {skill.version && (
            <span className={styles.versionTag}>v{skill.version}</span>
          )}
        </h2>
      </div>

      <Card className={styles.contentCard}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
        />
      </Card>
    </div>
  )
}
