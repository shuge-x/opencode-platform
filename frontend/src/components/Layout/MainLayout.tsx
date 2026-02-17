import { useState, useEffect } from 'react'
import { Layout, Menu, Drawer, Button } from 'antd'
import { 
  HomeOutlined, 
  ChatOutlined, 
  AppstoreOutlined, 
  SettingOutlined, 
  DashboardOutlined, 
  StarOutlined, 
  PartitionOutlined,
  MenuOutlined,
  CloseOutlined,
  CodeOutlined
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { LoadingIndicator } from '@/components/common'
import './MainLayout.css'

const { Header, Sider, Content } = Layout

// 响应式断点
const MOBILE_BREAKPOINT = 768

// Logo SVG Component
function OpenCodeLogo({ collapsed }: { collapsed?: boolean }) {
  return (
    <div className={`logo-container ${collapsed ? 'collapsed' : ''}`}>
      <div className="logo-icon">
        <svg viewBox="0 0 32 32" width="32" height="32">
          <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1890ff" />
              <stop offset="100%" stopColor="#722ed1" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#logoGradient)" />
          <path
            d="M10 8h12M10 16h12M10 24h8"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <circle cx="24" cy="24" r="3" fill="white" />
        </svg>
      </div>
      {!collapsed && (
        <div className="logo-text">
          <span className="logo-name">OpenCode</span>
          <span className="logo-tagline">Web Platform</span>
        </div>
      )}
    </div>
  )
}

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  // 检测屏幕宽度变化
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT
      setIsMobile(mobile)
      if (mobile) {
        setCollapsed(true)
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 路由变化时关闭移动端菜单
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/chat', icon: <ChatOutlined />, label: '对话' },
    { key: '/skills', icon: <AppstoreOutlined />, label: '技能' },
    { key: '/favorites', icon: <StarOutlined />, label: '收藏' },
    { key: '/workflows', icon: <PartitionOutlined />, label: '工作流' },
    { key: '/files', icon: <AppstoreOutlined />, label: '文件' },
    { key: '/monitoring', icon: <DashboardOutlined />, label: '监控' },
    { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  ]

  const handleMenuClick = (key: string) => {
    navigate(key)
    if (isMobile) {
      setMobileMenuOpen(false)
    }
  }

  const menuContent = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={(e) => handleMenuClick(e.key)}
      className="main-menu"
    />
  )

  // 移动端布局
  if (isMobile) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <LoadingIndicator />
        
        {/* 移动端顶部导航 */}
        <Header className="mobile-header">
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setMobileMenuOpen(true)}
            className="mobile-menu-button"
          />
          <div className="mobile-logo">
            <OpenCodeLogo collapsed />
          </div>
          <div style={{ width: 40 }} /> {/* 占位，保持标题居中 */}
        </Header>

        {/* 移动端侧边栏抽屉 */}
        <Drawer
          placement="left"
          open={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          width={280}
          className="mobile-menu-drawer"
          closable={false}
          styles={{
            body: { padding: 0, background: '#001529' },
            header: { display: 'none' }
          }}
        >
          <div className="drawer-header">
            <OpenCodeLogo />
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={() => setMobileMenuOpen(false)}
              className="drawer-close-btn"
            />
          </div>
          {menuContent}
          <div className="drawer-footer">
            <CodeOutlined /> v1.0.0
          </div>
        </Drawer>

        {/* 内容区域 */}
        <Content className="mobile-content">
          <Outlet />
        </Content>
      </Layout>
    )
  }

  // 桌面端布局
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <LoadingIndicator />
      
      <Sider
        collapsible
        theme="dark"
        width={220}
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className="main-sider"
      >
        <OpenCodeLogo collapsed={collapsed} />
        {menuContent}
        <div className="sider-footer">
          <CodeOutlined /> v1.0.0
        </div>
      </Sider>
      
      <Layout className="main-layout">
        <Header className="main-header">
          <h2 className="header-title">OpenCode Web 平台</h2>
          <div className="header-actions">
            {/* 可以添加用户头像、通知等 */}
          </div>
        </Header>
        <Content className="main-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
