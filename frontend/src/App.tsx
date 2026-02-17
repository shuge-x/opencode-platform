import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import MainLayout from '@/components/Layout/MainLayout'
import HomePage from '@/pages/Home'
import LoginPage from '@/pages/Login'
import ChatPage from '@/pages/Chat'
import SkillsPage from '@/pages/Skills'
import FilesPage from '@/pages/Files'
import SettingsPage from '@/pages/Settings'
import FavoritesPage from '@/pages/FavoritesPage'
import MonitoringDashboard from '@/pages/Monitoring'
import { WorkflowList, WorkflowEditor, ExecutionHistory, ExecutionDetail } from '@/pages/Workflows'
import { useAuthStore } from '@/stores/authStore'

// Protected Route
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route path="/" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
            <Route index element={<HomePage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="favorites" element={<FavoritesPage />} />
            <Route path="files" element={<FilesPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="monitoring" element={<MonitoringDashboard />} />
            <Route path="workflows" element={<WorkflowList />} />
            <Route path="workflows/new" element={<WorkflowEditor />} />
            <Route path="workflows/:id/edit" element={<WorkflowEditor />} />
            <Route path="workflows/:id/executions" element={<ExecutionHistory />} />
            <Route path="executions/:id" element={<ExecutionDetail />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
