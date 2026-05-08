# -*- coding: utf-8 -*-
"""应用图标加载工具。"""
import ctypes
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap

from src.config import config


ICON_SIZES = (16, 32, 48, 64, 128, 180, 192, 512)


def icon_path(size: int) -> str:
    return str(config.path.assets_path / "ico" / f"favicon-{size}x{size}.png")


def _source_icon_path(size: int) -> str:
    source_size = next((item for item in ICON_SIZES if item >= size), ICON_SIZES[-1])
    return icon_path(source_size)


def app_icon() -> QIcon:
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addFile(icon_path(size), QSize(size, size))
    return icon


def app_pixmap(size: int) -> QPixmap:
    return QPixmap(_source_icon_path(size)).scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "lezhi_tools.hupijiefangqi"
        )
    except Exception:
        pass
