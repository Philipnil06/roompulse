from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app import create_app


TOKEN = "test-device-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def make_client(tmp_path):
    app = create_app(db_path=tmp_path / "test.db", device_token=TOKEN)
    return TestClient(app)


def test_health_and_authentication(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/health").json()["status"] == "ok"
        denied = client.post(
            "/v1/measurements",
            json={
                "device_id": "genesis-mini",
                "temperature_c": 22.5,
                "humidity_pct": 45,
            },
        )
        assert denied.status_code == 401


def test_local_dashboard_cors_on_dynamic_port(tmp_path):
    with make_client(tmp_path) as client:
        response = client.options(
            "/v1/rooms/room-philip/latest",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3001"


def test_ingest_latest_history_and_summary(tmp_path):
    now = datetime.now(timezone.utc)
    with make_client(tmp_path) as client:
        for index, (temperature, humidity) in enumerate(
            [(21.0, 44.0), (22.0, 47.0), (23.0, 50.0)]
        ):
            response = client.post(
                "/v1/measurements",
                headers=HEADERS,
                json={
                    "device_id": "genesis-mini",
                    "room_id": "room-philip",
                    "temperature_c": temperature,
                    "humidity_pct": humidity,
                    "measured_at": (
                        now - timedelta(minutes=2 - index)
                    ).isoformat(),
                },
            )
            assert response.status_code == 201

        latest = client.get("/v1/rooms/room-philip/latest")
        assert latest.status_code == 200
        assert latest.json()["temperature_c"] == 23.0
        assert latest.json()["comfort"]["label"] == "comfortable"

        history = client.get("/v1/rooms/room-philip/history?hours=1")
        assert len(history.json()["measurements"]) == 3

        summary = client.get("/v1/rooms/room-philip/summary?hours=1").json()
        assert summary["sample_count"] == 3
        assert summary["temperature_c"] == {
            "min": 21.0,
            "max": 23.0,
            "average": 22.0,
            "change": 2.0,
            "trend": "rising",
        }
        assert summary["humidity_pct"]["trend"] == "rising"


def test_validation_rejects_impossible_sensor_values(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post(
            "/v1/measurements",
            headers=HEADERS,
            json={
                "device_id": "genesis-mini",
                "temperature_c": 70,
                "humidity_pct": 10,
            },
        )
        assert response.status_code == 422


def test_missing_room_returns_404(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/v1/rooms/unknown/latest").status_code == 404
        assert client.get("/v1/rooms/unknown/summary").status_code == 404
