import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, theme, Dropdown, Avatar, Typography, message, Badge, Popover, List, Empty, Tag, BackTop, Modal, Drawer, Grid, Tooltip } from 'antd';
import {
  CommentOutlined, BookOutlined, ExperimentOutlined, EditOutlined,
  SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined, UserOutlined,
  LogoutOutlined, LoginOutlined, BellOutlined, BgColorsOutlined,
  RocketOutlined, AppstoreOutlined, SafetyCertificateOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/useAuthStore';
import { useThemeStore, THEME_PRESETS } from '../stores/useThemeStore';
import api from '../services/api';

const { Text } = Typography;
const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/chat', icon: <CommentOutlined />, label: '对话', color: '#667eea' },
  { key: '/workspaces', icon: <AppstoreOutlined />, label: '项目空间', color: '#764ba2' },
  { key: '/papers', icon: <BookOutlined />, label: '论文库', color: '#00d2ff' },
  { key: '/research', icon: <ExperimentOutlined />, label: '研究方向', color: '#f5576c' },
  { key: '/writing', icon: <EditOutlined />, label: '写作助手', color: '#4facfe' },
  { key: '/admin', icon: <SafetyCertificateOutlined />, label: '管理员', color: '#fa8c16', adminOnly: true },
  { key: '/settings', icon: <SettingOutlined />, label: '设置', color: '#a18cd1' },
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
  const handleNotificationSelect = async (item: any) => {
    if (!item.is_read) await handleMarkRead(item.id);
    if (item.category === 'digest') {
      setNotifOpen(false);
      navigate('/papers/digests');
    }
  };
  const handleLogout = () => { logout(); message.success('已退出登录'); navigate('/'); };

  // ═══════ 侧栏 Logo ═══════
  const renderLogo = (compact: boolean) => (
    <div data-testid="sidebar-logo-link" style={{ width: '100%', cursor: 'pointer' }} onClick={() => navigate('/')}>
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
              AR · Research
            </div>
            <div style={{ fontSize: 10, color: '#999', marginTop: 1 }}>AI 科研搭子</div>
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
            {m.label}
          </span>
        ),
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
                    <Tooltip key={m.key} title={m.label} placement="right">
                      <div onClick={() => navigate(m.key)} style={{
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
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }} onClick={() => navigate('/settings')}>
                <Avatar size={32} src={user.avatar} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)', flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Text strong ellipsis style={{ fontSize: 13, display: 'block' }}>{user.display_name || user.username}</Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>{user.role === 'admin' ? '管理员' : '用户'}</Text>
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
            {/* 主题切换 */}
            <Dropdown menu={{ items: THEME_PRESETS.map(t => ({ key: t.id, icon: <span>{t.icon}</span>, label: t.name, onClick: () => themeStore.setTheme(t.id) })) }} placement="bottomRight">
              <Button type="text" icon={<BgColorsOutlined />} />
            </Dropdown>
            {/* 通知 */}
            {isAuthenticated && (
              <Popover trigger="click" open={notifOpen} onOpenChange={setNotifOpen} title="通知" content={
                <div style={{ width: 320 }}>
                  {notifications.length === 0 ? <Empty description="暂无通知" image={Empty.PRESENTED_IMAGE_SIMPLE} /> : (
                    <List style={{ maxHeight: 360, overflow: 'auto' }} dataSource={notifications} renderItem={(item: any) => (
                      <List.Item style={{ opacity: item.is_read ? 0.58 : 1, cursor: 'pointer' }} onClick={() => handleNotificationSelect(item)}>
                        <List.Item.Meta title={item.title} description={
                          <div>
                            <Text style={{ fontSize: 12 }} ellipsis>{item.content?.slice(0, 150)}</Text>
                            <div><Tag color={item.category === 'digest' ? 'blue' : 'default'} style={{ fontSize: 10 }}>{item.category}</Tag>
                              <Text type="secondary" style={{ fontSize: 10 }}>{new Date(item.created_at).toLocaleDateString()}</Text></div>
                          </div>
                        } />
                      </List.Item>
                    )} />
                  )}
                  <Button block type="link" icon={<BookOutlined />} onClick={() => { setNotifOpen(false); navigate('/papers/digests'); }} style={{ marginTop: 6 }}>进入论文推送中心</Button>
                </div>
              }>
                <Badge count={unreadCount} size="small"><Button type="text" icon={<BellOutlined />} onClick={handleNotifClick} /></Badge>
              </Popover>
            )}
            {/* 用户 */}
            {isAuthenticated && user ? (
              <Dropdown menu={{ items: [
                { key: 'role', label: `角色: ${user.role === 'admin' ? '管理员' : '用户'}`, disabled: true },
                { type: 'divider' },
                { key: 'settings', icon: <SettingOutlined />, label: '个人设置', onClick: () => navigate('/settings') },
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout, danger: true },
              ] }} placement="bottomRight">
                <div className="app-header-account"
                  onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <Avatar size={28} src={user.avatar} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)' }} />
                  <Text className="app-header-user-name" ellipsis style={{ fontSize: 13, maxWidth: 80 }}>{user.display_name || user.username}</Text>
                </div>
              </Dropdown>
            ) : (
              <Button type="link" icon={<LoginOutlined />} onClick={() => navigate('/login')}>登录</Button>
            )}
          </div>
        </Header>
        <Content className="app-layout-content" style={{ background: themeToken.colorBgContainer, borderRadius: themeToken.borderRadiusLG, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
      <BackTop />
      {/* 快捷键弹窗 */}
      <Modal title="⌨️ 快捷键" open={shortcutOpen} onCancel={() => setShortcutOpen(false)} footer={null} width={400}>
        {[
          ['?', '显示快捷键'], ['Ctrl+K', '搜索论文'], ['Ctrl+N', '新建对话'],
          ['Ctrl+B', '返回上一页'], ['Ctrl+H', '回到主页'],
          ['Enter', '发送消息'], ['Shift+Enter', '换行'],
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
