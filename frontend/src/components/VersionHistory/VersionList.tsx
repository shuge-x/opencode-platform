import React, { useState, useEffect, useCallback } from 'react'
import {
  List,
  Input,
  Select,
  Tag,
  Empty,
  Spin,
  Button,
  Space,
  Tooltip,
  Avatar,
  Typography
} from 'antd'
import {
  SearchOutlined,
  ClockCircleOutlined,
  UserOutlined,
  RollbackOutlined,
  DiffOutlined,
  TagOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { versionApi } from '@/api/version'
import type { VersionInfo, VersionSearchParams, VersionStatus } from '@/types/version'
import styles from './VersionList.module.css'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text } = Typography

interface VersionListProps {
  skillId: number
  currentFileId?: number
  onSelectVersion: (version: VersionInfo) => void
  onCompareVersion: (version: VersionInfo) => void
  onRevertVersion: (version: VersionInfo) => void
}

export default function VersionList({
  skillId,
  currentFileId,
  onSelectVersion,
  onCompareVersion,
  onRevertVersion
}: VersionListProps) {
  const [versions, setVersions] = useState<VersionInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<VersionStatus | undefined>()
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // 加载版本列表
  const loadVersions = useCallback(async () => {
    setLoading(true)
    try {
      const params: VersionSearchParams = {
        search: searchText || undefined,
        status: statusFilter,
        page: pagination.current,
        page_size: pagination.pageSize
      }

      const response = await versionApi.list(skillId, params)
      setVersions(response.items)
      setPagination(prev => ({
        ...prev,
        total: response.total
      }))
    } catch (error) {
      console.error('Failed to load versions:', error)
    } finally {
      setLoading(false)
    }
  }, [skillId, searchText, statusFilter, pagination.current, pagination.pageSize])

  useEffect(() => {
    loadVersions()
  }, [loadVersions])

  // 获取变更类型颜色
  const getChangeTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      added: 'green',
      modified: 'blue',
      deleted: 'red',
      renamed: 'orange'
    }
    return colors[type] || 'default'
  }

  // 获取状态标签颜色
  const getStatusColor = (status: VersionStatus) => {
    const colors: Record<string, string> = {
      active: 'green',
      archived: 'default',
      rollback: 'orange'
    }
    return colors[status] || 'default'
  }

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = dayjs(dateStr)
    const now = dayjs()
    const diffDays = now.diff(date, 'day')

    if (diffDays < 7) {
      return date.fromNow()
    }
    return date.format('YYYY-MM-DD HH:mm')
  }

  // 获取文件变更统计
  const getFileChangeStats = (version: VersionInfo) => {
    const stats = { added: 0, modified: 0, deleted: 0 }
    version.file_changes.forEach(change => {
      if (change.change_type === 'added') stats.added++
      else if (change.change_type === 'modified') stats.modified++
      else if (change.change_type === 'deleted') stats.deleted++
    })
    return stats
  }

  return (
    <div className={styles.versionList}>
      {/* 搜索和筛选 */}
      <div className={styles.searchBar}>
        <Input
          placeholder="搜索版本..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
          className={styles.searchInput}
        />
        <Select
          placeholder="状态筛选"
          value={statusFilter}
          onChange={setStatusFilter}
          allowClear
          className={styles.statusSelect}
          options={[
            { value: 'active', label: '活跃' },
            { value: 'archived', label: '已归档' },
            { value: 'rollback', label: '回退版本' }
          ]}
        />
      </div>

      {/* 版本列表 */}
      <Spin spinning={loading}>
        {versions.length > 0 ? (
          <List
            className={styles.list}
            dataSource={versions}
            renderItem={(version) => {
              const stats = getFileChangeStats(version)
              const isCurrentFileAffected = currentFileId && 
                version.file_changes.some(fc => fc.file_id === currentFileId)

              return (
                <List.Item
                  className={styles.listItem}
                  onClick={() => onSelectVersion(version)}
                >
                  <div className={styles.itemContent}>
                    {/* 版本信息 */}
                    <div className={styles.versionHeader}>
                      <div className={styles.versionMeta}>
                        <ClockCircleOutlined className={styles.timeIcon} />
                        <Text type="secondary" className={styles.time}>
                          {formatTime(version.created_at)}
                        </Text>
                        <Tag color={getStatusColor(version.status)}>
                          {version.status === 'active' ? '活跃' : 
                           version.status === 'archived' ? '已归档' : '回退版本'}
                        </Tag>
                      </div>
                      <div className={styles.author}>
                        <Avatar
                          size="small"
                          src={version.author.avatar_url}
                          icon={<UserOutlined />}
                        />
                        <Text className={styles.authorName}>
                          {version.author.username}
                        </Text>
                      </div>
                    </div>

                    {/* 提交信息 */}
                    <div className={styles.commitMessage}>
                      <Text strong>{version.commit_message}</Text>
                      <Text type="secondary" className={styles.commitHash}>
                        {version.commit_hash.substring(0, 7)}
                      </Text>
                    </div>

                    {/* 文件变更 */}
                    <div className={styles.fileChanges}>
                      {stats.added > 0 && (
                        <Tag color="green">+{stats.added} 新增</Tag>
                      )}
                      {stats.modified > 0 && (
                        <Tag color="blue">~{stats.modified} 修改</Tag>
                      )}
                      {stats.deleted > 0 && (
                        <Tag color="red">-{stats.deleted} 删除</Tag>
                      )}
                      {isCurrentFileAffected && (
                        <Tag color="purple">当前文件</Tag>
                      )}
                    </div>

                    {/* 标签 */}
                    {version.tags && version.tags.length > 0 && (
                      <div className={styles.tags}>
                        <TagOutlined className={styles.tagIcon} />
                        {version.tags.map(tag => (
                          <Tag key={tag}>{tag}</Tag>
                        ))}
                      </div>
                    )}

                    {/* 操作按钮 */}
                    <div className={styles.actions}>
                      <Space>
                        <Tooltip title="查看差异">
                          <Button
                            type="text"
                            size="small"
                            icon={<DiffOutlined />}
                            onClick={(e) => {
                              e.stopPropagation()
                              onCompareVersion(version)
                            }}
                          />
                        </Tooltip>
                        <Tooltip title="回退到此版本">
                          <Button
                            type="text"
                            size="small"
                            icon={<RollbackOutlined />}
                            onClick={(e) => {
                              e.stopPropagation()
                              onRevertVersion(version)
                            }}
                          />
                        </Tooltip>
                      </Space>
                    </div>
                  </div>
                </List.Item>
              )
            }}
            pagination={
              pagination.total > pagination.pageSize
                ? {
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    onChange: (page) => {
                      setPagination(prev => ({ ...prev, current: page }))
                    },
                    size: 'small',
                    simple: true
                  }
                : false
            }
          />
        ) : (
          <Empty
            description="暂无版本历史"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className={styles.empty}
          />
        )}
      </Spin>
    </div>
  )
}
