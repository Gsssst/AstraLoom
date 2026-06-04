import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/AppLayout';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import PapersPage from './pages/PapersPage';
import ResearchPage from './pages/ResearchPage';
import ResearchProjectPage from './pages/ResearchProjectPage';
import WritingPage from './pages/WritingPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PaperDetailPage from './pages/PaperDetailPage';
import PaperDigestInboxPage from './pages/PaperDigestInboxPage';
import WorkspacesPage from './pages/WorkspacesPage';
import WorkspaceDetailPage from './pages/WorkspaceDetailPage';
import AdminPage from './pages/AdminPage';
import ActionCenterPage from './pages/ActionCenterPage';
import { useAuthStore } from './stores/useAuthStore';
import { useThemeStore } from './stores/useThemeStore';

const App: React.FC = () => {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const themeConfig = useThemeStore((s) => s.current);

  useEffect(() => { fetchUser(); }, [fetchUser]);

  // 全局快捷键
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); window.location.href = '/papers'; }
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); window.location.href = '/chat'; }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: themeConfig.algorithm,
        token: themeConfig.token,
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Routes>
            {/* 主页 —— 无侧边栏，全屏展示 */}
            <Route path="/" element={<HomePage />} />
            {/* 登录和注册 */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            {/* 内页 —— 侧边栏布局 */}
            <Route element={<AppLayout />}>
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/actions" element={<ActionCenterPage />} />
              <Route path="/papers" element={<PapersPage />} />
              <Route path="/papers/digests" element={<PaperDigestInboxPage />} />
              <Route path="/papers/:paperId" element={<PaperDetailPage />} />
              <Route path="/research" element={<ResearchPage />} />
              <Route path="/research/:projectId" element={<ResearchProjectPage />} />
              <Route path="/writing" element={<WritingPage />} />
              <Route path="/workspaces" element={<WorkspacesPage />} />
              <Route path="/workspaces/:spaceId" element={<WorkspaceDetailPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
