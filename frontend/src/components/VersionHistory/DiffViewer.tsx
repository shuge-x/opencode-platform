import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Spin, Empty, Segmented, Select, Typography, Space, Tag, Tooltip } from 'antd'
import {
  PlusOutlined,
  MinusOutlined,
  EditOutlined,
  SwapOutlined
} from '@ant-design/icons'
import Editor, { Monaco, DiffEditor } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import type { DiffViewMode } from '@/types/version'
import styles from './DiffViewer.module.css'

const { Text } = Typography

interface DiffViewerProps {
  skillId: number
  oldVersionId?: number
  newVersionId: number
  fileId?: number
  oldContent?: string
  newContent?: string
  filename?: string
  language?: string
  viewMode?: DiffViewMode
  onViewModeChange?: (mode: DiffViewMode) => void
}

interface DiffStats {
  additions: number
  deletions: number
  modifications: number
}

export default function DiffViewer({
  skillId,
  oldVersionId,
  newVersionId,
  fileId,
  oldContent: providedOldContent,
  newContent: providedNewContent,
  filename,
  language = 'python',
  viewMode = 'side-by-side',
  onViewModeChange
}: DiffViewerProps) {
  const [loading, setLoading] = useState(false)
  const [oldContent, setOldContent] = useState(providedOldContent || '')
  const [newContent, setNewContent] = useState(providedNewContent || '')
  const [internalViewMode, setInternalViewMode] = useState<DiffViewMode>(viewMode)
  const [diffEditorRef, setDiffEditorRef] = useState<editor.IStandaloneDiffEditor | null>(null)

  // 更新内容
  useEffect(() => {
    if (providedOldContent !== undefined) {
      setOldContent(providedOldContent)
    }
    if (providedNewContent !== undefined) {
      setNewContent(providedNewContent)
    }
  }, [providedOldContent, providedNewContent])

  // 计算差异统计
  const diffStats = useMemo((): DiffStats => {
    const oldLines = oldContent.split('\n')
    const newLines = newContent.split('\n')
    
    // 简单统计，实际应用中可以使用更精确的 diff 算法
    let additions = 0
    let deletions = 0

    if (oldContent === newContent) {
      return { additions: 0, deletions: 0, modifications: 0 }
    }

    // 使用 Set 来统计不同行
    const oldSet = new Set(oldLines)
    const newSet = new Set(newLines)

    additions = newLines.filter(line => !oldSet.has(line)).length
    deletions = oldLines.filter(line => !newSet.has(line)).length

    return { additions, deletions, modifications: 0 }
  }, [oldContent, newContent])

  // 处理编辑器挂载
  const handleDiffEditorMount = (editor: editor.IStandaloneDiffEditor, monaco: Monaco) => {
    setDiffEditorRef(editor)
  }

  // 处理视图模式变更
  const handleViewModeChange = (value: string | number) => {
    const mode = value as DiffViewMode
    setInternalViewMode(mode)
    onViewModeChange?.(mode)
  }

  // 获取语言
  const getLanguage = (filename?: string): string => {
    if (!filename) return language
    const ext = filename.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      tsx: 'typescript',
      jsx: 'javascript',
      json: 'json',
      yaml: 'yaml',
      yml: 'yaml',
      md: 'markdown',
      css: 'css',
      scss: 'scss',
      html: 'html'
    }
    return langMap[ext || ''] || language
  }

  if (!oldContent && !newContent) {
    return (
      <div className={styles.diffViewer}>
        <Empty
          description="选择版本以查看差异"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          className={styles.empty}
        />
      </div>
    )
  }

  return (
    <div className={styles.diffViewer}>
      {/* 工具栏 */}
      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          <Space>
            {filename && (
              <Text className={styles.filename}>{filename}</Text>
            )}
            <Tag color="green">
              <PlusOutlined /> +{diffStats.additions}
            </Tag>
            <Tag color="red">
              <MinusOutlined /> -{diffStats.deletions}
            </Tag>
          </Space>
        </div>
        <div className={styles.toolbarRight}>
          <Segmented
            value={internalViewMode}
            onChange={handleViewModeChange}
            options={[
              {
                value: 'side-by-side',
                label: (
                  <Tooltip title="并排对比">
                    <SwapOutlined />
                  </Tooltip>
                )
              },
              {
                value: 'inline',
                label: (
                  <Tooltip title="内联对比">
                    <EditOutlined />
                  </Tooltip>
                )
              }
            ]}
            className={styles.viewModeSegment}
          />
        </div>
      </div>

      {/* Diff 编辑器 */}
      <div className={styles.editorContainer}>
        <Spin spinning={loading}>
          <DiffEditor
            height="100%"
            language={getLanguage(filename)}
            original={oldContent}
            modified={newContent}
            onMount={handleDiffEditorMount}
            theme="vs-dark"
            options={{
              fontSize: 13,
              fontFamily: "'Fira Code', 'Consolas', monospace",
              readOnly: true,
              renderSideBySide: internalViewMode === 'side-by-side',
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              automaticLayout: true,
              diffWordWrap: 'on',
              renderOverviewRuler: true,
              originalEditable: false,
              // 差异高亮
              diffAlgorithm: 'advanced',
              renderMarginRevertIcon: false,
              // 隐藏行号差异指示器
              glyphMargin: false,
              folding: false,
              lineNumbers: 'on',
              // 差异装饰
              renderIndicators: true,
              enableSplitViewResizing: true
            }}
          />
        </Spin>
      </div>
    </div>
  )
}
