from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from pydantic import AliasChoices, BaseModel, Field

from .db import init_db, row_to_dict, session
from .security import hash_password, make_token, verify_password


SESSION_COOKIE = "admin_session"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Lezhi License Server", version="0.1.0", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LicenseCreate(BaseModel):
    key: str | None = None
    owner: str | None = None
    max_devices: int = Field(default=1, ge=1)
    expires_at: str | None = None
    note: str | None = None
    status: str = "active"


class LicenseUpdate(BaseModel):
    owner: str | None = None
    max_devices: int | None = Field(default=None, ge=1)
    expires_at: str | None = None
    note: str | None = None
    status: str | None = None


class ActivateRequest(BaseModel):
    license_key: str = Field(validation_alias=AliasChoices("key", "license_key"), min_length=1)
    machine_id: str = Field(validation_alias=AliasChoices("machine_id", "client_id"), min_length=1)
    client_name: str | None = None
    app_version: str | None = None
    metadata: dict[str, Any] | None = None


class VerifyRequest(BaseModel):
    license_key: str | None = Field(default=None, validation_alias=AliasChoices("key", "license_key"))
    activation_token: str | None = None
    machine_id: str = Field(validation_alias=AliasChoices("machine_id", "client_id"), min_length=1)
    app_version: str | None = None


class EventRequest(BaseModel):
    event_type: str = Field(validation_alias=AliasChoices("event_type", "event_name"), min_length=1, max_length=80)
    license_key: str | None = Field(default=None, validation_alias=AliasChoices("key", "license_key"))
    activation_token: str | None = None
    machine_id: str | None = Field(default=None, validation_alias=AliasChoices("machine_id", "client_id"))
    payload: dict[str, Any] | None = None


class ReleaseCreate(BaseModel):
    version: str = Field(min_length=1)
    platform: str = "windows"
    download_url: str = Field(min_length=1)
    changelog: str | None = None
    mandatory: bool = False
    active: bool = True


class ReleaseUpdate(BaseModel):
    download_url: str | None = None
    changelog: str | None = None
    mandatory: bool | None = None
    active: bool | None = None


def require_admin(
    admin_session: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    token = admin_session
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

    with session() as conn:
        row = conn.execute(
            """
            SELECT admins.id, admins.username, admin_sessions.expires_at
            FROM admin_sessions
            JOIN admins ON admins.id = admin_sessions.admin_id
            WHERE admin_sessions.token = ?
            """,
            (token,),
        ).fetchone()
        if not row or parse_time(row["expires_at"]) <= utc_now():
            if row:
                conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_expired")
        return {"id": row["id"], "username": row["username"], "token": token}


def get_license_by_key(conn, key: str) -> dict | None:
    return row_to_dict(conn.execute("SELECT * FROM licenses WHERE key = ?", (key,)).fetchone())


def license_is_usable(license_row: dict) -> tuple[bool, str | None]:
    if license_row["status"] != "active":
        return False, "license_inactive"
    expires_at = parse_time(license_row.get("expires_at"))
    if expires_at and expires_at <= utc_now():
        return False, "license_expired"
    return True, None


def get_client_for_verify(conn, payload: VerifyRequest) -> tuple[dict | None, dict | None]:
    if payload.activation_token:
        client = row_to_dict(
            conn.execute(
                "SELECT * FROM clients WHERE activation_token = ? AND machine_id = ?",
                (payload.activation_token, payload.machine_id),
            ).fetchone()
        )
        if not client:
            return None, None
        license_row = row_to_dict(conn.execute("SELECT * FROM licenses WHERE id = ?", (client["license_id"],)).fetchone())
        return license_row, client
    if payload.license_key:
        license_row = get_license_by_key(conn, payload.license_key)
        if not license_row:
            return None, None
        client = row_to_dict(
            conn.execute(
                "SELECT * FROM clients WHERE license_id = ? AND machine_id = ?",
                (license_row["id"], payload.machine_id),
            ).fetchone()
        )
        return license_row, client
    return None, None


def event_payload(payload: dict[str, Any] | None) -> str | None:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) if payload is not None else None


def request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


@app.post("/api/admin/login")
def admin_login(payload: LoginRequest, response: Response) -> dict:
    with session() as conn:
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (payload.username,)).fetchone()
        if not admin or not verify_password(payload.password, admin["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
        token = make_token("adm_")
        expires_at = iso(utc_now() + timedelta(hours=12))
        conn.execute(
            "INSERT INTO admin_sessions (token, admin_id, expires_at) VALUES (?, ?, ?)",
            (token, admin["id"], expires_at),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=12 * 60 * 60,
    )
    return {"token": token, "expires_at": expires_at, "admin": {"id": admin["id"], "username": admin["username"]}}


@app.get("/api/admin/me")
def admin_me(admin: dict = Depends(require_admin)) -> dict:
    return {"admin": {"id": admin["id"], "username": admin["username"]}}


@app.post("/api/admin/logout")
def admin_logout(response: Response, admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        conn.execute("DELETE FROM admin_sessions WHERE token = ?", (admin["token"],))
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/admin/licenses")
def list_licenses(admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        rows = conn.execute("SELECT * FROM licenses ORDER BY id DESC").fetchall()
        return {"items": [dict(row) for row in rows]}


@app.post("/api/admin/licenses", status_code=status.HTTP_201_CREATED)
def create_license(payload: LicenseCreate, admin: dict = Depends(require_admin)) -> dict:
    key = payload.key or make_token("LIC-")
    with session() as conn:
        try:
            conn.execute(
                """
                INSERT INTO licenses (key, status, owner, max_devices, expires_at, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, payload.status, payload.owner, payload.max_devices, payload.expires_at, payload.note),
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="license_key_exists") from exc
        row = get_license_by_key(conn, key)
    return {"item": row}


@app.patch("/api/admin/licenses/{license_id}")
def update_license(license_id: int, payload: LicenseUpdate, admin: dict = Depends(require_admin)) -> dict:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="empty_update")
    fields = [f"{name} = ?" for name in data]
    values = list(data.values()) + [iso(utc_now()), license_id]
    with session() as conn:
        conn.execute(
            f"UPDATE licenses SET {', '.join(fields)}, updated_at = ? WHERE id = ?",
            values,
        )
        row = row_to_dict(conn.execute("SELECT * FROM licenses WHERE id = ?", (license_id,)).fetchone())
        if not row:
            raise HTTPException(status_code=404, detail="license_not_found")
    return {"item": row}


@app.get("/api/admin/clients")
def list_clients(admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        rows = conn.execute(
            """
            SELECT clients.*, licenses.key AS license_key
            FROM clients
            JOIN licenses ON licenses.id = clients.license_id
            ORDER BY clients.last_seen_at DESC
            """
        ).fetchall()
        return {"items": [dict(row) for row in rows]}


@app.post("/api/admin/clients/{client_id}/unbind")
def unbind_client(client_id: int, admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    return {"ok": True}


@app.get("/api/admin/releases")
def list_releases(admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        rows = conn.execute("SELECT * FROM releases ORDER BY created_at DESC, id DESC").fetchall()
        return {"items": [dict(row) for row in rows]}


@app.post("/api/admin/releases", status_code=status.HTTP_201_CREATED)
def create_release(payload: ReleaseCreate, admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        try:
            conn.execute(
                """
                INSERT INTO releases (version, platform, download_url, changelog, mandatory, active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.version,
                    payload.platform,
                    payload.download_url,
                    payload.changelog,
                    int(payload.mandatory),
                    int(payload.active),
                ),
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="release_exists") from exc
        row = row_to_dict(
            conn.execute(
                "SELECT * FROM releases WHERE version = ? AND platform = ?",
                (payload.version, payload.platform),
            ).fetchone()
        )
    return {"item": row}


@app.patch("/api/admin/releases/{release_id}")
def update_release(release_id: int, payload: ReleaseUpdate, admin: dict = Depends(require_admin)) -> dict:
    data = payload.model_dump(exclude_unset=True)
    for key in ("mandatory", "active"):
        if key in data:
            data[key] = int(data[key])
    if not data:
        raise HTTPException(status_code=400, detail="empty_update")
    fields = [f"{name} = ?" for name in data]
    with session() as conn:
        conn.execute(f"UPDATE releases SET {', '.join(fields)} WHERE id = ?", list(data.values()) + [release_id])
        row = row_to_dict(conn.execute("SELECT * FROM releases WHERE id = ?", (release_id,)).fetchone())
        if not row:
            raise HTTPException(status_code=404, detail="release_not_found")
    return {"item": row}


@app.get("/api/admin/events")
def list_events(
    event_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    admin: dict = Depends(require_admin),
) -> dict:
    sql = """
        SELECT events.*, licenses.key AS license_key
        FROM events
        LEFT JOIN licenses ON licenses.id = events.license_id
    """
    params: list[Any] = []
    if event_type:
        sql += " WHERE events.event_type = ?"
        params.append(event_type)
    sql += " ORDER BY events.id DESC LIMIT ?"
    params.append(limit)
    with session() as conn:
        rows = conn.execute(sql, params).fetchall()
        return {"items": [dict(row) for row in rows]}


@app.get("/api/admin/stats")
def admin_stats(admin: dict = Depends(require_admin)) -> dict:
    with session() as conn:
        license_counts = {
            row["status"]: row["count"]
            for row in conn.execute("SELECT status, COUNT(*) AS count FROM licenses GROUP BY status").fetchall()
        }
        event_counts = {
            row["event_type"]: row["count"]
            for row in conn.execute("SELECT event_type, COUNT(*) AS count FROM events GROUP BY event_type").fetchall()
        }
        total_clients = conn.execute("SELECT COUNT(*) AS count FROM clients").fetchone()["count"]
        total_releases = conn.execute("SELECT COUNT(*) AS count FROM releases").fetchone()["count"]
    return {
        "licenses": license_counts,
        "clients": {"total": total_clients},
        "releases": {"total": total_releases},
        "events": event_counts,
    }


@app.post("/api/license/activate")
def activate_license(payload: ActivateRequest, request: Request) -> dict:
    ip = request_ip(request)
    with session() as conn:
        license_row = get_license_by_key(conn, payload.license_key)
        if not license_row:
            raise HTTPException(status_code=404, detail="license_not_found")
        usable, reason = license_is_usable(license_row)
        if not usable:
            raise HTTPException(status_code=403, detail=reason)

        client = row_to_dict(
            conn.execute(
                "SELECT * FROM clients WHERE license_id = ? AND machine_id = ?",
                (license_row["id"], payload.machine_id),
            ).fetchone()
        )
        if not client:
            bound_count = conn.execute(
                "SELECT COUNT(*) AS count FROM clients WHERE license_id = ?",
                (license_row["id"],),
            ).fetchone()["count"]
            if bound_count >= license_row["max_devices"]:
                raise HTTPException(status_code=403, detail="device_limit_reached")
            activation_token = make_token("act_")
            conn.execute(
                """
                INSERT INTO clients (license_id, machine_id, client_name, app_version, activation_token, last_ip, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    license_row["id"],
                    payload.machine_id,
                    payload.client_name,
                    payload.app_version,
                    activation_token,
                    ip,
                ),
            )
        else:
            activation_token = client["activation_token"]
            conn.execute(
                """
                UPDATE clients
                SET client_name = COALESCE(?, client_name), app_version = COALESCE(?, app_version),
                    last_ip = COALESCE(?, last_ip), last_seen_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (payload.client_name, payload.app_version, ip, client["id"]),
            )
        client = row_to_dict(conn.execute("SELECT * FROM clients WHERE activation_token = ?", (activation_token,)).fetchone())
        conn.execute(
            """
            INSERT INTO events (license_id, client_id, machine_id, event_type, ip, payload)
            VALUES (?, ?, ?, 'license.activate', ?, ?)
            """,
            (license_row["id"], client["id"], payload.machine_id, ip, event_payload(payload.metadata)),
        )
    return {
        "valid": True,
        "activation_token": activation_token,
        "license": {
            "key": license_row["key"],
            "status": license_row["status"],
            "expires_at": license_row["expires_at"],
            "max_devices": license_row["max_devices"],
        },
    }


@app.post("/api/license/verify")
def verify_license(payload: VerifyRequest, request: Request) -> dict:
    ip = request_ip(request)
    with session() as conn:
        license_row, client = get_client_for_verify(conn, payload)
        if not license_row:
            raise HTTPException(status_code=404, detail="license_not_found")
        if not client:
            raise HTTPException(status_code=403, detail="client_not_activated")
        usable, reason = license_is_usable(license_row)
        if not usable:
            raise HTTPException(status_code=403, detail=reason)
        conn.execute(
            "UPDATE clients SET app_version = COALESCE(?, app_version), last_ip = COALESCE(?, last_ip), last_seen_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.app_version, ip, client["id"]),
        )
        conn.execute(
            "INSERT INTO events (license_id, client_id, machine_id, event_type, ip) VALUES (?, ?, ?, 'license.verify', ?)",
            (license_row["id"], client["id"], payload.machine_id, ip),
        )
    return {
        "valid": True,
        "license": {
            "key": license_row["key"],
            "status": license_row["status"],
            "expires_at": license_row["expires_at"],
        },
    }


@app.get("/api/update/latest")
def latest_release(platform: str = "windows") -> dict:
    with session() as conn:
        row = row_to_dict(
            conn.execute(
                """
                SELECT * FROM releases
                WHERE platform = ? AND active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (platform,),
            ).fetchone()
        )
    if not row:
        raise HTTPException(status_code=404, detail="release_not_found")
    row["mandatory"] = bool(row["mandatory"])
    row["active"] = bool(row["active"])
    return {"item": row}


@app.post("/api/events", status_code=status.HTTP_202_ACCEPTED)
def write_event(payload: EventRequest, request: Request) -> dict:
    ip = request_ip(request)
    with session() as conn:
        license_row = get_license_by_key(conn, payload.license_key) if payload.license_key else None
        client = None
        if payload.activation_token:
            client = row_to_dict(
                conn.execute("SELECT * FROM clients WHERE activation_token = ?", (payload.activation_token,)).fetchone()
            )
            if client and not license_row:
                license_row = row_to_dict(conn.execute("SELECT * FROM licenses WHERE id = ?", (client["license_id"],)).fetchone())
        conn.execute(
            """
            INSERT INTO events (license_id, client_id, machine_id, event_type, ip, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                license_row["id"] if license_row else None,
                client["id"] if client else None,
                payload.machine_id,
                payload.event_type,
                ip,
                event_payload(payload.payload),
            ),
        )
    return {"ok": True}
