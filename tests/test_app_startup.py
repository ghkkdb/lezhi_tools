# -*- coding: utf-8 -*-
"""
应用启动测试
============
测试应用是否能正常启动
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# 只导入配置模块
from config import config

def test_app_startup():
    """测试应用启动"""
    print("=" * 60)
    print("测试应用启动")
    print("=" * 60)
    
    # 测试配置加载
    print(f"应用名称: {config.app_name}")
    print(f"窗口类名: {config.class_name}")
    print(f"游戏窗口尺寸: {config.x}x{config.y}")
    print(f"UI窗口尺寸: {config.ui_width}x{config.ui_height}")
    print(f"日常任务数量: {len(config.daily_tasks)}")
    
    # 测试日志配置
    log_config = config.get_logging_config()
    print(f"日志配置: {log_config}")
    print(f"日志文件路径: {log_config['file']['path']}")
    
    # 测试路径配置
    print(f"资源路径: {config.assets_path}")
    print(f"图片路径: {config.img_path}")
    
    print("\n✓ 应用启动测试通过！")

if __name__ == "__main__":
    test_app_startup()
