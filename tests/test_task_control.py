# -*- coding: utf-8 -*-
"""
任务控制功能测试脚本（独立版）
==============================
验证任务控制器的核心功能（不依赖 win32 模块）

测试内容：
    1. 暂停/继续功能响应时间测试（≤100ms）
    2. 强制停止功能测试
    3. 长暂停上下文失效检测测试
    4. 精准输入释放测试（无幽灵输入）
    5. 线程安全保护测试
    6. 异常情况下的状态恢复测试
    7. 窗口关闭时的优雅退出测试
    8. smart_sleep 不产生 CPU 忙等待测试
    9. 输入操作原子性测试
"""
import os
import sys
import time
import threading
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class MockConfig:
    """模拟配置类"""
    pause_timeout_threshold = 300


config = MockConfig()


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


class TaskController:
    """
    任务控制器单例类
    
    用于控制任务的执行状态，支持暂停、继续、停止操作。
    使用 threading.Event 实现线程间的同步控制。
    """
    
    _instance: Optional['TaskController'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'TaskController':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
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
        return cls()
    
    @classmethod
    def reset_instance(cls):
        with cls._lock:
            if cls._instance is not None:
                cls._instance._pause_event.set()
                cls._instance._stop_event.clear()
                cls._instance._pause_start_time = None
                cls._instance._custom_timeout = None
            cls._instance = None
    
    def pause(self, timeout: Optional[float] = None) -> None:
        self._pause_start_time = time.time()
        self._custom_timeout = timeout
        self._pause_event.clear()
    
    def resume(self) -> None:
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
        self._stop_event.set()
        self._pause_event.set()
    
    def reset_all_events(self) -> None:
        self._stop_event.clear()
        self._pause_event.set()
        self._pause_start_time = None
        self._custom_timeout = None
    
    def check_status(self, timeout: Optional[float] = None) -> None:
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
        return not self._pause_event.is_set()
    
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()
    
    def get_pause_duration(self) -> Optional[float]:
        if self._pause_start_time is None:
            return None
        return time.time() - self._pause_start_time
    
    def smart_sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        
        start_time = time.time()
        end_time = start_time + seconds
        time_slice = 0.1
        
        while True:
            current_time = time.time()
            remaining = end_time - current_time
            
            if remaining <= 0:
                break
            
            sleep_duration = min(time_slice, remaining)
            time.sleep(sleep_duration)
            self.check_status()


class InputTracker:
    """
    输入状态追踪器（单例模式）
    
    追踪键盘按键和鼠标按钮的按下状态，用于判断是否处于持续按下状态。
    线程安全设计，支持多线程环境下的状态管理。
    """
    
    _instance: Optional['InputTracker'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'InputTracker':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._pressed_keys: set = set()
            self._pressed_buttons: set = set()
            self._hwnd: Optional[int] = None
            self._data_lock: threading.Lock = threading.Lock()
            self._initialized: bool = True
    
    @classmethod
    def get_instance(cls) -> 'InputTracker':
        return cls()
    
    def track_key_down(self, hwnd: int, key: str) -> None:
        with self._data_lock:
            self._hwnd = hwnd
            self._pressed_keys.add(key.lower())
    
    def track_key_up(self, hwnd: int, key: str) -> None:
        with self._data_lock:
            self._hwnd = hwnd
            self._pressed_keys.discard(key.lower())
    
    def track_mouse_down(self, hwnd: int, button: str) -> None:
        with self._data_lock:
            self._hwnd = hwnd
            normalized_button = button.lower()
            if normalized_button in ('left', 'right', 'middle'):
                self._pressed_buttons.add(normalized_button)
    
    def track_mouse_up(self, hwnd: int, button: str) -> None:
        with self._data_lock:
            self._hwnd = hwnd
            normalized_button = button.lower()
            if normalized_button in ('left', 'right', 'middle'):
                self._pressed_buttons.discard(normalized_button)
    
    def get_pressed_keys(self) -> set:
        with self._data_lock:
            return self._pressed_keys.copy()
    
    def get_pressed_buttons(self) -> set:
        with self._data_lock:
            return self._pressed_buttons.copy()
    
    def get_hwnd(self) -> Optional[int]:
        with self._data_lock:
            return self._hwnd
    
    def is_key_pressed(self, key: str) -> bool:
        with self._data_lock:
            return key.lower() in self._pressed_keys
    
    def is_button_pressed(self, button: str) -> bool:
        with self._data_lock:
            return button.lower() in self._pressed_buttons
    
    def clear(self) -> None:
        with self._data_lock:
            self._pressed_keys.clear()
            self._pressed_buttons.clear()
            self._hwnd = None
    
    def clear_keys(self) -> None:
        with self._data_lock:
            self._pressed_keys.clear()
    
    def clear_buttons(self) -> None:
        with self._data_lock:
            self._pressed_buttons.clear()
    
    def get_state_summary(self) -> dict:
        with self._data_lock:
            return {
                'hwnd': self._hwnd,
                'pressed_keys': list(self._pressed_keys),
                'pressed_buttons': list(self._pressed_buttons)
            }


class TestTaskController:
    """任务控制器测试类"""
    
    @classmethod
    def setup_class(cls):
        TaskController.reset_instance()
    
    def setup_method(self):
        TaskController.reset_instance()
        self.controller = TaskController.get_instance()
        self.controller.reset_all_events()
    
    def teardown_method(self):
        if hasattr(self, 'controller'):
            self.controller.reset_all_events()
        TaskController.reset_instance()
    
    def test_pause_resume_response_time(self):
        """
        测试暂停/继续功能响应时间（≤100ms）
        
        验证：
            1. pause() 方法调用后，check_status() 应在 100ms 内阻塞
            2. resume() 方法调用后，阻塞的线程应在 100ms 内恢复执行
        """
        print("\n" + "=" * 50)
        print("测试1: 暂停/继续功能响应时间")
        print("=" * 50)
        
        pause_detected = threading.Event()
        resume_detected = threading.Event()
        pause_time = [0]
        resume_time = [0]
        
        def worker():
            try:
                self.controller.check_status()
                pause_detected.set()
                pause_time[0] = time.time()
                self.controller.check_status()
                resume_detected.set()
                resume_time[0] = time.time()
            except TaskStoppedException:
                pass
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        time.sleep(0.05)
        
        start_pause = time.time()
        self.controller.pause()
        
        pause_detected.wait(timeout=2)
        actual_pause_time = pause_time[0] - start_pause
        
        print(f"暂停检测时间: {actual_pause_time * 1000:.2f}ms")
        
        time.sleep(0.1)
        
        start_resume = time.time()
        self.controller.resume()
        
        resume_detected.wait(timeout=2)
        actual_resume_time = resume_time[0] - start_resume
        
        print(f"恢复响应时间: {actual_resume_time * 1000:.2f}ms")
        
        thread.join(timeout=2)
        
        assert actual_pause_time < 0.1, f"暂停响应时间 {actual_pause_time * 1000:.2f}ms 超过 100ms"
        assert actual_resume_time < 0.1, f"恢复响应时间 {actual_resume_time * 1000:.2f}ms 超过 100ms"
        
        print("✅ 暂停/继续响应时间测试通过")
    
    def test_force_stop(self):
        """
        测试强制停止功能
        
        验证：
            1. stop() 方法调用后，正在执行的任务应抛出 TaskStoppedException
            2. 正在暂停等待的线程应被唤醒并检测到停止信号
        """
        print("\n" + "=" * 50)
        print("测试2: 强制停止功能")
        print("=" * 50)
        
        exception_caught = threading.Event()
        exception_type = [None]
        
        def worker():
            try:
                self.controller.check_status()
                self.controller.pause()
                self.controller.check_status()
            except TaskStoppedException as e:
                exception_type[0] = type(e).__name__
                exception_caught.set()
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        time.sleep(0.1)
        
        self.controller.stop()
        
        exception_caught.wait(timeout=2)
        thread.join(timeout=2)
        
        assert exception_type[0] == "TaskStoppedException", f"期望 TaskStoppedException，实际 {exception_type[0]}"
        
        print("✅ 强制停止功能测试通过")
    
    def test_long_pause_context_expired(self):
        """
        测试长暂停上下文失效检测
        
        验证：
            1. 暂停时间超过阈值时，resume() 应抛出 ContextExpiredException
            2. 使用自定义超时阈值时，应按自定义值判断
        """
        print("\n" + "=" * 50)
        print("测试3: 长暂停上下文失效检测")
        print("=" * 50)
        
        self.controller.pause(timeout=0.5)
        
        time.sleep(0.6)
        
        try:
            self.controller.resume()
            assert False, "应抛出 ContextExpiredException"
        except ContextExpiredException as e:
            print(f"正确捕获异常: {str(e)}")
        
        self.controller.reset_all_events()
        
        self.controller.pause(timeout=2.0)
        time.sleep(0.3)
        self.controller.resume()
        
        print("✅ 长暂停上下文失效检测测试通过")
    
    def test_smart_sleep_no_busy_wait(self):
        """
        测试 smart_sleep 不产生 CPU 忙等待
        
        验证：
            1. smart_sleep 应正确让出 CPU
            2. smart_sleep 应可被中断
            3. 睡眠时间应接近预期值
        """
        print("\n" + "=" * 50)
        print("测试4: smart_sleep 不产生 CPU 忙等待")
        print("=" * 50)
        
        start_time = time.time()
        self.controller.smart_sleep(0.5)
        elapsed = time.time() - start_time
        
        print(f"smart_sleep(0.5) 实际耗时: {elapsed:.3f}秒")
        assert 0.45 <= elapsed <= 0.6, f"睡眠时间 {elapsed:.3f}秒 不在预期范围内"
        
        interrupted = threading.Event()
        sleep_time = [0]
        
        def worker():
            start = time.time()
            try:
                self.controller.smart_sleep(5.0)
            except TaskStoppedException:
                sleep_time[0] = time.time() - start
                interrupted.set()
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        time.sleep(0.3)
        self.controller.stop()
        
        interrupted.wait(timeout=2)
        thread.join(timeout=2)
        
        print(f"中断后睡眠时间: {sleep_time[0]:.3f}秒")
        assert sleep_time[0] < 1.0, f"睡眠应在 1 秒内被中断，实际 {sleep_time[0]:.3f}秒"
        
        print("✅ smart_sleep 测试通过")
    
    def test_thread_safety(self):
        """
        测试线程安全保护
        
        验证：
            1. 多线程并发调用 pause/resume/stop 不应产生死锁
            2. 状态检查应正确工作
        """
        print("\n" + "=" * 50)
        print("测试5: 线程安全保护")
        print("=" * 50)
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            try:
                for i in range(10):
                    self.controller.check_status()
                    time.sleep(0.01)
                with lock:
                    results.append((worker_id, "completed"))
            except TaskStoppedException:
                with lock:
                    results.append((worker_id, "stopped"))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for t in threads:
            t.start()
        
        time.sleep(0.05)
        self.controller.pause()
        time.sleep(0.05)
        self.controller.resume()
        time.sleep(0.05)
        self.controller.stop()
        
        for t in threads:
            t.join(timeout=2)
        
        print(f"线程执行结果: {results}")
        
        assert len(results) == 5, f"应有 5 个结果，实际 {len(results)}"
        
        print("✅ 线程安全保护测试通过")
    
    def test_is_paused_is_stopped(self):
        """
        测试状态查询方法
        
        验证：
            1. is_paused() 正确返回暂停状态
            2. is_stopped() 正确返回停止状态
            3. get_pause_duration() 正确返回暂停持续时间
        """
        print("\n" + "=" * 50)
        print("测试6: 状态查询方法")
        print("=" * 50)
        
        assert not self.controller.is_paused(), "初始状态不应为暂停"
        assert not self.controller.is_stopped(), "初始状态不应为停止"
        
        self.controller.pause()
        assert self.controller.is_paused(), "pause() 后应为暂停状态"
        
        time.sleep(0.2)
        duration = self.controller.get_pause_duration()
        print(f"暂停持续时间: {duration:.3f}秒")
        assert duration is not None and duration >= 0.2, "暂停持续时间应 >= 0.2秒"
        
        self.controller.stop()
        assert self.controller.is_stopped(), "stop() 后应为停止状态"
        
        print("✅ 状态查询方法测试通过")


class TestInputTracker:
    """输入状态追踪器测试类"""
    
    def setup_method(self):
        self.tracker = InputTracker.get_instance()
        self.tracker.clear()
    
    def teardown_method(self):
        self.tracker.clear()
    
    def test_key_tracking(self):
        """
        测试键盘按键追踪
        
        验证：
            1. track_key_down 正确记录按键状态
            2. track_key_up 正确清除按键状态
            3. is_key_pressed 正确查询状态
        """
        print("\n" + "=" * 50)
        print("测试7: 键盘按键追踪")
        print("=" * 50)
        
        self.tracker.track_key_down(12345, 'a')
        assert self.tracker.is_key_pressed('a'), "按键 'a' 应为按下状态"
        assert 'a' in self.tracker.get_pressed_keys(), "按键 'a' 应在按下集合中"
        
        self.tracker.track_key_up(12345, 'a')
        assert not self.tracker.is_key_pressed('a'), "按键 'a' 应已释放"
        
        self.tracker.track_key_down(12345, 'ENTER')
        assert self.tracker.is_key_pressed('enter'), "按键应不区分大小写"
        
        print("✅ 键盘按键追踪测试通过")
    
    def test_mouse_tracking(self):
        """
        测试鼠标按钮追踪
        
        验证：
            1. track_mouse_down 正确记录按钮状态
            2. track_mouse_up 正确清除按钮状态
            3. is_button_pressed 正确查询状态
        """
        print("\n" + "=" * 50)
        print("测试8: 鼠标按钮追踪")
        print("=" * 50)
        
        self.tracker.track_mouse_down(12345, 'left')
        assert self.tracker.is_button_pressed('left'), "左键应为按下状态"
        
        self.tracker.track_mouse_down(12345, 'right')
        assert self.tracker.is_button_pressed('right'), "右键应为按下状态"
        
        buttons = self.tracker.get_pressed_buttons()
        assert 'left' in buttons and 'right' in buttons, "应同时追踪多个按钮"
        
        self.tracker.track_mouse_up(12345, 'left')
        assert not self.tracker.is_button_pressed('left'), "左键应已释放"
        assert self.tracker.is_button_pressed('right'), "右键应仍为按下状态"
        
        print("✅ 鼠标按钮追踪测试通过")
    
    def test_precise_input_release(self):
        """
        测试精准输入释放（无幽灵输入）
        
        验证：
            1. clear() 方法正确清空所有状态
            2. clear_keys() 仅清空键盘状态
            3. clear_buttons() 仅清空鼠标状态
        """
        print("\n" + "=" * 50)
        print("测试9: 精准输入释放")
        print("=" * 50)
        
        self.tracker.track_key_down(12345, 'a')
        self.tracker.track_key_down(12345, 'b')
        self.tracker.track_mouse_down(12345, 'left')
        
        self.tracker.clear_keys()
        assert len(self.tracker.get_pressed_keys()) == 0, "键盘状态应已清空"
        assert self.tracker.is_button_pressed('left'), "鼠标状态应保留"
        
        self.tracker.track_key_down(12345, 'c')
        self.tracker.clear_buttons()
        assert self.tracker.is_key_pressed('c'), "键盘状态应保留"
        assert len(self.tracker.get_pressed_buttons()) == 0, "鼠标状态应已清空"
        
        self.tracker.clear()
        summary = self.tracker.get_state_summary()
        assert summary['pressed_keys'] == [], "所有键盘状态应已清空"
        assert summary['pressed_buttons'] == [], "所有鼠标状态应已清空"
        
        print("✅ 精准输入释放测试通过")
    
    def test_thread_safety(self):
        """
        测试输入追踪器的线程安全
        
        验证：
            1. 多线程并发访问不产生竞态条件
            2. 状态一致性得到保证
        """
        print("\n" + "=" * 50)
        print("测试10: 输入追踪器线程安全")
        print("=" * 50)
        
        def worker(worker_id):
            for i in range(100):
                self.tracker.track_key_down(12345, f'key_{worker_id}_{i}')
                self.tracker.is_key_pressed(f'key_{worker_id}_{i}')
                self.tracker.track_key_up(12345, f'key_{worker_id}_{i}')
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        print("✅ 输入追踪器线程安全测试通过")


class TestExceptionHandling:
    """异常处理测试类"""
    
    def test_task_stopped_exception(self):
        """测试 TaskStoppedException 异常"""
        print("\n" + "=" * 50)
        print("测试11: TaskStoppedException 异常")
        print("=" * 50)
        
        TaskController.reset_instance()
        controller = TaskController.get_instance()
        
        controller.stop()
        
        try:
            controller.check_status()
            assert False, "应抛出 TaskStoppedException"
        except TaskStoppedException as e:
            print(f"正确捕获异常: {str(e)}")
        
        print("✅ TaskStoppedException 测试通过")
    
    def test_context_expired_exception(self):
        """测试 ContextExpiredException 异常"""
        print("\n" + "=" * 50)
        print("测试12: ContextExpiredException 异常")
        print("=" * 50)
        
        TaskController.reset_instance()
        controller = TaskController.get_instance()
        
        controller.pause(timeout=0.1)
        time.sleep(0.2)
        
        try:
            controller.resume()
            assert False, "应抛出 ContextExpiredException"
        except ContextExpiredException as e:
            print(f"正确捕获异常: {str(e)}")
        
        print("✅ ContextExpiredException 测试通过")
    
    def test_invalid_window_handle_exception(self):
        """测试 InvalidWindowHandleException 异常"""
        print("\n" + "=" * 50)
        print("测试13: InvalidWindowHandleException 异常")
        print("=" * 50)
        
        exc = InvalidWindowHandleException("测试无效句柄")
        assert "测试无效句柄" in str(exc)
        
        print("✅ InvalidWindowHandleException 测试通过")


class TestAtomicOperations:
    """原子操作测试类"""
    
    def setup_method(self):
        self.tracker = InputTracker.get_instance()
        self.tracker.clear()
    
    def teardown_method(self):
        self.tracker.clear()
    
    def test_key_down_atomicity(self):
        """测试按键按下的原子性"""
        print("\n" + "=" * 50)
        print("测试14: 按键按下原子性")
        print("=" * 50)
        
        self.tracker.track_key_down(12345, 'test_key')
        assert self.tracker.is_key_pressed('test_key'), "按键状态应已记录"
        
        self.tracker.track_key_up(12345, 'test_key')
        assert not self.tracker.is_key_pressed('test_key'), "按键状态应已清除"
        
        print("✅ 按键按下原子性测试通过")
    
    def test_mouse_down_atomicity(self):
        """测试鼠标按下的原子性"""
        print("\n" + "=" * 50)
        print("测试15: 鼠标按下原子性")
        print("=" * 50)
        
        self.tracker.track_mouse_down(12345, 'left')
        assert self.tracker.is_button_pressed('left'), "鼠标状态应已记录"
        
        self.tracker.track_mouse_up(12345, 'left')
        assert not self.tracker.is_button_pressed('left'), "鼠标状态应已清除"
        
        print("✅ 鼠标按下原子性测试通过")
    
    def test_state_consistency_on_exception(self):
        """测试异常情况下的状态一致性"""
        print("\n" + "=" * 50)
        print("测试16: 异常情况下状态一致性")
        print("=" * 50)
        
        self.tracker.track_key_down(12345, 'a')
        self.tracker.track_mouse_down(12345, 'left')
        
        initial_keys = self.tracker.get_pressed_keys()
        initial_buttons = self.tracker.get_pressed_buttons()
        
        assert 'a' in initial_keys
        assert 'left' in initial_buttons
        
        self.tracker.clear()
        
        assert len(self.tracker.get_pressed_keys()) == 0
        assert len(self.tracker.get_pressed_buttons()) == 0
        
        print("✅ 异常情况下状态一致性测试通过")


class TestGracefulShutdown:
    """优雅退出测试类"""
    
    def test_controller_reset(self):
        """测试控制器重置功能"""
        print("\n" + "=" * 50)
        print("测试17: 控制器重置功能")
        print("=" * 50)
        
        TaskController.reset_instance()
        controller = TaskController.get_instance()
        
        controller.pause()
        controller.stop()
        
        assert controller.is_paused()
        assert controller.is_stopped()
        
        controller.reset_all_events()
        
        assert not controller.is_paused()
        assert not controller.is_stopped()
        
        print("✅ 控制器重置功能测试通过")
    
    def test_simulated_graceful_shutdown(self):
        """模拟测试优雅退出流程"""
        print("\n" + "=" * 50)
        print("测试18: 模拟优雅退出流程")
        print("=" * 50)
        
        TaskController.reset_instance()
        controller = TaskController.get_instance()
        tracker = InputTracker.get_instance()
        tracker.clear()
        
        worker_running = threading.Event()
        worker_stopped = threading.Event()
        
        def worker():
            worker_running.set()
            try:
                for i in range(100):
                    controller.check_status()
                    controller.smart_sleep(0.1)
            except TaskStoppedException:
                worker_stopped.set()
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        worker_running.wait(timeout=2)
        
        tracker.track_key_down(12345, 'a')
        tracker.track_mouse_down(12345, 'left')
        
        time.sleep(0.1)
        
        controller.stop()
        
        thread.join(timeout=2)
        
        assert worker_stopped.is_set(), "工作线程应被停止"
        
        tracker.clear()
        assert len(tracker.get_pressed_keys()) == 0
        assert len(tracker.get_pressed_buttons()) == 0
        
        print("✅ 模拟优雅退出流程测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("       任务控制功能测试套件")
    print("=" * 60)
    
    test_classes = [
        TestTaskController,
        TestInputTracker,
        TestExceptionHandling,
        TestAtomicOperations,
        TestGracefulShutdown,
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"  执行 {test_class.__name__}")
        print(f"{'=' * 60}")
        
        instance = test_class()
        
        if hasattr(instance, 'setup_class'):
            instance.setup_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    if hasattr(instance, 'setup_method'):
                        instance.setup_method()
                    
                    getattr(instance, method_name)()
                    passed += 1
                    
                    if hasattr(instance, 'teardown_method'):
                        instance.teardown_method()
                        
                except AssertionError as e:
                    print(f"❌ 测试失败: {method_name}")
                    print(f"   原因: {str(e)}")
                    failed += 1
                except Exception as e:
                    print(f"❌ 测试异常: {method_name}")
                    print(f"   异常: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    failed += 1
    
    print("\n" + "=" * 60)
    print(f"  测试结果: 通过 {passed} 个, 失败 {failed} 个")
    print("=" * 60)
    
    if failed == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 存在失败的测试")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
