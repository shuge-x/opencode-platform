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
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
