# AGENTS.md

## 项目概览

本项目是一个 Windows 桌面游戏辅助工具，桌面端基于 Python、PyQt5、Win32 API 和 OpenCV。程序通过 GUI 提供任务配置、窗口绑定、任务方案保存、多窗口独立控制、运行日志展示和图像模板识别等能力。

项目当前还包含：

- `server/`：FastAPI + SQLite 授权、更新、事件和管理接口服务端。
- `admin/`：Vue 3 + Vite 管理后台，用于卡密管理、客户端绑定、版本发布和事件查看。
- `src/services/`：桌面端访问远程授权、更新和事件接口的轻量 HTTP 客户端。

桌面端入口文件是 `main.py`。启动后会设置 Windows App ID、应用图标和字体，验证本地缓存授权，检查版本更新，上报启动和心跳事件，然后显示 `src.ui.ClassicScriptUI` 主窗口。

自动化任务主要依赖：

- 绑定目标游戏窗口句柄。
- 对目标窗口进行后台点击、按键、拖拽和截图。
- 使用 OpenCV 模板匹配识别界面元素。
- 通过任务注册表动态查找并执行任务函数。
- 通过任务控制器支持暂停、继续、停止和可中断等待。
- 启动任务前验证卡密授权并确保目标窗口尺寸符合配置。

## 运行环境

桌面端：

- 操作系统：Windows。
- 推荐 Python：3.10。
- 主要依赖见 `requirements.txt`：
  - `PyQt5`
  - `opencv-python`
  - `Pillow`
  - `numpy`
  - `pywin32`

安装示例：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

启动桌面端：

```powershell
python main.py
```

常用检查：

```powershell
python -m compileall -q src main.py
python -m pytest tests\test_logger.py -q
```

服务端：

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="admin123"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pytest -q
```

管理后台：

```powershell
cd admin
npm install
npm run dev
npm run build
```

注意：许多桌面端功能依赖 `pywin32/win32gui` 和真实 Windows 窗口环境，部分测试或功能在非 Windows 环境、无目标窗口环境下无法完整运行。

## 目录结构

```text
.
├── admin/                  # Vue 3 + Vite 管理后台
├── assets/                 # 图像模板和应用图标资源
├── config/                 # 用户任务方案和本地运行缓存
├── docs/                   # 项目文档、架构分析、部署指南和变更记录
├── logs/                   # 运行日志，默认 app.log
├── scripts/                # 调试脚本
├── server/                 # FastAPI 授权与更新服务端
├── src/
│   ├── config/             # 全局配置、窗口配置、任务定义、UI 配置、路径和远程服务配置
│   ├── core/               # 任务控制器、worker、任务注册表、日常任务逻辑、状态管理
│   ├── services/           # 授权、更新、事件上报和客户端标识
│   ├── ui/                 # PyQt5 主窗口、面板、控件、图标和样式
│   └── utils/              # Win32 操作、图像识别、缓存、日志、输入追踪等工具
├── tests/                  # 桌面端测试脚本
├── tools/                  # 辅助工具
├── main.py                 # 桌面端入口
└── requirements.txt        # 桌面端依赖清单
```

## 核心模块

### 桌面端 UI 层

- `src/ui/main_window.py`
  - 定义主窗口 `ClassicScriptUI`。
  - 负责页面切换、授权状态展示、更新检查、窗口绑定、任务启动、暂停、停止、日志显示和关闭清理。
  - 基础设置页包含卡密授权、交流群和版本更新。
  - 日常任务页负责任务勾选和参数配置。
  - 多开控制页负责多个窗口的方案选择和独立执行控制。

- `src/ui/panels/`
  - `bottom_panel.py`：底部窗口绑定和运行控制。
  - `log_panel.py`：日志显示。
  - `task_list_panel.py`：任务列表。
  - `task_config_panel.py`：任务参数配置动态渲染。
  - `multi_window_panel.py`：多窗口绑定、方案选择、独立执行、日志弹窗和一键操作。

- `src/ui/widgets/`
  - 包含准星按钮、窗口选择器、导航标签、解绑按钮等控件。
  - `window_picker.py` 负责窗口拾取、截图预览、尺寸调整、锁定和解锁。
  - `tab_navigation.py` 负责顶部导航。

- `src/ui/app_icons.py`
  - 负责应用图标和 Windows App ID。

### Core 层

- `src/core/worker.py`
  - 定义 `ScriptWorker(QThread)`。
  - 每个 worker 接收任务列表、目标窗口句柄和任务参数。
  - 执行前会检查窗口是否有效，并通过任务注册表获取任务函数。
  - 每个 worker 使用独立 `TaskController(isolated=True)`，支持多窗口场景下独立暂停、继续、停止。

- `src/core/controller.py`
  - 定义 `TaskController`、`TaskControllerProxy` 和相关异常。
  - `task_controller.smart_sleep()` 会把长等待切成 100ms 小片段，期间检查暂停和停止信号。
  - 自动化任务中应优先使用 `task_controller.smart_sleep()`，避免直接使用长时间 `time.sleep()`。

- `src/core/task_registry.py`
  - 通过 `@register_task("任务名")` 注册任务函数。
  - worker 通过 `get_task(task_name)` 动态获取任务实现。

- `src/core/daily_tasks.py`
  - 日常任务主要实现文件。
  - 任务逻辑大量使用图像查找、后台点击、后台按键和固定坐标。

- `src/core/config_manager.py`
  - 从 `TaskConfigPanel` 收集扁平化任务参数。
  - 结合全局配置完成参数映射，返回 worker 需要的 `{task_name: params}` 字典。

- `src/core/state_manager.py`
  - 全局 UI 状态管理器。
  - 管理按钮状态：`IDLE`、`RUNNING`、`PAUSED`、`STOPPING`。
  - 管理当前绑定窗口句柄，并通过 Qt 信号通知 UI。

### Config 层

- `src/config/settings.py`
  - `Config` 门面类，整合窗口、任务、任务定义、UI、按键、路径、日志和用户配置。
  - 对外暴露兼容旧代码的属性和方法。

- `src/config/app_config.py`
  - 定义 `APP_VERSION`、`API_BASE_URL` 和 `REQUEST_TIMEOUT`。
  - 桌面端授权、更新检查和事件上报都依赖这里的远程服务配置。

- `src/config/window_config.py`
  - 应用窗口和目标窗口配置。
  - 当前目标窗口类名、游戏窗口尺寸和 UI 尺寸在这里维护。

- `src/config/task_config.py`
  - 定义日常任务列表、答题坐标权重、帮派按钮坐标、摇钱树选项等。

- `src/config/task_definition_config.py`
  - 定义任务配置 UI 的字段结构。
  - 支持 `dropdown`、`text`、`number`、`checkbox`、`spinbox`、`label`、`row`、`group`、`columns` 等控件类型。
  - 支持通过 `extends` 复用共享配置。

- `src/config/path_config.py`
  - 统一管理资源、配置、日志路径。
  - 支持开发环境和打包环境。

### Services 层

- `src/services/client_id.py`
  - 生成并读取本地客户端标识，写入 `config/client_identity.json`。

- `src/services/http_client.py`
  - 使用标准库 `urllib` 实现 JSON HTTP 请求，避免桌面端新增 `requests` 依赖。
  - 将服务端错误码映射为用户可读提示。

- `src/services/license_client.py`
  - 负责卡密激活、缓存读取、缓存写入和启动时授权验证。
  - 授权缓存写入 `config/license_cache.json`。

- `src/services/update_client.py`
  - 请求 `/api/update/latest`，并根据 `APP_VERSION` 判断是否有新版本。

- `src/services/telemetry_client.py`
  - 上报匿名活跃事件。
  - 目前只允许白名单事件：`app_start`、`app_heartbeat`、`license_activate`、`license_verify`、`update_check`。
  - 上报失败必须静默处理，不得影响主流程。

### Utils 层

- `src/utils/win_api.py`
  - 封装窗口绑定、后台点击、后台按键、后台拖拽、窗口截图和输入释放。
  - 点击和按键操作配合 `InputTracker` 追踪 down/up 状态，异常或停止时可释放残留输入。
  - 改变画面的输入操作会清理截图帧缓存。

- `src/utils/image_utils.py`
  - 封装 OpenCV 模板匹配。
  - 支持单目标匹配、多目标匹配、ROI、阈值、灰度匹配。
  - 使用 `template_cache` 和 `frame_cache` 减少模板读取和窗口截图开销。

- `src/utils/cache.py`
  - 模板缓存和截图帧缓存。

- `src/utils/logger.py`
  - 日志系统，支持控制台、文件和 Qt 信号输出，并支持多窗口日志上下文。
  - UI 展示前可使用 `strip_ui_log_context()` 隐藏内部路由上下文。

- `src/utils/input_tracker.py`
  - 追踪后台输入按下状态，配合窗口关闭、停止任务时释放输入。

### Server 层

- `server/app/main.py`
  - FastAPI 应用和主要接口。
  - 提供管理员登录、卡密管理、客户端绑定、版本发布、事件日志、统计、授权激活、授权验证、更新查询和事件写入。

- `server/app/db.py`
  - SQLite 数据库路径、连接、会话上下文、表结构初始化和默认管理员创建。
  - 默认数据库路径为 `server/data/server.sqlite3`，可用 `LICENSE_SERVER_DB` 覆盖。

- `server/app/security.py`
  - token 生成、PBKDF2 密码哈希和密码校验。

- `server/tests/test_api.py`
  - 覆盖管理员登录、卡密创建、激活、验证、设备限制、批量删除、版本发布、事件写入和统计。

### Admin 层

- `admin/src/App.vue`
  - 管理后台壳层、登录状态、侧边导航和页面切换。

- `admin/src/api.js`
  - 后台 API 封装，统一使用 `/api` 作为 base。

- `admin/src/pages/`
  - `DashboardPage.vue`：统计和最近活跃。
  - `CardKeysPage.vue`：卡密创建、启用、禁用、批量删除。
  - `ClientBindingsPage.vue`：客户端绑定和解绑。
  - `VersionsPage.vue`：版本发布。
  - `EventLogsPage.vue`：事件日志。
  - `LoginPage.vue`：管理员登录。

## 任务开发规则

新增任务时建议按以下流程：

1. 在 `src/core/daily_tasks.py` 或合适的新模块中实现任务函数。
2. 使用 `@register_task("任务名")` 注册任务。
3. 确保任务名与 `src/config/task_config.py` 中 UI 列表名称一致。
4. 如任务需要参数，在 `src/config/task_definition_config.py` 中添加配置定义。
5. 任务函数如果需要参数，签名使用 `def task_xxx(hwnd, task_params=None):`。
6. 在耗时等待处使用 `task_controller.smart_sleep()`。
7. 在循环、长流程、图像等待处适当调用 `task_controller.check_status()`。
8. 使用 `config.get_img_path("相对路径")` 获取模板图片路径。
9. 修改画面后注意截图缓存可能会被输入工具自动清理；如直接操作画面，可主动调用图像工具中的缓存清理函数。

## 多窗口与线程注意事项

- 单窗口主控使用主窗口中的 `ScriptWorker`。
- 多开控制页会为每个绑定窗口创建独立 worker。
- 每个 worker 都有独立 `TaskController`，避免不同窗口之间的暂停、继续、停止状态相互影响。
- 任务代码仍通过全局 `task_controller` 访问控制器；`TaskControllerProxy` 会根据当前线程转发到正确的控制器。
- worker 结束时会释放被追踪的输入状态，并发出完成信号。
- 单开任务运行时，多开控制页会限制一键整理、一键启动、一键停止、一键解绑等操作。
- 多开任务启动前同样需要通过授权检查。

## 授权、更新和事件规则

- 桌面端启动时调用 `license_client.verify_cached_license()`，没有缓存或验证失败时任务不能启动。
- 用户可在基础设置页输入卡密并调用 `license_client.activate_license()`。
- 桌面端启动和手动检查时调用 `update_client.check_update()`。
- `telemetry_client.track()` 只允许白名单事件，上报失败不能抛出到 UI 或阻断任务。
- 不要把 `config/client_identity.json`、`config/license_cache.json`、服务端 SQLite 数据库、日志或其他本地运行数据提交到仓库。
- 修改 `APP_VERSION`、服务端发布接口或更新返回结构时，要同步检查 `src/config/app_config.py`、`src/services/update_client.py`、`server/app/main.py` 和 `admin/src/pages/VersionsPage.vue`。

## 图像模板资源

图像模板集中在 `assets/img/` 下，按任务类型分组，例如：

- `chushihua_`：初始化和通用入口相关模板。
- `richang_`：日常任务模板。
- `mengjing_img`：梦境或匹配相关模板。
- `richang_/bangpai_JX`：帮派捐献相关模板。
- `richang_/fuben_louji`：副本流程相关模板。
- `richang_/lunji`：华山论剑相关模板。
- `richang_/meiriduihuan`：每日兑换相关模板。
- `richang_/shanheqi`：山河器相关模板。
- `richang_/yaoqianshu`：摇钱树相关模板。

模板匹配准确率会受窗口分辨率、DPI 缩放、游戏 UI 变化和模板图片版本影响。当前默认游戏窗口尺寸由 `src/config/window_config.py` 控制。

## 配置和数据文件

- 用户方案保存在 `config/user_task_configs.json`。
- 客户端身份缓存写入 `config/client_identity.json`。
- 授权缓存写入 `config/license_cache.json`。
- 日志默认写入 `logs/app.log`。
- 服务端默认数据库写入 `server/data/server.sqlite3`。
- `PathConfig` 会自动确保 `config/` 和 `logs/` 存在。

## 测试与维护提示

- 修改桌面端共享逻辑后，至少运行 `python -m compileall -q src main.py`。
- 修改服务端接口后，运行 `cd server; pytest -q`。
- 修改管理后台后，运行 `cd admin; npm run build`。
- 修改任务名时要同步检查：
  - `TaskConfig.daily_tasks`
  - `TaskDefinitionConfig.definitions`
  - `@register_task(...)`
  - 已保存的用户配置
- 修改窗口类名、分辨率、模板路径时，要同时验证窗口绑定、截图和模板匹配。
- 长流程任务应保持可中断，不要引入不可控的长时间阻塞。
- 停止或关闭窗口时必须释放输入状态，避免后台窗口残留按键或鼠标按下。

## Git 与生成物注意事项

不要提交：

- `admin/node_modules/`
- `admin/dist/`
- `__pycache__/`
- `.pytest_cache/`
- `server/data/`
- `*.sqlite`、`*.sqlite3`、`*.db`
- `config/client_identity.json`
- `config/license_cache.json`
- `logs/`
- `.env`、`.env.*`

需要提交：

- 桌面端源码、任务配置源码和模板资源。
- `server/app/`、`server/tests/`、`server/requirements.txt`。
- `admin/src/`、`admin/package.json`、`admin/package-lock.json`、`admin/vite.config.js`、`admin/index.html`。
- 部署文档和维护文档。

## 打包方式

- 本项目桌面端打包方式使用 Nuitka。
- 维护打包脚本或发布流程时，应优先围绕 Nuitka 参数、资源包含、依赖收集和 Windows 可执行文件产物进行说明。
- 不要把 PyInstaller 作为当前默认打包方案；历史说明中如出现 PyInstaller，仅作为旧上下文或路径兼容说明处理。
