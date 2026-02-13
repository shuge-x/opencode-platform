import { Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function HomePage() {
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <Title level={2}>OpenCode Web 平台</Title>
      <Paragraph>
        欢迎使用 OpenCode Web 管理平台
      </Paragraph>
      <Paragraph type="secondary">
        基于 opencode 的可视化管理系统
      </Paragraph>
    </div>
  )
}
