# AGENTS.md

## 项目概览

本项目是一个基于 Python、PyQt5、Win32 API 和 OpenCV 的 Windows 桌面游戏辅助工具。程序通过 GUI 提供任务配置、窗口绑定、任务方案保存、多窗口独立控制、运行日志展示和图像模板识别等能力。

自动化任务主要依赖：

- 绑定目标游戏窗口句柄。
- 对目标窗口进行后台点击、按键、拖拽和截图。
- 使用 OpenCV 模板匹配识别界面元素。
- 通过任务注册表动态查找并执行任务函数。
- 通过任务控制器支持暂停、继续、停止和可中断等待。

入口文件是 `main.py`，启动后创建 `QApplication`，设置字体，并显示 `src.ui.ClassicScriptUI` 主窗口。

## 运行环境

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

启动：

```powershell
python main.py
```

常用检查：

```powershell
python -m compileall -q src main.py
python -m pytest tests\test_logger.py -q
```

注意：许多功能依赖 `pywin32/win32gui` 和真实 Windows 窗口环境，部分测试或功能在非 Windows 环境、无目标窗口环境下无法完整运行。

## 目录结构

```text
.
├── assets/                 # 图像模板资源，主要供 OpenCV 模板匹配使用
├── config/                 # 用户任务方案配置，如 user_task_configs.json
├── docs/                   # 项目文档、架构分析、变更记录和使用说明
├── logs/                   # 运行日志，默认 app.log
├── scripts/                # 调试脚本
├── src/
│   ├── config/             # 全局配置、窗口配置、任务定义、UI 配置、路径和日志配置
│   ├── core/               # 任务控制器、worker、任务注册表、日常任务逻辑、状态管理
│   ├── ui/                 # PyQt5 主窗口、面板、控件和样式
│   └── utils/              # Win32 操作、图像识别、缓存、日志、输入追踪等工具
├── tests/                  # 测试脚本
├── tools/                  # 辅助工具
├── main.py                 # 程序入口
└── requirements.txt        # 依赖清单
```

## 核心模块

### UI 层

- `src/ui/main_window.py`
  - 定义主窗口 `ClassicScriptUI`。
  - 负责页面切换、窗口绑定、任务启动、暂停、停止、日志显示和关闭清理。
  - 主页面包含基础设置、日常任务、多开控制、挂机任务和其他功能等标签页。

- `src/ui/panels/`
  - `bottom_panel.py`：底部窗口绑定和运行控制。
  - `log_panel.py`：日志显示。
  - `task_list_panel.py`：任务列表。
  - `task_config_panel.py`：任务参数配置动态渲染。
  - `multi_window_panel.py`：多窗口绑定、方案选择和独立执行控制。

- `src/ui/widgets/`
  - 包含准星按钮、窗口选择器、导航标签、解绑按钮等控件。

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
  - 已注册任务包括：每日一卦、课业任务、帮派任务、茶馆说书、每日可换、摇钱树、山河器、帮派捐献、日常副本、华山论剑1V1 等。
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

- `src/config/window_config.py`
  - 应用窗口和目标窗口配置。
  - 当前目标窗口类名配置为 `Notepad`，注释中保留过 `Messiah_Game`，开发或正式使用时需确认目标窗口类名。
  - 游戏窗口尺寸默认 `960x540`，UI 尺寸默认 `900x540`。

- `src/config/task_config.py`
  - 定义日常任务列表、答题坐标权重、帮派按钮坐标、摇钱树选项等。

- `src/config/task_definition_config.py`
  - 定义任务配置 UI 的字段结构。
  - 支持 `dropdown`、`text`、`number`、`checkbox`、`spinbox`、`label`、`row`、`group`、`columns` 等控件类型。
  - 支持通过 `extends` 复用共享配置，例如组队配置可被日常副本、副本悬赏继承。

- `src/config/path_config.py`
  - 统一管理资源、配置、日志路径。
  - 支持开发环境和 PyInstaller 打包环境。

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

- `src/utils/input_tracker.py`
  - 追踪后台输入按下状态，配合窗口关闭、停止任务时释放输入。

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

模板匹配准确率会受窗口分辨率、DPI 缩放、游戏 UI 变化和模板图片版本影响。当前默认游戏窗口尺寸是 `960x540`。

## 配置和数据文件

- 用户方案保存在 `config/user_task_configs.json`。
- 日志默认写入 `logs/app.log`。
- `PathConfig` 会自动确保 `config/` 和 `logs/` 存在。
- 打包后资源路径和可写数据路径会分离：资源使用 `_MEIPASS` 或可执行文件路径，配置和日志写入可执行文件所在目录。

## 测试与维护提示

- 代码中有较多 Windows API 和 GUI 依赖，单元测试应尽量拆分纯逻辑部分。
- 修改任务名时要同步检查：
  - `TaskConfig.daily_tasks`
  - `TaskDefinitionConfig.definitions`
  - `@register_task(...)`
  - 已保存的用户配置
- 修改窗口类名、分辨率、模板路径时，要同时验证窗口绑定、截图和模板匹配。
- 长流程任务应保持可中断，不要引入不可控的长时间阻塞。
- 停止或关闭窗口时必须释放输入状态，避免后台窗口残留按键或鼠标按下。

## 已知现状

- `README.md` 和源码注释内容以中文为主，但在当前 PowerShell 输出中有编码显示异常；编辑时应保持文件编码为 UTF-8。
- 仓库中存在 `__pycache__` 和运行日志等生成文件。
- 根目录有一些临时或试验脚本，例如 `replace_sleep.py`、`temp_replace.py`、`test_dome.py`。
- 当前 git 工作区在读取时没有发现未提交改动。
