# -*- coding: utf-8 -*-
"""
任务自愈与重试引擎模块
====================
提供统一的任务重试机制、自愈功能和模板检测触发器。

主要功能：
    - with_retry: 任务重试装饰器
    - on_image_detected: 模板检测触发装饰器
    - on_images_detected: 多模板检测触发装饰器
    - on_map_transition: 过图检测装饰器
    - 自动调用自愈函数恢复游戏状态
"""
import functools
import threading
import time
from typing import Callable, Optional, Any, List, Tuple

from src.utils.logger import get_logger
from src.utils import find_image
from src.config import config
from src.core.controller import (
    TaskStoppedException,
    ContextExpiredException,
    InvalidWindowHandleException,
    TargetNotFoundError,
    GameStuckException,
    task_controller
)

logger = get_logger('recovery')


def with_retry(
    max_retries: int = 3,
    retry_delay: float = 2,
    recovery_func: Optional[Callable[[int], Any]] = None
) -> Callable:
    """
    任务重试装饰器
    
    为任务函数提供统一的异常捕获、重试和自愈机制。
    约定被装饰函数的第一个位置参数为窗口句柄 hwnd。
    
    参数：
        max_retries: 最大重试次数，默认 3 次
        retry_delay: 重试间隔时间（秒），默认 2 秒
        recovery_func: 自愈函数，接收 hwnd 参数，用于重试前恢复游戏状态
    
    返回：
        Callable: 装饰后的函数
    
    异常传递规则：
        - 特权放行异常：TaskStoppedException, ContextExpiredException, 
          InvalidWindowHandleException 直接向上抛出，不进行重试
        - 可恢复异常：TargetNotFoundError, GameStuckException, Exception 
          触发重试机制
    
    使用示例：
        @with_retry(max_retries=3, recovery_func=win_gb)
        def task_gua(hwnd, log_signal=None):
            # 任务逻辑
            if not find_npc():
                raise TargetNotFoundError("未找到 NPC")
            return True
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> bool:
            if not args:
                logger.error("被装饰函数缺少必需的 hwnd 参数")
                return False
            
            hwnd = args[0]
            
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                    
                except TaskStoppedException:
                    logger.info("任务被用户停止，直接退出")
                    raise
                    
                except ContextExpiredException:
                    logger.warning("上下文已过期，直接退出")
                    raise
                    
                except InvalidWindowHandleException:
                    logger.error("窗口句柄无效，直接退出")
                    raise
                    
                except (TargetNotFoundError, GameStuckException) as e:
                    logger.warning(f"遭遇异常 [{type(e).__name__}]: {str(e)}，准备第 {attempt} 次重试")
                    
                    if recovery_func is not None and hwnd is not None:
                        try:
                            recovery_func(hwnd)
                            logger.debug("自愈函数执行完成")
                        except Exception as recovery_error:
                            logger.warning(f"自愈函数执行异常: {recovery_error}")
                    
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"重试 {max_retries} 次后仍失败，任务终止")
                        return False
                        
                except Exception as e:
                    logger.warning(f"遭遇未预期异常 [{type(e).__name__}]: {str(e)}，准备第 {attempt} 次重试")
                    
                    if recovery_func is not None and hwnd is not None:
                        try:
                            recovery_func(hwnd)
                            logger.debug("自愈函数执行完成")
                        except Exception as recovery_error:
                            logger.warning(f"自愈函数执行异常: {recovery_error}")
                    
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"重试 {max_retries} 次后仍失败，任务终止")
                        return False
            
            return False
        
        return wrapper
    return decorator


def on_image_detected(
    image_path: str,
    action: Callable[[int, Tuple[int, int]], None],
    threshold: float = 0.8,
    interval: float = 2.0,
    roi: Optional[List[int]] = None,
    once: bool = True
) -> Callable:
    """
    模板检测触发装饰器
    
    在后台线程中持续检测指定图片，当匹配成功时执行对应的操作。
    不阻塞主任务流程，实现并行检测。
    
    参数：
        image_path: 图片路径（相对于 images 目录）
        action: 检测到图片时执行的回调函数，签名为 action(hwnd, pos) -> None
                - hwnd: 窗口句柄
                - pos: 匹配到的坐标 (x, y)
        threshold: 匹配阈值，默认 0.8
        interval: 检测间隔（秒），默认 2.0
        roi: 检测区域 [x, y, w, h]，默认全屏
        once: 是否只触发一次，默认 True
    
    返回：
        Callable: 装饰后的函数
    
    使用示例：
        def handle_popup(hwnd, pos):
            '''处理弹窗的回调函数'''
            logger.info(f"点击弹窗位置: {pos}")
            background_click(hwnd, pos[0], pos[1], button="left", delay=60)
        
        @on_image_detected(
            image_path="richang_/fuben_louji/special_popup.png",
            action=handle_popup,
            interval=1.0
        )
        def _fuben_louji(hwnd):
            # 主任务逻辑
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not args:
                logger.error("被装饰函数缺少必需的 hwnd 参数")
                return func(*args, **kwargs)
            
            hwnd = args[0]
            stop_flag = threading.Event()
            triggered = threading.Event()
            
            def detector():
                while not stop_flag.is_set():
                    try:
                        pos = find_image(
                            hwnd,
                            config.get_img_path(image_path),
                            roi=roi,
                            threshold=threshold
                        )
                        if pos is not None:
                            if once and triggered.is_set():
                                pass
                            else:
                                logger.info(f"检测到模板 [{image_path}]，执行操作")
                                try:
                                    action(hwnd, pos)
                                    triggered.set()
                                except Exception as e:
                                    logger.warning(f"模板检测回调执行异常: {e}")
                    except Exception as e:
                        logger.debug(f"模板检测异常: {e}")
                    
                    stop_flag.wait(interval)
            
            detector_thread = threading.Thread(target=detector, daemon=True)
            detector_thread.start()
            
            try:
                result = func(*args, **kwargs)
            finally:
                stop_flag.set()
                detector_thread.join(timeout=1)
            
            return result
        
        return wrapper
    return decorator


def on_map_transition(
    interval: float = 2.0,
    wait_time: float = 5.0,
    threshold: float = 0.8
) -> Callable:
    """
    过图检测装饰器
    
    在后台线程中持续检测过图动画，当检测到过图时等待过图完成。
    不阻塞主任务流程，实现并行检测。
    
    Args:
        interval: 检测间隔（秒），默认 2.0
        wait_time: 检测到过图后的等待时间（秒），默认 5.0
        threshold: 匹配阈值，默认 0.8
    
    Returns:
        Callable: 装饰后的函数
    
    使用示例：
        @on_map_transition(interval=2.0, wait_time=5.0)
        def my_task(hwnd):
            # 主任务逻辑
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not args:
                logger.error("被装饰函数缺少必需的 hwnd 参数")
                return func(*args, **kwargs)
            
            hwnd = args[0]
            stop_flag = threading.Event()
            
            goutu_images = [
                config.get_img_path("chushihua_/goutu_1.png"),
                config.get_img_path("chushihua_/goutu_2.png"),
                config.get_img_path("chushihua_/goutu_3.png"),
            ]
            
            def detector():
                while not stop_flag.is_set():
                    try:
                        pos = find_image(hwnd, goutu_images, threshold=threshold)
                        if pos is not None:
                            logger.info("过图动画中")
                            task_controller.smart_sleep(wait_time)
                    except Exception as e:
                        logger.debug(f"过图检测异常: {e}")
                    
                    stop_flag.wait(interval)
            
            detector_thread = threading.Thread(target=detector, daemon=True)
            detector_thread.start()
            
            try:
                result = func(*args, **kwargs)
            finally:
                stop_flag.set()
                detector_thread.join(timeout=1)
            
            return result
        
        return wrapper
    return decorator


def on_images_detected(
    patterns: List[dict],
    interval: float = 2.0
) -> Callable:
    """
    多模板检测触发装饰器
    
    同时检测多个图片模板，当任意一个匹配成功时执行对应的操作。
    
    参数：
        patterns: 检测模式列表，每个元素包含：
            - image_path: 图片路径（必需）
            - action: 触发函数 action(hwnd, pos) -> None（必需）
            - threshold: 匹配阈值，默认 0.8
            - roi: 检测区域 [x, y, w, h]，默认全屏
            - once: 是否只触发一次，默认 True
        interval: 检测间隔（秒），默认 2.0
    
    返回：
        Callable: 装饰后的函数
    
    使用示例：
        @on_images_detected([
            {
                "image_path": "richang_/popup1.png",
                "action": lambda h, p: background_click(h, p[0], p[1]),
                "threshold": 0.8
            },
            {
                "image_path": "richang_/popup2.png",
                "action": handle_popup2,
                "threshold": 0.9,
                "once": False
            }
        ], interval=1.0)
        def my_task(hwnd):
            # 主任务逻辑
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not args:
                logger.error("被装饰函数缺少必需的 hwnd 参数")
                return func(*args, **kwargs)
            
            hwnd = args[0]
            stop_flag = threading.Event()
            triggered = set()
            
            def detector():
                while not stop_flag.is_set():
                    for idx, pattern in enumerate(patterns):
                        if pattern.get("once", True) and idx in triggered:
                            continue
                        
                        try:
                            pos = find_image(
                                hwnd,
                                config.get_img_path(pattern["image_path"]),
                                roi=pattern.get("roi"),
                                threshold=pattern.get("threshold", 0.8)
                            )
                            if pos is not None:
                                logger.debug(f"检测到模板 [{pattern['image_path']}]")
                                try:
                                    pattern["action"](hwnd, pos)
                                    if pattern.get("once", True):
                                        triggered.add(idx)
                                except Exception as e:
                                    logger.warning(f"模板检测回调执行异常: {e}")
                        except Exception as e:
                            logger.debug(f"模板检测异常: {e}")
                    
                    stop_flag.wait(interval)
            
            detector_thread = threading.Thread(target=detector, daemon=True)
            detector_thread.start()
            
            try:
                result = func(*args, **kwargs)
            finally:
                stop_flag.set()
                detector_thread.join(timeout=1)
            
            return result
        
        return wrapper
    return decorator
