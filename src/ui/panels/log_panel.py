# -*- coding: utf-8 -*-
"""
日志显示面板组件
================
提供独立的日志显示面板。

核心功能：
    - QTextEdit 日志显示区域
    - 自动滚动到底部
    - 清空日志功能

使用示例：
    panel = LogPanel(colors)
    panel.append_message("[INFO] 程序启动")
"""
from typing import Dict

from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt


class LogPanel(QWidget):
    """
    日志显示面板组件
    
    提供独立的日志显示区域，支持自动滚动到底部。
    
    属性：
        log_area: QTextEdit 日志显示区域
    
    使用示例：
        panel = LogPanel(colors)
        panel.append_message("[INFO] 程序启动")
    """
    
    def __init__(self, colors: Dict[str, str], parent=None):
        """
        初始化日志面板
        
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
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors['surface_elevated']}; 
                border: 1px solid {self._colors['border_strong']};
                font-family: 'Consolas', 'SimSun';
                font-size: 9pt;
                padding: 2px;
                color: {self._colors['text_primary']};
            }}
        """)
        layout.addWidget(self.log_area)
    
    def append_message(self, message: str):
        """
        追加日志消息并自动滚动到底部
        
        参数：
            message: 日志消息
        """
        try:
            self.log_area.append(message)
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except RuntimeError:
            pass
    
    def clear(self):
        """
        清空日志
        """
        self.log_area.clear()
    
    def get_log_widget(self) -> QTextEdit:
        """
        获取日志控件（用于菜单操作等）
        
        返回：
            QTextEdit: 日志显示控件
        """
        return self.log_area
