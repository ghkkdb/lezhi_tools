# -*- coding: utf-8 -*-
"""
统一状态管理器模块
================
提供全局状态管理，实现 UI 与状态的解耦。

核心功能：
    - ButtonState: 按钮状态枚举类
    - StateManager: 单例状态管理器（继承 QObject）
    - 支持信号驱动的状态变化通知

使用示例：
    from src.core.state_manager import StateManager, ButtonState
    
    state_manager = StateManager.get_instance()
    state_manager.state_changed.connect(self._on_state_changed)
    state_manager.set_button_state(ButtonState.RUNNING)
"""
import threading
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal


class ButtonState:
    """
    按钮状态枚举类
    
    定义按钮的四种状态：
        - IDLE: 初始状态，主控按钮"开始执行"，暂停按钮禁用
        - RUNNING: 运行状态，主控按钮"强制停止"，暂停按钮"暂停运行"
        - PAUSED: 暂停状态，主控按钮"强制停止"，暂停按钮"继续运行"
        - STOPPING: 停止过渡状态，两个按钮都禁用
    
    属性：
        IDLE: 空闲状态常量
        RUNNING: 运行状态常量
        PAUSED: 暂停状态常量
        STOPPING: 停止中状态常量
    """
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class StateManager(QObject):
    """
    统一状态管理器（单例模式）
    
    继承自 QObject，支持信号槽机制。
    管理按钮状态和窗口绑定状态，状态变化时自动发射信号。
    
    属性：
        button_state: 当前按钮状态（ButtonState 枚举值）
        bound_hwnd: 当前绑定的窗口句柄
        
    信号：
        state_changed(str): 按钮状态变化信号
        window_bound(int): 窗口绑定信号
        window_unbound(): 窗口解绑信号
    
    使用示例：
        manager = StateManager.get_instance()
        manager.state_changed.connect(self._update_button_ui)
        manager.set_button_state(ButtonState.RUNNING)
    """
    
    _instance: Optional['StateManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    state_changed = pyqtSignal(str)
    window_bound = pyqtSignal(int)
    window_unbound = pyqtSignal()
    
    def __new__(cls) -> 'StateManager':
        """
        创建单例实例（线程安全）
        
        返回：
            StateManager: 状态管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化状态管理器
        
        仅在首次创建时执行初始化。
        """
        if self._initialized:
            return
        super().__init__()
        self._button_state: str = ButtonState.IDLE
        self._bound_hwnd: Optional[int] = None
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'StateManager':
        """
        获取单例实例
        
        返回：
            StateManager: 状态管理器实例
        """
        return cls()
    
    @property
    def button_state(self) -> str:
        """
        获取当前按钮状态
        
        返回：
            str: ButtonState 枚举值
        """
        return self._button_state
    
    @property
    def bound_hwnd(self) -> Optional[int]:
        """
        获取当前绑定的窗口句柄
        
        返回：
            int | None: 窗口句柄，未绑定时返回 None
        """
        return self._bound_hwnd
    
    def set_button_state(self, state: str) -> None:
        """
        设置按钮状态
        
        仅当状态实际改变时才发射信号。
        
        参数：
            state: 目标状态（ButtonState 枚举值）
        """
        if self._button_state != state:
            self._button_state = state
            self.state_changed.emit(state)
    
    def bind_window(self, hwnd: int) -> None:
        """
        绑定窗口
        
        设置当前窗口句柄并发射绑定信号。
        
        参数：
            hwnd: 窗口句柄
        """
        self._bound_hwnd = hwnd
        self.window_bound.emit(hwnd)
    
    def unbind_window(self) -> None:
        """
        解绑窗口
        
        清空窗口句柄并发射解绑信号。
        """
        self._bound_hwnd = None
        self.window_unbound.emit()
    
    def is_window_bound(self) -> bool:
        """
        检查是否已绑定窗口
        
        返回：
            bool: 已绑定返回 True，否则返回 False
        """
        return self._bound_hwnd is not None
    
    def reset(self) -> None:
        """
        重置所有状态
        
        将按钮状态重置为 IDLE，清空窗口绑定。
        """
        self.set_button_state(ButtonState.IDLE)
        self.unbind_window()
