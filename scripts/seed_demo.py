from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone

import httpx


API_URL = os.getenv("ROOMPULSE_API_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.getenv("ROOMPULSE_DEVICE_TOKEN", "local-development-token")


def main() -> None:
    now = datetime.now(timezone.utc)
    with httpx.Client(base_url=API_URL, timeout=10) as client:
        for index in range(24):
            hours_ago = (23 - index) * 0.5
            temperature = 22.2 + math.sin(index / 4.5) * 1.6 + index * 0.04
            humidity = 43.0 + math.cos(index / 5.0) * 4.0
            response = client.post(
                "/v1/measurements",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json={
                    "device_id": "demo-seed",
                    "room_id": "room-philip",
                    "temperature_c": round(temperature, 1),
                    "humidity_pct": round(humidity, 1),
                    "measured_at": (now - timedelta(hours=hours_ago)).isoformat(),
                },
            )
            response.raise_for_status()

        # Finish with a real-looking latest value matching the hardware test.
        response = client.post(
            "/v1/measurements",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "device_id": "genesis-mini",
                "room_id": "room-philip",
                "temperature_c": 25.0,
                "humidity_pct": 48.0,
            },
        )
        response.raise_for_status()
        print("Seeded 25 measurements; latest is 25.0 °C / 48.0 % RH.")


if __name__ == "__main__":
    main()

