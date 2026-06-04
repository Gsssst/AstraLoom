## Why

网络错误和超时静默失败，用户不知道是网络问题还是后端挂了。

## What Changes

- API 拦截器中添加全局错误通知
- 50x 错误和网络超时显示提示条

## Capabilities

### New Capabilities

- `global-error-handler`: 全局错误通知
