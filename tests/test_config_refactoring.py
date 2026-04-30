# -*- coding: utf-8 -*-
"""
配置模块测试脚本
================
独立测试配置模块的功能，不依赖其他模块
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# 只导入配置模块（不通过 src 包导入）
from config.window_config import WindowConfig
from config.task_config import TaskConfig
from config.task_definition_config import TaskDefinitionConfig
from config.ui_config import UIConfig
from config.key_config import KeyConfig
from config.path_config import PathConfig
from config.logging_config import LoggingConfig
from config.user_config import UserConfig
from config.settings import Config, config

def test_window_config():
    """测试窗口配置"""
    print("=" * 60)
    print("测试 WindowConfig")
    print("=" * 60)
    
    window_config = WindowConfig()
    print(f"app_name: {window_config.app_name}")
    print(f"class_name: {window_config.class_name}")
    print(f"game_width: {window_config.game_width}")
    print(f"game_height: {window_config.game_height}")
    print(f"ui_width: {window_config.ui_width}")
    print(f"ui_height: {window_config.ui_height}")
    print("✓ WindowConfig 测试通过\n")

def test_task_config():
    """测试任务配置"""
    print("=" * 60)
    print("测试 TaskConfig")
    print("=" * 60)
    
    task_config = TaskConfig()
    print(f"daily_tasks 数量: {len(task_config.daily_tasks)}")
    print(f"chaguan_dt: {task_config.chaguan_dt}")
    print(f"chaguan_dt_weights: {task_config.chaguan_dt_weights}")
    print(f"bangpai_btn: {task_config.bangpai_btn}")
    print(f"yaoqianshu_options: {task_config.yaoqianshu_options}")
    print("✓ TaskConfig 测试通过\n")

def test_task_definition_config():
    """测试任务定义配置"""
    print("=" * 60)
    print("测试 TaskDefinitionConfig")
    print("=" * 60)
    
    task_def_config = TaskDefinitionConfig()
    print(f"任务定义数量: {len(task_def_config.definitions)}")
    print(f"has_task_config('摇钱树'): {task_def_config.has_task_config('摇钱树')}")
    print(f"has_task_config('不存在'): {task_def_config.has_task_config('不存在')}")
    
    if task_def_config.has_task_config('摇钱树'):
        default_params = task_def_config.get_task_default_params('摇钱树')
        print(f"摇钱树默认参数: {default_params}")
    
    print("✓ TaskDefinitionConfig 测试通过\n")

def test_ui_config():
    """测试UI配置"""
    print("=" * 60)
    print("测试 UIConfig")
    print("=" * 60)
    
    ui_config = UIConfig()
    print(f"ui_sizes 数量: {len(ui_config.sizes)}")
    print(f"ui_layout 数量: {len(ui_config.layout)}")
    print(f"tooltips 数量: {len(ui_config.tooltips)}")
    print(f"nav_tabs 数量: {len(ui_config.nav_tabs)}")
    print(f"get_tooltip('pick_idle'): {ui_config.get_tooltip('pick_idle')}")
    print("✓ UIConfig 测试通过\n")

def test_key_config():
    """测试按键映射配置"""
    print("=" * 60)
    print("测试 KeyConfig")
    print("=" * 60)
    
    key_config = KeyConfig()
    print(f"VK_CODE 数量: {len(key_config.VK_CODE)}")
    print(f"VK_CODE['ESC']: {key_config.VK_CODE.get('ESC')}")
    print(f"VK_CODE['ENTER']: {key_config.VK_CODE.get('ENTER')}")
    print("✓ KeyConfig 测试通过\n")

def test_path_config():
    """测试路径配置"""
    print("=" * 60)
    print("测试 PathConfig")
    print("=" * 60)
    
    path_config = PathConfig()
    print(f"base_path: {path_config.base_path}")
    print(f"assets_path: {path_config.assets_path}")
    print(f"img_path: {path_config.img_path}")
    print(f"config_path: {path_config.config_path}")
    print(f"logs_path: {path_config.logs_path}")
    print(f"get_img_path('test.png'): {path_config.get_img_path('test.png')}")
    print(f"get_log_path(): {path_config.get_log_path()}")
    print("✓ PathConfig 测试通过\n")

def test_logging_config():
    """测试日志配置"""
    print("=" * 60)
    print("测试 LoggingConfig")
    print("=" * 60)
    
    logging_config = LoggingConfig()
    print(f"日志配置: {logging_config.get_log_config()}")
    print(f"控制台配置: {logging_config.get_console_config()}")
    print(f"文件配置: {logging_config.get_file_config()}")
    print(f"信号配置: {logging_config.get_signal_config()}")
    print("✓ LoggingConfig 测试通过\n")

def test_config_facade():
    """测试配置门面类"""
    print("=" * 60)
    print("测试 Config 门面类（向后兼容）")
    print("=" * 60)
    
    # 测试属性访问
    print(f"config.app_name: {config.app_name}")
    print(f"config.class_name: {config.class_name}")
    print(f"config.x: {config.x}")
    print(f"config.y: {config.y}")
    print(f"config.ui_width: {config.ui_width}")
    print(f"config.ui_height: {config.ui_height}")
    print(f"config.daily_tasks 数量: {len(config.daily_tasks)}")
    print(f"config.chaguan_dt: {config.chaguan_dt}")
    print(f"config.chaguan_dt_weights: {config.chaguan_dt_weights}")
    print(f"config.bangpai_btn: {config.bangpai_btn}")
    print(f"config.yaoqianshu_options: {config.yaoqianshu_options}")
    print(f"config.ui_sizes 数量: {len(config.ui_sizes)}")
    print(f"config.ui_layout 数量: {len(config.ui_layout)}")
    print(f"config.tooltips 数量: {len(config.tooltips)}")
    print(f"config.nav_tabs 数量: {len(config.nav_tabs)}")
    print(f"config.VK_CODE 数量: {len(config.VK_CODE)}")
    print(f"config.assets_path: {config.assets_path}")
    print(f"config.img_path: {config.img_path}")
    print(f"config.task_config_definitions 数量: {len(config.task_config_definitions)}")
    
    # 测试方法调用
    print(f"config.get_img_path('test.png'): {config.get_img_path('test.png')}")
    print(f"config.get_tooltip('pick_idle'): {config.get_tooltip('pick_idle')}")
    print(f"config.get_nav_tabs() 数量: {len(config.get_nav_tabs())}")
    print(f"config.get_logging_config(): {config.get_logging_config()}")
    print(f"config.get_log_path(): {config.get_log_path()}")
    print(f"config.has_task_config('摇钱树'): {config.has_task_config('摇钱树')}")
    print(f"config.has_task_config('不存在'): {config.has_task_config('不存在')}")
    print(f"config.get_task_default_params('摇钱树'): {config.get_task_default_params('摇钱树')}")
    print(f"config.get_task_mapped_param('摇钱树', 'choice', '轻轻摇【免费】'): {config.get_task_mapped_param('摇钱树', 'choice', '轻轻摇【免费】')}")
    print(f"config.get_config_names(): {config.get_config_names()}")
    print(f"config.is_default_config('默认配置'): {config.is_default_config('默认配置')}")
    
    print("✓ Config 门面类测试通过\n")

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始配置模块测试")
    print("=" * 60 + "\n")
    
    try:
        test_window_config()
        test_task_config()
        test_task_definition_config()
        test_ui_config()
        test_key_config()
        test_path_config()
        test_logging_config()
        test_config_facade()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
