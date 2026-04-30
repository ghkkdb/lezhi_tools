# -*- coding: utf-8 -*-
"""
按键映射配置模块
================
管理按键VK码映射配置
"""
import win32con
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KeyConfig:
    """
    按键映射配置类
    
    管理按键名称与VK码的映射关系
    
    属性：
        VK_CODE: 按键VK码映射字典
    """
    VK_CODE: Dict[str, int] = field(default_factory=lambda: {
        "ESC": win32con.VK_ESCAPE,
        "ENTER": win32con.VK_RETURN,
        "TAB": win32con.VK_TAB,
        "SPACE": win32con.VK_SPACE,
        "SHIFT": win32con.VK_SHIFT,
        "CTRL": win32con.VK_CONTROL,
        "ALT": win32con.VK_MENU,
        "BACKSPACE": win32con.VK_BACK,
        "UP": win32con.VK_UP,
        "DOWN": win32con.VK_DOWN,
        "LEFT": win32con.VK_LEFT,
        "RIGHT": win32con.VK_RIGHT,
        "F1": win32con.VK_F1,
        "F2": win32con.VK_F2,
        "F3": win32con.VK_F3,
        "F4": win32con.VK_F4,
        "F5": win32con.VK_F5,
        "F6": win32con.VK_F6,
        "F7": win32con.VK_F7,
        "F8": win32con.VK_F8,
        "F9": win32con.VK_F9,
        "F10": win32con.VK_F10,
        "F11": win32con.VK_F11,
        "F12": win32con.VK_F12,
    })
