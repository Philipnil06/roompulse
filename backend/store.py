from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def comfort_status(temperature_c: float, humidity_pct: float) -> dict[str, Any]:
    issues: list[str] = []
    if temperature_c < 18:
        issues.append("cool")
    elif temperature_c > 26:
        issues.append("warm")
    if humidity_pct < 30:
        issues.append("dry")
    elif humidity_pct > 60:
        issues.append("humid")

    if not issues:
        label = "comfortable"
        message = "Temperature and humidity are within the configured comfort band."
    else:
        label = issues[0] if len(issues) == 1 else "attention"
        message = "Room is " + " and ".join(issues) + "."

    return {
        "label": label,
        "issues": issues,
        "message": message,
        "temperature_band_c": [18, 26],
        "humidity_band_pct": [30, 60],
    }


class RoomPulseStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    temperature_c REAL NOT NULL,
                    humidity_pct REAL NOT NULL,
                    measured_at TEXT NOT NULL,
                    received_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_measurements_room_time
                ON measurements(room_id, measured_at DESC);
                """
            )
            connection.commit()

    def add_measurement(
        self,
        *,
        device_id: str,
        room_id: str,
        temperature_c: float,
        humidity_pct: float,
        measured_at: datetime | None = None,
    ) -> dict[str, Any]:
        measured_at = (measured_at or utc_now()).astimezone(timezone.utc)
        received_at = utc_now()
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO measurements
                  (device_id, room_id, temperature_c, humidity_pct, measured_at, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    room_id,
                    temperature_c,
                    humidity_pct,
                    measured_at.isoformat(),
                    received_at.isoformat(),
                ),
            )
            connection.commit()
            row_id = cursor.lastrowid
        return self.get_by_id(int(row_id))

    def get_by_id(self, measurement_id: int) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM measurements WHERE id = ?", (measurement_id,)
            ).fetchone()
        if row is None:
            raise KeyError(measurement_id)
        return self._serialize(row)

    def latest(self, room_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM measurements
                WHERE room_id = ?
                ORDER BY measured_at DESC, id DESC
                LIMIT 1
                """,
                (room_id,),
            ).fetchone()
        return self._serialize(row) if row else None

    def history(
        self, room_id: str, *, hours: int = 24, limit: int = 500
    ) -> list[dict[str, Any]]:
        cutoff = (utc_now() - timedelta(hours=hours)).isoformat()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT * FROM measurements
                WHERE room_id = ? AND measured_at >= ?
                ORDER BY measured_at ASC, id ASC
                LIMIT ?
                """,
                (room_id, cutoff, limit),
            ).fetchall()
        return [self._serialize(row) for row in rows]

    def summary(self, room_id: str, *, hours: int = 24) -> dict[str, Any] | None:
        rows = self.history(room_id, hours=hours, limit=10000)
        if not rows:
            return None
        temperatures = [row["temperature_c"] for row in rows]
        humidities = [row["humidity_pct"] for row in rows]
        temp_delta = temperatures[-1] - temperatures[0]
        humidity_delta = humidities[-1] - humidities[0]
        return {
            "room_id": room_id,
            "window_hours": hours,
            "sample_count": len(rows),
            "from": rows[0]["measured_at"],
            "to": rows[-1]["measured_at"],
            "temperature_c": {
                "min": round(min(temperatures), 1),
                "max": round(max(temperatures), 1),
                "average": round(sum(temperatures) / len(temperatures), 1),
                "change": round(temp_delta, 1),
                "trend": _trend(temp_delta, threshold=0.3),
            },
            "humidity_pct": {
                "min": round(min(humidities), 1),
                "max": round(max(humidities), 1),
                "average": round(sum(humidities) / len(humidities), 1),
                "change": round(humidity_delta, 1),
                "trend": _trend(humidity_delta, threshold=2.0),
            },
            "latest_comfort": comfort_status(temperatures[-1], humidities[-1]),
        }

    @staticmethod
    def _serialize(row: sqlite3.Row) -> dict[str, Any]:
        measured_at = parse_timestamp(row["measured_at"])
        age_seconds = max(0, int((utc_now() - measured_at).total_seconds()))
        temperature_c = float(row["temperature_c"])
        humidity_pct = float(row["humidity_pct"])
        return {
            "id": int(row["id"]),
            "device_id": row["device_id"],
            "room_id": row["room_id"],
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "measured_at": measured_at.isoformat(),
            "received_at": parse_timestamp(row["received_at"]).isoformat(),
            "age_seconds": age_seconds,
            "stale": age_seconds > 300,
            "comfort": comfort_status(temperature_c, humidity_pct),
        }


def _trend(delta: float, *, threshold: float) -> str:
    if delta >= threshold:
        return "rising"
    if delta <= -threshold:
        return "falling"
    return "stable"

