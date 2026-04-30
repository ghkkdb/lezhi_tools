# -*- coding: utf-8 -*-
"""
UI 面板组件模块
===============
提供独立的 UI 面板组件，实现组件化布局。

模块结构：
    - BottomControlPanel: 底部控制面板
    - LogPanel: 日志显示面板
    - TaskListPanel: 任务列表面板
    - TaskConfigPanel: 任务配置面板
"""
from .bottom_panel import BottomControlPanel
from .log_panel import LogPanel
from .task_list_panel import TaskListPanel
from .task_config_panel import TaskConfigPanel

__all__ = ['BottomControlPanel', 'LogPanel', 'TaskListPanel', 'TaskConfigPanel']
