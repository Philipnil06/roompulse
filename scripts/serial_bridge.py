from __future__ import annotations

import argparse
import os
import re
import time

import httpx
import serial


READING_PATTERN = re.compile(
    r"Temperature:\s*(?P<temperature>-?\d+(?:\.\d+)?)\s*C\s*\|\s*"
    r"Humidity:\s*(?P<humidity>\d+(?:\.\d+)?)\s*%"
)


def parse_reading(line: str) -> tuple[float, float] | None:
    match = READING_PATTERN.search(line)
    if not match:
        return None
    return float(match["temperature"]), float(match["humidity"])


def post_reading(
    *, api_url: str, token: str, temperature_c: float, humidity_pct: float
) -> dict:
    response = httpx.post(
        f"{api_url.rstrip('/')}/v1/measurements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "device_id": "genesis-mini-usb",
            "room_id": "room-philip",
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forward Genesis Mini serial readings to the local RoomPulse API."
    )
    parser.add_argument("--port", default="COM4")
    parser.add_argument("--baud", default=115200, type=int)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--timeout", default=30, type=int)
    args = parser.parse_args()

    api_url = os.getenv("ROOMPULSE_API_URL", "http://127.0.0.1:8000")
    token = os.getenv("ROOMPULSE_DEVICE_TOKEN", "local-development-token")
    deadline = time.monotonic() + args.timeout

    with serial.Serial(args.port, args.baud, timeout=1, dsrdtr=False, rtscts=False) as port:
        while time.monotonic() < deadline:
            line = port.readline().decode("utf-8", errors="replace").strip()
            reading = parse_reading(line)
            if reading is None:
                continue
            temperature_c, humidity_pct = reading
            created = post_reading(
                api_url=api_url,
                token=token,
                temperature_c=temperature_c,
                humidity_pct=humidity_pct,
            )
            print(
                f"Forwarded {created['temperature_c']:.1f} °C / "
                f"{created['humidity_pct']:.1f} % RH from {args.port}."
            )
            if args.once:
                return

    raise TimeoutError(f"No RoomPulse reading received from {args.port}")


if __name__ == "__main__":
    main()

