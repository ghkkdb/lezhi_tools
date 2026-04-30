# -*- coding: utf-8 -*-
"""
调试脚本
========
用于开发和测试阶段的功能验证
"""
import sys
sys.path.insert(0, '.')

from src.utils import bind_window, capture_window, find_image, background_click
from src.config import config
import time


def debug_capture():
    """
    调试截图功能
    """
    hwnd = bind_window(class_name=config.class_name)
    if hwnd:
        img = capture_window(hwnd, 'assets/img/test.jpg')
        print(f"截图成功: {img}")
    else:
        print("绑定窗口失败")


def debug_find_image():
    """
    调试图像识别功能
    """
    hwnd = bind_window(class_name=config.class_name)
    if hwnd:
        pos = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
        if pos:
            print(f"找到目标，坐标: {pos}")
            background_click(hwnd, pos[0], pos[1], button="left", delay=60)
        else:
            print("未找到目标")
    else:
        print("绑定窗口失败")


if __name__ == "__main__":
    print("调试脚本启动...")
    debug_capture()
