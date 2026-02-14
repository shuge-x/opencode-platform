import React, { useState, useEffect } from 'react'
import { Upload, Button, Table, message } from 'antd'
import { UploadOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import client from '@/api/client'

export default function FilesPage() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)

  const loadFiles = async () => {
    setLoading(true)
    try {
      const response = await client.get('/files')
      setFiles(response.data)
    } catch (error: any) {
      message.error('加载文件失败')
    } finally {
      setLoading(false)
    }
  }

  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      await client.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      message.success('上传成功')
      loadFiles()
    } catch (error: any) {
      message.error('上传失败')
    }
  }

  const downloadFile = async (fileId: string) => {
    window.open(`/api/files/${fileId}`, '_blank')
  }

  const deleteFile = async (fileId: string) => {
    try {
      await client.delete(`/files/${fileId}`)
      message.success('删除成功')
      loadFiles()
    } catch (error: any) {
      message.error('删除失败')
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: '修改时间',
      dataIndex: 'modified_at',
      key: 'modified_at',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => downloadFile(record.file_id)}
          >
            下载
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteFile(record.file_id)}
          >
            删除
          </Button>
        </>
      ),
    },
  ]

  return (
    <div style={{ padding: '20px' }}>
      <h2>文件管理</h2>

      <Upload
        beforeUpload={(file) => {
          uploadFile(file)
          return false
        }}
        showUploadList={false}
      >
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>

      <Table
        columns={columns}
        dataSource={files}
        rowKey="file_id"
        loading={loading}
        style={{ marginTop: '20px' }}
      />
    </div>
  )
}
