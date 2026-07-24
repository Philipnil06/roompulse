from datetime import datetime, timedelta, timezone

from backend.store import RoomPulseStore, comfort_status


def test_comfort_status():
    assert comfort_status(22, 45)["label"] == "comfortable"
    assert comfort_status(28, 70)["issues"] == ["warm", "humid"]
    assert comfort_status(16, 25)["issues"] == ["cool", "dry"]


def test_stale_reading(tmp_path):
    store = RoomPulseStore(tmp_path / "store.db")
    store.initialize()
    store.add_measurement(
        device_id="device",
        room_id="room",
        temperature_c=20,
        humidity_pct=40,
        measured_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    assert store.latest("room")["stale"] is True

