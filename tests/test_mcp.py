import httpx
import pytest

from mcp_server import server


@pytest.mark.asyncio
async def test_mcp_fetch_and_explanation(monkeypatch):
    payload = {
        "room_id": "room-philip",
        "window_hours": 24,
        "sample_count": 4,
        "from": "2026-07-24T08:00:00+00:00",
        "to": "2026-07-24T09:00:00+00:00",
        "temperature_c": {
            "min": 21.0,
            "max": 23.0,
            "average": 22.0,
            "change": 2.0,
            "trend": "rising",
        },
        "humidity_pct": {
            "min": 40.0,
            "max": 44.0,
            "average": 42.0,
            "change": 4.0,
            "trend": "rising",
        },
        "latest_comfort": {"label": "comfortable"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/rooms/room-philip/summary"
        return httpx.Response(200, json=payload)

    original_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(server.httpx, "AsyncClient", client_factory)
    result = await server.explain_room_change(hours=24)
    assert result["facts"]["sample_count"] == 4
    assert "Do not infer causes" in result["instruction"]

