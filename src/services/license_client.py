# -*- coding: utf-8 -*-
"""卡密激活、验证与本地缓存。"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import config
from src.config.app_config import APP_VERSION
from src.services.client_id import get_client_id
from src.services.http_client import ApiError, request_json


LICENSE_CACHE_FILE = "license_cache.json"


@dataclass
class LicenseState:
    ok: bool
    license_key: str = ""
    expire_at: str = ""
    message: str = "卡密未验证或已失效"
    offline: bool = False


def _cache_path() -> Path:
    return Path(config.path.get_config_path(LICENSE_CACHE_FILE))


def _read_cache() -> Dict[str, Any]:
    path = _cache_path()
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_cache(data: Dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_cached_license_key() -> str:
    return str(_read_cache().get("license_key", ""))


def _state_from_response(data: Dict[str, Any], license_key: str, offline: bool = False) -> LicenseState:
    ok = bool(data.get("ok") or data.get("valid"))
    license_data = data.get("license") or {}
    return LicenseState(
        ok=ok,
        license_key=license_key,
        expire_at=str(data.get("expire_at") or license_data.get("expires_at") or ""),
        message=str(data.get("message") or ("授权有效" if ok else "卡密未验证或已失效")),
        offline=offline,
    )


def activate_license(license_key: str) -> LicenseState:
    license_key = license_key.strip()
    if not license_key:
        return LicenseState(ok=False, message="请输入卡密")

    payload = {
        "key": license_key,
        "machine_id": get_client_id(),
        "app_version": APP_VERSION,
    }
    try:
        data = request_json("POST", "/api/license/activate", payload)
    except ApiError as exc:
        return LicenseState(ok=False, license_key=license_key, message=f"验证失败: {exc}", offline=True)

    state = _state_from_response(data, license_key)
    _write_cache({
        "license_key": license_key,
        "client_id": get_client_id(),
        "activation_token": data.get("activation_token", ""),
        "ok": state.ok,
        "expire_at": state.expire_at,
        "message": state.message,
    })
    return state


def verify_cached_license() -> LicenseState:
    license_key = get_cached_license_key()
    if not license_key:
        return LicenseState(ok=False, message="未填写卡密")

    payload = {
        "key": license_key,
        "machine_id": get_client_id(),
        "activation_token": str(_read_cache().get("activation_token", "")),
        "app_version": APP_VERSION,
    }
    try:
        data = request_json("POST", "/api/license/verify", payload)
    except ApiError as exc:
        return LicenseState(ok=False, license_key=license_key, message=f"授权验证失败: {exc}", offline=True)

    state = _state_from_response(data, license_key)
    _write_cache({
        "license_key": license_key,
        "client_id": get_client_id(),
        "activation_token": data.get("activation_token", _read_cache().get("activation_token", "")),
        "ok": state.ok,
        "expire_at": state.expire_at,
        "message": state.message,
    })
    return state
