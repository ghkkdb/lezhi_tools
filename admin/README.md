# 乐知工具后台前端

Vue 3 + Vite 前后端分离后台，所有接口请求统一使用 `/api` 作为 base。

## 页面

- 登录页
- 仪表盘
- 卡密管理
- 客户端绑定
- 版本发布
- 事件日志

## 运行

```powershell
cd D:\Desktop\lezhi_tools\admin
npm install
npm run dev
```

开发服务器默认会把 `/api` 代理到 `http://127.0.0.1:8000`，可在 `vite.config.js` 中调整。

## 构建

```powershell
cd D:\Desktop\lezhi_tools\admin
npm run build
```

构建产物输出到 `dist/`。
