# -*- coding: utf-8 -*-
"""
日志系统测试脚本
================
验证日志系统各级别输出功能

测试内容：
    1. 各日志级别输出测试
    2. 控制台输出测试
    3. 文件输出测试
    4. 日志轮转测试
    5. 性能测试
"""
import os
import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import (
    LogLevel, LogManager, get_logger, setup_logging,
    ConsoleHandler, FileHandler, SignalHandler
)


def test_log_levels():
    """
    测试各日志级别输出
    
    验证：
        1. DEBUG级别日志正确输出
        2. INFO级别日志正确输出
        3. SUCCESS级别日志正确输出
        4. WARNING级别日志正确输出
        5. ERROR级别日志正确输出
        6. FATAL级别日志正确输出
    """
    print("\n" + "=" * 50)
    print("测试1: 各日志级别输出")
    print("=" * 50)
    
    manager = LogManager.get_instance()
    manager.setup_console(LogLevel.DEBUG)
    
    logger = get_logger('test_levels')
    
    logger.debug("这是DEBUG级别日志 - 用于调试信息")
    logger.info("这是INFO级别日志 - 用于一般信息")
    logger.success("这是SUCCESS级别日志 - 用于成功信息")
    logger.warning("这是WARNING级别日志 - 用于警告信息")
    logger.error("这是ERROR级别日志 - 用于错误信息")
    logger.fatal("这是FATAL级别日志 - 用于致命错误")
    
    print("✅ 日志级别测试完成")


def test_file_output():
    """
    测试文件输出功能
    
    验证：
        1. 日志文件正确创建
        2. 日志内容正确写入
        3. 日志格式正确
    """
    print("\n" + "=" * 50)
    print("测试2: 文件输出功能")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, 'test.log')
        
        manager = LogManager.get_instance()
        manager._handlers.clear()
        manager.setup_file(log_file, LogLevel.DEBUG)
        
        logger = get_logger('test_file')
        
        logger.info("测试文件输出 - 第一条日志")
        logger.success("测试文件输出 - 成功日志")
        logger.error("测试文件输出 - 错误日志")
        
        manager.close()
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"日志文件内容:\n{content}")
                assert "测试文件输出 - 第一条日志" in content
                assert "SUCCESS" in content
                assert "ERROR" in content
            print("✅ 文件输出测试完成")
        else:
            print("❌ 日志文件未创建")


def test_signal_handler():
    """
    测试信号处理器功能
    
    验证：
        1. 信号回调正确触发
        2. 日志消息正确传递
    """
    print("\n" + "=" * 50)
    print("测试3: 信号处理器功能")
    print("=" * 50)
    
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    manager = LogManager.get_instance()
    manager._handlers.clear()
    manager.setup_signal(callback, LogLevel.INFO)
    
    logger = get_logger('test_signal')
    
    logger.debug("这条DEBUG日志不应被接收")
    logger.info("这条INFO日志应该被接收")
    logger.success("这条SUCCESS日志应该被接收")
    logger.warning("这条WARNING日志应该被接收")
    
    print(f"接收到的消息数量: {len(received_messages)}")
    for msg in received_messages:
        print(f"  - {msg}")
    
    assert len(received_messages) == 3
    assert "INFO日志" in received_messages[0]
    assert "SUCCESS日志" in received_messages[1]
    assert "WARNING日志" in received_messages[2]
    
    print("✅ 信号处理器测试完成")


def test_log_rotation():
    """
    测试日志轮转功能
    
    验证：
        1. 日志文件大小限制生效
        2. 备份文件正确创建
    """
    print("\n" + "=" * 50)
    print("测试4: 日志轮转功能")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, 'rotation.log')
        
        handler = FileHandler(
            log_file,
            level=LogLevel.DEBUG,
            max_size=500,
            backup_count=3
        )
        
        logger = get_logger('test_rotation')
        logger.add_handler(handler)
        
        for i in range(20):
            logger.info(f"测试日志轮转 - 第{i+1}条日志，这是一条较长的日志消息用于测试轮转功能")
        
        handler.close()
        
        files = list(Path(tmpdir).glob('rotation.log*'))
        print(f"生成的日志文件: {[f.name for f in files]}")
        
        assert len(files) > 1, "应该生成多个日志文件"
        
        print("✅ 日志轮转测试完成")


def test_performance():
    """
    测试日志性能
    
    验证：
        1. 大量日志输出性能
        2. 多处理器性能
    """
    print("\n" + "=" * 50)
    print("测试5: 日志性能测试")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, 'perf.log')
        
        manager = LogManager.get_instance()
        manager._handlers.clear()
        manager.setup_console(LogLevel.WARNING)
        manager.setup_file(log_file, LogLevel.DEBUG)
        
        logger = get_logger('test_perf')
        
        start_time = time.time()
        
        for i in range(1000):
            logger.debug(f"性能测试日志 - 第{i+1}条")
        
        elapsed = time.time() - start_time
        
        print(f"输出1000条日志耗时: {elapsed:.3f}秒")
        print(f"平均每条日志: {elapsed/1000*1000:.3f}毫秒")
        
        manager.close()
        
        print("✅ 性能测试完成")


def test_module_isolation():
    """
    测试模块隔离
    
    验证：
        1. 不同模块的日志记录器相互独立
        2. 全局处理器正确共享
    """
    print("\n" + "=" * 50)
    print("测试6: 模块隔离测试")
    print("=" * 50)
    
    received = {'module_a': [], 'module_b': []}
    
    def callback_a(msg):
        received['module_a'].append(msg)
    
    def callback_b(msg):
        received['module_b'].append(msg)
    
    manager = LogManager.get_instance()
    manager._handlers.clear()
    
    logger_a = get_logger('module_a')
    logger_b = get_logger('module_b')
    
    handler_a = SignalHandler(LogLevel.INFO, callback_a)
    handler_b = SignalHandler(LogLevel.INFO, callback_b)
    
    logger_a.add_handler(handler_a)
    logger_b.add_handler(handler_b)
    
    logger_a.info("模块A的日志")
    logger_b.info("模块B的日志")
    
    print(f"模块A接收: {received['module_a']}")
    print(f"模块B接收: {received['module_b']}")
    
    assert len(received['module_a']) == 1, "模块A应只接收自己的日志"
    assert len(received['module_b']) == 1, "模块B应只接收自己的日志"
    assert "模块A" in received['module_a'][0], "模块A应接收到自己的消息"
    assert "模块B" in received['module_b'][0], "模块B应接收到自己的消息"
    
    print("✅ 模块隔离测试完成")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("       日志系统测试套件")
    print("=" * 60)
    
    try:
        test_log_levels()
        test_file_output()
        test_signal_handler()
        test_log_rotation()
        test_performance()
        test_module_isolation()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        LogManager.get_instance().close()


if __name__ == '__main__':
    run_all_tests()
