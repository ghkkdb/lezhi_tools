# -*- coding: utf-8 -*-
"""
YMJH 游戏辅助工具 - 程序入口
============================

启动方式：
    python main.py
"""
import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from src.ui import ClassicScriptUI
from src.ui.app_icons import app_icon, set_windows_app_id
from src.services import license_client, telemetry_client, update_client


def main():
    """
    程序主入口函数
    """
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 9))
    app.setWindowIcon(app_icon())

    telemetry_client.track("app_start")
    license_state = license_client.verify_cached_license()
    update_info = update_client.check_update()
    telemetry_client.track(
        "update_check",
        {
            "has_update": update_info.has_update,
            "latest_version": update_info.latest_version,
            "message": update_info.message,
        },
        success=not bool(update_info.message),
    )
    
    window = ClassicScriptUI(license_state=license_state, update_info=update_info)
    window._activity_timer = QTimer(window)
    window._activity_timer.setInterval(5 * 60 * 1000)
    window._activity_timer.timeout.connect(lambda: telemetry_client.track("app_heartbeat"))
    window._activity_timer.start()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
