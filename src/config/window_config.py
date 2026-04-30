# -*- coding: utf-8 -*-
"""
窗口配置模块
============
管理应用程序窗口相关的配置参数
"""
from dataclasses import dataclass


@dataclass
class WindowConfig:
    """
    窗口配置类
    
    管理应用程序窗口和游戏窗口的配置参数
    
    属性：
        app_name: 应用程序名称
        class_name: 目标游戏窗口类名
        game_width: 游戏窗口宽度
        game_height: 游戏窗口高度
        ui_width: UI窗口宽度
        ui_height: UI窗口高度
    """
    app_name: str = '糊批解放器'
    # class_name: str = 'Messiah_Game'
    #test
    class_name: str = 'Notepad'
    game_width: int = 960
    game_height: int = 540
    ui_width: int = 900
    ui_height: int = 540
