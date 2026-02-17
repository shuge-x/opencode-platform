import { Layout, Menu } from 'antd'
import { HomeOutlined, ChatOutlined, AppstoreOutlined, SettingOutlined, DashboardOutlined, StarOutlined, ApartmentOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/chat', icon: <ChatOutlined />, label: '对话' },
    { key: '/skills', icon: <AppstoreOutlined />, label: '技能' },
    { key: '/workflows', icon: <ApartmentOutlined />, label: '工作流' },
    { key: '/favorites', icon: <StarOutlined />, label: '收藏' },
    { key: '/files', icon: <AppstoreOutlined />, label: '文件' },
    { key: '/monitoring', icon: <DashboardOutlined />, label: '监控' },
    { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          OpenCode
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={(e) => navigate(e.key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: '0 20px',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <h2 style={{ margin: 0, lineHeight: '64px' }}>OpenCode Web 平台</h2>
        </Header>
        <Content style={{ margin: '20px', background: '#fff', padding: '20px', borderRadius: '8px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
