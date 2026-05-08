# -*- coding: utf-8 -*-
"""匿名活跃指标上报。"""
from typing import Any, Dict, Optional

from src.config.app_config import APP_VERSION
from src.services.client_id import get_client_id
from src.services.http_client import ApiError, request_json
from src.services.license_client import get_cached_license_key


ALLOWED_EVENTS = {
    "app_start",
    "app_heartbeat",
    "license_activate",
    "license_verify",
    "update_check",
}


def track(
    event_name: str,
    payload: Optional[Dict[str, Any]] = None,
    task_name: Optional[str] = None,
    success: Optional[bool] = None,
    duration_ms: Optional[int] = None,
) -> bool:
    """上报匿名活跃事件；失败不抛出，避免影响主流程。"""
    if event_name not in ALLOWED_EVENTS:
        return False

    safe_payload = {
        "app_version": APP_VERSION,
        **(payload or {}),
    }
    if success is not None:
        safe_payload["success"] = success

    data = {
        "machine_id": get_client_id(),
        "key": get_cached_license_key(),
        "event_type": event_name,
        "payload": safe_payload,
    }
    try:
        request_json("POST", "/api/events", data)
        return True
    except ApiError:
        return False
