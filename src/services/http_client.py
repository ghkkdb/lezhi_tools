# -*- coding: utf-8 -*-
"""小型 JSON HTTP 客户端，避免给桌面端新增 requests 依赖。"""
import json
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config.app_config import API_BASE_URL, REQUEST_TIMEOUT


class ApiError(Exception):
    """远程 API 调用失败。"""


def _build_url(path: str, query: Optional[Dict[str, Any]] = None) -> str:
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


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
        raise ApiError(f"HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ApiError(str(exc)) from exc
