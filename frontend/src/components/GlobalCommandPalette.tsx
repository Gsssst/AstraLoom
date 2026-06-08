import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Avatar, Empty, Input, List, Modal, Space, Spin, Tag, Typography } from 'antd';
import {
  AppstoreOutlined,
  BookOutlined,
  BugOutlined,
  CommentOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  HomeOutlined,
  SearchOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { prefetchRouteIntent } from '../routes/lazyRoutes';
import { useAuthStore } from '../stores/useAuthStore';

const { Text } = Typography;

type CommandKind = 'route' | 'action' | 'paper' | 'research' | 'workspace' | 'issue' | 'writing';

interface CommandItem {
  id: string;
  group: string;
  title: string;
  subtitle?: string;
  keywords?: string[];
  path: string;
  icon: React.ReactNode;
  kind: CommandKind;
  shortcut?: string;
}

interface GlobalCommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const staticCommands: CommandItem[] = [
  { id: 'route-home', group: '导航', title: '首页', subtitle: '回到 AstraLoom 起始页', path: '/', icon: <HomeOutlined />, kind: 'route', keywords: ['home', 'start'] },
  { id: 'route-chat', group: '导航', title: 'AI 对话', subtitle: '打开通用研究对话工作区', path: '/chat', icon: <CommentOutlined />, kind: 'route', shortcut: 'Ctrl N', keywords: ['chat', 'llm', 'conversation'] },
  { id: 'route-actions', group: '导航', title: '行动中心', subtitle: '查看跨模块下一步任务', path: '/actions', icon: <ThunderboltOutlined />, kind: 'route', keywords: ['action', 'todo', 'next'] },
  { id: 'route-workspaces', group: '导航', title: '项目空间', subtitle: '管理论文、研究和写作资源集合', path: '/workspaces', icon: <AppstoreOutlined />, kind: 'route', keywords: ['workspace', 'space'] },
  { id: 'route-papers', group: '导航', title: '论文库', subtitle: '搜索、导入和维护论文', path: '/papers', icon: <BookOutlined />, kind: 'route', keywords: ['paper', 'library', 'search'] },
  { id: 'route-digests', group: '行动', title: '论文推送中心', subtitle: '查看每日推送和论文消化任务', path: '/papers/digests', icon: <BookOutlined />, kind: 'action', keywords: ['digest', 'notification'] },
  { id: 'route-research', group: '导航', title: '研究方向', subtitle: '管理研究方向和 Proposal 工作台', path: '/research', icon: <ExperimentOutlined />, kind: 'route', keywords: ['research', 'idea', 'proposal'] },
  { id: 'route-writing', group: '导航', title: '写作助手', subtitle: '打开论文写作和基金申请工作台', path: '/writing', icon: <FileTextOutlined />, kind: 'route', keywords: ['writing', 'draft', 'paper'] },
  { id: 'route-settings', group: '导航', title: '系统设置', subtitle: '配置账号、模型、API 和推送', path: '/settings', icon: <SettingOutlined />, kind: 'route', keywords: ['settings', 'api', 'model'] },
];

const itemText = (item: CommandItem) => [
  item.title,
  item.subtitle,
  item.group,
  item.kind,
  ...(item.keywords || []),
].filter(Boolean).join(' ').toLowerCase();

const includesQuery = (item: CommandItem, query: string) => itemText(item).includes(query.toLowerCase());

const uniqueItems = (items: CommandItem[]) => {
  const seen = new Set<string>();
  return items.filter(item => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });
};

const asArray = (value: any, key: string) => {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.[key])) return value[key];
  return [];
};

const normalizeYear = (item: any) => item?.year || item?.published_year || item?.created_at?.slice?.(0, 4) || '';

const normalizeSearchProbe = (kind: CommandKind, title: string, subtitle = '', keywords: string[] = []): CommandItem => ({
  id: title,
  group: '',
  title,
  subtitle,
  path: '',
  icon: null,
  kind,
  keywords,
});

export const searchResources = async (query: string): Promise<{ items: CommandItem[]; failed: boolean }> => {
  const trimmed = query.trim();
  if (!trimmed) return { items: [], failed: false };

  const requests = await Promise.allSettled([
    api.get('/papers/search', { params: { q: trimmed, source: 'local', page_size: 5 } }),
    api.get('/research/projects'),
    api.get('/workspaces'),
    api.get('/writing/projects'),
  ]);

  const [papersResult, researchResult, workspacesResult, writingResult] = requests;
  const failed = requests.some(result => result.status === 'rejected');
  const items: CommandItem[] = [];

  if (papersResult.status === 'fulfilled') {
    for (const paper of asArray(papersResult.value.data, 'items').slice(0, 5)) {
      if (!paper?.id) continue;
      items.push({
        id: `paper-${paper.id}`,
        group: '论文',
        title: paper.title || '未命名论文',
        subtitle: [paper.authors, normalizeYear(paper)].filter(Boolean).join(' · ') || paper.abstract?.slice?.(0, 80),
        path: `/papers/${paper.id}`,
        icon: <BookOutlined />,
        kind: 'paper',
        keywords: [paper.arxiv_id, paper.doi].filter(Boolean),
      });
    }
  }

  if (researchResult.status === 'fulfilled') {
    for (const project of asArray(researchResult.value.data, 'projects')
      .filter((project: any) => includesQuery(normalizeSearchProbe('research', project.name || '', project.description || '', project.keywords || []), trimmed))
      .slice(0, 4)) {
      items.push({
        id: `research-${project.id}`,
        group: '研究方向',
        title: project.name || '未命名研究方向',
        subtitle: project.description || `${project.ideas_count || 0} 个 Idea`,
        path: `/research/${project.id}`,
        icon: <ExperimentOutlined />,
        kind: 'research',
        keywords: project.keywords || [],
      });
    }
  }

  if (workspacesResult.status === 'fulfilled') {
    const spaces = asArray(workspacesResult.value.data, 'workspaces');
    for (const space of spaces
      .filter((space: any) => includesQuery(normalizeSearchProbe('workspace', space.name || '', space.description || ''), trimmed))
      .slice(0, 4)) {
      items.push({
        id: `workspace-${space.id}`,
        group: '项目空间',
        title: space.name || '未命名项目空间',
        subtitle: space.description || (space.role ? `角色：${space.role}` : '项目空间'),
        path: `/workspaces/${space.id}`,
        icon: <AppstoreOutlined />,
        kind: 'workspace',
      });
    }
    const issueMatches: CommandItem[] = [];
    for (const space of spaces) {
      for (const issue of Array.isArray(space.issue_summary) ? space.issue_summary : []) {
        const resourceReference = issue.resource_reference || {};
        const labels = Array.isArray(issue.labels) ? issue.labels : [];
        const probe = normalizeSearchProbe(
          'issue',
          issue.title || '',
          [
            space.name,
            issue.issue_type,
            issue.priority,
            resourceReference.title,
            resourceReference.resource_type,
          ].filter(Boolean).join(' '),
          labels,
        );
        if (!issue?.id || !includesQuery(probe, trimmed)) continue;
        issueMatches.push({
          id: `workspace-issue-${space.id}-${issue.id}`,
          group: '反馈 Issue',
          title: issue.title || '未命名 Issue',
          subtitle: [
            space.name || '项目空间',
            issue.priority ? `优先级：${issue.priority}` : null,
            resourceReference.title ? `关联：${resourceReference.title}` : null,
          ].filter(Boolean).join(' · '),
          path: issue.path || `/workspaces/${space.id}?issue=${issue.id}`,
          icon: <BugOutlined />,
          kind: 'issue',
          keywords: [issue.issue_type, issue.priority, resourceReference.resource_type, resourceReference.resource_id, ...labels].filter(Boolean),
        });
      }
    }
    items.push(...issueMatches.slice(0, 6));
  }

  if (writingResult.status === 'fulfilled') {
    for (const project of asArray(writingResult.value.data, 'projects')
      .filter((project: any) => includesQuery(normalizeSearchProbe('writing', project.title || '', project.description || '', [project.template_type, project.status].filter(Boolean)), trimmed))
      .slice(0, 4)) {
      items.push({
        id: `writing-${project.id}`,
        group: '写作项目',
        title: project.title || '未命名写作项目',
        subtitle: project.description || project.status || '写作项目',
        path: `/writing?project=${project.id}`,
        icon: <FileTextOutlined />,
        kind: 'writing',
        keywords: [project.template_type, project.status].filter(Boolean),
      });
    }
  }

  return { items: uniqueItems(items), failed };
};

const GlobalCommandPalette: React.FC<GlobalCommandPaletteProps> = ({ open, onOpenChange }) => {
  const navigate = useNavigate();
  const inputRef = useRef<any>(null);
  const isAuthenticated = useAuthStore(s => s.isAuthenticated);
  const user = useAuthStore(s => s.user);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const [resourceItems, setResourceItems] = useState<CommandItem[]>([]);
  const [resourceLoading, setResourceLoading] = useState(false);
  const [resourceFailed, setResourceFailed] = useState(false);

  const visibleStaticCommands = useMemo(
    () => staticCommands.filter(item => item.id !== 'route-settings' || isAuthenticated),
    [isAuthenticated],
  );

  const filteredStaticCommands = useMemo(() => {
    const trimmed = query.trim();
    if (!trimmed) return visibleStaticCommands;
    return visibleStaticCommands.filter(item => includesQuery(item, trimmed));
  }, [query, visibleStaticCommands]);

  const commands = useMemo(
    () => uniqueItems([...filteredStaticCommands, ...resourceItems]),
    [filteredStaticCommands, resourceItems],
  );

  useEffect(() => {
    if (!open) return;
    const timer = window.setTimeout(() => inputRef.current?.focus?.(), 50);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setActiveIndex(0);
  }, [query, open]);

  useEffect(() => {
    if (!open || !isAuthenticated || !query.trim()) {
      setResourceItems([]);
      setResourceLoading(false);
      setResourceFailed(false);
      return;
    }

    let cancelled = false;
    setResourceLoading(true);
    const timer = window.setTimeout(() => {
      searchResources(query).then(result => {
        if (cancelled) return;
        setResourceItems(result.items);
        setResourceFailed(result.failed);
      }).catch(() => {
        if (cancelled) return;
        setResourceItems([]);
        setResourceFailed(true);
      }).finally(() => {
        if (!cancelled) setResourceLoading(false);
      });
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query, open, isAuthenticated]);

  const closePalette = useCallback(() => {
    onOpenChange(false);
    setQuery('');
    setResourceItems([]);
    setResourceFailed(false);
  }, [onOpenChange]);

  const activate = useCallback((item?: CommandItem) => {
    if (!item) return;
    closePalette();
    navigate(item.path);
  }, [closePalette, navigate]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex(index => Math.min(index + 1, Math.max(commands.length - 1, 0)));
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex(index => Math.max(index - 1, 0));
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      activate(commands[activeIndex]);
    }
  };

  const groupedCommands = useMemo(() => {
    const groups: Array<{ group: string; items: CommandItem[] }> = [];
    for (const item of commands) {
      const existing = groups.find(group => group.group === item.group);
      if (existing) existing.items.push(item);
      else groups.push({ group: item.group, items: [item] });
    }
    return groups;
  }, [commands]);

  let runningIndex = -1;

  return (
    <Modal
      className="global-command-palette"
      open={open}
      onCancel={closePalette}
      footer={null}
      width={720}
      title={null}
      destroyOnHidden
      centered
    >
      <div className="command-palette-shell">
        <Input
          ref={inputRef}
          className="command-palette-input"
          size="large"
          allowClear
          prefix={<SearchOutlined />}
          placeholder="搜索页面、论文、研究方向、项目空间、Issue 或写作项目"
          value={query}
          onChange={event => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
        />

        <div className="command-palette-meta">
          <Space size={6} wrap>
            <Tag>↑↓ 选择</Tag>
            <Tag>Enter 打开</Tag>
            <Tag>Esc 关闭</Tag>
          </Space>
          {user && <Text type="secondary">当前用户：{user.display_name || user.username}</Text>}
        </div>

        <div className="command-palette-results">
          {groupedCommands.length === 0 && !resourceLoading ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的命令或资源" />
          ) : (
            groupedCommands.map(group => (
              <div className="command-palette-group" key={group.group}>
                <div className="command-palette-group-title">{group.group}</div>
                <List
                  dataSource={group.items}
                  renderItem={item => {
                    runningIndex += 1;
                    const itemIndex = runningIndex;
                    const active = itemIndex === activeIndex;
                    return (
                      <List.Item
                        className={`command-palette-item ${active ? 'is-active' : ''}`}
                        onMouseEnter={() => {
                          setActiveIndex(itemIndex);
                          prefetchRouteIntent(item.path);
                        }}
                        onClick={() => activate(item)}
                      >
                        <Avatar className="command-palette-icon" icon={item.icon} />
                        <div className="command-palette-copy">
                          <div className="command-palette-title-row">
                            <Text strong ellipsis>{item.title}</Text>
                            {item.shortcut && <Tag className="command-palette-shortcut">{item.shortcut}</Tag>}
                          </div>
                          {item.subtitle && <Text type="secondary" ellipsis>{item.subtitle}</Text>}
                        </div>
                        <Tag className="command-palette-kind">{item.kind}</Tag>
                      </List.Item>
                    );
                  }}
                />
              </div>
            ))
          )}
          {resourceLoading && (
            <div className="command-palette-resource-state">
              <Spin size="small" />
              <Text type="secondary">正在搜索资源...</Text>
            </div>
          )}
          {resourceFailed && (
            <div className="command-palette-resource-state">
              <Text type="secondary">部分资源搜索暂不可用，仍可使用上方命令。</Text>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default GlobalCommandPalette;
