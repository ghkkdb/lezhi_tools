# -*- coding: utf-8 -*-
"""
图像处理工具模块
================
封装 OpenCV 图像识别功能

主要功能：
    - find_image: 模板匹配查找图像（使用双重缓存优化）
    - find_image_grayscale: 灰度图模板匹配（性能优化版）
    - find_all_images: 查找所有匹配的图像（返回匹配数量和坐标列表）
"""
import cv2
import numpy as np
from typing import Optional, Tuple, List, Union

from src.utils.win_api import capture_window
from src.utils.cache import template_cache, frame_cache


def find_image(
    hwnd: int,
    template_path: Union[str, List[str]],
    roi: Optional[List[int]] = None,
    threshold: float = 0.8,
    use_grayscale: bool = False
) -> Optional[Tuple[int, int]]:
    """
    在指定句柄窗口的特定区域查找图片（双重缓存优化版）
    
    性能优化：
        - 使用 FrameCache 缓存截图，避免重复截图
        - 使用 TemplateCache 缓存模板，避免重复磁盘 I/O
        - 颜色转换提升到模板循环外部，每帧仅转换一次
    
    参数：
        hwnd: 窗口句柄
        template_path: 模板图片路径，可以是单个路径字符串或路径列表
        roi: 裁剪区域 [x, y, w, h]，不传则全屏查找
        threshold: 匹配阈值，默认 0.8
        use_grayscale: 是否使用灰度图匹配（性能更优），默认 False
    
    返回：
        tuple: (center_x, center_y) 窗口中心坐标，未找到返回 None
    """
    if use_grayscale:
        frame = frame_cache.get_frame_grayscale(hwnd, capture_window, ttl=0.1)
        if frame is None:
            return None
        match_area, rx, ry = _prepare_match_area_gray(frame, roi)
    else:
        frame = frame_cache.get_frame(hwnd, capture_window, ttl=0.1)
        if frame is None:
            return None
        match_area, rx, ry = _prepare_match_area_bgr(frame, roi)
    
    template_paths = template_path if isinstance(template_path, list) else [template_path]
    
    best_match = None
    best_val = -1.0
    
    for tpl_path in template_paths:
        template = template_cache.get(tpl_path)
        if template is None:
            print(f"警告: 无法读取模板 {tpl_path}")
            continue
        
        if use_grayscale:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            th, tw = template_gray.shape[:2]
            template_to_match = template_gray
        else:
            th, tw = template.shape[:2]
            template_to_match = template
        
        if th > match_area.shape[0] or tw > match_area.shape[1]:
            print(f"警告: 模板 {tpl_path} 尺寸大于匹配区域，跳过")
            continue
        
        result = cv2.matchTemplate(match_area, template_to_match, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val > best_val:
            best_val = max_val
            best_match = (max_loc, tw, th)
    
    if best_val >= threshold and best_match is not None:
        max_loc, tw, th = best_match
        center_x = max_loc[0] + rx + tw // 2
        center_y = max_loc[1] + ry + th // 2
        
        print(f"区域匹配成功! 置信度: {best_val:.2f}, 坐标: ({center_x}, {center_y})")
        return center_x, center_y
    
    return None


def find_image_grayscale(
    hwnd: int,
    template_path: Union[str, List[str]],
    roi: Optional[List[int]] = None,
    threshold: float = 0.8
) -> Optional[Tuple[int, int]]:
    """
    使用灰度图进行模板匹配（性能优化版）
    
    灰度图匹配计算量约为彩色图的三分之一，适用于对颜色不敏感的 UI 图标匹配。
    
    参数：
        hwnd: 窗口句柄
        template_path: 模板图片路径，可以是单个路径字符串或路径列表
        roi: 裁剪区域 [x, y, w, h]，不传则全屏查找
        threshold: 匹配阈值，默认 0.8
    
    返回：
        tuple: (center_x, center_y) 窗口中心坐标，未找到返回 None
    """
    return find_image(hwnd, template_path, roi, threshold, use_grayscale=True)


def _prepare_match_area_bgr(
    frame: np.ndarray,
    roi: Optional[List[int]]
) -> Tuple[np.ndarray, int, int]:
    """
    准备 BGR 格式的匹配区域
    
    参数：
        frame: BGR 格式的截图矩阵
        roi: 裁剪区域 [x, y, w, h]
    
    返回：
        tuple: (match_area, rx, ry) 匹配区域矩阵和偏移坐标
    """
    if roi:
        rx, ry, rw, rh = roi
        match_area = frame[ry:ry + rh, rx:rx + rw]
    else:
        rx, ry = 0, 0
        match_area = frame
    
    return match_area, rx, ry


def _prepare_match_area_gray(
    frame: np.ndarray,
    roi: Optional[List[int]]
) -> Tuple[np.ndarray, int, int]:
    """
    准备灰度格式的匹配区域
    
    参数：
        frame: 灰度格式的截图矩阵
        roi: 裁剪区域 [x, y, w, h]
    
    返回：
        tuple: (match_area, rx, ry) 匹配区域矩阵和偏移坐标
    """
    if roi:
        rx, ry, rw, rh = roi
        match_area = frame[ry:ry + rh, rx:rx + rw]
    else:
        rx, ry = 0, 0
        match_area = frame
    
    return match_area, rx, ry


def clear_frame_cache() -> None:
    """
    清空截图帧缓存
    
    在执行可能改变画面的操作（如点击、拖拽）后调用，
    确保后续图像识别使用最新画面。
    """
    frame_cache.clear()


def clear_template_cache() -> None:
    """
    清空模板缓存
    
    在模板图片更新后调用，强制重新从磁盘读取。
    """
    template_cache.clear()


def find_all_images(
    hwnd: int,
    template_path: Union[str, List[str]],
    roi: Optional[List[int]] = None,
    threshold: float = 0.8,
    use_grayscale: bool = False,
    min_distance: int = 10
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    查找图像中所有匹配模板的位置（多目标匹配）
    
    参数：
        hwnd: 窗口句柄
        template_path: 模板图片路径，可以是单个路径字符串或路径列表
        roi: 裁剪区域 [x, y, w, h]，不传则全屏查找
        threshold: 匹配阈值，默认 0.8
        use_grayscale: 是否使用灰度图匹配（性能更优），默认 False
        min_distance: 相邻匹配点的最小距离（像素），用于去重，默认 10
    
    返回：
        tuple: (count, positions) 
            - count: 匹配到的数量
            - positions: 坐标列表 [(center_x, center_y), ...]
    """
    if use_grayscale:
        frame = frame_cache.get_frame_grayscale(hwnd, capture_window, ttl=0.1)
        if frame is None:
            return 0, []
        match_area, rx, ry = _prepare_match_area_gray(frame, roi)
    else:
        frame = frame_cache.get_frame(hwnd, capture_window, ttl=0.1)
        if frame is None:
            return 0, []
        match_area, rx, ry = _prepare_match_area_bgr(frame, roi)
    
    template_paths = template_path if isinstance(template_path, list) else [template_path]
    all_positions: List[Tuple[int, int]] = []
    
    for tpl_path in template_paths:
        template = template_cache.get(tpl_path)
        if template is None:
            print(f"警告: 无法读取模板 {tpl_path}")
            continue
        
        if use_grayscale:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            th, tw = template_gray.shape[:2]
            template_to_match = template_gray
        else:
            th, tw = template.shape[:2]
            template_to_match = template
        
        if th > match_area.shape[0] or tw > match_area.shape[1]:
            print(f"警告: 模板 {tpl_path} 尺寸大于匹配区域，跳过")
            continue
        
        result = cv2.matchTemplate(match_area, template_to_match, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + rx + tw // 2
            center_y = pt[1] + ry + th // 2
            
            is_duplicate = False
            for existing_x, existing_y in all_positions:
                dist = np.sqrt((center_x - existing_x) ** 2 + (center_y - existing_y) ** 2)
                if dist < min_distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_positions.append((center_x, center_y))
    
    count = len(all_positions)
    if count > 0:
        print(f"多目标匹配成功! 找到 {count} 个匹配点")
    
    return count, all_positions
