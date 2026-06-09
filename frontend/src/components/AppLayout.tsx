import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, theme, Dropdown, Avatar, Typography, message, Badge, Popover, List, Empty, Tag, BackTop, Modal, Drawer, Grid, Tooltip } from 'antd';
import {
  CommentOutlined, BookOutlined, ExperimentOutlined, EditOutlined,
  SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined, UserOutlined,
  LogoutOutlined, LoginOutlined, BellOutlined, BgColorsOutlined,
  RocketOutlined, AppstoreOutlined, SafetyCertificateOutlined, ThunderboltOutlined,
  SearchOutlined, GlobalOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/useAuthStore';
import { useThemeStore, THEME_PRESETS } from '../stores/useThemeStore';
import { useLocaleStore } from '../stores/useLocaleStore';
import type { Language, MessageKey } from '../i18n';
import api from '../services/api';
import { prefetchRouteIntent } from '../routes/lazyRoutes';

const { Text } = Typography;
const { Header, Sider, Content } = Layout;

const notificationCategoryConfig: Record<string, { labelKey: MessageKey; color: string }> = {
  digest: { labelKey: 'notifications.category.digest', color: 'blue' },
  workspace_issue: { labelKey: 'notifications.category.workspaceIssue', color: 'purple' },
  system: { labelKey: 'notifications.category.system', color: 'default' },
};

const menuItems: Array<{
  key: string;
  icon: React.ReactNode;
  labelKey: MessageKey;
  color: string;
  adminOnly?: boolean;
}> = [
  { key: '/chat', icon: <CommentOutlined />, labelKey: 'nav.chat', color: '#667eea' },
  { key: '/actions', icon: <ThunderboltOutlined />, labelKey: 'nav.actions', color: '#f59e0b' },
  { key: '/workspaces', icon: <AppstoreOutlined />, labelKey: 'nav.workspaces', color: '#764ba2' },
  { key: '/papers', icon: <BookOutlined />, labelKey: 'nav.papers', color: '#00d2ff' },
  { key: '/research', icon: <ExperimentOutlined />, labelKey: 'nav.research', color: '#f5576c' },
  { key: '/writing', icon: <EditOutlined />, labelKey: 'nav.writing', color: '#4facfe' },
  { key: '/admin', icon: <SafetyCertificateOutlined />, labelKey: 'nav.admin', color: '#fa8c16', adminOnly: true },
  { key: '/settings', icon: <SettingOutlined />, labelKey: 'nav.settings', color: '#a18cd1' },
];

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [shortcutOpen, setShortcutOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token: themeToken } = theme.useToken();
  const screens = Grid.useBreakpoint();
  const isMobile = !screens.md;
  const { user, isAuthenticated, logout } = useAuthStore();
  const themeStore = useThemeStore();
  const language = useLocaleStore((s) => s.language);
  const setLanguage = useLocaleStore((s) => s.setLanguage);
  const t = useLocaleStore((s) => s.t);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const visibleMenuItems = menuItems.filter(item => !item.adminOnly || user?.role === 'admin');

  const selectedMenuKey = visibleMenuItems.find(item =>
    location.pathname === item.key || location.pathname.startsWith(`${item.key}/`)
  )?.key;

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) { e.preventDefault(); setShortcutOpen(true); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); navigate(-1); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'h') { e.preventDefault(); navigate('/'); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [navigate]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchUnread = () => { api.get('/notifications/unread-count').then(res => setUnreadCount(res.data.unread_count)).catch(() => {}); };
    fetchUnread();
    const timer = setInterval(fetchUnread, 60000);
    window.addEventListener('notifications:refresh', fetchUnread);
    return () => {
      clearInterval(timer);
      window.removeEventListener('notifications:refresh', fetchUnread);
    };
  }, [isAuthenticated]);

  const handleNotifClick = async () => {
    setNotifOpen(true);
    try { const res = await api.get('/notifications/list?limit=10'); setNotifications(res.data); } catch {}
  };
  const handleMarkRead = async (id: string) => {
    await api.post(`/notifications/${id}/read`);
    setUnreadCount(c => Math.max(0, c - 1));
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };
  const notificationTargetPath = (item: any) => {
    const metadata = item.metadata || {};
    if (item.category === 'workspace_issue') {
      if (metadata.path) return metadata.path;
      if (metadata.workspace_id && metadata.issue_id) return `/workspaces/${metadata.workspace_id}?issue=${metadata.issue_id}`;
    }
    if (item.category === 'digest') return '/papers/digests';
    return metadata.path || '';
  };
  const handleNotificationSelect = async (item: any) => {
    if (!item.is_read) await handleMarkRead(item.id);
    const targetPath = notificationTargetPath(item);
    if (targetPath) {
      setNotifOpen(false);
      navigate(targetPath);
    }
  };
  const handleMarkAllNotificationsRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications(prev => prev.map(item => ({ ...item, is_read: true })));
      setUnreadCount(0);
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch {
      message.warning(t('user.logout.failedRead'));
    }
  };
  const handleLogout = () => { logout(); message.success(t('user.logout.success')); navigate('/'); };
  const routeIntentProps = (path: string) => ({
    onMouseEnter: () => prefetchRouteIntent(path),
    onFocus: () => prefetchRouteIntent(path),
    onTouchStart: () => prefetchRouteIntent(path),
  });

  const switchLanguage = (nextLanguage: Language) => {
    setLanguage(nextLanguage);
  };

  const languageMenuItems = [
    { key: 'zh', label: t('header.language.zh'), onClick: () => switchLanguage('zh') },
    { key: 'en', label: t('header.language.en'), onClick: () => switchLanguage('en') },
  ];

  // ═══════ 侧栏 Logo ═══════
  const renderLogo = (compact: boolean) => (
    <div data-testid="sidebar-logo-link" style={{ width: '100%', cursor: 'pointer' }} onClick={() => navigate('/')} {...routeIntentProps('/')}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: compact ? 0 : 10,
        justifyContent: compact ? 'center' : 'flex-start',
        width: '100%', boxSizing: 'border-box',
        padding: compact ? '16px 0' : '16px 20px',
      }}>
        <div style={{
          width: compact ? 36 : 40, height: compact ? 36 : 40,
          borderRadius: 12,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 4px 15px rgba(102,126,234,0.4)',
        }}>
          <RocketOutlined style={{ color: '#fff', fontSize: compact ? 16 : 18 }} />
        </div>
        {!compact && (
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: 16, fontWeight: 800, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', lineHeight: 1.2 }}>
              AstraLoom
            </div>
            <div style={{ fontSize: 10, color: '#999', marginTop: 1 }}>AI Research Workspace</div>
          </div>
        )}
      </div>
    </div>
  );

  // ═══════ 菜单渲染 ═══════
  const renderMenu = (inline: boolean) => (
    <Menu
      mode={inline ? 'inline' : 'inline'}
      selectedKeys={selectedMenuKey ? [selectedMenuKey] : []}
      onClick={({ key }) => navigate(key)}
      style={{ borderRight: 0, background: 'transparent' }}
      items={visibleMenuItems.map(m => ({
        key: m.key,
        icon: (
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 32, height: 32, borderRadius: 10,
            background: selectedMenuKey === m.key ? `${m.color}18` : 'transparent',
            color: selectedMenuKey === m.key ? m.color : '#999',
            transition: 'all 0.25s',
          }}>
            {m.icon}
          </span>
        ),
        label: (
          <span style={{
            color: selectedMenuKey === m.key ? m.color : '#555',
            fontWeight: selectedMenuKey === m.key ? 600 : 400,
            fontSize: 13,
            transition: 'all 0.25s',
          }}>
            {t(m.labelKey)}
          </span>
        ),
        onMouseEnter: () => prefetchRouteIntent(m.key),
        onFocus: () => prefetchRouteIntent(m.key),
        onTouchStart: () => prefetchRouteIntent(m.key),
        style: {
          borderRadius: 10, margin: '2px 10px',
          transition: 'all 0.25s',
          ...(selectedMenuKey === m.key ? { background: `${m.color}0c` } : {}),
        },
      }))}
    />
  );

  // ═══════ 移动端 Drawer ═══════
  const mobileDrawer = (
    <Drawer title={renderLogo(false)} placement="left" width={260} open={mobileNavOpen} onClose={() => setMobileNavOpen(false)}
      styles={{ body: { padding: '8px 0' }, header: { borderBottom: '1px solid #f0f0f0', padding: '12px 16px' } }}>
      {renderMenu(true)}
    </Drawer>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isMobile && mobileDrawer}
      {/* ═══════ 桌面侧栏 ═══════ */}
      {!isMobile && (
        <Sider
          trigger={null} collapsible collapsed={collapsed}
          onMouseEnter={() => setCollapsed(false)}
          onMouseLeave={() => setCollapsed(true)}
          width={220} collapsedWidth={64}
          style={{
            background: '#fafbfc',
            borderRight: '1px solid #f0f0f0',
            transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
          }}
        >
          {/* Logo */}
          <div style={{
            height: 64, display: 'flex', alignItems: 'center', width: '100%',
            borderBottom: '1px solid #f0f0f0',
            background: 'linear-gradient(180deg, #fff 0%, #fafbfc 100%)',
          }}>
            {renderLogo(collapsed)}
          </div>

          {/* 菜单 */}
          <div style={{ padding: '12px 0' }}>
            {collapsed ? (
              // 折叠态：图标 + Tooltip
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                {visibleMenuItems.map(m => {
                  const isActive = selectedMenuKey === m.key;
                  return (
                    <Tooltip key={m.key} title={t(m.labelKey)} placement="right">
                      <div onClick={() => navigate(m.key)} {...routeIntentProps(m.key)} style={{
                        width: 40, height: 40, borderRadius: 12, cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: isActive ? `${m.color}12` : 'transparent',
                        color: isActive ? m.color : '#999',
                        fontSize: 18, transition: 'all 0.25s',
                        position: 'relative',
                      }}>
                        {m.icon}
                        {isActive && (
                          <div style={{
                            position: 'absolute', right: -10, top: '50%', transform: 'translateY(-50%)',
                            width: 3, height: 16, borderRadius: 3,
                            background: m.color,
                          }} />
                        )}
                      </div>
                    </Tooltip>
                  );
                })}
              </div>
            ) : (
              // 展开态：文字菜单
              renderMenu(true)
            )}
          </div>

          {/* 底部用户信息 */}
          {!collapsed && isAuthenticated && user && (
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              padding: '12px 16px', borderTop: '1px solid #f0f0f0',
              background: '#fafbfc',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }} onClick={() => navigate('/settings')} {...routeIntentProps('/settings')}>
                <Avatar size={32} src={user.avatar} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)', flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Text strong ellipsis style={{ fontSize: 13, display: 'block' }}>{user.display_name || user.username}</Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>{user.role === 'admin' ? t('role.admin') : t('role.user')}</Text>
                </div>
              </div>
            </div>
          )}
        </Sider>
      )}

      {/* ═══════ 右侧主体 ═══════ */}
      <Layout className="app-layout-main">
        <Header className="app-layout-header" style={{
          padding: '0 24px', height: 48, lineHeight: '48px',
          background: themeToken.colorBgContainer,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
        }}>
          <Button type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => isMobile ? setMobileNavOpen(true) : setCollapsed(!collapsed)}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button
              type="text"
              className="command-palette-trigger"
              icon={<SearchOutlined />}
              onClick={() => window.dispatchEvent(new Event('command-palette:open'))}
            >
              <Text type="secondary">{t('header.command')}</Text>
              {!isMobile && <Tag style={{ marginInlineEnd: 0 }}>⌘K</Tag>}
            </Button>
            {/* 主题切换 */}
            <Dropdown menu={{ items: THEME_PRESETS.map(preset => ({ key: preset.id, icon: <span>{preset.icon}</span>, label: preset.name, onClick: () => themeStore.setTheme(preset.id) })) }} placement="bottomRight">
              <Tooltip title={t('header.theme')}>
                <Button type="text" icon={<BgColorsOutlined />} />
              </Tooltip>
            </Dropdown>
            <Dropdown menu={{ selectedKeys: [language], items: languageMenuItems }} placement="bottomRight">
              <Tooltip title={t('header.language')}>
                <Button type="text" icon={<GlobalOutlined />}>{!isMobile ? language.toUpperCase() : null}</Button>
              </Tooltip>
            </Dropdown>
            {/* 通知 */}
            {isAuthenticated && (
              <Popover trigger="click" open={notifOpen} onOpenChange={setNotifOpen} title={t('notifications.title')} content={
                <div style={{ width: 320 }}>
                  <Button
                    block
                    size="small"
                    disabled={!notifications.some((item: any) => !item.is_read)}
                    onClick={handleMarkAllNotificationsRead}
                    style={{ marginBottom: 8, borderRadius: 8 }}
                  >
                    {t('notifications.markAllRead')}
                  </Button>
                  {notifications.length === 0 ? <Empty description={t('notifications.empty')} image={Empty.PRESENTED_IMAGE_SIMPLE} /> : (
                    <List style={{ maxHeight: 360, overflow: 'auto' }} dataSource={notifications} renderItem={(item: any) => (
                      <List.Item
                        style={{ opacity: item.is_read ? 0.58 : 1, cursor: 'pointer' }}
                        onClick={() => handleNotificationSelect(item)}
                        {...routeIntentProps(notificationTargetPath(item))}
                      >
                        <List.Item.Meta title={item.title} description={
                          <div>
                            <Text style={{ fontSize: 12 }} ellipsis>{item.content?.slice(0, 150)}</Text>
                            <div>
                              <Tag color={notificationCategoryConfig[item.category]?.color || 'default'} style={{ fontSize: 10 }}>
                                {notificationCategoryConfig[item.category]?.labelKey ? t(notificationCategoryConfig[item.category].labelKey) : item.category}
                              </Tag>
                              <Text type="secondary" style={{ fontSize: 10 }}>{new Date(item.created_at).toLocaleDateString()}</Text>
                            </div>
                          </div>
                        } />
                      </List.Item>
                    )} />
                  )}
                  <Button block type="link" icon={<BookOutlined />} onClick={() => { setNotifOpen(false); navigate('/papers/digests'); }} style={{ marginTop: 6 }} {...routeIntentProps('/papers/digests')}>{t('notifications.digestCenter')}</Button>
                </div>
              }>
                <Badge count={unreadCount} size="small"><Button type="text" icon={<BellOutlined />} onClick={handleNotifClick} /></Badge>
              </Popover>
            )}
            {/* 用户 */}
            {isAuthenticated && user ? (
              <Dropdown menu={{ items: [
                { key: 'role', label: `${t('user.role')}: ${user.role === 'admin' ? t('role.admin') : t('role.user')}`, disabled: true },
                { type: 'divider' },
                { key: 'settings', icon: <SettingOutlined />, label: t('user.settings'), onMouseEnter: () => prefetchRouteIntent('/settings'), onClick: () => navigate('/settings') },
                { key: 'logout', icon: <LogoutOutlined />, label: t('user.logout'), onClick: handleLogout, danger: true },
              ] }} placement="bottomRight">
                <div className="app-header-account"
                  onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <Avatar size={28} src={user.avatar} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)' }} />
                  <Text className="app-header-user-name" ellipsis style={{ fontSize: 13, maxWidth: 80 }}>{user.display_name || user.username}</Text>
                </div>
              </Dropdown>
            ) : (
              <Button type="link" icon={<LoginOutlined />} onClick={() => navigate('/login')} {...routeIntentProps('/login')}>{t('header.login')}</Button>
            )}
          </div>
        </Header>
        <Content className="app-layout-content" style={{ background: themeToken.colorBgContainer, borderRadius: themeToken.borderRadiusLG, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
      <BackTop />
      {/* 快捷键弹窗 */}
      <Modal title={`⌨️ ${t('shortcut.title')}`} open={shortcutOpen} onCancel={() => setShortcutOpen(false)} footer={null} width={400}>
        {[
          ['?', t('shortcut.showHelp')], ['Ctrl+K', t('shortcut.commandPalette')], ['Ctrl+N', t('shortcut.newChat')],
          ['Ctrl+B', t('shortcut.back')], ['Ctrl+H', t('shortcut.home')],
          ['Enter', t('shortcut.send')], ['Shift+Enter', t('shortcut.newline')],
        ].map(([k, d], i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
            <Tag style={{ fontFamily: 'monospace', fontSize: 13 }}>{k}</Tag>
            <Text>{d}</Text>
          </div>
        ))}
      </Modal>
    </Layout>
  );
};

export default AppLayout;
