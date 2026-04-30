# -*- coding: utf-8 -*-
"""
任务配置管理器模块
================
提供任务参数的收集和转换功能。

核心功能：
    - ConfigManager: 任务配置管理器
    - 收集 UI 面板的扁平化数据
    - 转换为 Worker 需要的映射后参数字典

使用示例：
    from src.core.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    params = config_manager.get_task_params(task_config_panel)
"""
from typing import Any, Dict

from src.config import config


class ConfigManager:
    """
    任务配置管理器
    
    负责：
        - 从 TaskConfigPanel 收集扁平化参数
        - 结合全局 config 进行参数映射转换
        - 返回 Worker 需要的参数字典
    
    注意：
        该类不直接 import UI 组件，通过方法参数注入面板实例，
        避免循环导入问题。
    
    使用示例：
        manager = ConfigManager()
        params = manager.get_task_params(self.task_config_panel)
        worker = ScriptWorker(tasks, hwnd, params)
    """
    
    def get_task_params(self, task_config_panel: Any) -> Dict[str, Dict[str, Any]]:
        """
        获取用于执行的任务参数（扁平化并映射）
        
        遍历所有日常任务，从 TaskConfigPanel 获取扁平化参数，
        并通过 config 进行映射转换。
        
        参数：
            task_config_panel: TaskConfigPanel 实例，需提供 get_flattened_task_params 方法
            
        返回：
            dict: 任务参数字典，格式为 {task_name: {param_name: mapped_value}}
        
        使用示例：
            params = config_manager.get_task_params(self.task_config_panel)
            # 返回: {"每日一卦": {"choice": 1}, "课业任务": {...}}
        """
        params: Dict[str, Dict[str, Any]] = {}
        
        for task_item in config.daily_tasks:
            if isinstance(task_item, list):
                task_names = task_item
            else:
                task_names = [task_item]
            
            for task_name in task_names:
                if not config.has_task_config(task_name):
                    continue
                
                flattened = task_config_panel.get_flattened_task_params(task_name)
                
                params[task_name] = {}
                for param_name, value in flattened.items():
                    mapped_value = config.get_task_mapped_param(task_name, param_name, value)
                    params[task_name][param_name] = mapped_value
        
        return params
