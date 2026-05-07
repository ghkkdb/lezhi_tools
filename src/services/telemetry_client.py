# -*- coding: utf-8 -*-
"""匿名使用事件上报。"""
from typing import Any, Dict, Optional

from src.config.app_config import APP_VERSION
from src.services.client_id import get_client_id
from src.services.http_client import ApiError, request_json
from src.services.license_client import get_cached_license_key


def track(
    event_name: str,
    payload: Optional[Dict[str, Any]] = None,
    task_name: Optional[str] = None,
    success: Optional[bool] = None,
    duration_ms: Optional[int] = None,
) -> bool:
    """上报使用事件；失败不抛出，避免影响主流程。"""
    data = {
        "machine_id": get_client_id(),
        "key": get_cached_license_key(),
        "event_type": event_name,
        "success": success,
        "payload": {
            "app_version": APP_VERSION,
            "task_name": task_name,
            "success": success,
            "duration_ms": duration_ms,
            **(payload or {}),
        },
    }
    try:
        request_json("POST", "/api/events", data)
        return True
    except ApiError:
        return False
