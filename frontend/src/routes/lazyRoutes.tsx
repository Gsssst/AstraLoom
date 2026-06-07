import { lazy, type ComponentType } from 'react';

type PageModule = { default: ComponentType<any> };
type RouteLoader = () => Promise<PageModule>;

export const routeLoaders = {
  HomePage: () => import('../pages/HomePage'),
  ChatPage: () => import('../pages/ChatPage'),
  PapersPage: () => import('../pages/PapersPage'),
  ResearchPage: () => import('../pages/ResearchPage'),
  ResearchProjectPage: () => import('../pages/ResearchProjectPage'),
  WritingPage: () => import('../pages/WritingPage'),
  SettingsPage: () => import('../pages/SettingsPage'),
  LoginPage: () => import('../pages/LoginPage'),
  RegisterPage: () => import('../pages/RegisterPage'),
  PaperDetailPage: () => import('../pages/PaperDetailPage'),
  PaperDigestInboxPage: () => import('../pages/PaperDigestInboxPage'),
  WorkspacesPage: () => import('../pages/WorkspacesPage'),
  WorkspaceDetailPage: () => import('../pages/WorkspaceDetailPage'),
  AdminPage: () => import('../pages/AdminPage'),
  ActionCenterPage: () => import('../pages/ActionCenterPage'),
} satisfies Record<string, RouteLoader>;

export const lazyPages = {
  HomePage: lazy(routeLoaders.HomePage),
  ChatPage: lazy(routeLoaders.ChatPage),
  PapersPage: lazy(routeLoaders.PapersPage),
  ResearchPage: lazy(routeLoaders.ResearchPage),
  ResearchProjectPage: lazy(routeLoaders.ResearchProjectPage),
  WritingPage: lazy(routeLoaders.WritingPage),
  SettingsPage: lazy(routeLoaders.SettingsPage),
  LoginPage: lazy(routeLoaders.LoginPage),
  RegisterPage: lazy(routeLoaders.RegisterPage),
  PaperDetailPage: lazy(routeLoaders.PaperDetailPage),
  PaperDigestInboxPage: lazy(routeLoaders.PaperDigestInboxPage),
  WorkspacesPage: lazy(routeLoaders.WorkspacesPage),
  WorkspaceDetailPage: lazy(routeLoaders.WorkspaceDetailPage),
  AdminPage: lazy(routeLoaders.AdminPage),
  ActionCenterPage: lazy(routeLoaders.ActionCenterPage),
};

const routePrefetchLoaders: Array<{ key: keyof typeof routeLoaders; match: RegExp; loader: RouteLoader }> = [
  { key: 'HomePage', match: /^\/$/, loader: routeLoaders.HomePage },
  { key: 'LoginPage', match: /^\/login\/?$/, loader: routeLoaders.LoginPage },
  { key: 'RegisterPage', match: /^\/register\/?$/, loader: routeLoaders.RegisterPage },
  { key: 'ChatPage', match: /^\/chat(?:\/.*)?$/, loader: routeLoaders.ChatPage },
  { key: 'ActionCenterPage', match: /^\/actions(?:\/.*)?$/, loader: routeLoaders.ActionCenterPage },
  { key: 'PaperDigestInboxPage', match: /^\/papers\/digests\/?$/, loader: routeLoaders.PaperDigestInboxPage },
  { key: 'PaperDetailPage', match: /^\/papers\/[^/]+\/?$/, loader: routeLoaders.PaperDetailPage },
  { key: 'PapersPage', match: /^\/papers(?:\/.*)?$/, loader: routeLoaders.PapersPage },
  { key: 'ResearchProjectPage', match: /^\/research\/[^/]+\/?$/, loader: routeLoaders.ResearchProjectPage },
  { key: 'ResearchPage', match: /^\/research(?:\/.*)?$/, loader: routeLoaders.ResearchPage },
  { key: 'WritingPage', match: /^\/writing(?:\/.*)?$/, loader: routeLoaders.WritingPage },
  { key: 'WorkspaceDetailPage', match: /^\/workspaces\/[^/]+\/?$/, loader: routeLoaders.WorkspaceDetailPage },
  { key: 'WorkspacesPage', match: /^\/workspaces(?:\/.*)?$/, loader: routeLoaders.WorkspacesPage },
  { key: 'AdminPage', match: /^\/admin(?:\/.*)?$/, loader: routeLoaders.AdminPage },
  { key: 'SettingsPage', match: /^\/settings(?:\/.*)?$/, loader: routeLoaders.SettingsPage },
];

const prefetchedRoutes = new Map<string, Promise<PageModule>>();

const normalizePath = (path: string) => {
  try {
    return new URL(path, window.location.origin).pathname;
  } catch {
    return path.split(/[?#]/)[0] || '/';
  }
};

export const prefetchRouteChunk = (path?: string | null) => {
  if (!path) return undefined;
  const pathname = normalizePath(path);
  const entry = routePrefetchLoaders.find(item => item.match.test(pathname));
  if (!entry) return undefined;
  if (!prefetchedRoutes.has(entry.key)) {
    prefetchedRoutes.set(entry.key, entry.loader().catch(error => {
      prefetchedRoutes.delete(entry.key);
      throw error;
    }));
  }
  return prefetchedRoutes.get(entry.key);
};

export const prefetchRouteIntent = (path?: string | null) => {
  prefetchRouteChunk(path)?.catch(() => {});
};
