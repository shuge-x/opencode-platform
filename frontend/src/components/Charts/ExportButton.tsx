import { Button, DatePicker, Dropdown, Modal, Progress, Space } from 'antd'
import { DownloadOutlined, FileTextOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useState } from 'react'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import { exportStatisticsData } from '@/api/statistics'

const { RangePicker } = DatePicker

interface ExportButtonProps {
  endpoint: string
  filename?: string
  onExportStart?: () => void
  onExportEnd?: () => void
}

export default function ExportButton({
  endpoint,
  filename,
  onExportStart,
  onExportEnd,
}: ExportButtonProps) {
  const [showDatePicker, setShowDatePicker] = useState(false)
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [exporting, setExporting] = useState(false)
  const [progress, setProgress] = useState(0)

  const downloadFile = (blob: Blob, format: 'csv' | 'json') => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename || 'statistics'}_${dayjs().format('YYYYMMDD_HHmmss')}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  const handleExport = async (format: 'csv' | 'json') => {
    setExporting(true)
    setProgress(0)
    onExportStart?.()

    try {
      // 模拟进度
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const params = dateRange
        ? {
            startDate: dateRange[0].format('YYYY-MM-DD'),
            endDate: dateRange[1].format('YYYY-MM-DD'),
          }
        : undefined

      const blob = await exportStatisticsData(endpoint, format, params)

      clearInterval(progressInterval)
      setProgress(100)

      downloadFile(blob, format)

      setTimeout(() => {
        setExporting(false)
        setProgress(0)
        setShowDatePicker(false)
        onExportEnd?.()
      }, 500)
    } catch (error) {
      console.error('Export failed:', error)
      setExporting(false)
      setProgress(0)
      onExportEnd?.()
    }
  }

  const items: MenuProps['items'] = [
    {
      key: 'csv',
      label: (
        <Space>
          <FileTextOutlined />
          导出 CSV
        </Space>
      ),
      onClick: () => handleExport('csv'),
    },
    {
      key: 'json',
      label: (
        <Space>
          <FileTextOutlined />
          导出 JSON
        </Space>
      ),
      onClick: () => handleExport('json'),
    },
    {
      type: 'divider',
    },
    {
      key: 'range',
      label: '选择日期范围...',
      onClick: () => setShowDatePicker(true),
    },
  ]

  return (
    <>
      <Dropdown menu={{ items }} disabled={exporting}>
        <Button type="primary" icon={<DownloadOutlined />} loading={exporting}>
          导出数据
        </Button>
      </Dropdown>

      <Modal
        title="选择日期范围"
        open={showDatePicker}
        onOk={() => {
          setShowDatePicker(false)
        }}
        onCancel={() => {
          setShowDatePicker(false)
          setDateRange(null)
        }}
        footer={[
          <Button key="cancel" onClick={() => setShowDatePicker(false)}>
            取消
          </Button>,
          <Button
            key="export"
            type="primary"
            onClick={() => {
              setShowDatePicker(false)
              handleExport('csv')
            }}
          >
            导出
          </Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <RangePicker
            style={{ width: '100%' }}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setDateRange([dates[0], dates[1]])
              } else {
                setDateRange(null)
              }
            }}
            value={dateRange}
          />
        </Space>
      </Modal>

      <Modal
        title="导出中"
        open={exporting}
        footer={null}
        closable={false}
        centered
      >
        <Progress percent={progress} status={progress === 100 ? 'success' : 'active'} />
      </Modal>
    </>
  )
}
