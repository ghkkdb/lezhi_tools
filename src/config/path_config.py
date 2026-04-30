# -*- coding: utf-8 -*-
"""
路径配置模块
============
管理资源文件路径配置，支持 PyInstaller 打包
"""
import os
import sys
from pathlib import Path
from typing import Optional


class PathConfig:
    """
    路径配置类
    
    管理资源文件路径，支持开发环境和 PyInstaller 打包环境
    
    在 PyInstaller 打包环境下：
        - base_path (sys._MEIPASS): 临时解压目录，用于只读资源（图片等）
        - data_path (sys.executable.parent): 可执行文件所在目录，用于可读写数据（日志、配置）
    
    在开发环境下：
        - base_path 和 data_path 都指向项目根目录
    
    属性：
        base_path: 只读资源基础路径（图片等静态资源）
        data_path: 可读写数据基础路径（日志、配置文件）
        assets_path: 资源文件根目录路径
        img_path: 图片资源目录路径
        config_path: 配置文件目录路径
        logs_path: 日志文件目录路径
        
    方法：
        get_img_path: 获取图片资源的绝对路径
        get_config_path: 获取配置文件的绝对路径
        get_log_path: 获取日志文件的绝对路径
    """
    
    def __init__(self):
        """初始化路径配置"""
        self.base_path: Path = self._get_base_path()
        self.data_path: Path = self._get_data_path()
        
        self.assets_path: Path = self.base_path / 'assets'
        self.img_path: Path = self.assets_path / 'img'
        
        self.config_path: Path = self.data_path / 'config'
        self.logs_path: Path = self.data_path / 'logs'
        
        self._ensure_directories()
    
    def _get_base_path(self) -> Path:
        """
        获取项目根目录路径
        
        优先级：
        1. PyInstaller 打包后的路径 (sys._MEIPASS)
        2. 开发环境路径 (通过定位项目根目录标识文件)
        
        返回：
            Path: 项目根目录路径
        """
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return Path(sys._MEIPASS)
            else:
                return Path(sys.executable).parent
        else:
            current_file = Path(__file__).resolve()
            current_dir = current_file.parent
            
            root_markers = ['.git', 'README.md', 'requirements.txt', 'pyproject.toml']
            
            for _ in range(10):
                for marker in root_markers:
                    if (current_dir / marker).exists():
                        return current_dir
                
                parent = current_dir.parent
                if parent == current_dir:
                    break
                current_dir = parent
            
            return current_file.parent.parent.parent
    
    def _get_data_path(self) -> Path:
        """
        获取数据文件基础路径（可读写）
        
        在打包环境下，使用可执行文件所在目录，
        确保日志和配置文件在程序退出后不会丢失。
        在开发环境下，使用项目根目录。
        
        返回：
            Path: 可读写数据目录路径
        """
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return self.base_path
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
    
    def get_img_path(self, relative_path: str) -> str:
        """
        获取图片资源的绝对路径
        
        参数：
            relative_path: 相对于img目录的路径
            
        返回：
            str: 图片的绝对路径字符串
        """
        return str(self.img_path / relative_path)
    
    def get_config_path(self, filename: str) -> str:
        """
        获取配置文件的绝对路径
        
        参数：
            filename: 配置文件名
            
        返回：
            str: 配置文件的绝对路径字符串
        """
        return str(self.config_path / filename)
    
    def get_log_path(self, filename: str = 'app.log') -> str:
        """
        获取日志文件的绝对路径
        
        参数：
            filename: 日志文件名
            
        返回：
            str: 日志文件的绝对路径字符串
        """
        return str(self.logs_path / filename)
