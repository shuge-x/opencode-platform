import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Layout, Tree, Button, Modal, Input, Select, message, Dropdown, Empty, Drawer, Tooltip } from 'antd'
import {
  FileOutlined,
  FolderOutlined,
  FileAddOutlined,
  FolderAddOutlined,
  DeleteOutlined,
  EditOutlined,
  SaveOutlined,
  PlayCircleOutlined,
  BugOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HistoryOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import Editor, { Monaco } from '@monaco-editor/react'
import { skillsDevApi, Skill, SkillFile, SkillTemplate } from '@/api/skills-dev'
import { DebugPanel } from '@/components/Debug'
import { VersionHistoryPanel } from '@/components/VersionHistory'
import type { editor } from 'monaco-editor'
import styles from './SkillEditor.module.css'

const { Sider, Content } = Layout

export default function SkillEditor() {
  const { skillId } = useParams<{ skillId: string }>()
  const [skill, setSkill] = useState<Skill | null>(null)
  const [files, setFiles] = useState<SkillFile[]>([])
  const [currentFile, setCurrentFile] = useState<SkillFile | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showNewFileModal, setShowNewFileModal] = useState(false)
  const [newFileName, setNewFileName] = useState('')
  const [debugPanelVisible, setDebugPanelVisible] = useState(true)
  const [debugPanelWidth, setDebugPanelWidth] = useState(400)
  const [debugMode, setDebugMode] = useState(false)
  const [versionPanelVisible, setVersionPanelVisible] = useState(false)
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
  const monacoRef = useRef<Monaco | null>(null)

  // 加载技能和文件
  useEffect(() => {
    if (skillId) {
      loadSkill()
    }
  }, [skillId])

  const loadSkill = async () => {
    setLoading(true)
    try {
      const skillData = await skillsDevApi.get(Number(skillId))
      setSkill(skillData)
      setFiles(skillData.files || [])

      // 默认打开 main.py
      const mainFile = skillData.files?.find(f => f.filename === 'main.py')
      if (mainFile) {
        selectFile(mainFile)
      }
    } catch (error) {
      message.error('加载技能失败')
    } finally {
      setLoading(false)
    }
  }

  const selectFile = (file: SkillFile) => {
    setCurrentFile(file)
    setFileContent(file.content || '')
  }

  const saveFile = async () => {
    if (!currentFile || !skillId) return

    setSaving(true)
    try {
      await skillsDevApi.updateFile(Number(skillId), currentFile.id, {
        content: fileContent
      })
      message.success('保存成功')

      // 更新本地文件列表
      setFiles(files.map(f =>
        f.id === currentFile.id ? { ...f, content: fileContent } : f
      ))
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const createNewFile = async () => {
    if (!newFileName || !skillId) return

    try {
      const fileType = getFileType(newFileName)
      const file = await skillsDevApi.createFile(Number(skillId), {
        filename: newFileName,
        file_path: newFileName,
        file_type: fileType,
        content: ''
      })

      setFiles([...files, file])
      setShowNewFileModal(false)
      setNewFileName('')
      message.success('文件创建成功')

      // 自动打开新文件
      selectFile(file)
    } catch (error) {
      message.error('创建文件失败')
    }
  }

  const deleteFile = async (file: SkillFile) => {
    if (!skillId) return

    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文件 "${file.filename}" 吗？`,
      onOk: async () => {
        try {
          await skillsDevApi.deleteFile(Number(skillId), file.id)
          setFiles(files.filter(f => f.id !== file.id))

          if (currentFile?.id === file.id) {
            setCurrentFile(null)
            setFileContent('')
          }

          message.success('删除成功')
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const getFileType = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase()
    const typeMap: { [key: string]: string } = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'md': 'markdown',
      'json': 'config',
      'yaml': 'config',
      'yml': 'config'
    }
    return typeMap[ext || ''] || 'text'
  }

  const getLanguage = (fileType: string): string => {
    const langMap: { [key: string]: string } = {
      'python': 'python',
      'javascript': 'javascript',
      'typescript': 'typescript',
      'markdown': 'markdown',
      'config': 'json'
    }
    return langMap[fileType] || 'plaintext'
  }

  // 编辑器挂载回调
  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editor
    monacoRef.current = monaco
  }

  // 跳转到代码位置
  const goToCodeLocation = useCallback((file: string, line: number, column?: number) => {
    // 如果文件名与当前文件匹配
    if (currentFile?.filename === file && editorRef.current) {
      editorRef.current.revealLineInCenter(line)
      editorRef.current.setPosition({
        lineNumber: line,
        column: column || 1
      })
      editorRef.current.focus()
    } else {
      // 查找并打开对应文件
      const targetFile = files.find(f => f.filename === file || f.file_path === file)
      if (targetFile) {
        selectFile(targetFile)
        // 延迟跳转，等待编辑器加载
        setTimeout(() => {
          if (editorRef.current) {
            editorRef.current.revealLineInCenter(line)
            editorRef.current.setPosition({
              lineNumber: line,
              column: column || 1
            })
            editorRef.current.focus()
          }
        }, 100)
      }
    }
  }, [currentFile, files])

  // 切换调试模式
  const toggleDebugMode = () => {
    setDebugMode(!debugMode)
    setDebugPanelVisible(!debugMode)
  }

  // 版本回退成功后刷新文件
  const handleRevertSuccess = async () => {
    // 重新加载技能文件
    await loadSkill()
    message.success('文件已从历史版本恢复')
  }

  // 文件树数据
  const treeData = files.map(file => ({
    key: file.id.toString(),
    title: file.filename,
    icon: <FileOutlined />,
    isLeaf: true
  }))

  // 右键菜单
  const contextMenuItems: MenuProps['items'] = [
    {
      key: 'rename',
      icon: <EditOutlined />,
      label: '重命名'
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true
    }
  ]

  return (
    <Layout className={styles.editorLayout}>
      <Sider width={250} className={styles.fileTreeSider}>
        <div className={styles.siderHeader}>
          <h3>{skill?.name || '技能编辑器'}</h3>
          <Button
            type="text"
            icon={<FileAddOutlined />}
            onClick={() => setShowNewFileModal(true)}
            title="新建文件"
          />
        </div>

        <Tree
          showIcon
          selectedKeys={currentFile ? [currentFile.id.toString()] : []}
          treeData={treeData}
          onSelect={(keys) => {
            const fileId = keys[0] as string
            const file = files.find(f => f.id.toString() === fileId)
            if (file) selectFile(file)
          }}
        />

        {files.length === 0 && (
          <Empty
            description="暂无文件"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Sider>

      <Content className={styles.editorContent}>
        {currentFile ? (
          <div className={styles.editorContainer}>
            <div className={styles.editorToolbar}>
              <div className={styles.fileInfo}>
                <FileOutlined /> {currentFile.filename}
              </div>
              <div className={styles.toolbarActions}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={saving}
                  onClick={saveFile}
                >
                  保存
                </Button>
                <Tooltip title="版本历史">
                  <Button
                    icon={<HistoryOutlined />}
                    onClick={() => setVersionPanelVisible(true)}
                  >
                    版本历史
                  </Button>
                </Tooltip>
                <Tooltip title={debugMode ? '隐藏调试面板' : '显示调试面板'}>
                  <Button
                    icon={<BugOutlined />}
                    type={debugMode ? 'primary' : 'default'}
                    onClick={toggleDebugMode}
                  >
                    调试
                  </Button>
                </Tooltip>
                <Button
                  icon={<PlayCircleOutlined />}
                  onClick={() => {
                    setDebugMode(true)
                    setDebugPanelVisible(true)
                  }}
                >
                  运行
                </Button>
              </div>
            </div>

            <div className={styles.editorBody}>
              <div className={styles.codeEditor}>
                <Editor
                  height="100%"
                  language={getLanguage(currentFile.file_type)}
                  value={fileContent}
                  onChange={(value) => setFileContent(value || '')}
                  onMount={handleEditorDidMount}
                  theme="vs-dark"
                  options={{
                    fontSize: 14,
                    fontFamily: "'Fira Code', 'Consolas', monospace",
                    minimap: { enabled: true },
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    tabSize: 2,
                    glyphMargin: true, // 用于断点标记
                    folding: true,
                    lineNumbers: 'on',
                    renderLineHighlight: 'all'
                  }}
                />
              </div>

              {debugPanelVisible && debugMode && (
                <div
                  className={styles.debugPanel}
                  style={{ width: debugPanelWidth }}
                >
                  <div
                    className={styles.resizeHandle}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      const startX = e.clientX
                      const startWidth = debugPanelWidth

                      const handleMouseMove = (e: MouseEvent) => {
                        const newWidth = startWidth - (e.clientX - startX)
                        setDebugPanelWidth(Math.max(300, Math.min(800, newWidth)))
                      }

                      const handleMouseUp = () => {
                        document.removeEventListener('mousemove', handleMouseMove)
                        document.removeEventListener('mouseup', handleMouseUp)
                      }

                      document.addEventListener('mousemove', handleMouseMove)
                      document.addEventListener('mouseup', handleMouseUp)
                    }}
                  />
                  <div className={styles.debugPanelHeader}>
                    <span><BugOutlined /> 调试控制台</span>
                    <Button
                      type="text"
                      size="small"
                      icon={debugPanelVisible ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />}
                      onClick={() => setDebugPanelVisible(false)}
                    />
                  </div>
                  <div className={styles.debugPanelContent}>
                    <DebugPanel
                      skillId={Number(skillId)}
                      onCodeLocationClick={goToCodeLocation}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className={styles.emptyEditor}>
            <Empty description="请选择文件" />
          </div>
        )}
      </Content>

      <Modal
        title="新建文件"
        open={showNewFileModal}
        onOk={createNewFile}
        onCancel={() => setShowNewFileModal(false)}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="文件名（例如：main.py）"
          value={newFileName}
          onChange={(e) => setNewFileName(e.target.value)}
          onPressEnter={createNewFile}
        />
      </Modal>
    </Layout>
  )
}
