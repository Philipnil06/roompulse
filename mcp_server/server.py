from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


API_BASE_URL = os.getenv("ROOMPULSE_API_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_ROOM_ID = os.getenv("ROOMPULSE_ROOM_ID", "room-philip")

mcp = FastMCP(
    "RoomPulse",
    instructions=(
        "Use these read-only tools for room climate questions. Always include the "
        "measurement timestamp and mention when a reading is stale."
    ),
)


async def fetch_json(path: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10) as client:
        response = await client.get(path)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_current_room_conditions(room_id: str = DEFAULT_ROOM_ID) -> dict[str, Any]:
    """Get the latest verified temperature and humidity reading for a room."""
    return await fetch_json(f"/v1/rooms/{room_id}/latest")


@mcp.tool()
async def get_room_trend(
    hours: int = 24, room_id: str = DEFAULT_ROOM_ID
) -> dict[str, Any]:
    """Get min, max, average, change, and trend for the requested time window."""
    safe_hours = min(max(hours, 1), 168)
    return await fetch_json(f"/v1/rooms/{room_id}/summary?hours={safe_hours}")


@mcp.tool()
async def explain_room_change(
    hours: int = 24, room_id: str = DEFAULT_ROOM_ID
) -> dict[str, Any]:
    """Get grounded facts an assistant can use to explain a room climate change."""
    summary = await get_room_trend(hours=hours, room_id=room_id)
    return {
        "room_id": room_id,
        "window_hours": summary["window_hours"],
        "facts": {
            "temperature": summary["temperature_c"],
            "humidity": summary["humidity_pct"],
            "sample_count": summary["sample_count"],
            "from": summary["from"],
            "to": summary["to"],
            "latest_comfort": summary["latest_comfort"],
        },
        "instruction": (
            "Explain only these measured facts. Do not infer causes such as an open "
            "window or heater unless the user supplies that context."
        ),
    }


if __name__ == "__main__":
    transport = os.getenv("ROOMPULSE_MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)

