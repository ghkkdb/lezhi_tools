# lezhi_tools

基于 Python、PyQt5、Win32 API 和 OpenCV 的 Windows 桌面游戏辅助工具。

项目提供窗口绑定、任务方案配置、自动化任务执行、多窗口独立控制、日志输出和图像模板识别等能力。任务主要通过后台窗口输入与模板匹配推进，适用于多开日常任务管理场景。

## 功能概览

- 桌面 GUI：基于 PyQt5 的任务配置与运行控制界面。
- 窗口绑定：通过瞄准镜拖拽绑定目标游戏窗口，并锁定窗口尺寸。
- 日常任务：支持每日可换、山河器、每日一卦、茶馆说书、课业任务、帮派任务、帮派捐献、摇钱树、日常副本等任务入口。
- 任务方案：可保存、加载和删除不同任务方案。
- 多开控制：支持绑定多个窗口，为每个窗口选择已保存任务方案，并独立开始、暂停、继续和停止。
- 独立日志：多开任务可为每个窗口弹出专属日志窗口，底部日志区在多窗口场景下显示状态汇总。
- 图像识别：基于 OpenCV 模板匹配，配合截图帧缓存和模板缓存减少重复 I/O。

## 项目结构

```text
.
├── assets/                 # 模板图片等资源
├── config/                 # 用户任务配置文件
├── docs/                   # 项目文档、架构分析和变更记录
├── scripts/                # 调试脚本
├── src/
│   ├── config/             # 全局配置、任务定义、UI配置、路径配置
│   ├── core/               # 任务控制器、worker、任务注册表、任务逻辑
│   ├── ui/                 # PyQt5 主窗口、面板和控件
│   └── utils/              # Win32、图像识别、日志、缓存等工具
├── tests/                  # 测试脚本
├── tools/                  # 辅助工具
├── main.py                 # 程序入口
└── requirements.txt        # Python 依赖
```

## 环境要求

- Windows
- Python 3.10 推荐
- 目标游戏窗口类名需与配置一致
- 依赖见 `requirements.txt`

主要依赖：

```text
PyQt5
opencv-python
Pillow
numpy
pywin32
```

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果使用 Conda：

```powershell
conda create -n lezhi_tools python=3.10
conda activate lezhi_tools
pip install -r requirements.txt
```

## 启动

```powershell
python main.py
```

## 基本使用

1. 打开程序。
2. 在“日常任务”中勾选任务并配置参数。
3. 保存任务方案。
4. 使用底部瞄准镜绑定游戏窗口。
5. 点击开始执行。

多开流程：

1. 先在“日常任务”页保存一个或多个任务方案。
2. 切换到“多开控制”页。
3. 使用底部瞄准镜依次绑定多个非重复窗口。
4. 每个窗口行选择任务方案。
5. 分别点击对应窗口的开始或暂停按钮。

## 测试与检查

语法检查：

```powershell
python -m compileall -q src main.py
```

局部测试示例：

```powershell
python -m pytest tests\test_logger.py -q
```

注意：部分测试和功能依赖 `pywin32/win32gui`，需要在正确的 Windows Python 环境中运行。

## 开发说明

- 新任务应通过 `@register_task("任务名称")` 注册。
- UI 任务名称、任务配置定义和注册名称必须保持一致。
- 自动化任务中应优先使用 `task_controller.smart_sleep()`，避免长时间不可中断的 `time.sleep()`。
- 多开 worker 使用独立任务控制器，避免不同窗口的暂停、停止状态互相影响。

## 备注

本项目包含大量图像模板资源。模板文件、窗口分辨率、UI 缩放和游戏界面变化都会影响识别准确率。
