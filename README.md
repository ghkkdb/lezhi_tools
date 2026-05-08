# lezhi_tools

`lezhi_tools` 是一个 Windows 桌面游戏辅助工具，桌面端基于 Python、PyQt5、Win32 API 和 OpenCV 构建。项目当前还包含一个 FastAPI 授权服务端和一个 Vue 3 管理后台，用于卡密授权、客户端绑定、版本发布、更新检查和活跃事件查看。

桌面端入口是 `main.py`。启动后会创建 `QApplication`、设置应用图标和字体、验证本地缓存卡密、检查远程更新、上报启动与心跳事件，然后显示 `src.ui.ClassicScriptUI` 主窗口。

## 主要功能

- 桌面 GUI：任务配置、窗口绑定、任务启动、暂停、停止、日志展示。
- 单开任务：绑定一个目标窗口后执行勾选的日常任务。
- 多开控制：绑定多个窗口，为每个窗口选择已保存方案并独立启停。
- 图像识别：使用 OpenCV 模板匹配识别界面元素，配合截图帧缓存和模板缓存降低 I/O。
- 后台输入：通过 Win32 API 对目标窗口进行后台点击、按键、拖拽和截图。
- 任务控制：`TaskController` 支持暂停、继续、停止和可中断等待。
- 授权与更新：桌面端支持卡密激活、缓存验证、启动更新检查和手动检查更新。
- 服务端：FastAPI + SQLite 提供卡密、客户端绑定、版本发布、事件日志和统计接口。
- 管理后台：Vue 3 + Vite 提供仪表盘、卡密管理、客户端绑定、版本发布和事件日志页面。

## 项目结构

```text
.
├── admin/                  # Vue 3 + Vite 管理后台
│   └── src/                # 后台页面、组件、API 封装和样式
├── assets/                 # 图像模板、图标等资源
├── config/                 # 本地运行配置，用户任务方案写入这里
├── docs/                   # 架构说明、部署指南、变更记录和使用文档
├── logs/                   # 桌面端运行日志
├── scripts/                # 调试或维护脚本
├── server/                 # FastAPI 授权与更新服务端
│   ├── app/                # API、SQLite 初始化和安全工具
│   └── tests/              # 服务端接口测试
├── src/
│   ├── config/             # 全局配置、任务定义、路径、UI、服务端地址
│   ├── core/               # worker、任务控制器、任务注册表、任务逻辑
│   ├── services/           # 桌面端授权、更新、事件上报 HTTP 客户端
│   ├── ui/                 # PyQt5 主窗口、面板、控件、图标和样式
│   └── utils/              # Win32、图像识别、缓存、日志、输入追踪
├── tests/                  # 桌面端测试
├── tools/                  # 辅助工具
├── main.py                 # 桌面端入口
├── requirements.txt        # 桌面端 Python 依赖
└── README.md
```

## 桌面端环境

- 操作系统：Windows
- 推荐 Python：3.10
- 主要依赖：
  - `PyQt5`
  - `opencv-python`
  - `Pillow`
  - `numpy`
  - `pywin32`

安装：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

启动：

```powershell
python main.py
```

常用检查：

```powershell
python -m compileall -q src main.py
python -m pytest tests\test_logger.py -q
```

部分能力依赖真实 Windows 窗口、`pywin32/win32gui`、目标窗口类名和固定分辨率；无目标窗口或非 Windows 环境下无法完整验证桌面端自动化流程。

## 服务端

服务端位于 `server/`，使用 FastAPI + SQLite。默认数据库路径是 `server/data/server.sqlite3`，也可以通过 `LICENSE_SERVER_DB` 指定。

安装与启动：

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="admin123"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

生产环境必须修改默认管理员密码。

主要接口：

- `POST /api/license/activate`：桌面端卡密激活。
- `POST /api/license/verify`：桌面端缓存授权验证。
- `GET /api/update/latest`：获取最新发布版本。
- `POST /api/events`：写入客户端活跃事件。
- `POST /api/admin/login`：管理后台登录。
- `GET /api/admin/stats`：后台统计。
- `GET/POST/PATCH /api/admin/licenses`：卡密管理。
- `GET /api/admin/clients`：客户端绑定列表。
- `GET/POST/PATCH /api/admin/releases`：版本发布管理。
- `GET /api/admin/events`：事件日志。

服务端测试：

```powershell
cd server
pytest -q
```

## 管理后台

管理后台位于 `admin/`，使用 Vue 3 + Vite。开发服务器默认将 `/api` 代理到本地 FastAPI 服务。

安装与启动：

```powershell
cd admin
npm install
npm run dev
```

构建：

```powershell
npm run build
```

源码需要提交，`admin/node_modules/` 和 `admin/dist/` 是生成物，不应提交。

## 授权与更新配置

桌面端远程服务配置在 `src/config/app_config.py`：

- `APP_VERSION`：当前桌面端版本。
- `API_BASE_URL`：授权、更新和事件上报服务地址。
- `REQUEST_TIMEOUT`：桌面端 HTTP 超时时间。

桌面端本地运行时会写入：

- `config/client_identity.json`：客户端机器标识。
- `config/license_cache.json`：卡密、授权 token 和验证缓存。
- `logs/app.log`：运行日志。

这些都是本地运行数据，已在 `.gitignore` 中忽略。

## 基本使用

1. 启动桌面端。
2. 在“基础设置”页验证卡密，必要时检查更新。
3. 在“日常任务”页勾选任务并配置参数。
4. 保存任务方案。
5. 使用底部准星按钮绑定目标游戏窗口。
6. 点击开始执行。

多开流程：

1. 先在“日常任务”页保存任务方案。
2. 切换到“多开控制”页。
3. 使用底部准星依次绑定多个非重复窗口。
4. 每个窗口行选择一个任务方案。
5. 分别启动，或使用一键启动。

任务启动前会检查授权状态，并确保目标窗口尺寸符合配置。任务运行中会锁定目标窗口尺寸，结束后解锁。

## 任务开发

新增任务通常需要同步修改：

1. 在 `src/core/daily_tasks.py` 或合适模块中实现任务函数。
2. 使用 `@register_task("任务名")` 注册任务。
3. 在 `src/config/task_config.py` 中加入 UI 任务列表。
4. 如需参数，在 `src/config/task_definition_config.py` 中加入配置定义。
5. 任务函数签名推荐使用 `def task_xxx(hwnd, task_params=None):`。
6. 长等待使用 `task_controller.smart_sleep()`。
7. 循环、图像等待、长流程中适当调用 `task_controller.check_status()`。
8. 模板路径使用 `config.get_img_path("相对路径")`。

## 打包

桌面端当前默认打包方案是 Nuitka。维护发布流程时应围绕 Nuitka 参数、资源包含、依赖收集和 Windows 可执行文件产物处理。历史文档中如出现 PyInstaller，仅作为旧上下文或兼容说明。

## 注意事项

- 模板匹配准确率会受窗口分辨率、DPI 缩放、游戏 UI 变化和模板图片版本影响。
- 当前目标窗口类名与尺寸配置在 `src/config/window_config.py`。
- 修改任务名时要同步检查任务列表、任务配置定义、任务注册名和已保存用户配置。
- 停止任务、解绑窗口或关闭程序时必须释放被追踪的输入状态。
- 不要提交 `node_modules/`、`dist/`、`__pycache__/`、SQLite 数据库、本地授权缓存和日志文件。
