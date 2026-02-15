import { useState } from 'react'
import { Table, Tag, Button, Space, Modal, Typography } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { ErrorRecord, ErrorDetail } from '@/types/monitoring'
import { useErrorDetail } from '@/hooks/useMonitoring'
import dayjs from 'dayjs'

const { Text, Paragraph } = Typography

interface ErrorListProps {
  data?: ErrorRecord[]
  total?: number
  loading?: boolean
  onPageChange?: (page: number, pageSize: number) => void
  onSearch?: (filters: Record<string, any>) => void
}

export default function ErrorList({
  data,
  total = 0,
  loading = false,
  onPageChange,
}: ErrorListProps) {
  const [selectedErrorId, setSelectedErrorId] = useState<string | null>(null)
  const [modalVisible, setModalVisible] = useState(false)

  const { data: errorDetail, isLoading: detailLoading } = useErrorDetail(selectedErrorId || '')

  const handleViewDetail = (errorId: string) => {
    setSelectedErrorId(errorId)
    setModalVisible(true)
  }

  const columns: ColumnsType<ErrorRecord> = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true,
    },
    {
      title: '技能名称',
      dataIndex: 'skillName',
      key: 'skillName',
    },
    {
      title: '错误类型',
      dataIndex: 'errorType',
      key: 'errorType',
      render: (value: string) => <Tag color="red">{value}</Tag>,
    },
    {
      title: '错误消息',
      dataIndex: 'errorMessage',
      key: 'errorMessage',
      ellipsis: true,
      render: (value: string) => (
        <Text ellipsis title={value}>
          {value}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.id)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{
          total,
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: onPageChange,
        }}
      />

      <Modal
        title="错误详情"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
        loading={detailLoading}
      >
        {errorDetail && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>技能名称：</Text>
              <Text>{errorDetail.skillName}</Text>
            </div>
            <div>
              <Text strong>错误类型：</Text>
              <Tag color="red">{errorDetail.errorType}</Tag>
            </div>
            <div>
              <Text strong>错误消息：</Text>
              <br />
              <Text type="danger">{errorDetail.errorMessage}</Text>
            </div>
            <div>
              <Text strong>发生时间：</Text>
              <Text>{dayjs(errorDetail.timestamp).format('YYYY-MM-DD HH:mm:ss')}</Text>
            </div>
            {errorDetail.input && (
              <div>
                <Text strong>输入参数：</Text>
                <br />
                <Paragraph code copyable>
                  {errorDetail.input}
                </Paragraph>
              </div>
            )}
            {errorDetail.stackTrace && (
              <div>
                <Text strong>堆栈信息：</Text>
                <br />
                <Paragraph
                  code
                  copyable
                  style={{
                    maxHeight: 300,
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5',
                    padding: 12,
                  }}
                >
                  <pre style={{ margin: 0 }}>{errorDetail.stackTrace}</pre>
                </Paragraph>
              </div>
            )}
          </Space>
        )}
      </Modal>
    </>
  )
}
