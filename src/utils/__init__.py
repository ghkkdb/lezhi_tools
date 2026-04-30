# -*- coding: utf-8 -*-
"""工具模块轻量入口。"""

_WIN_API_EXPORTS = {
    "bind_window", "background_click", "background_key", "background_drag",
    "capture_window", "run_key_config",
}
_IMAGE_EXPORTS = {"find_image", "find_all_images"}
_LOGGER_EXPORTS = {
    "LogLevel", "LogRecord", "Handler", "ConsoleHandler", "FileHandler",
    "SignalHandler", "Logger", "LogManager", "get_logger", "setup_logging",
    "set_log_context", "get_log_context",
}
_TRACKER_EXPORTS = {"InputTracker"}

__all__ = sorted(_WIN_API_EXPORTS | _IMAGE_EXPORTS | _LOGGER_EXPORTS | _TRACKER_EXPORTS)


def __getattr__(name):
    if name in _WIN_API_EXPORTS:
        from . import win_api
        return getattr(win_api, name)
    if name in _IMAGE_EXPORTS:
        from . import image_utils
        return getattr(image_utils, name)
    if name in _LOGGER_EXPORTS:
        from . import logger
        return getattr(logger, name)
    if name in _TRACKER_EXPORTS:
        from .input_tracker import InputTracker
        return InputTracker
    raise AttributeError(f"module 'src.utils' has no attribute {name!r}")
