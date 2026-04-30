# -*- coding: utf-8 -*-
"""核心任务模块轻量入口。"""
from .task_registry import register_task, get_task, get_all_task_names
from .state_manager import StateManager, ButtonState
from .config_manager import ConfigManager
from .controller import (
    TaskController,
    TaskControllerProxy,
    TaskStoppedException,
    ContextExpiredException,
    InvalidWindowHandleException,
    task_controller
)

__all__ = [
    'register_task', 'get_task', 'get_all_task_names',
    'StateManager', 'ButtonState', 'ConfigManager',
    'TaskController', 'TaskControllerProxy',
    'TaskStoppedException',
    'ContextExpiredException',
    'InvalidWindowHandleException',
    'task_controller',
]
