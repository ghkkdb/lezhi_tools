# main_window.py 解耦重构分析报告

> 本报告提取实现 MVC 解耦重构最关键的 4 个基础部分，不修改原始逻辑，仅做结构化展示。

---

## 一、依赖与初始化 (Imports & Initialization)

### 1.1 所有 import 语句

```python
# 标准库
import sys
import time
import win32gui
from pathlib import Path

# PyQt5 核心组件
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit, QGroupBox, QStackedWidget,
    QFrame, QGraphicsOpacityEffect, QMenuBar, QMenu,
    QScrollArea, QComboBox, QInputDialog, QMessageBox,
    QSizePolicy, QLineEdit, QSpinBox
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, 
    QPropertyAnimation, QEasingCurve, pyqtProperty
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QCloseEvent

# 项目内部模块
from src.config import config
from src.core import (
    task_gua, task_keye, task_bangpai, task_chaguan, 
    task_bangpai_yao, task_shanheqi, task_meiri_kehuan,
    task_controller, TaskStoppedException, ContextExpiredException, 
    InvalidWindowHandleException, reset_game_state
)
from src.ui.widgets import CrosshairButton, UnbindButton, WindowPicker
from src.utils.logger import LogManager, LogLevel, get_logger
from src.utils.win_api import release_tracked_inputs
```

### 1.2 主窗口类 `__init__` 方法

```python
class ClassicScriptUI(QMainWindow):
    """
    主界面类
    
    管理所有UI组件和交互逻辑
    """
    
    def __init__(self):
        super().__init__()
        
        # 基础配置
        self.setWindowTitle(config.app_name)
        self.setFixedSize(config.ui_width, config.ui_height)
        
        # 状态变量初始化
        self.task_widgets = {}              # 任务复选框字典（已弃用）
        self.bound_hwnd = None              # 当前绑定的窗口句柄
        self.window_picker = WindowPicker() # 窗口选择器实例
        self.worker = None                  # 后台任务线程
        self._colors = ColorScheme.get_colors()
        self.task_list_panel = None         # 任务列表面板
        self.task_config_panel = None       # 任务配置面板
        self._button_state = ButtonState.IDLE
        
        # 初始化流程
        self._setup_logging_base()    # 1. 日志系统基础配置
        self.init_ui()                # 2. 初始化UI
        self._setup_logging_signal()  # 3. 日志信号处理器
```

### 1.3 初始化方法定义头部

```python
def _setup_logging_base(self):
    """
    初始化日志系统基础配置
    配置控制台和文件输出
    """
    log_config = config.get_logging_config()
    manager = LogManager.get_instance()
    # ... 配置控制台和文件日志 ...

def _setup_logging_signal(self):
    """
    初始化日志信号处理器
    在UI创建后调用，连接到日志显示区域
    """
    log_config = config.get_logging_config()
    if log_config['signal']['enabled']:
        level = LogLevel[log_config['signal']['level']]
        LogManager.get_instance().setup_signal(self._append_log, level)

def init_ui(self):
    """
    初始化用户界面
    
    布局结构：
        main_layout (垂直)
        ├── tab_nav (选项卡导航栏)
        ├── config_group (配置区域)
        └── bottom_group (运行控制区域)
    """
    # ... UI 组装代码 ...
```

---

## 二、核心 UI 布局骨架 (UI Layout Skeleton)

### 2.1 布局组装主干代码（剔除样式）

```python
def init_ui(self):
    # === 主容器 ===
    main_widget = QWidget()
    self.setCentralWidget(main_widget)
    main_layout = QVBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # === 顶部导航栏 ===
    self.tab_nav = TabNavigationBar()
    self.config_group = QGroupBox()
    config_layout = QVBoxLayout(self.config_group)
    
    # === 中间内容区（堆栈布局）===
    self.pages = QStackedWidget()
    self.pages.addWidget(self._create_daily_page())      # 日常任务页
    self.pages.addWidget(self._create_placeholder_page("副本任务"))
    self.pages.addWidget(self._create_placeholder_page("挂机任务"))
    self.pages.addWidget(self._create_placeholder_page("其他功能"))
    config_layout.addWidget(self.pages)

    # === 底部控制区 ===
    bottom_group = QGroupBox()
    bottom_layout = QHBoxLayout(bottom_group)
    
    # --- 左侧控制区 ---
    left_widget = QWidget()
    left_layout = QGridLayout(left_widget)
    
    # 第一行：瞄准镜 | 窗口句柄 | 开始按钮
    self.pick_btn = CrosshairButton()
    left_layout.addWidget(self.pick_btn, 0, 0)
    
    self.hwnd_label = QLabel("未绑定窗口")
    left_layout.addWidget(self.hwnd_label, 0, 1)
    
    self.start_btn = QPushButton("开始执行")
    left_layout.addWidget(self.start_btn, 0, 2)
    
    # 第二行：解绑按钮 | 预览标签 | 暂停按钮
    self.unbind_btn = UnbindButton()
    left_layout.addWidget(self.unbind_btn, 1, 0)
    
    self.preview_label = QLabel("未绑定角色")
    left_layout.addWidget(self.preview_label, 1, 1)
    
    self.stop_btn = QPushButton("暂停运行")
    left_layout.addWidget(self.stop_btn, 1, 2)

    # --- 中间弹性区 ---
    middle_widget = QWidget()
    middle_layout = QVBoxLayout(middle_widget)

    # --- 右侧日志区 ---
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    
    self.log_area = QTextEdit()
    self.log_area.setReadOnly(True)
    right_layout.addWidget(self.log_area)

    # === 组装底部布局 ===
    bottom_layout.addWidget(left_widget)
    bottom_layout.addWidget(middle_widget, stretch=1)
    bottom_layout.addWidget(right_widget)

    # === 组装主布局 ===
    main_layout.addWidget(self.tab_nav)
    main_layout.addWidget(self.config_group)
    main_layout.addWidget(bottom_group)
```

### 2.2 UI 布局 ASCII Art 草图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ClassicScriptUI                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [日常任务]  [副本任务]  [挂机任务]  [其他功能]   ← TabNavigationBar │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        config_group                                │  │
│  │  ┌──────────────────┐  ┌────────────────────────────────────────┐ │  │
│  │  │  TaskListPanel   │  │        TaskConfigPanel                 │ │  │
│  │  │  ┌────────────┐  │  │  ┌──────────────────────────────────┐  │ │  │
│  │  │  │ 任务列表   │  │  │  │ 任务配置管理区                   │  │ │  │
│  │  │  │ ☐ 每日一卦 │  │  │  │ [配置方案▼] [保存] [删除]        │  │ │  │
│  │  │  │ ☐ 课业任务 │  │  │  └──────────────────────────────────┘  │ │  │
│  │  │  │ ☐ 帮派任务 │  │  │  ┌──────────────────────────────────┐  │ │  │
│  │  │  │ ☐ 茶馆说书 │  │  │  │ 【每日一卦】配置区               │  │ │  │
│  │  │  │ ☐ 摇钱树   │  │  │  │ 卦象选择: [下拉框]               │  │ │  │
│  │  │  │ ☐ 山河器   │  │  │  └──────────────────────────────────┘  │ │  │
│  │  │  │ ☐ 每日可换 │  │  │  ┌──────────────────────────────────┐  │ │  │
│  │  │  └────────────┘  │  │  │ 【课业任务】配置区               │  │ │  │
│  │  │  (280px 宽)      │  │  │ ...                              │  │ │  │
│  │  └──────────────────┘  │  └──────────────────────────────────┘  │ │  │
│  │                        │         (弹性宽度)                       │ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         bottom_group                               │  │
│  │  ┌─────────────────────┐  ┌──────────┐  ┌───────────────────────┐ │  │
│  │  │     left_widget     │  │ (弹性区) │  │     right_widget      │ │  │
│  │  │  ┌────┬──────┬────┐ │  │          │  │  ┌─────────────────┐  │ │  │
│  │  │  │瞄准│句柄  │开始│ │  │          │  │  │                 │  │ │  │
│  │  │  │镜  │标签  │按钮│ │  │          │  │  │   log_area      │  │ │  │
│  │  │  ├────┼──────┼────┤ │  │          │  │  │   (日志显示)    │  │ │  │
│  │  │  │解绑│预览  │暂停│ │  │          │  │  │                 │  │ │  │
│  │  │  │按钮│标签  │按钮│ │  │          │  │  │                 │  │ │  │
│  │  │  └────┴──────┴────┘ │  │          │  │  └─────────────────┘  │ │  │
│  │  │     (固定宽度)       │  │          │  │      (固定宽度)       │ │  │
│  │  └─────────────────────┘  └──────────┘  └───────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、信号与槽的绑定逻辑 (Signals & Slots)

### 3.1 所有 `.connect()` 绑定代码

```python
# ========== 导航栏信号 ==========
self.tab_nav.currentChanged.connect(self._on_tab_changed)

# ========== 任务列表信号 ==========
self.task_list_panel.task_checked.connect(self._on_task_checked)

# ========== 按钮信号 ==========
self.pick_btn.released_at.connect(self._on_drag_released)
self.start_btn.clicked.connect(self._run_script)
self.unbind_btn.clicked.connect(self._unbind_window)
self.stop_btn.clicked.connect(self._on_pause_btn_clicked)

# ========== 窗口选择器信号 ==========
self.window_picker.window_picked.connect(self._on_window_picked)
self.window_picker.pick_failed.connect(self._on_pick_failed)
self.window_picker.pick_status.connect(self._on_pick_status)

# ========== Worker 线程信号 ==========
self.worker.finished_sig.connect(self._on_task_finished)
self.worker.task_completed.connect(self._on_task_completed)

# ========== TaskConfigPanel 内部信号 ==========
self.config_combo.currentTextChanged.connect(self._on_config_selected)
self.config_combo.currentIndexChanged.connect(self._on_config_index_changed)
self.save_btn.clicked.connect(self._on_save_config)
self.delete_btn.clicked.connect(self._on_delete_config)

# ========== TabNavigationBar 内部信号 ==========
tab.clicked.connect(lambda checked, idx=index: self._on_tab_clicked(idx))

# ========== TaskListPanel 内部信号 ==========
cb.stateChanged.connect(lambda state, name=task_name: self._on_task_checked(name, state))
```

### 3.2 槽函数定义头部

```python
# ========== 导航相关 ==========
def _on_tab_changed(self, index):
    """选项卡切换事件处理"""
    self.pages.setCurrentIndex(index)

# ========== 任务勾选相关 ==========
def _on_task_checked(self, task_name: str, checked: bool):
    """任务勾选状态变化处理"""
    if checked and config.has_task_config(task_name):
        self.task_config_panel.scroll_to_task(task_name)

# ========== 窗口绑定相关 ==========
def _on_drag_released(self, x, y):
    """拖动释放事件处理"""
    self.pick_btn.setEnabled(False)
    self.logger.debug(f"在位置 ({x}, {y}) 释放，开始识别窗口...")
    QTimer.singleShot(50, lambda: self.window_picker.pick_at_position(self))

def _on_window_picked(self, hwnd, img):
    """窗口选择成功回调"""
    self.bound_hwnd = hwnd
    self.hwnd_label.setText(f"{hwnd}")
    # ... 更新 UI 状态 ...

def _on_pick_failed(self):
    """窗口选择失败回调"""
    self.pick_btn.setEnabled(True)
    self.logger.error("窗口选择失败，请重试")

def _on_pick_status(self, status):
    """状态更新回调"""
    self.logger.info(status)

def _unbind_window(self):
    """解绑窗口"""
    # ... 停止线程、释放资源、重置状态 ...

# ========== 任务执行相关 ==========
def _run_script(self):
    """启动脚本执行"""
    if not self.bound_hwnd:
        self.logger.warning("请先通过瞄准镜按钮绑定游戏窗口")
        return
    # ... 创建并启动 Worker 线程 ...

def _toggle_run_state(self):
    """切换运行状态（停止）"""
    if self.worker and self.worker.isRunning():
        self._set_button_state(ButtonState.STOPPING)
        self.worker.stop()

def _on_pause_btn_clicked(self):
    """暂停按钮点击处理"""
    if self._button_state == ButtonState.RUNNING:
        task_controller.pause()
        self._set_button_state(ButtonState.PAUSED)
    elif self._button_state == ButtonState.PAUSED:
        task_controller.resume()
        self._set_button_state(ButtonState.RUNNING)

# ========== 任务完成回调 ==========
def _on_task_completed(self, task_name: str, result):
    """处理任务完成信号"""
    # ... 更新 UI 勾选状态 ...

def _on_task_finished(self):
    """任务完成回调，恢复按钮状态"""
    self._set_button_state(ButtonState.IDLE)

# ========== 日志相关 ==========
def _append_log(self, message: str):
    """追加日志消息并自动滚动到底部"""
    self.log_area.append(message)
    scrollbar = self.log_area.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())

# ========== 按钮状态管理 ==========
def _set_button_state(self, state: str):
    """设置按钮状态，更新文字、样式和启用状态"""
    self._button_state = state
    # ... 根据状态更新 UI ...
```

---

## 四、核心线程生命周期 (Worker Thread Lifecycle)

### 4.1 ScriptWorker 类定义

```python
class ScriptWorker(QThread):
    """
    后台脚本执行线程
    
    用于在后台执行用户选择的任务，避免阻塞UI线程
    """
    
    # 信号定义
    finished_sig = pyqtSignal()                    # 任务完成信号
    task_completed = pyqtSignal(str, object)       # 单任务完成信号

    def __init__(self, selected_tasks, hwnd, task_params=None):
        """
        初始化线程
        
        参数：
            selected_tasks: 用户选择的任务名称列表
            hwnd: 窗口句柄
            task_params: 任务参数字典（可选）
        """
        super().__init__()
        self.tasks = selected_tasks
        self.hwnd = hwnd
        self.task_params = task_params or {}
        self.logger = get_logger('ScriptWorker')

    def run(self):
        """
        线程执行入口
        
        流程：
            1. 重置控制器状态
            2. 遍历执行选中的任务
            3. 捕获各类异常并处理
            4. 清理输入状态并发送完成信号
        """
        task_controller.reset_all_events()
        
        try:
            for task_name in self.tasks:
                # 检查窗口有效性
                if not win32gui.IsWindow(self.hwnd):
                    raise InvalidWindowHandleException("游戏窗口已关闭或无效")
                
                # 检查控制信号
                task_controller.check_status()
                
                # 任务映射表
                logic_map = {
                    "每日一卦": task_gua,
                    "课业任务": task_keye,
                    "帮派任务": task_bangpai,
                    "茶馆说书": task_chaguan,
                    "摇钱树": task_bangpai_yao,
                    "山河器": task_shanheqi,
                    "每日可换": task_meiri_kehuan
                }
                
                # 执行任务并发送完成信号
                if task_name in logic_map:
                    task_func = logic_map[task_name]
                    params = self.task_params.get(task_name, {})
                    result = task_func(self.hwnd, **params)
                    self.task_completed.emit(task_name, result)
                    
        except TaskStoppedException:
            self.logger.warning("任务被用户中止")
            
        except Exception as e:
            self.logger.error(f"任务执行错误: {str(e)}")
            
        finally:
            release_tracked_inputs(self.hwnd)
            self.finished_sig.emit()

    def stop(self):
        """停止任务执行"""
        task_controller.stop()
```

### 4.2 Worker 实例化与启动

```python
def _run_script(self):
    """启动脚本执行"""
    # ... 前置检查 ...
    
    # 清空日志
    self.log_area.clear()
    
    # 更新按钮状态
    self._set_button_state(ButtonState.RUNNING)
    
    # 获取任务参数
    task_params = self._get_task_params_for_execution()
    
    # 创建 Worker 实例
    self.worker = ScriptWorker(selected, self.bound_hwnd, task_params)
    
    # 连接信号
    self.worker.finished_sig.connect(self._on_task_finished)
    self.worker.task_completed.connect(self._on_task_completed)
    
    # 启动线程
    self.worker.start()
```

### 4.3 信号接收与生命周期管理

```python
# ========== 信号接收 ==========

def _on_task_completed(self, task_name: str, result):
    """处理任务完成信号（UI线程执行）"""
    # 更新任务勾选状态
    # 记录日志

def _on_task_finished(self):
    """所有任务完成回调（UI线程执行）"""
    self._set_button_state(ButtonState.IDLE)

# ========== 生命周期管理 ==========

def _toggle_run_state(self):
    """停止 Worker"""
    if self.worker and self.worker.isRunning():
        self._set_button_state(ButtonState.STOPPING)
        self.worker.stop()  # 发送停止信号

def closeEvent(self, event: QCloseEvent):
    """窗口关闭事件，优雅退出"""
    if self.worker and self.worker.isRunning():
        task_controller.stop()
        
        # 等待线程退出（最多500ms）
        if not self.worker.wait(500):
            self.worker.terminate()  # 超时强制终止
            self.worker.wait()
        
        release_tracked_inputs(self.bound_hwnd)
    
    event.accept()
```

---

## 五、解耦建议

### 5.1 当前问题

| 问题 | 描述 | 影响 |
|------|------|------|
| **职责过多** | ClassicScriptUI 包含 UI、业务、配置、线程管理 | 难以维护和测试 |
| **信号绑定分散** | 信号绑定散落在 init_ui 各处 | 难以追踪信号流 |
| **状态管理混乱** | 按钮状态、任务状态、窗口状态混杂 | 状态转换不清晰 |
| **硬编码映射** | logic_map 任务映射硬编码在 Worker 中 | 扩展性差 |

### 5.2 MVC 解耦方向

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MVC 解耦建议                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │     Model       │    │    Controller   │    │       View      │ │
│  │                 │    │                 │    │                 │ │
│  │  - TaskState    │◄───│  - TaskExecutor │───►│  - MainWindow   │ │
│  │  - WindowState  │    │  - StateManager │    │  - TaskListPanel│ │
│  │  - ConfigState  │    │  - SignalRouter │    │  - TaskConfig   │ │
│  │                 │    │                 │    │  - BottomPanel  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                     │
│  建议拆分文件：                                                      │
│  - views/main_window.py      (仅 UI 布局)                           │
│  - views/panels/             (各面板组件)                            │
│  - controllers/task_ctrl.py  (任务执行控制)                          │
│  - controllers/state_ctrl.py (状态管理)                              │
│  - models/task_model.py      (任务数据模型)                          │
│  - models/config_model.py    (配置数据模型)                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 优先拆分项

| 优先级 | 拆分项 | 目标文件 | 预期收益 |
|--------|--------|----------|----------|
| **P0** | TaskListPanel | views/panels/task_list_panel.py | 已独立，仅需迁移 |
| **P0** | TaskConfigPanel | views/panels/task_config_panel.py | 已独立，仅需迁移 |
| **P1** | ScriptWorker | workers/script_worker.py | 分离线程逻辑 |
| **P1** | ButtonState + 状态管理 | controllers/state_manager.py | 集中状态管理 |
| **P2** | 信号绑定 | controllers/signal_router.py | 集中信号路由 |
| **P2** | 任务映射 logic_map | models/task_registry.py | 可扩展注册表 |

---

**报告版本**: v1.0  
**分析日期**: 2026-03-09  
**源文件**: [main_window.py](file:///e:/Tare_project/YMJH/src/ui/main_window.py) (2424 行)
