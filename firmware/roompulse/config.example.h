#pragma once

// Copy this file to config.h for real Wi-Fi uploads. config.h is git-ignored.
#define ROOMPULSE_WIFI_SSID "YOUR_WIFI_NAME"
#define ROOMPULSE_WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// A Genesis Mini cannot reach 127.0.0.1 on your computer. For a local test,
// replace this with the computer's LAN address, for example:
// http://192.168.1.42:8000
#define ROOMPULSE_API_BASE_URL "http://192.168.1.42:8000"
#define ROOMPULSE_DEVICE_TOKEN "local-development-token"
#define ROOMPULSE_DEVICE_ID "genesis-mini"
#define ROOMPULSE_ROOM_ID "room-philip"

// Keep false for the first serial-only sensor test. Change to true after
// setting the values above and making port 8000 reachable on the local network.
#define ROOMPULSE_ENABLE_UPLOAD false
