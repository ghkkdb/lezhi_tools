# -*- coding: utf-8 -*-
"""
后台任务执行线程模块
==================
提供独立的后台任务执行线程，通过任务注册表动态获取任务函数。

核心功能：
    - ScriptWorker: 后台脚本执行线程类
    - 支持任务暂停/继续/停止
    - 异常隔离，单任务崩溃不影响整体

使用示例：
    worker = ScriptWorker(selected_tasks, hwnd, task_params)
    worker.finished_sig.connect(on_finished)
    worker.task_completed.connect(on_task_completed)
    worker.start()
"""
import time
import inspect
import win32gui
from typing import Dict, Any, Optional, List

from PyQt5.QtCore import QThread, pyqtSignal

# 导入任务实现模块，触发 @register_task 装饰器注册任务。
from . import daily_tasks  # noqa: F401
from .task_registry import get_task
from .controller import (
    TaskController,
    task_controller,
    TaskStoppedException,
    ContextExpiredException,
    InvalidWindowHandleException
)
from .helpers import reset_game_state
from src.utils.logger import get_logger, set_log_context
from src.utils.win_api import release_tracked_inputs


class ScriptWorker(QThread):
    """
    后台脚本执行线程
    
    用于在后台执行用户选择的任务，避免阻塞UI线程。
    通过任务注册表动态获取任务函数，实现任务与执行器的解耦。
    
    属性：
        tasks: 用户选择的任务列表
        hwnd: 窗口句柄
        task_params: 任务参数字典
        
    信号：
        finished_sig: 任务完成信号
        task_completed: 单个任务完成信号 (task_name, result: bool | dict)
    """
    
    finished_sig = pyqtSignal()
    task_completed = pyqtSignal(str, object)

    def __init__(
        self,
        selected_tasks: List[str],
        hwnd: int,
        task_params: Optional[Dict[str, Any]] = None,
        log_context: Optional[str] = None
    ):
        """
        初始化线程
        
        参数：
            selected_tasks: 用户选择的任务名称列表
            hwnd: 窗口句柄
            task_params: 任务参数字典（可选）
        """
        super().__init__()
        self.tasks = selected_tasks
        self.hwnd = hwnd
        self.task_params = task_params or {}
        self.controller = TaskController(isolated=True)
        self.log_context = log_context
        self.logger = get_logger('ScriptWorker')

    def run(self):
        """
        线程执行入口
        
        流程：
            1. 重置控制器状态
            2. 遍历执行选中的任务
            3. 捕获各类异常并处理
            4. 清理输入状态并发送完成信号
        
        异常隔离：
            - 每个任务执行都有独立的 try...except 块
            - 单任务崩溃不会导致整个线程意外退出
        """
        task_controller.bind_for_current_thread(self.controller)
        self.controller.reset_all_events()
        set_log_context(self.log_context)
        
        try:
            for task_name in self.tasks:
                try:
                    # 检查窗口有效性
                    if not win32gui.IsWindow(self.hwnd):
                        raise InvalidWindowHandleException("游戏窗口已关闭或无效")
                    
                    # 检查控制信号（暂停/停止）
                    task_controller.check_status()
                    
                    # 通过注册表动态获取任务函数
                    task_func = get_task(task_name)
                    
                    if task_func is not None:
                        params = self.task_params.get(task_name, {})
                        
                        sig = inspect.signature(task_func)
                        if 'task_params' in sig.parameters:
                            result = task_func(self.hwnd, task_params=params)
                        else:
                            result = task_func(self.hwnd)
                        
                        if result is None:
                            result = False
                        
                        self.task_completed.emit(task_name, result)
                    else:
                        self.logger.info(f"任务 [{task_name}] 暂未编写逻辑实现")
                        time.sleep(1)
                        
                except TaskStoppedException:
                    self.logger.warning(f"任务 [{task_name}] 被用户中止")
                    self.task_completed.emit(task_name, False)
                    raise
                    
                except ContextExpiredException:
                    self.logger.warning(f"任务 [{task_name}] 上下文失效，尝试重置游戏状态")
                    reset_game_state(self.hwnd)
                    
                except InvalidWindowHandleException as e:
                    self.logger.error(f"{str(e)}，请重新绑定窗口")
                    break
                    
                except Exception as e:
                    self.logger.error(f"任务 [{task_name}] 执行异常: {str(e)}")
                    self.task_completed.emit(task_name, False)
            
            self.logger.info("当前任务已全部完成")
            
        except TaskStoppedException:
            self.logger.warning("任务被用户中止")
            
        except Exception as e:
            self.logger.error(f"任务执行错误: {str(e)}")
            
        finally:
            release_tracked_inputs(self.hwnd)
            set_log_context(None)
            task_controller.unbind_for_current_thread()
            self.finished_sig.emit()

    def stop(self):
        """
        停止任务执行
        
        通过控制器发送停止信号，任务线程将在下一个检查点抛出 TaskStoppedException。
        """
        self.controller.stop()

    def pause(self):
        """
        暂停当前 Worker 对应的任务控制器。
        """
        self.controller.pause()

    def resume(self):
        """
        恢复当前 Worker 对应的任务控制器。
        """
        self.controller.resume()
