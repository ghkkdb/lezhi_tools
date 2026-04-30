# -*- coding: utf-8 -*-
"""
底部控制面板组件
================
提供窗口绑定、任务执行控制等功能的独立面板组件。

核心功能：
    - 窗口绑定控制（瞄准镜按钮、解绑按钮）
    - 任务执行控制（开始/暂停按钮）
    - 状态显示（窗口句柄、预览图）

信号：
    - sig_start_clicked: 开始按钮点击信号
    - sig_pause_clicked: 暂停按钮点击信号
    - sig_unbind_clicked: 解绑按钮点击信号
    - sig_pick_released: 瞄准镜释放信号 (x, y)

使用示例：
    panel = BottomControlPanel(colors)
    panel.sig_start_clicked.connect(self._run_script)
    panel.update_state(ButtonState.RUNNING, hwnd)
"""
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

from src.config import config
from src.ui.widgets import CrosshairButton, UnbindButton
from src.core.state_manager import ButtonState


class BottomControlPanel(QWidget):
    """
    底部控制面板组件
    
    提供窗口绑定、任务执行控制等功能。
    面板内部不处理业务逻辑，所有交互通过信号向上传递。
    
    属性：
        pick_btn: 瞄准镜按钮
        unbind_btn: 解绑按钮
        start_btn: 开始/停止按钮
        stop_btn: 暂停/继续按钮
        hwnd_label: 窗口句柄标签
        preview_label: 预览标签
    
    信号：
        sig_start_clicked: 开始按钮点击信号
        sig_pause_clicked: 暂停按钮点击信号
        sig_unbind_clicked: 解绑按钮点击信号
        sig_pick_released: 瞄准镜释放信号 (x, y)
    """
    
    sig_start_clicked = pyqtSignal()
    sig_pause_clicked = pyqtSignal()
    sig_unbind_clicked = pyqtSignal()
    sig_pick_released = pyqtSignal(int, int)
    
    def __init__(self, colors: Dict[str, str], parent=None):
        """
        初始化底部控制面板
        
        参数：
            colors: 颜色方案字典
            parent: 父组件
        """
        super().__init__(parent)
        self._colors = colors
        self._setup_ui()
    
    def _setup_ui(self):
        """
        设置 UI 布局
        
        布局结构：
            QGridLayout
            ├── [0,0] pick_btn (瞄准镜)
            ├── [0,1] hwnd_label (窗口句柄)
            ├── [0,2] start_btn (开始按钮)
            ├── [1,0] unbind_btn (解绑按钮)
            ├── [1,1] preview_label (预览标签)
            └── [1,2] stop_btn (暂停按钮)
        """
        layout = QGridLayout(self)
        
        left_margin = config.ui_layout["left"]["margin"]
        layout.setContentsMargins(*left_margin)
        layout.setHorizontalSpacing(config.ui_layout["left"]["h_spacing"])
        layout.setVerticalSpacing(config.ui_layout["left"]["v_spacing"])
        
        row_height = config.ui_layout["left"]["row_height"]
        row_count = config.ui_layout["left"]["row_count"]
        for i in range(row_count):
            layout.setRowMinimumHeight(i, row_height)
        
        layout.setColumnMinimumWidth(0, config.ui_sizes["pick_btn"][0])
        layout.setColumnMinimumWidth(1, config.ui_sizes["hwnd_label"][0])
        layout.setColumnMinimumWidth(2, config.ui_sizes["start_btn"][0])
        
        # 瞄准镜按钮
        self.pick_btn = CrosshairButton()
        self.pick_btn.released_at.connect(self._on_pick_released)
        layout.addWidget(self.pick_btn, 0, 0)
        
        # 窗口句柄标签
        self.hwnd_label = QLabel("未绑定窗口")
        self.hwnd_label.setAlignment(Qt.AlignCenter)
        hwnd_size = config.ui_sizes["hwnd_label"]
        self.hwnd_label.setFixedSize(*hwnd_size)
        self._update_hwnd_label_style(None)
        layout.addWidget(self.hwnd_label, 0, 1)
        
        # 开始按钮
        self.start_btn = QPushButton("开始执行")
        self.start_btn.clicked.connect(self.sig_start_clicked.emit)
        start_size = config.ui_sizes["start_btn"]
        self.start_btn.setFixedSize(*start_size)
        layout.addWidget(self.start_btn, 0, 2)
        
        # 解绑按钮
        self.unbind_btn = UnbindButton()
        self.unbind_btn.clicked.connect(self.sig_unbind_clicked.emit)
        self.unbind_btn.setEnabled(False)
        layout.addWidget(self.unbind_btn, 1, 0)
        
        # 预览标签
        self.preview_label = QLabel("未绑定角色")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_size = config.ui_sizes["preview_label"]
        self.preview_label.setFixedSize(*preview_size)
        self.preview_label.setStyleSheet(
            f"background-color: {self._colors['surface_elevated']}; "
            f"border: 1px solid {self._colors['border']}; border-radius: 4px; "
            f"color: {self._colors['text_secondary']}; font-size: 9pt;"
        )
        layout.addWidget(self.preview_label, 1, 1)
        
        # 暂停按钮
        self.stop_btn = QPushButton("暂停运行")
        self.stop_btn.clicked.connect(self.sig_pause_clicked.emit)
        self.stop_btn.setEnabled(False)
        stop_size = config.ui_sizes["stop_btn"]
        self.stop_btn.setFixedSize(*stop_size)
        layout.addWidget(self.stop_btn, 1, 2)
        
        # 第三行占位
        row3_placeholder = QLabel("")
        row3_placeholder.setFixedHeight(row_height)
        layout.addWidget(row3_placeholder, row_count - 1, 0, 1, 3)
    
    def _on_pick_released(self, x: int, y: int):
        """
        瞄准镜释放事件处理
        
        参数：
            x: 屏幕 X 坐标
            y: 屏幕 Y 坐标
        """
        self.pick_btn.setEnabled(False)
        self.sig_pick_released.emit(x, y)
    
    def update_state(self, button_state: str, bound_hwnd: Optional[int]):
        """
        更新面板状态
        
        根据按钮状态和窗口绑定状态更新 UI 显示。
        
        参数：
            button_state: 按钮状态（ButtonState 枚举值）
            bound_hwnd: 窗口句柄（None 表示未绑定）
        """
        self._update_button_ui(button_state)
        self._update_hwnd_label_style(bound_hwnd)
    
    def _update_button_ui(self, state: str):
        """
        更新按钮 UI
        
        参数：
            state: 按钮状态
        """
        if state == ButtonState.IDLE:
            self.start_btn.setText("开始执行")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet("")
            self.stop_btn.setText("暂停运行")
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet("")
            self.pick_btn.set_disabled(False)
            self.unbind_btn.set_running(False)
            
        elif state == ButtonState.RUNNING:
            self.start_btn.setText("强制停止")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(
                f"background-color: {self._colors['danger']}; color: white;"
            )
            self.stop_btn.setText("暂停运行")
            self.stop_btn.setEnabled(True)
            self.stop_btn.setStyleSheet("")
            self.pick_btn.set_disabled(True)
            self.unbind_btn.set_running(True)
            
        elif state == ButtonState.PAUSED:
            self.start_btn.setText("强制停止")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(
                f"background-color: {self._colors['danger']}; color: white;"
            )
            self.stop_btn.setText("继续运行")
            self.stop_btn.setEnabled(True)
            self.stop_btn.setStyleSheet(
                f"background-color: {self._colors['success']}; color: white;"
            )
            self.pick_btn.set_disabled(True)
            self.unbind_btn.set_running(True)
            
        elif state == ButtonState.STOPPING:
            self.start_btn.setText("正在停止...")
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet(
                f"background-color: {self._colors['secondary']}; color: white;"
            )
            self.stop_btn.setText("暂停运行")
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet("")
            self.pick_btn.set_disabled(True)
    
    def _update_hwnd_label_style(self, hwnd: Optional[int]):
        """
        更新窗口句柄标签样式
        
        参数：
            hwnd: 窗口句柄
        """
        if hwnd:
            self.hwnd_label.setText(f"{hwnd}")
            self.hwnd_label.setStyleSheet(
                f"font-weight: bold; color: {self._colors['success']}; font-size: 9pt; "
                f"border: 1px solid {self._colors['success']}; "
                f"background-color: {self._colors['surface_elevated']};"
            )
        else:
            self.hwnd_label.setText("未绑定窗口")
            self.hwnd_label.setStyleSheet(
                f"font-weight: bold; color: {self._colors['text_secondary']}; font-size: 9pt; "
                f"border: 1px solid {self._colors['border']}; border-radius: 4px; "
                f"background-color: {self._colors['surface']};"
            )
    
    def set_window_bound(self, hwnd: int, img=None):
        """
        设置窗口绑定状态
        
        参数：
            hwnd: 窗口句柄
            img: 预览图片（可选）
        """
        self.pick_btn.setEnabled(True)
        self.pick_btn.set_bound_state(True)
        self.pick_btn.set_disabled(True)
        self.unbind_btn.set_enabled_state(True)
        
        if img is not None:
            qimg = QImage(img.tobytes(), img.width, img.height,
                         img.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(
                pixmap.scaled(90, 30, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        
        self._update_hwnd_label_style(hwnd)
    
    def set_window_unbound(self):
        """
        设置窗口解绑状态
        """
        self.preview_label.clear()
        self.preview_label.setText("未绑定角色")
        self.pick_btn.set_bound_state(False)
        self.pick_btn.set_disabled(False)
        self.unbind_btn.set_enabled_state(False)
        self.unbind_btn.set_running(False)
        self._update_hwnd_label_style(None)
    
    def enable_pick_button(self, enabled: bool = True):
        """
        启用/禁用瞄准镜按钮
        
        参数：
            enabled: 是否启用
        """
        self.pick_btn.setEnabled(enabled)
