# -*- coding: utf-8 -*-
"""
Windows API 工具模块
====================
封装 Windows API 实现后台操作功能

主要功能：
    - bind_window: 绑定窗口句柄
    - background_click: 后台点击
    - background_key: 后台按键
    - background_drag: 后台拖拽
    - capture_window: 窗口截图
"""
import time
import json
import win32gui
import win32api
import win32con
import win32ui
import win32process
import ctypes
from PIL import Image
from src.config import config
from src.utils.input_tracker import InputTracker
from src.core.controller import InvalidWindowHandleException
from src.utils.cache import frame_cache


def _validate_hwnd(hwnd: int) -> None:
    """
    验证窗口句柄有效性
    
    参数：
        hwnd: 窗口句柄
        
    异常：
        InvalidWindowHandleException: 当窗口句柄无效时抛出
    """
    if not win32gui.IsWindow(hwnd):
        raise InvalidWindowHandleException(f"窗口句柄无效: {hwnd}")


def bind_window(title=None, class_name=None, index=0, pid=None, pick=False, timeout=10):
    """
    绑定窗口句柄（通用版）

    参数：
        title       : 窗口标题（可选）
        class_name  : 窗口类名（可选）
        index       : 多开时选择第几个（默认第0个）
        pid         : 指定进程PID（最高精度）
        pick        : 是否启用鼠标点选绑定（True时忽略其它条件）
        timeout     : 等待窗口出现的时间

    返回：
        hwnd (int)  : 成功返回句柄，失败返回 None
    """
    if pick:
        print("请在 {} 秒内把鼠标移动到目标窗口上...".format(3))
        time.sleep(3)
        pos = win32api.GetCursorPos()
        hwnd = win32gui.WindowFromPoint(pos)
        hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
        if win32gui.IsWindow(hwnd):
            print("✔ 点选绑定成功:", hwnd)
            return hwnd
        return None

    end_time = time.time() + timeout
    while time.time() < end_time:
        hwnd_list = []

        def enum_handler(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            t = win32gui.GetWindowText(hwnd)
            c = win32gui.GetClassName(hwnd)
            if title and title not in t:
                return
            if class_name and class_name != c:
                return
            if pid:
                _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
                if win_pid != pid:
                    return
            hwnd_list.append(hwnd)

        win32gui.EnumWindows(enum_handler, None)

        if hwnd_list:
            if index >= len(hwnd_list):
                print("⚠ 找到窗口 {} 个，但 index={} 越界".format(len(hwnd_list), index))
                return None
            hwnd = hwnd_list[index]
            print("✔ 绑定成功:", hwnd)
            return hwnd
        time.sleep(0.5)

    print("✖ 绑定失败：未找到窗口")
    return None


def background_click(hwnd, x, y, button="left", action="click", delay=50):
    """
    后台点击函数（支持原子性保证）

    参数：
        hwnd    : 目标窗口句柄
        x, y    : 点击坐标（客户区坐标，不是屏幕坐标）
        button  : "left" | "right" | "middle"
        action  : "click"（按下并释放）| "down"（仅按下）| "up"（仅释放）| "double"（双击）
        delay   : 点击按下与抬起之间的延迟（毫秒）

    返回：
        bool: 操作是否成功

    异常：
        InvalidWindowHandleException: 当窗口句柄无效时抛出

    原子性保证:
        - action="down": 先记录到 InputTracker，再发送 API，失败时撤销记录
        - action="up": 先发送 API，再清除 InputTracker 记录
        - action="click"/"double": 追踪整个按下-释放过程
    """
    _validate_hwnd(hwnd)

    tracker = InputTracker.get_instance()
    lparam = (y << 16) | x
    button_lower = button.lower()

    try:
        win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)

        if action == "down":
            if button_lower == "left":
                tracker.track_mouse_down(hwnd, "left")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "left")
                    print(f"发送 LBUTTONDOWN 失败: {e}")
                    return False

            elif button_lower == "right":
                tracker.track_mouse_down(hwnd, "right")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "right")
                    print(f"发送 RBUTTONDOWN 失败: {e}")
                    return False

            elif button_lower == "middle":
                tracker.track_mouse_down(hwnd, "middle")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, lparam)
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "middle")
                    print(f"发送 MBUTTONDOWN 失败: {e}")
                    return False

            else:
                print(f"不支持的鼠标按钮: {button}")
                return False

        elif action == "up":
            if button_lower == "left":
                try:
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "left")
                    return True
                except Exception as e:
                    print(f"发送 LBUTTONUP 失败: {e}")
                    return False

            elif button_lower == "right":
                try:
                    win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "right")
                    return True
                except Exception as e:
                    print(f"发送 RBUTTONUP 失败: {e}")
                    return False

            elif button_lower == "middle":
                try:
                    win32api.PostMessage(hwnd, win32con.WM_MBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "middle")
                    return True
                except Exception as e:
                    print(f"发送 MBUTTONUP 失败: {e}")
                    return False

            else:
                print(f"不支持的鼠标按钮: {button}")
                return False

        elif action == "click":
            if button_lower == "left":
                tracker.track_mouse_down(hwnd, "left")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    time.sleep(delay / 1000.0)
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "left")
                    frame_cache.clear()
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "left")
                    print(f"发送左键点击失败: {e}")
                    return False

            elif button_lower == "right":
                tracker.track_mouse_down(hwnd, "right")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
                    time.sleep(delay / 1000.0)
                    win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "right")
                    frame_cache.clear()
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "right")
                    print(f"发送右键点击失败: {e}")
                    return False

            elif button_lower == "middle":
                tracker.track_mouse_down(hwnd, "middle")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, lparam)
                    time.sleep(delay / 1000.0)
                    win32api.PostMessage(hwnd, win32con.WM_MBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "middle")
                    frame_cache.clear()
                    return True
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "middle")
                    print(f"发送中键点击失败: {e}")
                    return False

            else:
                print(f"不支持的鼠标按钮: {button}")
                return False

        elif action == "double":
            if button_lower == "left":
                tracker.track_mouse_down(hwnd, "left")
                try:
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    tracker.track_mouse_up(hwnd, "left")
                    time.sleep(0.05)
                    tracker.track_mouse_down(hwnd, "left")
                    try:
                        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                        time.sleep(delay / 1000.0)
                        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                        tracker.track_mouse_up(hwnd, "left")
                        frame_cache.clear()
                        return True
                    except Exception as e:
                        tracker.track_mouse_up(hwnd, "left")
                        print(f"发送双击第二次点击失败: {e}")
                        return False
                except Exception as e:
                    tracker.track_mouse_up(hwnd, "left")
                    print(f"发送双击第一次点击失败: {e}")
                    return False

            else:
                print(f"双击仅支持左键，当前按钮: {button}")
                return False

        else:
            print(f"不支持的 action 参数: {action}")
            return False

    except Exception as e:
        print(f"后台点击失败: {e}")
        return False


def _get_vk(key: str):
    """
    自动识别字母 / 特殊键
    
    参数：
        key: 按键名称
        
    返回：
        int: VK码
    """
    key = key.upper()
    if key in config.VK_CODE:
        return config.VK_CODE[key]
    if len(key) == 1:
        return ord(key)
    raise ValueError(f"不支持的按键: {key}")


def background_key(hwnd, key, action="press", hold=50):
    """
    向指定窗口后台发送按键（支持原子性保证）

    参数:
        hwnd   : 窗口句柄
        key    : 'A' / 'ESC' / 'ENTER'
        action : "press"（按下并释放）| "down"（仅按下）| "up"（仅释放）
        hold   : 按下持续时间(ms)，仅 action="press" 时有效

    返回:
        bool: 操作是否成功

    异常:
        InvalidWindowHandleException: 当窗口句柄无效时抛出

    原子性保证:
        - action="down": 先记录到 InputTracker，再发送 API，失败时撤销记录
        - action="up": 先发送 API，再清除 InputTracker 记录
        - action="press": 追踪整个按下-释放过程
    """
    _validate_hwnd(hwnd)

    tracker = InputTracker.get_instance()
    vk = _get_vk(key)
    scan = win32api.MapVirtualKey(vk, 0)

    lparam_down = 1 | (scan << 16)
    lparam_up = 1 | (scan << 16) | (1 << 30) | (1 << 31)

    key_lower = key.lower()

    if action == "down":
        tracker.track_key_down(hwnd, key_lower)
        try:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, lparam_down)
            return True
        except Exception as e:
            tracker.track_key_up(hwnd, key_lower)
            print(f"发送 KeyDown 失败 (key={key}): {e}")
            return False

    elif action == "up":
        try:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, lparam_up)
            tracker.track_key_up(hwnd, key_lower)
            return True
        except Exception as e:
            print(f"发送 KeyUp 失败 (key={key}): {e}")
            return False

    elif action == "press":
        tracker.track_key_down(hwnd, key_lower)
        try:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, lparam_down)
            time.sleep(hold / 1000)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, lparam_up)
            tracker.track_key_up(hwnd, key_lower)
            return True
        except Exception as e:
            tracker.track_key_up(hwnd, key_lower)
            print(f"发送按键失败 (key={key}): {e}")
            return False

    else:
        print(f"不支持的 action 参数: {action}")
        return False


def run_key_config(hwnd, config_path):
    """
    按配置文件顺序执行按键
    """
    with open(config_path, "r", encoding="utf-8") as f:
        actions = json.load(f)

    for act in actions:
        key = act["key"]
        delay = act.get("delay", 300)
        background_key(hwnd, key)
        time.sleep(delay / 1000)


def capture_window(hwnd, save_path=None):
    """
    截取窗口客户区图像

    参数：
        hwnd: 窗口句柄
        save_path: 保存路径（可选）

    返回：
        PIL.Image: 截图图像，失败返回None
    """
    try:
        if not win32gui.IsWindow(hwnd):
            print("截图失败：无效的窗口句柄")
            return None
        
        if not win32gui.IsWindowVisible(hwnd):
            print("截图失败：窗口不可见")
            return None
        
        ctypes.windll.user32.SetProcessDPIAware()

        left, top, right, bot = win32gui.GetClientRect(hwnd)
        w = right - left
        h = bot - top
        
        if w <= 0 or h <= 0:
            print("截图失败：窗口尺寸无效")
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)
        if not hwndDC:
            print("截图失败：无法获取窗口DC")
            return None
        
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)

        point = win32gui.ClientToScreen(hwnd, (0, 0))
        window_rect = win32gui.GetWindowRect(hwnd)

        offset_x = point[0] - window_rect[0]
        offset_y = point[1] - window_rect[1]

        saveDC.BitBlt((0, 0), (w, h), mfcDC, (offset_x, offset_y), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        if save_path:
            im.save(save_path)
            print(f"截图已保存到: {save_path}")
            return True
        return im
    
    except Exception as e:
        print(f"截图失败：{e}")
        return None


def background_drag(hwnd, start_x, start_y, end_x, end_y, drag_duration=0.5):
    """
    后台拖拽操作（支持原子性保证）

    参数：
        hwnd: 窗口句柄
        start_x, start_y: 起始坐标
        end_x, end_y: 结束坐标
        drag_duration: 拖拽时长（秒）

    返回：
        bool: 操作是否成功

    异常：
        InvalidWindowHandleException: 当窗口句柄无效时抛出

    原子性保证:
        - 拖拽开始时记录 left down 到 InputTracker
        - 拖拽过程中持续追踪左键状态
        - 拖拽结束时记录 left up，失败时撤销记录
    """
    _validate_hwnd(hwnd)

    tracker = InputTracker.get_instance()

    def make_lparam(x, y):
        return win32api.MAKELONG(x, y)

    tracker.track_mouse_down(hwnd, "left")
    try:
        l_param_start = make_lparam(start_x, start_y)
        win32gui.SendMessage(
            hwnd,
            win32con.WM_LBUTTONDOWN,
            win32con.MK_LBUTTON,
            l_param_start
        )
        time.sleep(0.05)

        steps = int(drag_duration / 0.01)
        dx = (end_x - start_x) / steps
        dy = (end_y - start_y) / steps

        current_x, current_y = start_x, start_y
        for _ in range(steps):
            current_x += dx
            current_y += dy
            l_param_move = make_lparam(int(current_x), int(current_y))
            win32gui.SendMessage(
                hwnd,
                win32con.WM_MOUSEMOVE,
                win32con.MK_LBUTTON,
                l_param_move
            )
            time.sleep(0.01)

        l_param_end = make_lparam(end_x, end_y)
        win32gui.SendMessage(
            hwnd,
            win32con.WM_LBUTTONUP,
            0,
            l_param_end
        )
        tracker.track_mouse_up(hwnd, "left")
        frame_cache.clear()

        print(f"✅ 后台滑动操作完成：({start_x}, {start_y}) → ({end_x}, {end_y})")
        return True

    except Exception as e:
        tracker.track_mouse_up(hwnd, "left")
        print(f"❌ 后台滑动操作失败：{e}")
        return False


def _send_key_up(hwnd: int, key: str) -> bool:
    """
    发送单个按键的 KeyUp 事件
    
    参数：
        hwnd: 窗口句柄
        key: 按键名称（如 'a', 'enter', 'space' 等）
        
    返回：
        bool: 操作是否成功
    """
    try:
        vk = _get_vk(key)
        scan = win32api.MapVirtualKey(vk, 0)
        lparam_up = 1 | (scan << 16) | (1 << 30) | (1 << 31)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, lparam_up)
        return True
    except Exception as e:
        print(f"发送 KeyUp 失败 (key={key}): {e}")
        return False


def _send_button_up(hwnd: int, button: str, x: int = 0, y: int = 0) -> bool:
    """
    发送单个鼠标按钮的 ButtonUp 事件
    
    参数：
        hwnd: 窗口句柄
        button: 鼠标按钮名称（'left', 'right', 'middle'）
        x: X 坐标（默认为 0）
        y: Y 坐标（默认为 0）
        
    返回：
        bool: 操作是否成功
    """
    try:
        lparam = (y << 16) | x
        button = button.lower()
        
        if button == "left":
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        elif button == "right":
            win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
        elif button == "middle":
            win32api.PostMessage(hwnd, win32con.WM_MBUTTONUP, 0, lparam)
        else:
            print(f"不支持的鼠标按钮: {button}")
            return False
        return True
    except Exception as e:
        print(f"发送 ButtonUp 失败 (button={button}): {e}")
        return False


def release_tracked_inputs(hwnd: int) -> bool:
    """
    精准释放追踪到的输入状态
    
    从 InputTracker 获取处于 Down 状态的按键和鼠标按钮，
    仅对这些按键和按钮发送 KeyUp/ButtonUp 事件，然后清空追踪状态。
    
    如果 InputTracker 为空或无记录，则仅发送鼠标左键和右键的 ButtonUp 作为兜底。
    
    参数：
        hwnd: 窗口句柄
        
    返回：
        bool: 操作是否成功（即使部分失败也返回 True，除非发生严重错误）
        
    注意：
        - 不会遍历所有虚拟键码发送 KeyUp
        - 不会触发系统粘滞键功能
        - 不会干扰用户正在进行的物理输入
        - 异常不会向外抛出，确保 finally 块继续执行
    """
    try:
        if not win32gui.IsWindow(hwnd):
            print(f"释放输入失败：无效的窗口句柄 {hwnd}")
            return False
        
        tracker = InputTracker.get_instance()
        pressed_keys = tracker.get_pressed_keys()
        pressed_buttons = tracker.get_pressed_buttons()
        
        has_tracked_inputs = bool(pressed_keys) or bool(pressed_buttons)
        
        if has_tracked_inputs:
            for key in pressed_keys:
                _send_key_up(hwnd, key)
            
            for button in pressed_buttons:
                _send_button_up(hwnd, button)
            
            tracker.clear()
            
            print(f"✅ 已释放追踪的输入: keys={list(pressed_keys)}, buttons={list(pressed_buttons)}")
        else:
            _send_button_up(hwnd, "left")
            _send_button_up(hwnd, "right")
            
            print("⚠ 无追踪记录，已执行兜底释放（仅鼠标左右键）")
        
        return True
        
    except Exception as e:
        print(f"❌ 释放输入时发生错误: {e}")
        return False
