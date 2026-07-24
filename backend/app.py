from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.store import RoomPulseStore


class MeasurementInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    room_id: str = Field(
        default="room-philip", min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    temperature_c: float = Field(ge=0, le=50)
    humidity_pct: float = Field(ge=20, le=90)
    measured_at: datetime | None = None

    @field_validator("measured_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("measured_at must include a timezone")
        return value


def create_app(
    *,
    db_path: str | Path | None = None,
    device_token: str | None = None,
) -> FastAPI:
    resolved_db_path = Path(
        db_path or os.getenv("ROOMPULSE_DB_PATH", "data/roompulse.db")
    )
    resolved_token = device_token or os.getenv(
        "ROOMPULSE_DEVICE_TOKEN", "local-development-token"
    )
    store = RoomPulseStore(resolved_db_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        store.initialize()
        yield

    app = FastAPI(
        title="RoomPulse API",
        version="0.1.0",
        description="Ingestion and read API for live room climate measurements.",
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.device_token = resolved_token
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def require_device_token(
        request: Request, authorization: str | None = Header(default=None)
    ) -> None:
        expected = f"Bearer {request.app.state.device_token}"
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device token",
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "roompulse-api"}

    @app.post(
        "/v1/measurements",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_device_token)],
    )
    def create_measurement(payload: MeasurementInput, request: Request) -> dict:
        return request.app.state.store.add_measurement(**payload.model_dump())

    @app.get("/v1/rooms/{room_id}/latest")
    def latest(room_id: str, request: Request) -> dict:
        reading = request.app.state.store.latest(room_id)
        if reading is None:
            raise HTTPException(status_code=404, detail="No measurements for room")
        return reading

    @app.get("/v1/rooms/{room_id}/history")
    def history(
        room_id: str,
        request: Request,
        hours: int = Query(default=24, ge=1, le=168),
        limit: int = Query(default=500, ge=1, le=2000),
    ) -> dict:
        return {
            "room_id": room_id,
            "window_hours": hours,
            "measurements": request.app.state.store.history(
                room_id, hours=hours, limit=limit
            ),
        }

    @app.get("/v1/rooms/{room_id}/summary")
    def summary(
        room_id: str,
        request: Request,
        hours: int = Query(default=24, ge=1, le=168),
    ) -> dict:
        result = request.app.state.store.summary(room_id, hours=hours)
        if result is None:
            raise HTTPException(status_code=404, detail="No measurements for room")
        return result

    return app


app = create_app()
