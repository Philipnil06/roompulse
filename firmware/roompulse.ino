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

// AX22-0011's official Arduino example uses GPIO 14. Confirm this after
// the first serial test if the module is moved to a different AX22 port.
constexpr uint8_t DHT_PIN = 14;
constexpr uint8_t DHT_TYPE = DHT11;
constexpr unsigned long REPORT_INTERVAL_MS = 60UL * 1000UL;

// Configure locally before flashing. Keep this file private after adding secrets.
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* API_BASE_URL = "https://your-roompulse-api.example.com";
const char* DEVICE_TOKEN = "replace-with-a-long-random-device-token";
const char* DEVICE_ID = "room-philip";

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastReportAt = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to Wi-Fi %s", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf("\nConnected: %s\n", WiFi.localIP().toString().c_str());
}

void sendMeasurement(float temperatureC, float humidityPct) {
  WiFiClientSecure client;
  client.setInsecure(); // MVP only. Pin the deployment CA certificate before public release.
  HTTPClient http;
  const String url = String(API_BASE_URL) + "/v1/measurements";

  if (!http.begin(client, url)) {
    Serial.println("Could not open HTTPS connection");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
  const String payload = String("{\"device_id\":\"") + DEVICE_ID +
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
  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
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
