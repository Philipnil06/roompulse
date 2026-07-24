# RoomPulse — NexusHacks execution plan

## Project positioning

**Name:** RoomPulse: Ask Your Room

**One-line pitch:** A physical AI companion for your room: a plug-in ESP32 sensor that turns live environmental data into trustworthy answers in Codex or ChatGPT.

**Track:** Embedded AI / IoT + AI (select the closest offered option in the form).

### Judge-facing distinction

The hardware is not an afterthought. The system closes the loop from a physical measurement to a constrained AI answer: the model calls read-only tools that fetch the timestamped sensor data and must cite the measurement time. That is more compelling than an ordinary dashboard or an unconstrained chatbot.

## 12-hour MVP schedule

| Time | Outcome | Done when |
| --- | --- | --- |
| 0:00–0:45 | Sensor proof | Serial Monitor shows temperature and humidity on COM4. |
| 0:45–2:00 | Device to cloud | The ESP32 posts a reading every minute to a deployed API. |
| 2:00–3:30 | Data API | `/latest`, `/history`, and `/summary` return persisted data. |
| 3:30–5:00 | AI interface | MCP tools `get_current_room_conditions` and `get_room_trend` work. |
| 5:00–6:30 | Dashboard | A public read-only page shows current state and 24-hour chart. |
| 6:30–8:00 | Intelligence | Add comfort-band alerts and a simple change/anomaly detector. |
| 8:00–10:00 | Proof | Record a 60–90 second demo and take architecture/hardware photos. |
| 10:00–12:00 | Submission | Publish Notion page, test every link, submit. |

## Technical implementation

### Device

- **Board:** Axiometa Genesis Mini (ESP32-S3), already connected as `COM4`.
- **Sensor:** AX22-0011 DHT11. It is a single-wire device; the vendor example uses GPIO 14.
- **Cadence:** one sample/minute (the sensor itself updates at most once/second).
- **Resilience:** reconnect Wi-Fi, do not transmit invalid `NaN` samples, add an offline queue only after end-to-end ingestion works.
- **Power:** after flashing, use any suitable USB-C wall adapter. The board then works independently from the computer.

### Server (recommended implementation)

Deploy a small Dockerized FastAPI service to Render, Railway, Fly.io, or a VPS. Use PostgreSQL (Supabase/Neon are good choices) for persistence.

| Endpoint | Caller | Purpose |
| --- | --- | --- |
| `POST /v1/measurements` | ESP32 | Authenticated ingestion of temperature and humidity. |
| `GET /v1/rooms/{id}/latest` | dashboard/MCP | Most recent verified reading + staleness. |
| `GET /v1/rooms/{id}/summary?window=24h` | dashboard/MCP | min/max/average, trend, comfort status. |
| `GET /v1/rooms/{id}/history` | dashboard | Chart points. |

Use one long random device token in an `Authorization: Bearer` header. Rate-limit ingestion and reject implausible readings. Never expose the ingestion token in a public dashboard or repository.

### ChatGPT/Codex integration

Implement a tiny remote MCP server around the read-only endpoints. It should expose exactly:

- `get_current_room_conditions()` → current temperature, humidity, reading age, comfort status.
- `get_room_trend(hours)` → min/max/average and direction.
- `explain_room_change(hours)` → deterministic data summary that an LLM can explain.

The tool response includes the actual timestamp so the assistant can say *"last measured at …"*. This prevents made-up sensor values. For the demo, run it in Codex with the MCP connection; if public ChatGPT connector setup takes longer, show the same tools in the local MCP Inspector and state that the remote endpoint is ready.

## Definition of done

- [ ] Device is running from wall power, not USB tethered to the laptop.
- [ ] Dashboard has at least 20 minutes of real readings.
- [ ] Natural-language query retrieves a live timestamped reading.
- [ ] Repo is public with setup instructions and no secrets.
- [ ] Demo video shows hardware, dashboard, and a Codex/ChatGPT question.
- [ ] Public Notion page includes all required form items.

## Demo script (75 seconds)

1. Show the Genesis Mini and DHT11 in S1: “This is the physical source of truth.”
2. Unplug it from the laptop and show it remain powered by USB-C wall power.
3. Open the dashboard; point out a newly arrived timestamped measurement.
4. Ask: “What is my room like right now, and has it changed today?”
5. Show the tool-backed response and the 24-hour trend.
6. Close: “RoomPulse makes ambient data usable in the same AI workspace where I plan and work.”

## Notion submission page outline

Copy this structure into a public Notion page:

1. **RoomPulse: Ask Your Room** — one-line pitch and hero photo/GIF.
2. **Problem statement** — environmental data is inaccessible and not actionable.
3. **Solution overview** — sensor → cloud → MCP → natural language.
4. **Live build** — embedded dashboard link and latest screenshot.
5. **Technology stack** — ESP32-S3, DHT11, Arduino, FastAPI, PostgreSQL, Docker, MCP.
6. **Architecture** — use the Mermaid diagram from the README (export as PNG if Notion does not render Mermaid).
7. **AI/engineering detail** — explain tool-grounded answers and staleness checks.
8. **GitHub repository** — link this repository.
9. **Demo video** — embed/upload the 60–90 sec video.
10. **Additional remarks** — real hardware, modular AX22 design, and future sensors/automation.

## Evidence and caveats

- The Genesis Mini has an ESP32-S3 and supports Arduino; the board has four AX22 ports.
- The AX22-0011 sensor is a DHT11, published as 0–50 °C, 20–90% RH, ±2 °C / ±5% RH, at 1 Hz. Keep the claims modest.
- The public form requires a public Notion submission page and GitHub repo; it also asks for a demo/deployment/engineering resources only where applicable. Test all links before submitting.

## Post-hackathon upgrades

- Replace DHT11 with BME280 or SHT31 for improved accuracy.
- Add battery, OTA updates, buffering, and a certificate-pinned HTTPS client.
- Add a relay/fan or humidifier module for safe, user-approved automation.
