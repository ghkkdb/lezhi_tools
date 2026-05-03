# -*- coding: utf-8 -*-
"""
主界面模块
==========
提供任务配置、窗口选择、脚本运行等功能

模块结构：
    1. ClassicScriptUI: 主界面类

界面布局：
    - 顶部：功能导航栏
    - 中间：任务配置区
    - 底部：运行控制区（窗口选择 + 操作按钮 + 运行日志）
"""
import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton,
                             QTextEdit, QGroupBox, QStackedWidget,
                             QFrame, QMenuBar, QMenu,
                             QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtProperty
from PyQt5.QtGui import QFont, QCloseEvent
from src.config import config
from src.core.worker import ScriptWorker
from src.core.helpers import reset_game_state
from src.core.state_manager import StateManager, ButtonState
from src.core.config_manager import ConfigManager
from src.ui.widgets import WindowPicker, TabNavigationBar
from src.ui.panels.bottom_panel import BottomControlPanel
from src.ui.panels.log_panel import LogPanel
from src.ui.panels.task_list_panel import TaskListPanel
from src.ui.panels.task_config_panel import TaskConfigPanel
from src.ui.panels.multi_window_panel import MultiWindowControlPage
from src.ui.styles import ColorScheme
from src.utils.logger import LogManager, LogLevel, get_logger
from src.utils.win_api import release_tracked_inputs


class ClassicScriptUI(QMainWindow):
    """
    主界面类
    
    管理所有UI组件和交互逻辑
    
    属性：
        task_widgets: 任务复选框字典（已弃用，保留兼容性）
        window_picker: 窗口选择器实例
        worker: 后台任务线程
        task_list_panel: 任务列表面板
        task_config_panel: 任务配置面板
        state_manager: 状态管理器实例
        config_manager: 配置管理器实例
    """
    
    def __init__(self):
        """
        初始化主界面
        """
        super().__init__()
        self.setWindowTitle(config.app_name)
        self.setFixedSize(config.ui_width, config.ui_height)
        
        self.task_widgets = {}
        self.window_picker = WindowPicker()
        self.worker = None
        self._colors = ColorScheme.get_colors()
        self.task_list_panel = None
        self.task_config_panel = None
        self.multi_window_page = None
        
        # 获取状态管理器和配置管理器实例
        self.state_manager = StateManager.get_instance()
        self.config_manager = ConfigManager()
        
        self._setup_logging_base()
        self.init_ui()
        self._setup_logging_signal()
        
        # 连接状态管理器信号（必须在 init_ui 之后）
        self._connect_state_signals()
    
    def _connect_state_signals(self):
        """
        连接状态管理器信号到 UI 槽函数
        
        实现信号驱动的 UI 更新：
            - state_changed -> _update_button_ui
            - window_bound -> _on_window_bound
            - window_unbound -> _on_window_unbound
        """
        self.state_manager.state_changed.connect(self._update_button_ui)
        self.state_manager.window_bound.connect(self._on_window_bound)
        self.state_manager.window_unbound.connect(self._on_window_unbound)
    
    def _setup_logging_base(self):
        """
        初始化日志系统基础配置
        
        配置控制台和文件输出
        """
        log_config = config.get_logging_config()
        manager = LogManager.get_instance()
        
        if log_config['console']['enabled']:
            level = LogLevel[log_config['console']['level']]
            manager.setup_console(level, log_config['console']['use_color'])
        
        if log_config['file']['enabled']:
            level = LogLevel[log_config['file']['level']]
            manager.setup_file(
                log_config['file']['path'],
                level,
                log_config['file']['max_size'],
                log_config['file']['backup_count']
            )
        
        self.logger = get_logger('UI')
    
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
            ├── menu_bar (顶部菜单栏)
            ├── tab_nav (选项卡导航栏)
            ├── config_group (配置区域)
            └── bottom_group (运行控制区域) - 固定高度
        """
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_nav = TabNavigationBar()
        self.tab_nav.currentChanged.connect(self._on_tab_changed)

        self.config_group = QGroupBox()
        self.config_group.setContentsMargins(10, 12, 10, 8)
        self.config_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border_strong']};
                margin: 0px;
                padding: 0px;
            }}
        """)
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setContentsMargins(6, 6, 6, 6)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self._create_settings_page())
        self.pages.addWidget(self._create_daily_page())
        self.multi_window_page = MultiWindowControlPage(
            self._colors,
            unlock_callback=self.window_picker.unlock_window_size
        )
        self.multi_window_page.status_changed.connect(self._refresh_multi_status_log)
        if self.task_config_panel is not None:
            self.task_config_panel.config_list_changed.connect(
                self.multi_window_page.refresh_config_names
            )
        self.pages.addWidget(self.multi_window_page)
        self.pages.addWidget(self._create_placeholder_page("挂机任务"))
        self.pages.addWidget(self._create_placeholder_page("其他功能"))
        config_layout.addWidget(self.pages)

        bottom_group = QGroupBox()
        bottom_group.setFixedHeight(config.ui_layout["bottom_group_height"])
        bottom_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border_strong']};
                border-top: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_group)
        bottom_layout.setSpacing(config.ui_layout["bottom_spacing"])
        
        self.bottom_control_panel = BottomControlPanel(self._colors)
        self.bottom_control_panel.setFixedWidth(config.ui_sizes["left_ctrl_width"])
        
        self.log_panel = LogPanel(self._colors)
        self.log_panel.setFixedWidth(config.ui_sizes["log_width"])
        
        middle_widget = QWidget()
        middle_min_width = config.ui_layout["middle"]["min_width"]
        if middle_min_width > 0:
            middle_widget.setMinimumWidth(middle_min_width)
        middle_layout = QVBoxLayout(middle_widget)
        middle_margin = config.ui_layout["middle"]["margin"]
        middle_layout.setContentsMargins(*middle_margin)
        
        bottom_layout.addWidget(self.bottom_control_panel)
        bottom_layout.addWidget(middle_widget, stretch=1)
        bottom_layout.addWidget(self.log_panel)

        main_layout.addWidget(self.tab_nav)
        main_layout.addWidget(self.config_group)
        main_layout.addWidget(bottom_group)
        
        self.window_picker.window_picked.connect(self._on_window_picked)
        self.window_picker.pick_failed.connect(self._on_pick_failed)
        self.window_picker.pick_status.connect(self._on_pick_status)
        
        self.bottom_control_panel.sig_start_clicked.connect(self._run_script)
        self.bottom_control_panel.sig_pause_clicked.connect(self._on_pause_btn_clicked)
        self.bottom_control_panel.sig_unbind_clicked.connect(self._unbind_window)
        self.bottom_control_panel.sig_pick_released.connect(self._on_drag_released)

        self._apply_style()
    
    def _append_log(self, message: str):
        """
        追加日志消息并自动滚动到底部
        
        参数：
            message: 日志消息
        """
        if self.multi_window_page is not None:
            consumed_by_multi = self.multi_window_page.append_log(message)
            if consumed_by_multi and self.multi_window_page.bound_count > 1:
                self._refresh_multi_status_log()
                return

        self.log_panel.append_message(message)

    def _refresh_multi_status_log(self):
        """
        多开绑定多个窗口时，底部日志区显示窗口状态汇总。

        只有一个多开窗口时，底部日志仍可显示这个窗口的任务日志；
        多个窗口并发时，详细日志转到各自专属日志窗口，底部只保留概览。
        """
        if self.multi_window_page is None or self.multi_window_page.bound_count <= 1:
            return

        self.log_panel.clear()
        for line in self.multi_window_page.status_lines():
            self.log_panel.append_message(line)
    
    def _create_menu_bar(self):
        """
        创建经典Windows样式菜单栏
        
        菜单结构：
            - 文件: 退出
            - 编辑: 全选、清除日志
            - 帮助: 关于
        """
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        
        file_menu = QMenu("文件(&F)", self)
        exit_action = file_menu.addAction("退出(&X)")
        exit_action.triggered.connect(self.close)
        menubar.addMenu(file_menu)
        
        edit_menu = QMenu("编辑(&E)", self)
        select_all_action = edit_menu.addAction("全选(&A)")
        select_all_action.triggered.connect(self._select_all_tasks)
        clear_log_action = edit_menu.addAction("清除日志(&L)")
        clear_log_action.triggered.connect(self.log_panel.clear)
        menubar.addMenu(edit_menu)
        
        help_menu = QMenu("帮助(&H)", self)
        about_action = help_menu.addAction("关于(&A)")
        about_action.triggered.connect(self._show_about)
        menubar.addMenu(help_menu)
    
    def _select_all_tasks(self):
        """全选所有任务"""
        for task_item in config.daily_tasks:
            if isinstance(task_item, list):
                for task_name in task_item:
                    self.task_list_panel.set_task_checked(task_name, True)
            else:
                self.task_list_panel.set_task_checked(task_item, True)
    
    def _show_about(self):
        """显示关于对话框"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于", "游戏辅助工具 v1.0\n\n基于PyQt5开发的桌面辅助工具")

    def _on_tab_changed(self, index):
        """
        选项卡切换事件处理
        
        参数：
            index: 新选中的选项卡索引
        """
        self.pages.setCurrentIndex(index)

    def _create_settings_page(self):
        """
        创建基础设置页面
        
        返回：
            QWidget: 基础设置页面组件
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("基础设置功能开发中...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #999; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()
        
        return page

    def _create_placeholder_page(self, title):
        """
        创建占位页面
        
        参数：
            title: 页面标题
            
        返回：
            QWidget: 占位页面组件
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel(f"{title}功能开发中...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #999; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()
        
        return page

    def _create_daily_page(self):
        """
        创建日常任务配置页面
        
        使用左右分栏布局：
            - 左侧：任务列表滚动区域 (280px)
            - 右侧：任务配置滚动区域 (550px)

        返回：
            QWidget: 包含任务配置的页面组件
        """
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        self.task_list_panel = TaskListPanel(self._colors)
        self.task_config_panel = TaskConfigPanel(self.task_list_panel, self._colors)
        
        self.task_list_panel.task_checked.connect(self._on_task_checked)
        
        layout.addWidget(self.task_list_panel)
        layout.addWidget(self.task_config_panel, stretch=1)
        
        QTimer.singleShot(100, self.task_config_panel.load_last_config)
        
        return page
    
    def _on_task_checked(self, task_name: str, checked: bool):
        """
        任务勾选状态变化处理
        
        参数：
            task_name: 任务名称
            checked: 是否勾选
        """
        if checked and config.has_task_config(task_name):
            self.task_config_panel.scroll_to_task(task_name)

    def _run_script(self):
        """
        启动脚本执行

        流程：
            1. 验证窗口绑定
            2. 检查是否有正在运行的线程
            3. 提取被选中的任务
            4. 验证是否有选中任务
            5. 清空日志
            6. 创建并启动后台线程
        """
        if self._is_multi_window_page_active():
            self.logger.info("多开控制页请使用对应窗口行的开始按钮")
            return

        if not self.state_manager.bound_hwnd:
            self.logger.warning("请先通过瞄准镜按钮绑定游戏窗口")
            return
        
        if self.worker and self.worker.isRunning():
            self._toggle_run_state()
            return
        
        selected = self.task_list_panel.get_checked_tasks()
        
        if not selected:
            self.logger.warning("未勾选任何任务")
            return

        self.log_panel.clear()
        self.state_manager.set_button_state(ButtonState.RUNNING)
        
        task_params = self.config_manager.get_task_params(self.task_config_panel)
        
        self.worker = ScriptWorker(
            selected,
            self.state_manager.bound_hwnd,
            task_params,
            f"主控:{self.state_manager.bound_hwnd}"
        )
        self.worker.finished_sig.connect(self._on_task_finished)
        self.worker.task_completed.connect(self._on_task_completed)
        self.worker.start()

    def _stop_script(self):
        """
        停止脚本执行（已弃用，保留兼容性）
        """
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.logger.warning("正在停止运行...")

    def _toggle_run_state(self):
        """
        切换运行状态
        
        当任务正在运行时，点击主控按钮会触发停止操作。
        停止时禁用启动按钮，等待线程结束后恢复。
        """
        if self.worker and self.worker.isRunning():
            self.state_manager.set_button_state(ButtonState.STOPPING)
            self.worker.stop()
            self.logger.warning("正在停止运行...")

    def _on_pause_btn_clicked(self):
        """
        暂停按钮点击处理
        
        根据当前状态切换暂停/继续：
            - RUNNING -> PAUSED: 暂停任务
            - PAUSED -> RUNNING: 继续任务
        """
        if self._is_multi_window_page_active():
            self.logger.info("多开控制页请使用对应窗口行的暂停按钮")
            return

        current_state = self.state_manager.button_state
        if current_state == ButtonState.RUNNING:
            if self.worker:
                self.worker.pause()
            self.state_manager.set_button_state(ButtonState.PAUSED)
            self.logger.info("任务已暂停")
        elif current_state == ButtonState.PAUSED:
            if self.worker:
                self.worker.resume()
            self.state_manager.set_button_state(ButtonState.RUNNING)
            self.logger.info("任务已继续")

    def _update_button_ui(self, state: str):
        """
        更新按钮 UI（槽函数）
        
        委托给 BottomControlPanel.update_state 处理。
        由 StateManager.state_changed 信号触发。
        
        参数：
            state: 目标状态（ButtonState 枚举值）
        """
        self.bottom_control_panel.update_state(state, self.state_manager.bound_hwnd)

    def _on_task_completed(self, task_name: str, result):
        """
        处理任务完成信号
        
        参数：
            task_name: 任务名称
            result: True/False 或 {"子项名": True/False, ...}
        """
        if result is None:
            result = False
        
        if result is False:
            self.logger.warning(f"任务 [{task_name}] 执行失败或被中止")
            return
        
        if self.task_config_panel.has_config_checkboxes(task_name):
            self.task_config_panel.blockSignals(True)
            self.task_list_panel.blockSignals(True)
            try:
                if result is True:
                    self.task_config_panel.set_all_config_checkboxes(task_name, False)
                    self.logger.success(f"任务 [{task_name}] 执行完成")
                elif isinstance(result, dict):
                    self.task_config_panel.set_specific_config_checkboxes(task_name, result)
                    success_count = sum(1 for v in result.values() if v)
                    total_count = len(result)
                    self.logger.success(f"任务 [{task_name}] 执行完成 ({success_count}/{total_count})")
                
                if self.task_config_panel.are_all_config_checkboxes_unchecked(task_name):
                    self.task_list_panel.set_task_checked(task_name, False)
            finally:
                self.task_config_panel.blockSignals(False)
                self.task_list_panel.blockSignals(False)
        else:
            self.task_list_panel.blockSignals(True)
            try:
                if result is True or (isinstance(result, dict) and all(result.values())):
                    self.task_list_panel.set_task_checked(task_name, False)
                    self.logger.success(f"任务 [{task_name}] 执行完成")
            finally:
                self.task_list_panel.blockSignals(False)

    def _on_task_finished(self):
        """
        任务完成回调
        
        当后台线程完成时恢复按钮状态到初始状态
        """
        self.state_manager.set_button_state(ButtonState.IDLE)

    def closeEvent(self, event: QCloseEvent):
        """
        窗口关闭事件处理
        
        实现优雅退出：
            1. 检查是否有正在运行的 Worker 线程
            2. 如果有，调用 worker.stop() 并等待线程退出
            3. 最长等待 500ms，超时后强制接受关闭事件
            4. 释放输入资源
            5. 解锁窗口大小
            6. 清理输入状态
        
        Args:
            event: 关闭事件对象
        """
        bound_hwnd = self.state_manager.bound_hwnd
        if self.worker and self.worker.isRunning():
            self.logger.info("正在等待任务线程退出...")
            self.worker.stop()
            
            if not self.worker.wait(500):
                self.logger.warning("线程退出超时，强制关闭")
                self.worker.terminate()
                self.worker.wait()
            
            if bound_hwnd:
                release_tracked_inputs(bound_hwnd)

        if self.multi_window_page is not None:
            self.multi_window_page.shutdown()
        
        if bound_hwnd:
            self.window_picker.unlock_window_size(bound_hwnd)
        
        event.accept()

    def _on_drag_released(self, x, y):
        """
        拖动释放事件处理

        参数：
            x: 释放时的屏幕X坐标
            y: 释放时的屏幕Y坐标
        """
        self.bottom_control_panel.enable_pick_button(False)
        self.logger.debug(f"在位置 ({x}, {y}) 释放，开始识别窗口...")
        QTimer.singleShot(50, lambda: self.window_picker.pick_at_position(self))

    def _on_window_picked(self, hwnd, img):
        """
        窗口选择成功回调

        Args:
            hwnd: 窗口句柄
            img: 截取的区域图片
        """
        if self._is_multi_window_page_active():
            if self.multi_window_page.has_window(hwnd):
                self.bottom_control_panel.enable_pick_button(True)
                self.bottom_control_panel.set_window_unbound()
                QMessageBox.warning(self, "重复绑定", f"窗口句柄 {hwnd} 已在多开控制中绑定")
                self.logger.warning(f"窗口句柄 {hwnd} 已绑定，不能重复添加")
                return

            self.multi_window_page.add_window(hwnd, img)
            self.bottom_control_panel.set_window_unbound()
            self.bottom_control_panel.enable_pick_button(True)
            self.logger.success(f"多开控制已添加窗口，句柄: {hwnd}")
            self._refresh_multi_status_log()
            return

        self.state_manager.bind_window(hwnd)
        self.bottom_control_panel.set_window_bound(hwnd, img)
        self.logger.success(f"成功绑定窗口，句柄: {hwnd}")
    
    def _on_window_bound(self, hwnd: int):
        """
        窗口绑定成功槽函数
        
        由 StateManager.window_bound 信号触发。
        UI 更新已由 BottomControlPanel.set_window_bound 处理。
        
        参数：
            hwnd: 窗口句柄
        """
        pass

    def _on_pick_failed(self):
        """窗口选择失败回调"""
        self.bottom_control_panel.enable_pick_button(True)
        self.logger.error("窗口选择失败，请重试")

    def _on_pick_status(self, status):
        """
        状态更新回调

        参数：
            status: 状态消息字符串
        """
        self.logger.info(status)

    def _unbind_window(self):
        """
        解绑窗口
        
        流程：
            1. 检查是否有运行中的脚本，如有则停止
            2. 等待脚本线程退出
            3. 释放输入资源
            4. 解锁窗口大小
            5. 重置任务控制器状态
            6. 通过 StateManager 解绑窗口（会触发 window_unbound 信号）
        """
        if self._is_multi_window_page_active():
            self.logger.info("多开控制页请使用对应窗口行的解除按钮")
            return

        bound_hwnd = self.state_manager.bound_hwnd
        if self.worker and self.worker.isRunning():
            self.logger.warning("正在停止运行...")
            self.worker.stop()
            
            if not self.worker.wait(500):
                self.logger.warning("线程退出超时，强制终止")
                self.worker.terminate()
                self.worker.wait()
            
            if bound_hwnd:
                release_tracked_inputs(bound_hwnd)
            
        if bound_hwnd:
            self.window_picker.unlock_window_size(bound_hwnd)
            
        if self.worker:
            self.worker.controller.reset_all_events()
        
        self.state_manager.unbind_window()
        self.logger.info("已解除窗口绑定")
    
    def _on_window_unbound(self):
        """
        窗口解绑槽函数
        
        由 StateManager.window_unbound 信号触发。
        UI 更新已由 BottomControlPanel.set_window_unbound 处理。
        """
        self.bottom_control_panel.set_window_unbound()

    def _apply_style(self):
        """应用界面样式"""
        self.setStyleSheet(ColorScheme.generate_stylesheet())

    def _is_multi_window_page_active(self) -> bool:
        """当前是否处于多开控制页。"""
        return self.pages.currentWidget() is self.multi_window_page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 9))
    window = ClassicScriptUI()
    window.show()
    sys.exit(app.exec())
