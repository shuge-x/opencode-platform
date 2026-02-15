import { Select, Space, DatePicker } from 'antd'
import { useState } from 'react'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

interface TimeRangeSelectorProps {
  onChange?: (value: { timeRange?: string; startDate?: string; endDate?: string }) => void
  defaultValue?: string
}

export default function TimeRangeSelector({ onChange, defaultValue = '24h' }: TimeRangeSelectorProps) {
  const [timeRange, setTimeRange] = useState(defaultValue)
  const [customRange, setCustomRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null)

  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value)
    if (value !== 'custom') {
      setCustomRange(null)
      onChange?.({ timeRange: value })
    }
  }

  const handleCustomRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setCustomRange(dates)
      onChange?.({
        timeRange: 'custom',
        startDate: dates[0].format('YYYY-MM-DD HH:mm:ss'),
        endDate: dates[1].format('YYYY-MM-DD HH:mm:ss'),
      })
    }
  }

  return (
    <Space>
      <Select
        value={timeRange}
        onChange={handleTimeRangeChange}
        style={{ width: 150 }}
        options={[
          { label: '最近 1 小时', value: '1h' },
          { label: '最近 6 小时', value: '6h' },
          { label: '最近 24 小时', value: '24h' },
          { label: '最近 7 天', value: '7d' },
          { label: '最近 30 天', value: '30d' },
          { label: '自定义', value: 'custom' },
        ]}
      />
      {timeRange === 'custom' && (
        <RangePicker
          showTime
          value={customRange}
          onChange={handleCustomRangeChange}
          format="YYYY-MM-DD HH:mm:ss"
        />
      )}
    </Space>
  )
}
