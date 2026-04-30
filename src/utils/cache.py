# -*- coding: utf-8 -*-
"""
缓存管理模块
============
提供模板图片和截图帧的内存缓存机制，优化图像识别性能

主要功能：
    - TemplateCache: 模板图片缓存（懒加载、线程安全、中文路径兼容）
    - FrameCache: 截图帧缓存（TTL 过期策略、线程安全、支持强制清除）
"""
import time
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any

import cv2
import numpy as np
from PIL import Image


class TemplateCache:
    """
    模板图片缓存单例类
    
    功能：
        - 懒加载：首次访问时从磁盘读取，后续从内存返回
        - 线程安全：使用 threading.Lock() 保障多线程安全
        - 中文路径兼容：使用 cv2.imdecode + np.fromfile 替代 cv2.imread
    
    使用示例：
        cache = TemplateCache.get_instance()
        template = cache.get("path/to/template.png")
    """
    
    _instance: Optional['TemplateCache'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'TemplateCache':
        """
        单例模式：确保全局唯一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化缓存字典和线程锁
        """
        if self._initialized:
            return
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_lock: threading.Lock = threading.Lock()
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'TemplateCache':
        """
        获取单例实例
        
        返回：
            TemplateCache: 全局唯一的缓存实例
        """
        return cls()
    
    def get(self, template_path: str) -> Optional[np.ndarray]:
        """
        获取模板图片（带缓存）
        
        首次调用时从磁盘读取并缓存，后续调用直接从内存返回。
        使用 cv2.imdecode + np.fromfile 解决 Windows 中文路径问题。
        
        参数：
            template_path: 模板图片路径
            
        返回：
            np.ndarray: 模板图片矩阵（BGR 格式），读取失败返回 None
        """
        path = str(template_path)
        
        with self._cache_lock:
            if path in self._cache:
                return self._cache[path]
        
        template = self._load_template(path)
        
        if template is not None:
            with self._cache_lock:
                self._cache[path] = template
        
        return template
    
    def _load_template(self, path: str) -> Optional[np.ndarray]:
        """
        从磁盘加载模板图片（支持中文路径）
        
        使用 cv2.imdecode + np.fromfile 组合替代 cv2.imread，
        彻底解决 Windows 环境下中文路径读取失败的问题。
        
        参数：
            path: 模板图片路径
            
        返回：
            np.ndarray: 模板图片矩阵（BGR 格式），读取失败返回 None
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                print(f"警告: 模板文件不存在 {path}")
                return None
            
            file_bytes = np.fromfile(str(path_obj), dtype=np.uint8)
            template = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if template is None:
                print(f"警告: 无法解码模板图片 {path}")
                return None
            
            return template
        except Exception as e:
            print(f"警告: 读取模板失败 {path}, 错误: {e}")
            return None
    
    def clear(self) -> None:
        """
        清空所有缓存
        """
        with self._cache_lock:
            self._cache.clear()
    
    def remove(self, template_path: str) -> bool:
        """
        移除指定模板的缓存
        
        参数：
            template_path: 模板图片路径
            
        返回：
            bool: 是否成功移除
        """
        path = str(template_path)
        with self._cache_lock:
            if path in self._cache:
                del self._cache[path]
                return True
            return False
    
    def size(self) -> int:
        """
        获取缓存中的模板数量
        
        返回：
            int: 缓存的模板数量
        """
        with self._cache_lock:
            return len(self._cache)


class FrameCache:
    """
    截图帧缓存单例类
    
    功能：
        - TTL 过期策略：在有效期内返回缓存的截图，超时则重新截图
        - 线程安全：使用 threading.Lock() 保障多线程安全
        - 强制清除：提供 clear() 方法供外部主动清空陈旧画面
    
    使用示例：
        cache = FrameCache.get_instance()
        frame = cache.get_frame(hwnd, capture_window, ttl=0.1)
        
        # 点击后清除缓存，确保获取最新画面
        background_click(hwnd, x, y)
        cache.clear()
    """
    
    _instance: Optional['FrameCache'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'FrameCache':
        """
        单例模式：确保全局唯一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化缓存数据和时间戳
        """
        if self._initialized:
            return
        self._frame: Optional[np.ndarray] = None
        self._frame_bgr: Optional[np.ndarray] = None
        self._frame_gray: Optional[np.ndarray] = None
        self._timestamp: float = 0.0
        self._hwnd: Optional[int] = None
        self._cache_lock: threading.Lock = threading.Lock()
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'FrameCache':
        """
        获取单例实例
        
        返回：
            FrameCache: 全局唯一的缓存实例
        """
        return cls()
    
    def get_frame(
        self,
        hwnd: int,
        capture_func: Callable[[int], Optional[Image.Image]],
        ttl: float = 0.1
    ) -> Optional[np.ndarray]:
        """
        获取截图帧（带 TTL 缓存）
        
        在 TTL 有效期内返回缓存的截图，超时则调用回调函数重新截图。
        
        参数：
            hwnd: 窗口句柄
            capture_func: 截图回调函数，接收 hwnd 参数，返回 PIL.Image
            ttl: 缓存有效期（秒），默认 0.1 秒（100 毫秒）
            
        返回：
            np.ndarray: 截图的 BGR 矩阵，截图失败返回 None
        """
        current_time = time.time()
        
        with self._cache_lock:
            if (self._frame_bgr is not None and 
                self._hwnd == hwnd and 
                current_time - self._timestamp < ttl):
                return self._frame_bgr
        
        img = capture_func(hwnd)
        if img is None:
            return None
        
        frame_rgb = np.array(img)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        with self._cache_lock:
            self._frame = frame_rgb
            self._frame_bgr = frame_bgr
            self._frame_gray = None
            self._timestamp = current_time
            self._hwnd = hwnd
        
        return frame_bgr
    
    def get_frame_grayscale(
        self,
        hwnd: int,
        capture_func: Callable[[int], Optional[Image.Image]],
        ttl: float = 0.1
    ) -> Optional[np.ndarray]:
        """
        获取截图帧的灰度图（带 TTL 缓存）
        
        在 TTL 有效期内返回缓存的灰度图，超时则重新截图并转换。
        灰度图匹配可减少三分之一的计算量。
        
        参数：
            hwnd: 窗口句柄
            capture_func: 截图回调函数
            ttl: 缓存有效期（秒），默认 0.1 秒
            
        返回：
            np.ndarray: 截图的灰度矩阵，截图失败返回 None
        """
        current_time = time.time()
        
        with self._cache_lock:
            if (self._frame_gray is not None and 
                self._hwnd == hwnd and 
                current_time - self._timestamp < ttl):
                return self._frame_gray
        
        frame_bgr = self.get_frame(hwnd, capture_func, ttl)
        if frame_bgr is None:
            return None
        
        frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        with self._cache_lock:
            self._frame_gray = frame_gray
        
        return frame_gray
    
    def clear(self) -> None:
        """
        清空当前缓存的截图
        
        在执行可能改变画面的操作（如点击、拖拽）后调用，
        确保后续图像识别使用最新画面，避免"陈旧画面"问题。
        """
        with self._cache_lock:
            self._frame = None
            self._frame_bgr = None
            self._frame_gray = None
            self._timestamp = 0.0
            self._hwnd = None
    
    def is_cached(self) -> bool:
        """
        检查当前是否有缓存的截图
        
        返回：
            bool: 是否有缓存
        """
        with self._cache_lock:
            return self._frame_bgr is not None
    
    def get_age(self) -> float:
        """
        获取当前缓存的年龄（秒）
        
        返回：
            float: 缓存年龄，无缓存返回 -1
        """
        with self._cache_lock:
            if self._frame_bgr is None:
                return -1.0
            return time.time() - self._timestamp


template_cache = TemplateCache()
frame_cache = FrameCache()
