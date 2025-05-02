#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <time.h>

// WiFi Credentials
const char* ssid = "Noor";
const char* password = "mah00000";

// Firebase Configuration
const String FIREBASE_HOST = "iot-lab-11-7e668-default-rtdb.firebaseio.com";
const String FIREBASE_AUTH = "upN3VEd6EaqzC3k0GWpp5SbAiJFaEVBnr3kzWYPg";
const String FIREBASE_PATH = "/sensor_data";

// DHT Sensor
#define DHTPIN 4
#define DHTTYPE DHT11

// Timing
const unsigned long SEND_INTERVAL = 10000;
const unsigned long SENSOR_DELAY = 2000;

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastSendTime = 0;
unsigned long lastReadTime = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 DHT11 Firebase Logger with Time");

  dht.begin();

  WiFi.disconnect(true);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    // Time config
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    Serial.print("Waiting for NTP time sync");
    while (time(nullptr) < 100000) {
      Serial.print(".");
      delay(500);
    }
    Serial.println("\nTime synchronized.");
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(ssid, password);
    return;
  }

  if (millis() - lastReadTime >= SENSOR_DELAY) {
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    if (!isnan(temp) && !isnan(hum)) {
      Serial.printf("DHT Read: %.1f°C, %.1f%%\n", temp, hum);
      if (millis() - lastSendTime >= SEND_INTERVAL) {
        sendToFirebase(temp, hum);
        lastSendTime = millis();
      }
    } else {
      Serial.println("Failed to read from DHT sensor!");
    }

    lastReadTime = millis();
  }
}

void sendToFirebase(float temp, float hum) {
  HTTPClient http;

  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  char timeString[25];
  strftime(timeString, sizeof(timeString), "%Y-%m-%d %H:%M:%S", timeinfo);

  String url = "https://" + FIREBASE_HOST + FIREBASE_PATH + ".json?auth=" + FIREBASE_AUTH;

  String payload = "{";
  payload += "\"temperature\":" + String(temp) + ",";
  payload += "\"humidity\":" + String(hum) + ",";
  payload += "\"datetime\":\"" + String(timeString) + "\"";
  payload += "}";

  Serial.println("Sending to Firebase...");
  Serial.println(payload);

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(payload);

  if (httpCode == 200) {
    Serial.println("Firebase update successful");
  } else {
    Serial.printf("Firebase error: %d\n", httpCode);
  }

  http.end();
}
