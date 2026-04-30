# -*- coding: utf-8 -*-
"""
YMJH 游戏辅助工具 - 程序入口
============================

启动方式：
    python main.py
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from src.ui import ClassicScriptUI


def main():
    """
    程序主入口函数
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 9))
    
    window = ClassicScriptUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
