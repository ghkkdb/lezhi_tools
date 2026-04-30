# -*- coding: utf-8 -*-
"""
任务控制器模块
==============
提供任务执行的控制功能，包括暂停、继续、停止等操作

主要功能：
    - TaskController: 任务控制器单例类
    - TaskStoppedException: 用户强制停止异常
    - ContextExpiredException: 上下文过期异常
    - InvalidWindowHandleException: 窗口句柄无效异常
"""
import threading
import time
from typing import Optional
from src.config import config


class TaskStoppedException(Exception):
    """
    任务被用户强制停止异常
    
    当用户点击停止按钮或调用 stop() 方法后，
    任务执行过程中检测到停止信号时抛出此异常
    """
    pass


class ContextExpiredException(Exception):
    """
    上下文过期异常
    
    当任务暂停时间超过阈值，导致游戏状态可能发生变化，
    继续执行可能产生不可预期结果时抛出此异常
    """
    pass


class InvalidWindowHandleException(Exception):
    """
    窗口句柄无效异常
    
    当目标窗口句柄无效或窗口已关闭时抛出此异常
    """
    pass


class TargetNotFoundError(Exception):
    """
    目标未找到异常
    
    当任务执行过程中无法找到目标对象（如 NPC、按钮等）时抛出此异常
    """
    pass


class GameStuckException(Exception):
    """
    流程卡死异常
    
    当任务执行过程中遇到流程卡死或未知界面时抛出此异常
    """
    pass


class TaskController:
    """
    任务控制器单例类
    
    用于控制任务的执行状态，支持暂停、继续、停止操作。
    使用 threading.Event 实现线程间的同步控制。
    
    属性：
        _instance: 单例实例
        _pause_event: 暂停事件（True=放行，False=阻塞）
        _stop_event: 停止事件（True=触发停止）
        _pause_start_time: 暂停开始时间戳
        _custom_timeout: 任务自定义超时阈值（秒）
    
    使用示例：
        controller = TaskController.get_instance()
        
        # 在任务执行前
        controller.check_status()  # 检查是否需要停止或暂停
        
        # UI 控制
        controller.pause()   # 暂停任务
        controller.resume()  # 继续任务
        controller.stop()    # 停止任务
    """
    
    _instance: Optional['TaskController'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls, isolated: bool = False) -> 'TaskController':
        """
        创建单例实例
        
        返回：
            TaskController: 单例实例
        """
        if isolated:
            instance = super().__new__(cls)
            instance._initialized = False
            return instance

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, isolated: bool = False):
        """
        初始化任务控制器
        
        初始化事件对象和状态变量
        """
        if self._initialized:
            return
        
        self._pause_event: threading.Event = threading.Event()
        self._stop_event: threading.Event = threading.Event()
        self._pause_start_time: Optional[float] = None
        self._custom_timeout: Optional[float] = None
        self._initialized = True
        
        self._pause_event.set()
    
    @classmethod
    def get_instance(cls) -> 'TaskController':
        """
        获取单例实例
        
        返回：
            TaskController: 单例实例
        """
        return cls()
    
    @classmethod
    def reset_instance(cls):
        """
        重置单例实例
        
        用于测试或需要完全重置控制器状态时使用
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance._pause_event.set()
                cls._instance._stop_event.clear()
                cls._instance._pause_start_time = None
                cls._instance._custom_timeout = None
            cls._instance = None
    
    def pause(self, timeout: Optional[float] = None) -> None:
        """
        暂停任务执行
        
        清除暂停事件，使任务在调用 check_status() 时阻塞。
        同时记录暂停开始时间戳，用于后续超时检测。
        
        参数：
            timeout: 可选的自定义超时时间（秒），
                    如果暂停时间超过此值，resume() 时会抛出异常
                    None 表示使用默认超时或不检测超时
        """
        self._pause_start_time = time.time()
        self._custom_timeout = timeout
        self._pause_event.clear()
    
    def resume(self) -> None:
        """
        恢复任务执行
        
        设置暂停事件，使阻塞的任务继续执行。
        如果暂停时间超过超时阈值，抛出 ContextExpiredException。
        优先使用任务自定义超时，否则使用全局默认超时阈值。
        
        异常：
            ContextExpiredException: 当暂停时间超过超时阈值时抛出
        """
        if self._pause_start_time is not None:
            pause_duration = time.time() - self._pause_start_time
            timeout_threshold = self._custom_timeout or config.pause_timeout_threshold
            
            if pause_duration > timeout_threshold:
                self._pause_event.set()
                self._pause_start_time = None
                self._custom_timeout = None
                raise ContextExpiredException(
                    f"暂停时间 {pause_duration:.1f}秒 超过阈值 {timeout_threshold:.1f}秒，上下文已过期"
                )
        
        self._pause_event.set()
        self._pause_start_time = None
        self._custom_timeout = None
    
    def stop(self) -> None:
        """
        停止任务执行
        
        同时设置停止事件和暂停事件。
        设置暂停事件是为了唤醒正在暂停等待中的线程，
        让其能够检测到停止信号并退出。
        """
        self._stop_event.set()
        self._pause_event.set()
    
    def reset_all_events(self) -> None:
        """
        重置所有事件和状态
        
        将控制器恢复到初始状态：
        - 清除停止事件
        - 设置暂停事件（放行状态）
        - 清除暂停时间戳
        - 清除自定义超时
        """
        self._stop_event.clear()
        self._pause_event.set()
        self._pause_start_time = None
        self._custom_timeout = None
    
    def check_status(self, timeout: Optional[float] = None) -> None:
        """
        检查任务状态
        
        先检查是否收到停止信号，如果已停止则抛出 TaskStoppedException。
        然后等待暂停事件，如果任务被暂停则阻塞直到恢复。
        
        参数：
            timeout: 等待暂停事件的最大时间（秒），
                    None 表示无限等待
                    0 表示立即返回（仅检测，不等待）
        
        异常：
            TaskStoppedException: 当任务被停止时抛出
        """
        if self._stop_event.is_set():
            raise TaskStoppedException("任务已被用户停止")
        
        if timeout == 0:
            return
        
        if not self._pause_event.is_set():
            if timeout is not None:
                self._pause_event.wait(timeout=timeout)
            else:
                self._pause_event.wait()
            
            if self._stop_event.is_set():
                raise TaskStoppedException("任务已被用户停止")
    
    def is_paused(self) -> bool:
        """
        检查任务是否处于暂停状态
        
        返回：
            bool: True 表示已暂停，False 表示正在运行
        """
        return not self._pause_event.is_set()
    
    def is_stopped(self) -> bool:
        """
        检查任务是否收到停止信号
        
        返回：
            bool: True 表示已停止，False 表示未停止
        """
        return self._stop_event.is_set()
    
    def get_pause_duration(self) -> Optional[float]:
        """
        获取当前暂停持续时间
        
        返回：
            Optional[float]: 暂停持续时间（秒），
                            如果未处于暂停状态则返回 None
        """
        if self._pause_start_time is None:
            return None
        return time.time() - self._pause_start_time
    
    def smart_sleep(self, seconds: float) -> None:
        """
        智能睡眠函数
        
        将睡眠时间切分为 100ms 时间片，每个时间片结束后检查控制状态，
        实现可中断的睡眠。使用操作系统级 time.sleep 让出 CPU，避免忙等待。
        
        设计原理：
            1. 时间片切分：将长时间睡眠切分为 100ms 的小片段
            2. CPU 让出：每个时间片调用 time.sleep(0.1) 让出 CPU
            3. 状态检查：每个时间片后调用 check_status() 检查暂停/停止
            4. 精度补偿：动态计算剩余时间，避免累积误差
        
        参数：
            seconds: 睡眠时长（秒），支持浮点数
        
        异常：
            TaskStoppedException: 当睡眠期间收到停止信号时抛出
        
        使用示例：
            controller.smart_sleep(5.0)  # 睡眠 5 秒，期间可被中断
            controller.smart_sleep(0.5)  # 睡眠 0.5 秒
        """
        if seconds <= 0:
            return
        
        start_time = time.time()
        end_time = start_time + seconds
        time_slice = 0.1  # 100ms 时间片
        
        while True:
            current_time = time.time()
            remaining = end_time - current_time
            
            if remaining <= 0:
                break
            
            sleep_duration = min(time_slice, remaining)
            
            time.sleep(sleep_duration)
            
            self.check_status()


class TaskControllerProxy:
    """
    任务控制器代理

    默认委托到全局控制器；Worker 线程启动后会为当前线程绑定独立控制器，
    让既有任务代码继续通过 task_controller.check_status() 等接口访问，
    同时支持多窗口任务独立暂停、继续和停止。
    """

    def __init__(self):
        self._default_controller = TaskController.get_instance()
        self._local = threading.local()

    def bind_for_current_thread(self, controller: TaskController) -> None:
        self._local.controller = controller

    def unbind_for_current_thread(self) -> None:
        if hasattr(self._local, "controller"):
            del self._local.controller

    def get_current(self) -> TaskController:
        return getattr(self._local, "controller", self._default_controller)

    def pause(self, timeout: Optional[float] = None) -> None:
        self.get_current().pause(timeout)

    def resume(self) -> None:
        self.get_current().resume()

    def stop(self) -> None:
        self.get_current().stop()

    def reset_all_events(self) -> None:
        self.get_current().reset_all_events()

    def check_status(self, timeout: Optional[float] = None) -> None:
        self.get_current().check_status(timeout)

    def is_paused(self) -> bool:
        return self.get_current().is_paused()

    def is_stopped(self) -> bool:
        return self.get_current().is_stopped()

    def get_pause_duration(self) -> Optional[float]:
        return self.get_current().get_pause_duration()

    def smart_sleep(self, seconds: float) -> None:
        self.get_current().smart_sleep(seconds)


task_controller = TaskControllerProxy()
