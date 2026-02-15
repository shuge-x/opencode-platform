import React, { useState, useCallback } from 'react'
import { Tabs, Drawer, Button, Space, message, Typography, Divider } from 'antd'
import {
  HistoryOutlined,
  DiffOutlined,
  CloseOutlined,
  RefreshOutlined
} from '@ant-design/icons'
import VersionList from './VersionList'
import DiffViewer from './DiffViewer'
import RevertDialog from './RevertDialog'
import { versionApi } from '@/api/version'
import type { VersionInfo, DiffViewMode } from '@/types/version'
import styles from './VersionHistoryPanel.module.css'

const { Text } = Typography

interface VersionHistoryPanelProps {
  skillId: number
  currentFileId?: number
  currentFileName?: string
  currentFileContent?: string
  open: boolean
  onClose: () => void
  onRevertSuccess?: () => void
}

type PanelTab = 'history' | 'diff'

export default function VersionHistoryPanel({
  skillId,
  currentFileId,
  currentFileName,
  currentFileContent,
  open,
  onClose,
  onRevertSuccess
}: VersionHistoryPanelProps) {
  const [activeTab, setActiveTab] = useState<PanelTab>('history')
  const [selectedVersion, setSelectedVersion] = useState<VersionInfo | null>(null)
  const [compareVersion, setCompareVersion] = useState<VersionInfo | null>(null)
  const [diffViewMode, setDiffViewMode] = useState<DiffViewMode>('side-by-side')
  const [revertDialogOpen, setRevertDialogOpen] = useState(false)
  const [revertTargetVersion, setRevertTargetVersion] = useState<VersionInfo | null>(null)
  const [oldContent, setOldContent] = useState('')
  const [newContent, setNewContent] = useState('')

  // 选择版本查看详情
  const handleSelectVersion = useCallback(async (version: VersionInfo) => {
    setSelectedVersion(version)
    
    // 如果有当前文件，加载对比
    if (currentFileId && currentFileContent !== undefined) {
      try {
        // 获取该版本下文件的内容
        const response = await versionApi.getFileAtVersion(skillId, version.id, currentFileId)
        setOldContent(response.content)
        setNewContent(currentFileContent)
        setActiveTab('diff')
      } catch (error) {
        console.error('Failed to load version content:', error)
        // 如果获取失败，可能是该版本中文件不存在
        setOldContent('')
        setNewContent(currentFileContent)
        setActiveTab('diff')
      }
    }
  }, [skillId, currentFileId, currentFileContent])

  // 对比版本
  const handleCompareVersion = useCallback(async (version: VersionInfo) => {
    setCompareVersion(version)
    
    if (currentFileId && currentFileContent !== undefined) {
      try {
        const response = await versionApi.getFileAtVersion(skillId, version.id, currentFileId)
        setOldContent(response.content)
        setNewContent(currentFileContent)
        setActiveTab('diff')
      } catch (error) {
        setOldContent('')
        setNewContent(currentFileContent)
        setActiveTab('diff')
      }
    }
  }, [skillId, currentFileId, currentFileContent])

  // 回退版本
  const handleRevertVersion = useCallback((version: VersionInfo) => {
    setRevertTargetVersion(version)
    setRevertDialogOpen(true)
  }, [])

  // 确认回退
  const handleConfirmRevert = useCallback(async (options: {
    message: string
    createNewVersion: boolean
  }): Promise<boolean> => {
    if (!revertTargetVersion) return false

    try {
      const result = await versionApi.revert(skillId, revertTargetVersion.id, options)
      
      if (result.success) {
        message.success(result.message)
        onRevertSuccess?.()
        return true
      } else {
        message.error(result.message || '回退失败')
        return false
      }
    } catch (error: any) {
      message.error(error.message || '回退失败')
      return false
    }
  }, [skillId, revertTargetVersion, onRevertSuccess])

  // 关闭回退对话框
  const handleCloseRevertDialog = useCallback(() => {
    setRevertDialogOpen(false)
    setRevertTargetVersion(null)
  }, [])

  // 刷新
  const handleRefresh = useCallback(() => {
    // 刷新操作由 VersionList 内部处理
    // 这里可以重置状态
    setSelectedVersion(null)
    setCompareVersion(null)
  }, [])

  // Tab 配置
  const tabItems = [
    {
      key: 'history',
      label: (
        <span>
          <HistoryOutlined />
          版本历史
        </span>
      ),
      children: (
        <VersionList
          skillId={skillId}
          currentFileId={currentFileId}
          onSelectVersion={handleSelectVersion}
          onCompareVersion={handleCompareVersion}
          onRevertVersion={handleRevertVersion}
        />
      )
    },
    {
      key: 'diff',
      label: (
        <span>
          <DiffOutlined />
          版本对比
        </span>
      ),
      children: (
        <DiffViewer
          skillId={skillId}
          newVersionId={selectedVersion?.id || 0}
          fileId={currentFileId}
          oldContent={oldContent}
          newContent={newContent}
          filename={currentFileName}
          viewMode={diffViewMode}
          onViewModeChange={setDiffViewMode}
        />
      )
    }
  ]

  return (
    <>
      <Drawer
        title={
          <div className={styles.drawerTitle}>
            <HistoryOutlined />
            <span>版本管理</span>
            {currentFileName && (
              <Text type="secondary" className={styles.currentFile}>
                · {currentFileName}
              </Text>
            )}
          </div>
        }
        placement="right"
        width={640}
        open={open}
        onClose={onClose}
        extra={
          <Space>
            <Button
              type="text"
              icon={<RefreshOutlined />}
              onClick={handleRefresh}
              title="刷新"
            />
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={onClose}
              title="关闭"
            />
          </Space>
        }
        className={styles.versionDrawer}
        styles={{
          body: { padding: 0 }
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as PanelTab)}
          items={tabItems}
          className={styles.panelTabs}
          size="small"
        />
      </Drawer>

      <RevertDialog
        open={revertDialogOpen}
        version={revertTargetVersion}
        skillId={skillId}
        onConfirm={handleConfirmRevert}
        onCancel={handleCloseRevertDialog}
      />
    </>
  )
}
