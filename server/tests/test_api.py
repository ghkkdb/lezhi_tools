import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


def make_client(tmp_path: Path) -> TestClient:
    os.environ["LICENSE_SERVER_DB"] = str(tmp_path / "test.sqlite3")
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "secret"

    from app.main import app

    return TestClient(app)


def login(client: TestClient) -> str:
    response = client.post("/api/admin/login", json={"username": "admin", "password": "secret"})
    assert response.status_code == 200
    return response.json()["token"]


def test_admin_license_activation_verify_and_stats(tmp_path):
    with make_client(tmp_path) as client:
        token = login(client)
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post(
            "/api/admin/licenses",
            headers=headers,
            json={"key": "LIC-TEST-1", "owner": "tester", "max_devices": 1},
        )
        assert created.status_code == 201

        activated = client.post(
            "/api/license/activate",
            json={"key": "LIC-TEST-1", "machine_id": "machine-a", "app_version": "1.0.0"},
        )
        assert activated.status_code == 200
        activation_token = activated.json()["activation_token"]

        verified = client.post(
            "/api/license/verify",
            json={"activation_token": activation_token, "machine_id": "machine-a"},
        )
        assert verified.status_code == 200
        assert verified.json()["valid"] is True

        rejected = client.post(
            "/api/license/activate",
            json={"key": "LIC-TEST-1", "machine_id": "machine-b"},
        )
        assert rejected.status_code == 403
        assert rejected.json()["detail"] == "device_limit_reached"

        stats = client.get("/api/admin/stats", headers=headers)
        assert stats.status_code == 200
        assert stats.json()["licenses"]["active"] == 1
        assert stats.json()["licenses"]["active_usable"] == 1
        assert stats.json()["clients"]["total"] == 1

        bulk = client.post(
            "/api/admin/licenses",
            headers=headers,
            json={"count": 3, "max_devices": 1},
        )
        assert bulk.status_code == 201
        assert len(bulk.json()["items"]) == 3

        deleted = client.post(
            "/api/admin/licenses/bulk-delete",
            headers=headers,
            json={"ids": [item["id"] for item in bulk.json()["items"]]},
        )
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] == 3


def test_release_latest_and_events(tmp_path):
    with make_client(tmp_path) as client:
        token = login(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/admin/releases",
            headers=headers,
            json={
                "version": "1.2.3",
                "platform": "windows",
                "download_url": "https://example.com/app.zip",
                "mandatory": True,
            },
        )
        assert response.status_code == 201

        latest = client.get("/api/update/latest?platform=windows")
        assert latest.status_code == 200
        assert latest.json()["item"]["version"] == "1.2.3"
        assert latest.json()["item"]["mandatory"] is True

        event = client.post(
            "/api/events",
            json={"event_type": "app_start", "machine_id": "machine-a", "payload": {"ok": True}},
        )
        assert event.status_code == 202

        events = client.get("/api/admin/events", headers=headers)
        assert events.status_code == 200
        assert events.json()["items"][0]["event_type"] == "app_start"
