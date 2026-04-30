# -*- coding: utf-8 -*-
"""
日志配置模块
============
管理日志系统配置
"""
from typing import Dict


class LoggingConfig:
    """
    日志配置类
    
    管理日志系统的配置参数
    
    属性：
        config: 日志配置字典
    """
    
    def __init__(self, log_path: str = None):
        """
        初始化日志配置
        
        参数：
            log_path: 日志文件路径（可选）
        """
        self.config: Dict[str, any] = {
            'console': {
                'enabled': True,
                'level': 'DEBUG',
                'use_color': True,
            },
            'file': {
                'enabled': True,
                'level': 'DEBUG',
                'path': log_path or 'logs/app.log',
                'max_size': 10 * 1024 * 1024,
                'backup_count': 5,
            },
            'signal': {
                'enabled': True,
                'level': 'INFO',
            },
        }
    
    def get_log_config(self) -> Dict[str, any]:
        """
        获取日志配置
        
        返回：
            Dict[str, any]: 日志配置字典
        """
        return self.config
    
    def get_console_config(self) -> Dict[str, any]:
        """
        获取控制台日志配置
        
        返回：
            Dict[str, any]: 控制台日志配置
        """
        return self.config.get('console', {})
    
    def get_file_config(self) -> Dict[str, any]:
        """
        获取文件日志配置
        
        返回：
            Dict[str, any]: 文件日志配置
        """
        return self.config.get('file', {})
    
    def get_signal_config(self) -> Dict[str, any]:
        """
        获取信号日志配置
        
        返回：
            Dict[str, any]: 信号日志配置
        """
        return self.config.get('signal', {})
