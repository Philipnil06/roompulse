$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Missing .venv. Run: python -m venv .venv"
}

Write-Host "RoomPulse API:       http://127.0.0.1:8000"
Write-Host "RoomPulse API docs:  http://127.0.0.1:8000/docs"
& $python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
