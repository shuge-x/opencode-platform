import { Space, Select, DatePicker } from 'antd'
import dayjs from 'dayjs'
import type { TimeRange, BillingQueryParams } from '@/types/billing'

const { RangePicker } = DatePicker

interface TimeRangeSelectorProps {
  value: BillingQueryParams
  onChange: (value: BillingQueryParams) => void
}

const timeRangeOptions: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' },
  { value: '90d', label: '近 90 天' },
  { value: '1y', label: '近 1 年' },
  { value: 'custom', label: '自定义' },
]

export default function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  const handleRangeChange = (range: TimeRange) => {
    if (range === 'custom') {
      onChange({
        ...value,
        timeRange: 'custom',
        startDate: undefined,
        endDate: undefined,
      })
    } else {
      onChange({
        ...value,
        timeRange: range,
        startDate: undefined,
        endDate: undefined,
      })
    }
  }

  const handleCustomDateChange = (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      onChange({
        ...value,
        timeRange: 'custom',
        startDate: dates[0].format('YYYY-MM-DD'),
        endDate: dates[1].format('YYYY-MM-DD'),
      })
    }
  }

  return (
    <Space>
      <Select
        value={value.timeRange}
        onChange={handleRangeChange}
        options={timeRangeOptions}
        style={{ width: 120 }}
      />
      {value.timeRange === 'custom' && (
        <RangePicker
          value={
            value.startDate && value.endDate
              ? [dayjs(value.startDate), dayjs(value.endDate)]
              : null
          }
          onChange={handleCustomDateChange}
          allowClear
        />
      )}
    </Space>
  )
}
