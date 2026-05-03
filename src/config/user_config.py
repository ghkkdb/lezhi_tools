# -*- coding: utf-8 -*-
"""
用户配置方案管理模块
====================
管理用户保存的任务配置方案
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class UserConfig:
    """
    用户配置方案管理类
    
    管理用户保存的任务配置方案，包括保存、加载、删除等功能
    
    属性：
        DEFAULT_CONFIG_NAME: 默认配置名称
        user_config_path: 用户配置文件路径
        saved_configs: 已保存的配置方案字典
        current_config_name: 当前使用的配置方案名称
        
    方法：
        save_config: 保存配置方案
        delete_config: 删除配置方案
        load_config: 加载配置方案
        get_config_names: 获取所有配置方案名称
        get_last_used_config: 获取最近使用的配置方案
        is_default_config: 检查是否为默认配置
    """
    
    DEFAULT_CONFIG_NAME = "默认配置"
    
    def __init__(self, config_path: Path, task_definitions: Dict[str, Any]):
        """
        初始化用户配置管理器
        
        参数：
            config_path: 配置文件路径
            task_definitions: 任务配置定义字典
        """
        self.user_config_path = config_path / 'user_task_configs.json'
        self.task_definitions = task_definitions
        self.saved_configs: Dict[str, Dict[str, Any]] = {}
        self.current_config_name: Optional[str] = None
        
        self._load_saved_configs()
        self._ensure_default_config()
    
    def _load_saved_configs(self) -> None:
        """加载已保存的任务配置方案"""
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    self.saved_configs = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.saved_configs = {}
    
    def _ensure_default_config(self) -> None:
        """确保默认配置存在"""
        if self.DEFAULT_CONFIG_NAME not in self.saved_configs:
            default_task_params = {}
            for task_name, task_def in self.task_definitions.items():
                default_task_params[task_name] = self._extract_default_params(
                    task_def.get("fields", [])
                )
            
            self.saved_configs[self.DEFAULT_CONFIG_NAME] = {
                "last_used": datetime.now().isoformat(),
                "checked_tasks": [],
                "task_params": default_task_params
            }
            self.save_all_configs()
    
    def _extract_default_params(self, fields: list) -> dict:
        """
        递归提取字段的默认参数值
        
        参数：
            fields: 字段列表
            
        返回：
            dict: 默认参数字典
        """
        params = {}
        for field in fields:
            field_type = field.get("type", "dropdown")
            
            if field_type == "row":
                items = field.get("items", [])
                params.update(self._extract_default_params(items))
            elif field_type == "group":
                sub_fields = field.get("fields", [])
                params.update(self._extract_default_params(sub_fields))
            elif field_type not in ("label",):
                params[field["name"]] = field.get("default", "")
        
        return params
    
    def save_all_configs(self) -> None:
        """保存所有配置方案到文件"""
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.user_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.saved_configs, f, ensure_ascii=False, indent=2)
    
    def save_config(self, config_name: str, checked_tasks: list, task_params: dict) -> None:
        """
        保存单个配置方案
        
        参数：
            config_name: 配置方案名称
            checked_tasks: 勾选的任务列表
            task_params: 任务参数字典
        """
        self.saved_configs[config_name] = {
            "last_used": datetime.now().isoformat(),
            "checked_tasks": checked_tasks,
            "task_params": task_params
        }
        self.current_config_name = config_name
        self.save_all_configs()
    
    def delete_config(self, config_name: str) -> bool:
        """
        删除配置方案
        
        参数：
            config_name: 要删除的配置方案名称
            
        返回：
            bool: 是否删除成功
        """
        if config_name == self.DEFAULT_CONFIG_NAME:
            return False
        
        if config_name in self.saved_configs:
            del self.saved_configs[config_name]
            if self.current_config_name == config_name:
                self.current_config_name = None
            self.save_all_configs()
            return True
        
        return False

    def clear_saved_configs(self) -> bool:
        """清空所有自定义保存的配置方案，并保留默认配置。"""
        try:
            self.saved_configs = {}
            self.current_config_name = None
            self._ensure_default_config()
            return True
        except Exception:
            return False
    
    def is_default_config(self, config_name: str) -> bool:
        """
        检查是否为默认配置
        
        参数：
            config_name: 配置名称
            
        返回：
            bool: 是否为默认配置
        """
        return config_name == self.DEFAULT_CONFIG_NAME
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        加载配置方案
        
        参数：
            config_name: 配置方案名称
            
        返回：
            dict: 配置内容，包含 checked_tasks 和 task_params
        """
        if config_name in self.saved_configs:
            self.current_config_name = config_name
            self.saved_configs[config_name]["last_used"] = datetime.now().isoformat()
            self.save_all_configs()
            return self.saved_configs[config_name]
        return None
    
    def get_config_names(self) -> list:
        """
        获取所有配置方案名称列表
        
        返回：
            list: 配置方案名称列表
        """
        return list(self.saved_configs.keys())
    
    def get_last_used_config(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        获取最近使用的配置方案
        
        返回：
            tuple: (配置名称, 配置内容) 或 (None, None)
        """
        if not self.saved_configs:
            return None, None
        
        last_config_name = None
        last_used_time = None
        
        for name, config in self.saved_configs.items():
            config_time = config.get("last_used", "")
            if last_used_time is None or config_time > last_used_time:
                last_used_time = config_time
                last_config_name = name
        
        return last_config_name, self.saved_configs.get(last_config_name)
