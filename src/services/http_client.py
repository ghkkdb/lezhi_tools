# -*- coding: utf-8 -*-
"""小型 JSON HTTP 客户端，避免给桌面端新增 requests 依赖。"""
import json
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config.app_config import API_BASE_URL, REQUEST_TIMEOUT


ERROR_TEXT = {
    "license_not_found": "卡密不存在",
    "license_inactive": "卡密已被禁用",
    "license_expired": "卡密已过期",
    "client_not_activated": "当前设备尚未激活，请重新验证卡密",
    "device_limit_reached": "该卡密绑定设备数量已达上限",
    "release_not_found": "暂无可用更新版本",
}


class ApiError(Exception):
    """远程 API 调用失败。"""

    def __init__(self, message: str, status_code: int | None = None, detail: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


def _build_url(path: str, query: Optional[Dict[str, Any]] = None) -> str:
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def _error_message(status_code: int, raw: str) -> str:
    detail = raw
    try:
        data = json.loads(raw) if raw else {}
        detail = str(data.get("detail") or data.get("message") or raw)
    except json.JSONDecodeError:
        pass
    return ERROR_TEXT.get(detail, f"服务器返回错误 {status_code}")


def request_json(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
    timeout: float = REQUEST_TIMEOUT,
) -> Dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(_build_url(path, query), data=body, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ApiError(_error_message(exc.code, detail), status_code=exc.code, detail=detail) from exc
    except (URLError, TimeoutError, OSError):
        raise ApiError("无法连接服务器，请检查网络或稍后重试") from None
    except json.JSONDecodeError:
        raise ApiError("服务器响应格式异常") from None
