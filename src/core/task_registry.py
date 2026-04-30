# -*- coding: utf-8 -*-
"""
任务注册表模块
==============
提供基于装饰器的任务注册机制，实现任务名称与任务函数的解耦映射。

核心功能：
    - register_task: 装饰器，用于注册任务函数
    - get_task: 获取已注册的任务函数
    - get_all_task_names: 获取所有已注册的任务名称

使用示例：
    @register_task("每日一卦")
    def task_gua(hwnd):
        ...

    task_func = get_task("每日一卦")
"""
import threading
from typing import Callable, Dict, Optional, List


class _TaskRegistry:
    """
    任务注册表（单例模式）
    
    线程安全的任务函数注册表，存储任务名称与任务函数的映射关系。
    
    属性：
        _instance: 单例实例
        _lock: 线程锁
        _tasks: 任务映射字典
    """
    
    _instance: Optional['_TaskRegistry'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> '_TaskRegistry':
        """
        创建单例实例（线程安全）
        
        返回：
            _TaskRegistry: 注册表实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Callable] = {}
        return cls._instance
    
    def register(self, name: str, func: Callable) -> None:
        """
        注册任务函数
        
        参数：
            name: 任务名称（如 "每日一卦"）
            func: 任务函数
        """
        with self._lock:
            self._tasks[name] = func
    
    def get(self, name: str) -> Optional[Callable]:
        """
        获取任务函数
        
        参数：
            name: 任务名称
            
        返回：
            Callable | None: 任务函数，未找到返回 None
        """
        with self._lock:
            return self._tasks.get(name)
    
    def get_all_names(self) -> List[str]:
        """
        获取所有已注册的任务名称
        
        返回：
            List[str]: 任务名称列表
        """
        with self._lock:
            return list(self._tasks.keys())


_registry = _TaskRegistry()


def register_task(name: str) -> Callable:
    """
    任务注册装饰器
    
    将任务函数注册到全局注册表中，实现任务名称与函数的解耦映射。
    
    参数：
        name: 任务名称（如 "每日一卦"、"课业任务"）
        
    返回：
        Callable: 装饰器函数
        
    使用示例：
        @register_task("每日一卦")
        def task_gua(hwnd):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _registry.register(name, func)
        return func
    return decorator


def get_task(name: str) -> Optional[Callable]:
    """
    获取已注册的任务函数
    
    通过任务名称获取对应的任务函数，用于动态调用。
    
    参数：
        name: 任务名称
        
    返回：
        Callable | None: 任务函数，未找到返回 None
        
    使用示例：
        task_func = get_task("每日一卦")
        if task_func:
            result = task_func(hwnd)
    """
    return _registry.get(name)


def get_all_task_names() -> List[str]:
    """
    获取所有已注册的任务名称
    
    返回当前注册表中所有任务的名称列表，用于遍历或校验。
    
    返回：
        List[str]: 任务名称列表
        
    使用示例：
        names = get_all_task_names()
        for name in names:
            print(f"已注册任务: {name}")
    """
    return _registry.get_all_names()
