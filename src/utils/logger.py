# -*- coding: utf-8 -*-
"""
日志管理模块
============
提供统一的日志记录和管理功能

主要组件：
    - LogLevel: 日志级别枚举
    - LogRecord: 日志记录对象
    - Handler: 日志处理器基类
    - ConsoleHandler: 控制台输出处理器
    - FileHandler: 文件输出处理器（支持轮转）
    - SignalHandler: PyQt信号输出处理器
    - Logger: 日志记录器
    - LogManager: 日志管理器（单例）

日志级别说明：
    - DEBUG: 调试信息，详细的程序运行状态
    - INFO: 一般信息，正常的程序运行状态
    - SUCCESS: 成功信息，操作成功完成
    - WARNING: 警告信息，潜在问题但不影响运行
    - ERROR: 错误信息，功能异常但程序可继续
    - FATAL: 致命错误，程序无法继续运行

使用示例：
    from src.utils.logger import get_logger, LogManager
    
    # 获取日志记录器
    logger = get_logger('daily_tasks')
    
    # 记录日志
    logger.info("任务开始执行")
    logger.success("任务执行成功")
    logger.error("任务执行失败", exc_info=True)
    
    # 配置日志管理器
    manager = LogManager.get_instance()
    manager.add_handler(ConsoleHandler())
    manager.add_handler(FileHandler('logs/app.log'))
"""
import os
import sys
import threading
import time
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Callable, List, Optional, TextIO
from dataclasses import dataclass, field
from PyQt5.QtCore import QObject, pyqtSignal


_log_context = threading.local()


def set_log_context(label: str = None) -> None:
    """设置当前线程日志上下文，用于多开窗口日志标识。"""
    if label:
        _log_context.label = label
    elif hasattr(_log_context, "label"):
        del _log_context.label


def get_log_context() -> str:
    """获取当前线程日志上下文。"""
    return getattr(_log_context, "label", "")


class LogLevel(IntEnum):
    """
    日志级别枚举
    
    级别从低到高：
        DEBUG < INFO < SUCCESS < WARNING < ERROR < FATAL
    """
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    FATAL = 50
    
    @classmethod
    def get_name(cls, level: int) -> str:
        """
        获取日志级别名称
        
        参数：
            level: 日志级别值
            
        返回：
            str: 日志级别名称
        """
        for member in cls:
            if member.value == level:
                return member.name
        return 'UNKNOWN'


@dataclass
class LogRecord:
    """
    日志记录对象
    
    属性：
        level: 日志级别
        message: 日志消息
        module: 模块名称
        timestamp: 时间戳
        exc_info: 异常信息
    """
    level: LogLevel
    message: str
    module: str
    timestamp: datetime = field(default_factory=datetime.now)
    exc_info: Optional[tuple] = None
    context: str = ""
    
    def format(self, fmt: str = None) -> str:
        """
        格式化日志记录
        
        参数：
            fmt: 格式字符串，支持 {time}, {level}, {module}, {message}
            
        返回：
            str: 格式化后的日志字符串
        """
        if fmt is None:
            fmt = "[{time}] [{level}] [{module}] {message}"
        
        level_name = LogLevel.get_name(self.level)
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        result = fmt.format(
            time=time_str,
            level=level_name,
            module=self.module,
            message=self.message
        )
        
        if self.exc_info:
            import traceback
            result += "\n" + "".join(traceback.format_exception(*self.exc_info))
        
        return result


class Handler:
    """
    日志处理器基类
    
    所有日志处理器必须继承此类并实现 emit 方法
    """
    
    def __init__(self, level: LogLevel = LogLevel.DEBUG, fmt: str = None):
        """
        初始化处理器
        
        参数：
            level: 处理器最低日志级别
            fmt: 日志格式字符串
        """
        self.level = level
        self.fmt = fmt
        self._lock = threading.Lock()
    
    def handle(self, record: LogRecord) -> bool:
        """
        处理日志记录
        
        参数：
            record: 日志记录对象
            
        返回：
            bool: 是否处理成功
        """
        if record.level < self.level:
            return False
        
        with self._lock:
            try:
                self.emit(record)
                return True
            except Exception:
                return False
    
    def emit(self, record: LogRecord):
        """
        输出日志记录（子类必须实现）
        
        参数：
            record: 日志记录对象
        """
        raise NotImplementedError("子类必须实现 emit 方法")
    
    def close(self):
        """关闭处理器，释放资源"""
        pass


class ConsoleHandler(Handler):
    """
    控制台输出处理器
    
    将日志输出到标准输出流，支持彩色显示
    """
    
    COLOR_MAP = {
        LogLevel.DEBUG: '\033[36m',      # 青色
        LogLevel.INFO: '\033[37m',       # 白色
        LogLevel.SUCCESS: '\033[32m',    # 绿色
        LogLevel.WARNING: '\033[33m',    # 黄色
        LogLevel.ERROR: '\033[31m',      # 红色
        LogLevel.FATAL: '\033[35m',      # 紫色
    }
    COLOR_RESET = '\033[0m'
    
    def __init__(self, level: LogLevel = LogLevel.DEBUG, use_color: bool = True, stream: TextIO = None):
        """
        初始化控制台处理器
        
        参数：
            level: 最低日志级别
            use_color: 是否使用彩色输出
            stream: 输出流，默认为 sys.stdout
        """
        super().__init__(level)
        self.use_color = use_color and self._supports_color()
        self.stream = stream or sys.stdout
    
    @staticmethod
    def _supports_color() -> bool:
        """
        检测终端是否支持彩色输出
        
        返回：
            bool: 是否支持彩色
        """
        if sys.platform == 'win32':
            return True
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return True
        return False
    
    def emit(self, record: LogRecord):
        """
        输出日志到控制台
        
        参数：
            record: 日志记录对象
        """
        message = record.format(self.fmt)
        
        if self.use_color:
            color = self.COLOR_MAP.get(record.level, '')
            message = f"{color}{message}{self.COLOR_RESET}"
        
        print(message, file=self.stream)


class FileHandler(Handler):
    """
    文件输出处理器
    
    将日志输出到文件，支持日志轮转和归档
    """
    
    def __init__(
        self,
        file_path: str,
        level: LogLevel = LogLevel.DEBUG,
        max_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        encoding: str = 'utf-8'
    ):
        """
        初始化文件处理器
        
        参数：
            file_path: 日志文件路径
            level: 最低日志级别
            max_size: 单个日志文件最大大小（字节），默认10MB
            backup_count: 保留的备份文件数量
            encoding: 文件编码
        """
        super().__init__(level)
        self.file_path = Path(file_path)
        self.max_size = max_size
        self.backup_count = backup_count
        self.encoding = encoding
        self._file = None
        self._ensure_dir()
        self._open_file()
    
    def _ensure_dir(self):
        """确保日志目录存在"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _open_file(self):
        """打开日志文件"""
        self._file = open(self.file_path, 'a', encoding=self.encoding)
    
    def _should_rotate(self) -> bool:
        """
        检查是否需要轮转
        
        返回：
            bool: 是否需要轮转
        """
        if not self.file_path.exists():
            return False
        return self.file_path.stat().st_size >= self.max_size
    
    def _do_rotate(self):
        """执行日志轮转"""
        if self._file:
            self._file.close()
            self._file = None
        
        for i in range(self.backup_count - 1, 0, -1):
            src = self.file_path.with_suffix(f'.log.{i}')
            dst = self.file_path.with_suffix(f'.log.{i + 1}')
            if src.exists():
                src.rename(dst)
        
        new_backup = self.file_path.with_suffix('.log.1')
        if self.file_path.exists():
            self.file_path.rename(new_backup)
        
        self._open_file()
    
    def emit(self, record: LogRecord):
        """
        输出日志到文件
        
        参数：
            record: 日志记录对象
        """
        if self._should_rotate():
            self._do_rotate()
        
        message = record.format(self.fmt)
        self._file.write(message + '\n')
        self._file.flush()
    
    def close(self):
        """关闭文件处理器"""
        if self._file:
            self._file.close()
            self._file = None


class LogSignal(QObject):
    """
    日志信号类
    
    用于跨线程安全发送日志消息到UI
    """
    log_message = pyqtSignal(str)


class SignalHandler(Handler):
    """
    PyQt信号输出处理器
    
    将日志通过PyQt信号发送到UI界面，确保线程安全
    """
    
    def __init__(self, level: LogLevel = LogLevel.INFO, callback: Callable[[str], None] = None):
        """
        初始化信号处理器
        
        参数：
            level: 最低日志级别
            callback: 日志回调函数，接收格式化后的日志字符串
        """
        super().__init__(level)
        self.log_signal = LogSignal()
        if callback:
            self.log_signal.log_message.connect(callback)
    
    def set_callback(self, callback: Callable[[str], None]):
        """
        设置日志回调函数
        
        参数：
            callback: 回调函数
        """
        self.log_signal.log_message.connect(callback)
    
    def emit(self, record: LogRecord):
        """
        通过信号发送日志（线程安全）
        
        参数：
            record: 日志记录对象
        """
        message = self._format_for_ui(record)
        self.log_signal.log_message.emit(message)
    
    def _format_for_ui(self, record: LogRecord) -> str:
        """
        为UI显示格式化日志
        
        参数：
            record: 日志记录对象
            
        返回：
            str: 格式化后的日志字符串
        """
        time_str = record.timestamp.strftime("%H:%M:%S")
        if record.context:
            return f"[{time_str}] [{record.context}] {record.message}"
        return f"[{time_str}] {record.message}"


class Logger:
    """
    日志记录器
    
    提供便捷的日志记录方法，支持模块级别的日志管理
    """
    
    def __init__(self, name: str, level: LogLevel = LogLevel.DEBUG):
        """
        初始化日志记录器
        
        参数：
            name: 记录器名称（通常为模块名）
            level: 记录器最低日志级别
        """
        self.name = name
        self.level = level
        self._handlers: List[Handler] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: Handler):
        """
        添加日志处理器
        
        参数：
            handler: 处理器实例
        """
        with self._lock:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: Handler):
        """
        移除日志处理器
        
        参数：
            handler: 要移除的处理器
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
    
    def _log(self, level: LogLevel, message: str, exc_info: bool = False):
        """
        记录日志的内部方法
        
        参数：
            level: 日志级别
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        if level < self.level:
            return
        
        exc_tuple = None
        if exc_info:
            exc_tuple = sys.exc_info()
        
        record = LogRecord(
            level=level,
            message=message,
            module=self.name,
            exc_info=exc_tuple,
            context=get_log_context()
        )
        
        with self._lock:
            for handler in self._handlers:
                handler.handle(record)
    
    def debug(self, message: str, exc_info: bool = False):
        """
        记录DEBUG级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.DEBUG, message, exc_info)
    
    def info(self, message: str, exc_info: bool = False):
        """
        记录INFO级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.INFO, message, exc_info)
    
    def success(self, message: str, exc_info: bool = False):
        """
        记录SUCCESS级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.SUCCESS, message, exc_info)
    
    def warning(self, message: str, exc_info: bool = False):
        """
        记录WARNING级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.WARNING, message, exc_info)
    
    def error(self, message: str, exc_info: bool = False):
        """
        记录ERROR级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.ERROR, message, exc_info)
    
    def fatal(self, message: str, exc_info: bool = False):
        """
        记录FATAL级别日志
        
        参数：
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self._log(LogLevel.FATAL, message, exc_info)


class LogManager:
    """
    日志管理器（单例模式）
    
    管理所有日志记录器和处理器，提供全局配置接口
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """
        单例模式实现
        
        返回：
            LogManager: 唯一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if not hasattr(self, '_initialized'):
            self._loggers: dict = {}
            self._handlers: List[Handler] = []
            self._default_level = LogLevel.DEBUG
            self._signal_handler: Optional[SignalHandler] = None
            self._file_handler: Optional[FileHandler] = None
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'LogManager':
        """
        获取日志管理器实例
        
        返回：
            LogManager: 日志管理器实例
        """
        return cls()
    
    def get_logger(self, name: str) -> Logger:
        """
        获取或创建日志记录器
        
        参数：
            name: 记录器名称
            
        返回：
            Logger: 日志记录器实例
        """
        if name not in self._loggers:
            logger = Logger(name, self._default_level)
            for handler in self._handlers:
                logger.add_handler(handler)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def add_handler(self, handler: Handler):
        """
        添加全局处理器
        
        参数：
            handler: 处理器实例
        """
        self._handlers.append(handler)
        for logger in self._loggers.values():
            logger.add_handler(handler)
    
    def remove_handler(self, handler: Handler):
        """
        移除全局处理器
        
        参数：
            handler: 要移除的处理器
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
        for logger in self._loggers.values():
            logger.remove_handler(handler)
    
    def set_level(self, level: LogLevel):
        """
        设置全局日志级别
        
        参数：
            level: 日志级别
        """
        self._default_level = level
        for logger in self._loggers.values():
            logger.level = level
    
    def setup_console(self, level: LogLevel = LogLevel.DEBUG, use_color: bool = True):
        """
        配置控制台输出
        
        参数：
            level: 最低日志级别
            use_color: 是否使用彩色输出
        """
        handler = ConsoleHandler(level, use_color)
        self.add_handler(handler)
    
    def setup_file(
        self,
        file_path: str,
        level: LogLevel = LogLevel.DEBUG,
        max_size: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        """
        配置文件输出
        
        参数：
            file_path: 日志文件路径
            level: 最低日志级别
            max_size: 单文件最大大小
            backup_count: 备份文件数量
        """
        if self._file_handler:
            self.remove_handler(self._file_handler)
            self._file_handler.close()
        
        self._file_handler = FileHandler(file_path, level, max_size, backup_count)
        self.add_handler(self._file_handler)
    
    def setup_signal(self, callback: Callable[[str], None], level: LogLevel = LogLevel.INFO):
        """
        配置信号输出（用于UI显示）
        
        参数：
            callback: 日志回调函数
            level: 最低日志级别
        """
        if self._signal_handler:
            self._signal_handler.set_callback(callback)
        else:
            self._signal_handler = SignalHandler(level, callback)
            self.add_handler(self._signal_handler)
    
    def close(self):
        """关闭所有处理器"""
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()
        self._loggers.clear()
        self._signal_handler = None
        self._file_handler = None


def get_logger(name: str = 'app') -> Logger:
    """
    获取日志记录器的便捷函数
    
    参数：
        name: 记录器名称
        
    返回：
        Logger: 日志记录器实例
    """
    return LogManager.get_instance().get_logger(name)


def setup_logging(
    console_level: LogLevel = LogLevel.DEBUG,
    file_path: str = None,
    file_level: LogLevel = LogLevel.DEBUG,
    signal_callback: Callable[[str], None] = None,
    signal_level: LogLevel = LogLevel.INFO
):
    """
    快速配置日志系统的便捷函数
    
    参数：
        console_level: 控制台日志级别
        file_path: 日志文件路径（可选）
        file_level: 文件日志级别
        signal_callback: UI信号回调（可选）
        signal_level: 信号日志级别
    """
    manager = LogManager.get_instance()
    
    manager.setup_console(console_level)
    
    if file_path:
        manager.setup_file(file_path, file_level)
    
    if signal_callback:
        manager.setup_signal(signal_callback, signal_level)
