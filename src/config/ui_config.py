# -*- coding: utf-8 -*-
"""
UI配置模块
==========
管理用户界面相关的配置参数
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, List


@dataclass
class UIConfig:
    """
    UI配置类
    
    管理用户界面的配置参数
    
    属性：
        sizes: UI控件尺寸配置
        layout: 布局参数配置
        tooltips: 提示文本配置
        nav_tabs: 导航选项卡配置
    """
    sizes: Dict[str, Any] = field(default_factory=lambda: {
        "pick_btn": (30, 30),
        "unbind_btn": (30, 30),
        "hwnd_label": (90, 30),
        "preview_label": (90, 30),
        "start_btn": (85, 30),
        "stop_btn": (85, 30),
        "nav_height": 36,
        "tab_height": 30,
        "tab_min_width": 80,
        "left_ctrl_width": 240,
        "log_width": 350,
    })
    
    layout: Dict[str, Any] = field(default_factory=lambda: {
        "left": {
            "margin": (10, 8, 10, 8),
            "h_spacing": 10,
            "v_spacing": 10,
            "row_height": 30,
            "row_count": 3,
        },
        "middle": {
            "margin": (0, 0, 0, 0),
            "min_width": 0,
        },
        "right": {
            "margin": (4, 0, 4, 0),
        },
        "bottom_group_height": 140,
        "bottom_spacing": 8,
    })
    
    tooltips: Dict[str, str] = field(default_factory=lambda: {
        "pick_idle": "长按拖动到游戏窗口释放",
        "pick_bound": "已绑定窗口，点击解绑后可重新选择",
        "pick_dragging": "拖动到目标窗口后释放",
        "unbind_disabled": "未绑定窗口，无法解绑",
        "unbind_enabled": "点击解绑已绑定的窗口",
    })
    
    nav_tabs: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "基础设置", "key": "settings", "icon": None},
        {"name": "日常任务", "key": "daily", "icon": None},
        {"name": "多开控制", "key": "multi_window", "icon": None},
        {"name": "挂机任务", "key": "afk", "icon": None},
        {"name": "其他功能", "key": "other", "icon": None},
    ])
    
    def get_tooltip(self, tooltip_key: str) -> str:
        """
        获取提示文本
        
        参数：
            tooltip_key: 提示文本键名
            
        返回：
            str: 提示文本内容
        """
        return self.tooltips.get(tooltip_key, "")
    
    def get_nav_tabs(self) -> list:
        """
        获取导航选项卡列表
        
        返回：
            list: 导航选项卡配置列表
        """
        return self.nav_tabs
    
    def add_nav_tab(self, name: str, key: str = None, icon: str = None):
        """
        添加导航选项卡
        
        参数：
            name: 选项卡显示名称
            key: 选项卡唯一标识
            icon: 选项卡图标路径
        """
        if key is None:
            key = name.lower()
        self.nav_tabs.append({"name": name, "key": key, "icon": icon})
