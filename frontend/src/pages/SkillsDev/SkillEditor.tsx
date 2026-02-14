import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Layout, Tree, Button, Modal, Input, Select, message, Dropdown, Empty } from 'antd'
import {
  FileOutlined,
  FolderOutlined,
  FileAddOutlined,
  FolderAddOutlined,
  DeleteOutlined,
  EditOutlined,
  SaveOutlined,
  PlayCircleOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import Editor from '@monaco-editor/react'
import { skillsDevApi, Skill, SkillFile, SkillTemplate } from '@/api/skills-dev'
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
          <>
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
                <Button
                  icon={<PlayCircleOutlined />}
                  onClick={() => message.info('测试功能开发中')}
                >
                  测试
                </Button>
              </div>
            </div>

            <Editor
              height="calc(100vh - 200px)"
              language={getLanguage(currentFile.file_type)}
              value={fileContent}
              onChange={(value) => setFileContent(value || '')}
              theme="vs-dark"
              options={{
                fontSize: 14,
                fontFamily: "'Fira Code', 'Consolas', monospace",
                minimap: { enabled: true },
                automaticLayout: true,
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                tabSize: 2
              }}
            />
          </>
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
