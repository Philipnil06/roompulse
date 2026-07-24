/*
 * RoomPulse firmware for Axiometa Genesis Mini + AX22-0011 DHT11.
 *
 * Install in Arduino IDE:
 *   - esp32 by Espressif Systems
 *   - DHT sensor library by Adafruit
 *   - Adafruit Unified Sensor
 *
 * Select: Axiometa Genesis Mini / COM4
 * Never commit your real Wi-Fi password or device token.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

#if __has_include("config.h")
#include "config.h"
#else
#include "config.example.h"
#endif

// AX22-0011's official schematic routes DHT11 DATA to AX22 IO1.
// The installed Genesis Mini board definition maps S1/P1 IO1 to GPIO 3.
constexpr uint8_t DHT_PIN = P1_IO1;
constexpr uint8_t DHT_TYPE = DHT11;
constexpr unsigned long REPORT_INTERVAL_MS =
  ROOMPULSE_ENABLE_UPLOAD ? 60UL * 1000UL : 5UL * 1000UL;

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastReportAt = 0;

bool connectWiFi() {
  if (!ROOMPULSE_ENABLE_UPLOAD) {
    return false;
  }
  WiFi.mode(WIFI_STA);
  WiFi.begin(ROOMPULSE_WIFI_SSID, ROOMPULSE_WIFI_PASSWORD);
  Serial.printf("Connecting to Wi-Fi %s", ROOMPULSE_WIFI_SSID);
  const unsigned long startedAt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startedAt < 15000) {
    delay(500);
    Serial.print('.');
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nWi-Fi connection timed out; sensor readings continue locally.");
    return false;
  }
  Serial.printf("\nConnected: %s\n", WiFi.localIP().toString().c_str());
  return true;
}

void sendMeasurement(float temperatureC, float humidityPct) {
  if (!ROOMPULSE_ENABLE_UPLOAD || WiFi.status() != WL_CONNECTED) {
    return;
  }
  WiFiClient plainClient;
  WiFiClientSecure secureClient;
  HTTPClient http;
  const String url = String(ROOMPULSE_API_BASE_URL) + "/v1/measurements";
  NetworkClient* client = &plainClient;
  if (url.startsWith("https://")) {
    // Hackathon MVP: validate HTTPS transport without bundling a mutable CA.
    // Replace with setCACert(...) before long-term deployment.
    secureClient.setInsecure();
    client = &secureClient;
  }

  if (!http.begin(*client, url)) {
    Serial.println("Could not open API connection");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + ROOMPULSE_DEVICE_TOKEN);
  const String payload = String("{\"device_id\":\"") + ROOMPULSE_DEVICE_ID +
    "\",\"room_id\":\"" + ROOMPULSE_ROOM_ID +
    "\",\"temperature_c\":" + String(temperatureC, 1) +
    ",\"humidity_pct\":" + String(humidityPct, 1) + "}";

  const int status = http.POST(payload);
  Serial.printf("API status: %d\n", status);
  if (status > 0) Serial.println(http.getString());
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  dht.begin();
  delay(2000);
  if (ROOMPULSE_ENABLE_UPLOAD) {
    connectWiFi();
  } else {
    Serial.println("RoomPulse sensor-only mode. Wi-Fi upload is disabled.");
  }
  lastReportAt = millis() - REPORT_INTERVAL_MS;
}

void loop() {
  if (ROOMPULSE_ENABLE_UPLOAD && WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (millis() - lastReportAt < REPORT_INTERVAL_MS) return;
  lastReportAt = millis();

  const float humidity = dht.readHumidity();
  const float temperature = dht.readTemperature();
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11 read failed; check module orientation and S1 pin mapping.");
    return;
  }
  Serial.printf("Temperature: %.1f C | Humidity: %.1f %%\n", temperature, humidity);
  sendMeasurement(temperature, humidity);
}
