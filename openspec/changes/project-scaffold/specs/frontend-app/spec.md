## ADDED Requirements

### Requirement: 前端应用启动
前端应用 SHALL 使用 Vite 作为构建工具，React 18+ 作为 UI 框架，TypeScript 作为开发语言。

#### Scenario: 开发服务器启动
- **WHEN** 运行 `npm run dev` 或在 Docker 中启动 frontend 服务
- **THEN** 开发服务器在 `http://localhost:5173` 上响应
- **AND** 支持 HMR (Hot Module Replacement)

#### Scenario: 生产构建
- **WHEN** 运行 `npm run build`
- **THEN** 生成优化后的静态文件到 `dist/` 目录
- **AND** Nginx 可直接提供静态文件服务

### Requirement: 路由系统
前端 SHALL 使用 React Router 实现客户端路由，支持页面导航和 URL 参数。

#### Scenario: 页面导航
- **WHEN** 用户点击导航链接
- **THEN** URL 更新且对应页面组件渲染
- **AND** 浏览器前进/后退按钮正常工作

### Requirement: API 通信层
前端 SHALL 通过 Axios 封装统一的 API 请求层，自动处理认证 Token 和错误。

#### Scenario: 发送 API 请求
- **WHEN** 前端组件调用 API 服务
- **THEN** 请求自动携带 `Authorization` 头部
- **AND** 401 响应时自动触发重新登录

### Requirement: 状态管理
前端 SHALL 使用 Zustand 进行全局状态管理。

#### Scenario: 全局状态更新
- **WHEN** 用户登录成功
- **THEN** 用户信息存储到 Zustand store
- **AND** 所有订阅该状态的组件自动更新

### Requirement: UI 组件库
前端 SHALL 使用 Ant Design 5.x 作为 UI 组件库，提供一致的中文友好界面。

#### Scenario: 使用 Ant Design 组件
- **WHEN** 渲染表单、表格、按钮等界面元素
- **THEN** 使用 Ant Design 组件并获得一致的视觉效果
- **AND** 组件支持中文语言包

### Requirement: 基础布局
前端 SHALL 提供包含侧边栏导航和内容区域的基础布局。

#### Scenario: 应用基础布局
- **WHEN** 用户访问任何已认证页面
- **THEN** 显示侧边栏导航（可折叠）和主内容区域
- **AND** 顶部显示用户信息和系统名称
