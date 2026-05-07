# -*- coding: utf-8 -*-
"""匿名客户端 ID 管理。"""
import json
import uuid
from pathlib import Path

from src.config import config


IDENTITY_FILE = "client_identity.json"


def _identity_path() -> Path:
    return Path(config.path.get_config_path(IDENTITY_FILE))


def get_client_id() -> str:
    """返回匿名客户端 ID；首次运行时生成并持久化。"""
    path = _identity_path()
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            client_id = data.get("client_id")
            if client_id:
                return str(client_id)
    except Exception:
        pass

    client_id = str(uuid.uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"client_id": client_id}, f, ensure_ascii=False, indent=2)
    return client_id
