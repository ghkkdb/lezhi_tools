# -*- coding: utf-8 -*-
"""版本检查和更新提醒数据。"""
from dataclasses import dataclass
from typing import Optional

from src.config.app_config import APP_VERSION
from src.services.http_client import ApiError, request_json


@dataclass
class UpdateInfo:
    has_update: bool = False
    latest_version: str = ""
    download_url: str = ""
    sha256: str = ""
    notes: str = ""
    message: str = ""


def _version_tuple(version: str):
    parts = []
    for part in version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def check_update() -> UpdateInfo:
    try:
        data = request_json("GET", "/api/update/latest", query={"version": APP_VERSION})
    except ApiError as exc:
        return UpdateInfo(message=f"检查更新失败: {exc}")

    data = data.get("item") or data
    latest = str(data.get("latest_version") or data.get("version") or "")
    has_update = bool(data.get("has_update"))
    if latest and not has_update:
        has_update = _version_tuple(latest) > _version_tuple(APP_VERSION)

    return UpdateInfo(
        has_update=has_update,
        latest_version=latest,
        download_url=str(data.get("download_url") or data.get("package_url") or ""),
        sha256=str(data.get("sha256") or ""),
        notes=str(data.get("notes") or ""),
        message=str(data.get("message") or ""),
    )
