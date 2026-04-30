# -*- coding: utf-8 -*-
"""
任务列表面板模块
================
提供任务复选框列表的显示和管理功能

模块结构：
    TaskListPanel: 左侧任务列表面板，支持两列布局和垂直滚动
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QCheckBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal

from src.config import config


class TaskListPanel(QScrollArea):
    """
    左侧任务列表面板
    
    显示所有日常任务的复选框列表，支持两列布局和垂直滚动
    
    信号：
        task_checked: 任务勾选状态变化信号 (task_name, checked)
    
    属性：
        task_widgets: 任务复选框字典 {task_name: QCheckBox}
    """
    
    task_checked = pyqtSignal(str, bool)
    
    def __init__(self, colors: dict, parent=None):
        """
        初始化任务列表面板
        
        Args:
            colors (dict): 配色方案字典
            parent: 父组件
        """
        super().__init__(parent)
        self._colors = colors
        self.task_widgets = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """
        初始化UI
        
        创建滚动区域、标题标签和任务复选框网格布局
        """
        self.setWidgetResizable(True)
        self.setFixedWidth(280)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
            }}
        """)
        
        container = QWidget()
        self.setWidget(container)
        
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)
        
        title_label = QLabel("任务列表")
        title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 13px;
            color: {self._colors['text_primary']};
            padding: 4px 0px;
        """)
        self._layout.addWidget(title_label)
        
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(8)
        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(1, 1)
        
        self._layout.addWidget(self._grid_widget)
        self._layout.addStretch()
        
        self._load_tasks()
    
    def _load_tasks(self):
        """
        加载任务列表
        
        从配置中读取日常任务列表，创建对应的复选框控件
        支持任务组配置（列表形式），展开为独立复选框
        """
        daily_tasks = config.daily_tasks
        flat_tasks = []
        
        for task_item in daily_tasks:
            if isinstance(task_item, list):
                flat_tasks.extend(task_item)
            else:
                flat_tasks.append(task_item)
        
        for i, task_name in enumerate(flat_tasks):
            cb = QCheckBox(task_name)
            cb.setChecked(False)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 12px;
                    color: {self._colors['text_primary']};
                }}
            """)
            cb.stateChanged.connect(lambda state, name=task_name: self._on_task_checked(name, state))
            
            row = i // 2
            col = i % 2
            self._grid_layout.addWidget(cb, row, col)
            self.task_widgets[task_name] = cb
    
    def _on_task_checked(self, task_name: str, state: int):
        """
        任务勾选状态变化处理
        
        Args:
            task_name (str): 任务名称
            state (int): 勾选状态（Qt.Checked 或 Qt.Unchecked）
        """
        checked = state == Qt.Checked
        self.task_checked.emit(task_name, checked)
    
    def set_task_checked(self, task_name: str, checked: bool):
        """
        设置任务勾选状态
        
        Args:
            task_name (str): 任务名称
            checked (bool): 是否勾选
        """
        if task_name in self.task_widgets:
            cb = self.task_widgets[task_name]
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
    
    def get_checked_tasks(self) -> list:
        """
        获取所有勾选的任务
        
        Returns:
            list: 勾选的任务名称列表
        """
        return [name for name, cb in self.task_widgets.items() if cb.isChecked()]
    
    def set_checked_tasks(self, task_names: list):
        """
        设置勾选的任务
        
        Args:
            task_names (list): 要勾选的任务名称列表
        """
        for name, cb in self.task_widgets.items():
            cb.blockSignals(True)
            cb.setChecked(name in task_names)
            cb.blockSignals(False)
