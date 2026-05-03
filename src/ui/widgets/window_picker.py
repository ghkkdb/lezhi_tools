# -*- coding: utf-8 -*-
"""
窗口选择器组件
==============
实现鼠标拖拽识别目标窗口的功能

主要功能：
    - 窗口识别：通过鼠标拖拽识别目标游戏窗口
    - 窗口调整：绑定前自动调整窗口大小和位置
    - 区域截图：截取窗口指定区域图片
    - 窗口锁定：锁定窗口大小，防止用户调整
"""
import win32gui
import win32api
import win32con
import time
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from src.utils import background_key, capture_window
from src.config import config


class WindowPicker(QObject):
    """
    窗口选择器类
    
    信号：
        window_picked: 窗口选择成功，参数为(句柄, 区域截图)
        pick_failed: 窗口选择失败
        pick_status: 状态更新消息
    """
    
    window_picked = pyqtSignal(int, object)
    pick_failed = pyqtSignal()
    pick_status = pyqtSignal(str)
    
    LOCKED_STYLES = (
        win32con.WS_THICKFRAME |  
        win32con.WS_MAXIMIZEBOX |
        win32con.WS_MINIMIZEBOX   
    )

    def __init__(self):
        """
        初始化窗口选择器
        """
        super().__init__()
        self.is_picking = False
        self.target_class_name = config.class_name
        self.target_width = config.x
        self.target_height = config.y
        
        self.capture_x = 420
        self.capture_y = 170
        self.capture_width = 100
        self.capture_height = 30
        
        self._original_styles = {}

    def get_same_class_windows(self, exclude_hwnd: int = None) -> list:
        """
        获取所有同类型窗口的位置和尺寸信息

        Args:
            exclude_hwnd: 要排除的窗口句柄（通常是当前正在绑定的窗口）

        Returns:
            list: 窗口信息列表，每个元素为 (hwnd, x, y, width, height)
        """
        windows = []
        
        def enum_callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                class_name = win32gui.GetClassName(hwnd)
                if class_name != self.target_class_name:
                    return True
                
                if hwnd == exclude_hwnd:
                    return True
                
                rect = win32gui.GetWindowRect(hwnd)
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y
                
                if width <= 0 or height <= 0:
                    return True
                
                windows.append((hwnd, x, y, width, height))
                
            except Exception:
                pass
            
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        
        windows.sort(key=lambda w: (w[2], w[1]))
        
        return windows

    def calculate_window_position(self, exclude_hwnd: int = None) -> tuple:
        """
        计算新窗口的最佳位置

        Args:
            exclude_hwnd: 要排除的窗口句柄

        Returns:
            tuple: (x, y) 目标位置坐标
        """
        try:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
        except Exception:
            screen_width = 1920
            screen_height = 1080
        
        window_spacing = getattr(config, 'window_spacing', 10)
        
        same_windows = self.get_same_class_windows(exclude_hwnd)
        
        if not same_windows:
            return (0, 0)
        
        max_x = 0
        max_y = 0
        last_window = None
        
        for win_info in same_windows:
            _, x, y, width, height = win_info
            if y <= max_y:
                if x + width > max_x:
                    max_x = x + width
                    last_window = win_info
                max_y = y
        
        if last_window:
            _, last_x, last_y, last_width, last_height = last_window
            new_x = last_x + last_width + window_spacing
            new_y = last_y
            
            if new_x + self.target_width > screen_width:
                max_row_height = 0
                for win_info in same_windows:
                    _, _, y, _, height = win_info
                    if y == last_y:
                        max_row_height = max(max_row_height, height)
                
                new_x = 0
                new_y = last_y + max_row_height + window_spacing
                
                if new_y + self.target_height > screen_height:
                    return (0, 0)
            
            return (new_x, new_y)
        
        return (0, 0)

    def resize_and_move_window(self, hwnd, use_smart_arrangement: bool = None):
        """
        调整窗口大小并移动到指定位置

        Args:
            hwnd: 窗口句柄
            use_smart_arrangement: 是否使用智能排列（None时使用配置值）

        Returns:
            bool: 操作成功返回True，失败返回False
        """
        try:
            if use_smart_arrangement is None:
                use_smart_arrangement = getattr(config, 'smart_arrangement', True)
            
            if use_smart_arrangement:
                x, y = self.calculate_window_position(exclude_hwnd=hwnd)
            else:
                x, y = 0, 0
            
            win32gui.SetWindowPos(
                hwnd,
                0,
                x,
                y,
                self.target_width,
                self.target_height,
                0x0004 | 0x0040
            )
            
            time.sleep(0.3)
            return True
            
        except Exception as e:
            print(f"调整窗口大小失败: {str(e)}")
            return False

    def resize_window_keep_position(self, hwnd) -> bool:
        """按配置调整窗口大小，保持当前窗口位置不变。"""
        try:
            if not win32gui.IsWindow(hwnd):
                return False

            left, top, _right, _bottom = win32gui.GetWindowRect(hwnd)
            win32gui.SetWindowPos(
                hwnd,
                0,
                left,
                top,
                self.target_width,
                self.target_height,
                0x0004 | 0x0040
            )

            time.sleep(0.3)
            return True

        except Exception as e:
            print(f"调整窗口大小失败: {str(e)}")
            return False

    def capture_region(self, hwnd, adjust_window: bool = True):
        """
        截取窗口指定区域的图片

        参数：
            hwnd: 窗口句柄

        返回：
            PIL.Image: 截取的区域图片，失败返回None
        """
        try:
            if adjust_window and not self.resize_window_keep_position(hwnd):
                self.pick_status.emit("警告：窗口大小调整失败")
            
            # background_key(hwnd, 'SPACE')
            # time.sleep(3)
            
            full_img = capture_window(hwnd)
            if full_img is None:
                return None
            
            region_img = full_img.crop((
                self.capture_x,
                self.capture_y,
                self.capture_x + self.capture_width,
                self.capture_y + self.capture_height
            ))
            
            return region_img
            
        except Exception as e:
            print(f"截取区域失败: {str(e)}")
            return None

    def start_pick(self, parent_widget=None):
        """
        开始选择窗口（定时方式）

        参数：
            parent_widget: 父窗口，用于显示警告对话框
        """
        self.is_picking = True
        self.pick_status.emit("请将鼠标移动到目标窗口...")
        
        time.sleep(2)
        
        try:
            pos = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(pos)
            hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            
            if not win32gui.IsWindow(hwnd):
                self.pick_status.emit("错误：无效的窗口句柄")
                self.is_picking = False
                if parent_widget:
                    QMessageBox.warning(parent_widget, "警告", "未找到有效的窗口！")
                self.pick_failed.emit()
                return
            
            class_name = win32gui.GetClassName(hwnd)
            self.pick_status.emit(f"检测到窗口类名: {class_name}")
            
            if class_name == self.target_class_name:
                self.pick_status.emit(f"窗口匹配成功！句柄: {hwnd}")
                self.pick_status.emit("正在绑定窗口并截图...")
                region_img = self.capture_region(hwnd)
                self.window_picked.emit(hwnd, region_img)
            else:
                self.pick_status.emit(f"窗口类名不匹配: {class_name}")
                if parent_widget:
                    QMessageBox.warning(
                        parent_widget,
                        "警告",
                        f"未找到目标窗口！\n\n检测到的窗口类名: {class_name}\n目标窗口类名: {self.target_class_name}"
                    )
                self.pick_failed.emit()
                
        except Exception as e:
            self.pick_status.emit(f"选择窗口时发生错误: {str(e)}")
            if parent_widget:
                QMessageBox.warning(parent_widget, "错误", f"选择窗口时发生错误:\n{str(e)}")
            self.pick_failed.emit()
    
    def lock_window_size(self, hwnd: int) -> bool:
        """
        锁定窗口大小，禁止用户调整窗口尺寸

        Args:
            hwnd: 窗口句柄

        Returns:
            bool: 操作成功返回 True，失败返回 False
        """
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            
            if hwnd not in self._original_styles:
                self._original_styles[hwnd] = current_style
            
            new_style = current_style & ~self.LOCKED_STYLES
            
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
            
            win32gui.SetWindowPos(
                hwnd,
                0,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
            )
            
            return True
            
        except Exception as e:
            print(f"锁定窗口大小失败: {str(e)}")
            return False
    
    def unlock_window_size(self, hwnd: int) -> bool:
        """
        解锁窗口大小，恢复用户调整窗口尺寸的能力

        Args:
            hwnd: 窗口句柄

        Returns:
            bool: 操作成功返回 True，失败返回 False
        """
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            if hwnd not in self._original_styles:
                return True
            
            original_style = self._original_styles[hwnd]
            
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, original_style)
            
            win32gui.SetWindowPos(
                hwnd,
                0,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
            )
            
            del self._original_styles[hwnd]
            
            return True
            
        except Exception as e:
            print(f"解锁窗口大小失败: {str(e)}")
            return False

    def pick_at_position(self, parent_widget=None):
        """
        在当前位置立即执行窗口识别

        参数：
            parent_widget: 父窗口，用于显示警告对话框
        """
        try:
            pos = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(pos)
            hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            
            if not win32gui.IsWindow(hwnd):
                self.pick_status.emit("错误：无效的窗口句柄")
                if parent_widget:
                    QMessageBox.warning(parent_widget, "警告", "未找到有效的窗口！")
                self.pick_failed.emit()
                return
            
            class_name = win32gui.GetClassName(hwnd)
            self.pick_status.emit(f"检测到窗口类名: {class_name}")
            
            if class_name == self.target_class_name:
                self.pick_status.emit(f"窗口匹配成功！句柄: {hwnd}")
                self.pick_status.emit("正在绑定窗口并截图...")
                region_img = self.capture_region(hwnd)
                self.window_picked.emit(hwnd, region_img)
            else:
                self.pick_status.emit(f"窗口类名不匹配: {class_name}")
                if parent_widget:
                    QMessageBox.warning(
                        parent_widget,
                        "警告",
                        f"未找到目标窗口！\n\n检测到的窗口类名: {class_name}\n目标窗口类名: {self.target_class_name}"
                    )
                self.pick_failed.emit()
                
        except Exception as e:
            self.pick_status.emit(f"选择窗口时发生错误: {str(e)}")
            if parent_widget:
                QMessageBox.warning(parent_widget, "错误", f"选择窗口时发生错误:\n{str(e)}")
            self.pick_failed.emit()
