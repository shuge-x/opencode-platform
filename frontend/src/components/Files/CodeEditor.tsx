import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { Button, Space, Select, message } from 'antd'
import { SaveOutlined, FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons'
import { FileItem } from '@/stores/fileStore'

interface CodeEditorProps {
  file: FileItem
  onSave: (content: string) => void
}

const languageMap: Record<string, string> = {
  'js': 'javascript',
  'jsx': 'javascript',
  'ts': 'typescript',
  'tsx': 'typescript',
  'py': 'python',
  'rb': 'ruby',
  'java': 'java',
  'c': 'c',
  'cpp': 'cpp',
  'go': 'go',
  'rs': 'rust',
  'php': 'php',
  'html': 'html',
  'css': 'css',
  'scss': 'scss',
  'less': 'less',
  'json': 'json',
  'xml': 'xml',
  'yaml': 'yaml',
  'yml': 'yaml',
  'md': 'markdown',
  'sql': 'sql',
  'sh': 'shell',
  'bash': 'shell'
}

export default function CodeEditor({ file, onSave }: CodeEditorProps) {
  const [content, setContent] = useState(file.content || '')
  const [language, setLanguage] = useState(file.language || 'plaintext')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    setContent(file.content || '')
    const ext = file.name.split('.').pop() || ''
    const detectedLang = languageMap[ext] || file.language || 'plaintext'
    setLanguage(detectedLang)
    setHasChanges(false)
  }, [file])

  const handleSave = () => {
    onSave(content)
    setHasChanges(false)
    message.success('文件已保存')
  }

  const handleEditorChange = (value: string | undefined) => {
    setContent(value || '')
    setHasChanges(value !== file.content)
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    }
  }

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [content])

  const editorHeight = isFullscreen ? 'calc(100vh - 200px)' : '500px'

  return (
    <div style={{ height: editorHeight }}>
      {/* Toolbar */}
      <div style={{
        marginBottom: 12,
        padding: '8px 12px',
        background: '#f5f5f5',
        borderRadius: '4px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Space>
          <Select
            value={language}
            onChange={setLanguage}
            style={{ width: 150 }}
            options={[
              { value: 'javascript', label: 'JavaScript' },
              { value: 'typescript', label: 'TypeScript' },
              { value: 'python', label: 'Python' },
              { value: 'java', label: 'Java' },
              { value: 'cpp', label: 'C++' },
              { value: 'go', label: 'Go' },
              { value: 'rust', label: 'Rust' },
              { value: 'html', label: 'HTML' },
              { value: 'css', label: 'CSS' },
              { value: 'json', label: 'JSON' },
              { value: 'yaml', label: 'YAML' },
              { value: 'markdown', label: 'Markdown' },
              { value: 'sql', label: 'SQL' },
              { value: 'shell', label: 'Shell' },
              { value: 'plaintext', label: 'Plain Text' }
            ]}
          />
          
          {hasChanges && (
            <span style={{ color: '#ff4d4f', fontSize: 12 }}>
              * 未保存的更改
            </span>
          )}
        </Space>

        <Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            disabled={!hasChanges}
          >
            保存 (Ctrl+S)
          </Button>
          <Button
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            {isFullscreen ? '退出全屏' : '全屏'}
          </Button>
        </Space>
      </div>

      {/* Monaco Editor */}
      <Editor
        height={isFullscreen ? 'calc(100% - 60px)' : '450px'}
        language={language}
        value={content}
        onChange={handleEditorChange}
        theme="vs-dark"
        options={{
          fontSize: 14,
          fontFamily: "'Fira Code', 'Consolas', monospace",
          minimap: { enabled: true },
          automaticLayout: true,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          tabSize: 2,
          insertSpaces: true,
          formatOnPaste: true,
          formatOnType: true,
          suggestOnTriggerCharacters: true,
          quickSuggestions: true,
          snippetSuggestions: 'top',
          renderLineHighlight: 'all',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          padding: { top: 10 }
        }}
        loading={
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%'
          }}>
            加载编辑器...
          </div>
        }
      />
    </div>
  )
}
