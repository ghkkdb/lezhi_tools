# -*- coding: utf-8 -*-
"""
全局配置类（门面模式）
======================
统一配置管理器，提供向后兼容的配置访问接口

该类作为门面（Facade），整合所有子配置类，确保 100% 向后兼容。
外部代码无需任何修改即可正常运行。
"""
from typing import Any, Optional, Tuple
from pathlib import Path

from .window_config import WindowConfig
from .task_config import TaskConfig
from .task_definition_config import TaskDefinitionConfig
from .ui_config import UIConfig
from .key_config import KeyConfig
from .path_config import PathConfig
from .logging_config import LoggingConfig
from .user_config import UserConfig


class Config:
    """
    全局配置类（门面模式）
    
    整合所有子配置类，提供统一的配置访问接口
    
    属性：
        window: 窗口配置
        task: 任务配置
        task_definition: 任务定义配置
        ui: UI配置
        key: 按键映射配置
        path: 路径配置
        logging: 日志配置
        user: 用户配置方案管理
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.window = WindowConfig()
        self.task = TaskConfig()
        self.task_definition = TaskDefinitionConfig()
        self.ui = UIConfig()
        self.key = KeyConfig()
        self.path = PathConfig()
        self.logging_config = LoggingConfig(log_path=self.path.get_log_path())
        self.user = UserConfig(self.path.config_path, self.task_definition.definitions)
        
        self.pause_timeout_threshold = 300
    
    # ==================== 窗口配置属性（向后兼容） ====================
    
    @property
    def app_name(self) -> str:
        """应用程序名称"""
        return self.window.app_name
    
    @property
    def class_name(self) -> str:
        """目标窗口类名"""
        return self.window.class_name
    
    @property
    def x(self) -> int:
        """游戏窗口宽度"""
        return self.window.game_width
    
    @property
    def y(self) -> int:
        """游戏窗口高度"""
        return self.window.game_height
    
    @property
    def ui_width(self) -> int:
        """UI窗口宽度"""
        return self.window.ui_width
    
    @property
    def ui_height(self) -> int:
        """UI窗口高度"""
        return self.window.ui_height
    
    # ==================== 任务配置属性（向后兼容） ====================
    
    @property
    def daily_tasks(self) -> list:
        """日常任务列表"""
        return self.task.daily_tasks
    
    @property
    def chaguan_dt(self) -> list:
        """茶馆答题选项坐标"""
        return self.task.chaguan_dt
    
    @property
    def chaguan_dt_weights(self) -> list:
        """答题选项权重"""
        return self.task.chaguan_dt_weights
    
    @property
    def bangpai_btn(self) -> tuple:
        """帮派按钮坐标"""
        return self.task.bangpai_btn
    
    @property
    def yaoqianshu_options(self) -> dict:
        """摇钱树选项配置"""
        return self.task.yaoqianshu_options
    
    # ==================== UI配置属性（向后兼容） ====================
    
    @property
    def ui_sizes(self) -> dict:
        """UI控件尺寸配置"""
        return self.ui.sizes
    
    @property
    def ui_layout(self) -> dict:
        """布局参数配置"""
        return self.ui.layout
    
    @property
    def tooltips(self) -> dict:
        """提示文本配置"""
        return self.ui.tooltips
    
    @property
    def nav_tabs(self) -> list:
        """导航选项卡配置"""
        return self.ui.nav_tabs
    
    # ==================== 按键映射配置属性（向后兼容） ====================
    
    @property
    def VK_CODE(self) -> dict:
        """按键VK码映射"""
        return self.key.VK_CODE
    
    # ==================== 路径配置属性（向后兼容） ====================
    
    @property
    def assets_path(self) -> Path:
        """资源文件根路径"""
        return self.path.assets_path
    
    @property
    def img_path(self) -> Path:
        """图片资源目录路径"""
        return self.path.img_path
    
    # ==================== 任务配置定义属性（向后兼容） ====================
    
    @property
    def task_config_definitions(self) -> dict:
        """任务配置定义"""
        return self.task_definition.definitions
    
    # ==================== 方法包装器（向后兼容） ====================
    
    def get_img_path(self, relative_path: str) -> str:
        """
        获取图片资源的绝对路径
        
        参数：
            relative_path: 相对于img目录的路径
            
        返回：
            str: 图片的绝对路径字符串
        """
        return self.path.get_img_path(relative_path)
    
    def get_tooltip(self, tooltip_key: str) -> str:
        """
        获取提示文本
        
        参数：
            tooltip_key: 提示文本键名
            
        返回：
            str: 提示文本内容
        """
        return self.ui.get_tooltip(tooltip_key)
    
    def get_nav_tabs(self) -> list:
        """
        获取导航选项卡列表
        
        返回：
            list: 导航选项卡配置列表
        """
        return self.ui.get_nav_tabs()
    
    def add_nav_tab(self, name: str, key: str = None, icon: str = None):
        """
        添加导航选项卡
        
        参数：
            name: 选项卡显示名称
            key: 选项卡唯一标识
            icon: 选项卡图标路径
        """
        self.ui.add_nav_tab(name, key, icon)
    
    def get_logging_config(self) -> dict:
        """
        获取日志配置
        
        返回：
            dict: 日志配置字典
        """
        return self.logging_config.get_log_config()
    
    def get_log_path(self) -> str:
        """
        获取日志文件路径
        
        返回：
            str: 日志文件路径
        """
        return self.path.get_log_path()
    
    # ==================== 任务配置定义方法（向后兼容） ====================
    
    def has_task_config(self, task_name: str) -> bool:
        """
        检查任务是否有配置项
        
        参数：
            task_name: 任务名称
            
        返回：
            bool: 是否有配置项
        """
        return self.task_definition.has_task_config(task_name)
    
    def get_task_default_params(self, task_name: str) -> dict:
        """
        获取任务的默认参数
        
        参数：
            task_name: 任务名称
            
        返回：
            dict: 默认参数字典
        """
        return self.task_definition.get_task_default_params(task_name)
    
    def get_task_mapped_param(self, task_name: str, param_name: str, value: Any) -> Any:
        """
        获取映射后的参数值
        
        参数：
            task_name: 任务名称
            param_name: 参数名称
            value: 原始值
            
        返回：
            Any: 映射后的值
        """
        return self.task_definition.get_task_mapped_param(task_name, param_name, value)
    
    # ==================== 用户配置属性（向后兼容） ====================
    
    @property
    def current_config_name(self) -> Optional[str]:
        """当前使用的配置方案名称"""
        return self.user.current_config_name
    
    @current_config_name.setter
    def current_config_name(self, value: str):
        """设置当前配置方案名称"""
        self.user.current_config_name = value
    
    # ==================== 用户配置方案管理方法（向后兼容） ====================
    
    def save_config(self, config_name: str, checked_tasks: list, task_params: dict):
        """
        保存单个配置方案
        
        参数：
            config_name: 配置方案名称
            checked_tasks: 勾选的任务列表
            task_params: 任务参数字典
        """
        self.user.save_config(config_name, checked_tasks, task_params)
    
    def delete_config(self, config_name: str) -> bool:
        """
        删除配置方案
        
        参数：
            config_name: 要删除的配置方案名称
            
        返回：
            bool: 是否删除成功
        """
        return self.user.delete_config(config_name)
    
    def is_default_config(self, config_name: str) -> bool:
        """
        检查是否为默认配置
        
        参数：
            config_name: 配置名称
            
        返回：
            bool: 是否为默认配置
        """
        return self.user.is_default_config(config_name)
    
    def load_config(self, config_name: str) -> Optional[dict]:
        """
        加载配置方案
        
        参数：
            config_name: 配置方案名称
            
        返回：
            dict: 配置内容，包含 checked_tasks 和 task_params
        """
        return self.user.load_config(config_name)
    
    def get_config_names(self) -> list:
        """
        获取所有配置方案名称列表
        
        返回：
            list: 配置方案名称列表
        """
        return self.user.get_config_names()
    
    def get_last_used_config(self) -> Tuple[Optional[str], Optional[dict]]:
        """
        获取最近使用的配置方案
        
        返回：
            tuple: (配置名称, 配置内容) 或 (None, None)
        """
        return self.user.get_last_used_config()
    
    def save_all_configs(self):
        """保存所有配置方案到文件"""
        self.user.save_all_configs()


config = Config()
