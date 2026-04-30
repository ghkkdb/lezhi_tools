# -*- coding: utf-8 -*-
"""
输入状态追踪模块
================
追踪键盘和鼠标的按下状态，用于判断按键/按钮是否处于持续按下状态。

主要组件：
    - InputTracker: 输入状态追踪器（单例模式）

功能说明：
    - 追踪键盘按键的 Down/Up 状态
    - 追踪鼠标按钮的 Down/Up 状态
    - 线程安全的状态管理
    - 支持窗口句柄关联

使用示例：
    from src.utils.input_tracker import InputTracker
    
    tracker = InputTracker.get_instance()
    
    # 记录按键状态
    tracker.track_key_down(hwnd, 'a')
    tracker.track_key_up(hwnd, 'a')
    
    # 查询当前状态
    pressed_keys = tracker.get_pressed_keys()
    pressed_buttons = tracker.get_pressed_buttons()
"""
import threading
from typing import Set, Optional


class InputTracker:
    """
    输入状态追踪器（单例模式）
    
    追踪键盘按键和鼠标按钮的按下状态，用于判断是否处于持续按下状态。
    线程安全设计，支持多线程环境下的状态管理。
    
    属性：
        _instance: 单例实例
        _lock: 线程锁
        _pressed_keys: 处于 Down 状态的键盘按键集合
        _pressed_buttons: 处于 Down 状态的鼠标按钮集合
        _hwnd: 关联的窗口句柄
    """
    
    _instance: Optional['InputTracker'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'InputTracker':
        """
        单例模式实现
        
        返回：
            InputTracker: 唯一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化输入状态追踪器"""
        if not hasattr(self, '_initialized'):
            self._pressed_keys: Set[str] = set()
            self._pressed_buttons: Set[str] = set()
            self._hwnd: Optional[int] = None
            self._data_lock: threading.Lock = threading.Lock()
            self._initialized: bool = True
    
    @classmethod
    def get_instance(cls) -> 'InputTracker':
        """
        获取输入状态追踪器实例
        
        返回：
            InputTracker: 追踪器实例
        """
        return cls()
    
    def track_key_down(self, hwnd: int, key: str) -> None:
        """
        记录键盘按键按下状态
        
        当检测到键盘按键按下时调用此方法，将按键添加到按下状态集合中。
        
        参数：
            hwnd: 窗口句柄
            key: 按键名称（如 'a', 'b', 'enter', 'space' 等）
        """
        with self._data_lock:
            self._hwnd = hwnd
            self._pressed_keys.add(key.lower())
    
    def track_key_up(self, hwnd: int, key: str) -> None:
        """
        清除键盘按键按下状态
        
        当检测到键盘按键释放时调用此方法，将按键从按下状态集合中移除。
        
        参数：
            hwnd: 窗口句柄
            key: 按键名称（如 'a', 'b', 'enter', 'space' 等）
        """
        with self._data_lock:
            self._hwnd = hwnd
            self._pressed_keys.discard(key.lower())
    
    def track_mouse_down(self, hwnd: int, button: str) -> None:
        """
        记录鼠标按钮按下状态
        
        当检测到鼠标按钮按下时调用此方法，将按钮添加到按下状态集合中。
        
        参数：
            hwnd: 窗口句柄
            button: 鼠标按钮名称（'left', 'right', 'middle'）
        """
        with self._data_lock:
            self._hwnd = hwnd
            normalized_button = button.lower()
            if normalized_button in ('left', 'right', 'middle'):
                self._pressed_buttons.add(normalized_button)
    
    def track_mouse_up(self, hwnd: int, button: str) -> None:
        """
        清除鼠标按钮按下状态
        
        当检测到鼠标按钮释放时调用此方法，将按钮从按下状态集合中移除。
        
        参数：
            hwnd: 窗口句柄
            button: 鼠标按钮名称（'left', 'right', 'middle'）
        """
        with self._data_lock:
            self._hwnd = hwnd
            normalized_button = button.lower()
            if normalized_button in ('left', 'right', 'middle'):
                self._pressed_buttons.discard(normalized_button)
    
    def get_pressed_keys(self) -> Set[str]:
        """
        获取当前按下的键盘按键集合
        
        返回当前所有处于按下状态的键盘按键名称集合。
        
        返回：
            Set[str]: 按下的键盘按键集合（按键名称均为小写）
        """
        with self._data_lock:
            return self._pressed_keys.copy()
    
    def get_pressed_buttons(self) -> Set[str]:
        """
        获取当前按下的鼠标按钮集合
        
        返回当前所有处于按下状态的鼠标按钮名称集合。
        
        返回：
            Set[str]: 按下的鼠标按钮集合（'left', 'right', 'middle'）
        """
        with self._data_lock:
            return self._pressed_buttons.copy()
    
    def get_hwnd(self) -> Optional[int]:
        """
        获取当前关联的窗口句柄
        
        返回：
            Optional[int]: 窗口句柄，未设置时返回 None
        """
        with self._data_lock:
            return self._hwnd
    
    def is_key_pressed(self, key: str) -> bool:
        """
        检查指定键盘按键是否处于按下状态
        
        参数：
            key: 按键名称
            
        返回：
            bool: 按键是否按下
        """
        with self._data_lock:
            return key.lower() in self._pressed_keys
    
    def is_button_pressed(self, button: str) -> bool:
        """
        检查指定鼠标按钮是否处于按下状态
        
        参数：
            button: 鼠标按钮名称（'left', 'right', 'middle'）
            
        返回：
            bool: 按钮是否按下
        """
        with self._data_lock:
            return button.lower() in self._pressed_buttons
    
    def clear(self) -> None:
        """
        清空所有输入状态
        
        清空键盘按键和鼠标按钮的按下状态，重置窗口句柄。
        通常在窗口切换或任务结束时调用。
        """
        with self._data_lock:
            self._pressed_keys.clear()
            self._pressed_buttons.clear()
            self._hwnd = None
    
    def clear_keys(self) -> None:
        """
        仅清空键盘按键状态
        
        保留鼠标按钮状态和窗口句柄。
        """
        with self._data_lock:
            self._pressed_keys.clear()
    
    def clear_buttons(self) -> None:
        """
        仅清空鼠标按钮状态
        
        保留键盘按键状态和窗口句柄。
        """
        with self._data_lock:
            self._pressed_buttons.clear()
    
    def get_state_summary(self) -> dict:
        """
        获取当前状态的摘要信息
        
        返回包含所有状态信息的字典，用于调试和日志记录。
        
        返回：
            dict: 状态摘要，包含 hwnd、pressed_keys、pressed_buttons
        """
        with self._data_lock:
            return {
                'hwnd': self._hwnd,
                'pressed_keys': list(self._pressed_keys),
                'pressed_buttons': list(self._pressed_buttons)
            }
