# NexusHacks submission guide

## Project summary

**Project name:** RoomPulse: Ask Your Room

**One-line pitch:** A Wi-Fi sensor that turns room temperature and humidity into reliable, timestamped answers in Codex.

**Suggested track:** Embedded AI / IoT + AI (choose the closest option offered in the submission form).

## Problem

Room climate data is often isolated in a small display or a proprietary mobile app. That makes simple questions—such as whether a room is comfortable or whether humidity has changed—needlessly inconvenient.

## Solution

RoomPulse connects an Axiometa Genesis Mini and AX22-0011 temperature/humidity sensor to a lightweight API. A read-only MCP server gives Codex grounded access to the latest reading and trends. The assistant receives timestamp and freshness information, so it can report measured facts instead of inventing sensor values or causes.

## Technology stack

- Axiometa Genesis Mini (ESP32-S3)
- AX22-0011 DHT11 sensor
- Arduino C++ and Wi-Fi
- FastAPI and SQLite
- Docker / reverse proxy deployment
- Model Context Protocol (MCP)
- Codex

## Architecture

```text
Sensor → Genesis Mini → Wi-Fi → FastAPI + SQLite → MCP → Codex
```

## Engineering evidence to include

1. A photo of the Genesis Mini with the AX22-0011 connected in S1.
2. A short clip showing the board powered from a USB adapter rather than the development computer.
3. A Codex prompt such as “What is the temperature in room-philip?” and its timestamped result.
4. The public GitHub repository: https://github.com/Philipnil06/roompulse
5. A brief note that firmware secrets are kept in ignored `config.h`, not in the repository.

## Demo-video outline (60–90 seconds)

1. Introduce the physical board and sensor.
2. Explain that the board uploads independently over Wi-Fi.
3. Show a fresh measurement arriving at the server.
4. Ask Codex for the current room conditions and a trend.
5. Explain that the answer is grounded in a timestamped, read-only MCP tool.

## Final submission checklist

- [ ] Public Notion submission page
- [ ] Public GitHub repository
- [ ] Team and project details completed in the form
- [ ] Correct track selected
- [ ] Hardware photo added
- [ ] Demo video uploaded or linked
- [ ] All links tested in a logged-out browser
- [ ] No Wi-Fi password, API token, database, or personal server configuration visible
