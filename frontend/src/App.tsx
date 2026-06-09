import React, { Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import AppLayout from './components/AppLayout';
import GlobalCommandPalette from './components/GlobalCommandPalette';
import { WorkflowLoadingState } from './components/WorkflowState';
import { lazyPages } from './routes/lazyRoutes';
import { useAuthStore } from './stores/useAuthStore';
import { useThemeStore } from './stores/useThemeStore';
import { antdLocales } from './i18n';
import { useLocaleStore } from './stores/useLocaleStore';

const {
  HomePage,
  ChatPage,
  PapersPage,
  ToolboxPage,
  ResearchPage,
  ResearchProjectPage,
  WritingPage,
  SettingsPage,
  LoginPage,
  RegisterPage,
  PaperDetailPage,
  PaperDigestInboxPage,
  WorkspacesPage,
  WorkspaceDetailPage,
  AdminPage,
  ActionCenterPage,
} = lazyPages;

const App: React.FC = () => {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const themeConfig = useThemeStore((s) => s.current);
  const language = useLocaleStore((s) => s.language);
  const t = useLocaleStore((s) => s.t);
  const [commandPaletteOpen, setCommandPaletteOpen] = React.useState(false);

  const routeFallback = (
    <div style={{ width: 'min(960px, calc(100vw - 32px))', margin: '40px auto' }}>
      <WorkflowLoadingState
        title={t('app.loading.title')}
        description={t('app.loading.description')}
        rows={3}
      />
    </div>
  );

  const lazyRoute = (element: React.ReactNode) => (
    <Suspense fallback={routeFallback}>{element}</Suspense>
  );

  useEffect(() => { fetchUser(); }, [fetchUser]);

  // 全局快捷键
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); setCommandPaletteOpen(true); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); window.location.href = '/chat'; }
    };
    const openCommandPalette = () => setCommandPaletteOpen(true);
    window.addEventListener('keydown', handler);
    window.addEventListener('command-palette:open', openCommandPalette);
    return () => {
      window.removeEventListener('keydown', handler);
      window.removeEventListener('command-palette:open', openCommandPalette);
    };
  }, []);

  return (
    <ConfigProvider
      locale={antdLocales[language]}
      theme={{
        algorithm: themeConfig.algorithm,
        token: themeConfig.token,
      }}
    >
      <AntApp>
        <BrowserRouter>
          <GlobalCommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
          <Routes>
            {/* 主页 —— 无侧边栏，全屏展示 */}
            <Route path="/" element={lazyRoute(<HomePage />)} />
            {/* 登录和注册 */}
            <Route path="/login" element={lazyRoute(<LoginPage />)} />
            <Route path="/register" element={lazyRoute(<RegisterPage />)} />
            {/* 内页 —— 侧边栏布局 */}
            <Route element={<AppLayout />}>
              <Route path="/chat" element={lazyRoute(<ChatPage />)} />
              <Route path="/actions" element={lazyRoute(<ActionCenterPage />)} />
              <Route path="/papers" element={lazyRoute(<PapersPage />)} />
              <Route path="/toolbox" element={lazyRoute(<ToolboxPage />)} />
              <Route path="/papers/digests" element={lazyRoute(<PaperDigestInboxPage />)} />
              <Route path="/papers/:paperId" element={lazyRoute(<PaperDetailPage />)} />
              <Route path="/research" element={lazyRoute(<ResearchPage />)} />
              <Route path="/research/:projectId" element={lazyRoute(<ResearchProjectPage />)} />
              <Route path="/writing" element={lazyRoute(<WritingPage />)} />
              <Route path="/workspaces" element={lazyRoute(<WorkspacesPage />)} />
              <Route path="/workspaces/:spaceId" element={lazyRoute(<WorkspaceDetailPage />)} />
              <Route path="/admin" element={lazyRoute(<AdminPage />)} />
              <Route path="/settings" element={lazyRoute(<SettingsPage />)} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
