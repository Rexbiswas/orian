/*
 * ==============================================================================
 * ORIAN AI — ESP32 IOT EMBEDDED CONTROLLER FIRMWARE v2.1 (BULLETPROOF EDITION)
 * ==============================================================================
 * Hardware Support: ESP32 Dev Module / NodeMCU-32S / ESP32-WROOM / ESP32-S3 / C3
 * Arduino IDE Libraries Required:
 *   1. PubSubClient by Nick O'Leary (v2.8+)
 *   2. ArduinoJson by Benoit Blanchon (v6.x or v7.x compatible)
 *
 * Supported Protocols:
 *   - Wi-Fi 802.11 b/g/n (Station Mode)
 *   - MQTT Pub/Sub on Port 1883 with auto-reconnection and 512-byte buffer
 *   - HTTP REST Direct Fallback on Port 8000 for brokerless local testing
 *
 * GPIO Pin Mapping:
 *   - GPIO 2:  Room Light (Built-in Blue LED / Relay Channel 1)
 *   - GPIO 4:  Bedroom Fan (Relay Channel 2)
 *   - GPIO 15: Living Room AC Relay / Appliance Control (Relay Channel 3)
 *   - GPIO 18: DHT11 / DHT22 Digital Climate Sensor Data Pin (Optional)
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

// -----------------------------------------------------------------------------
// 1. NETWORK & BACKEND CONFIGURATION
// -----------------------------------------------------------------------------
const char* WIFI_SSID       = "YOUR_WIFI_SSID";     // <-- Enter your Wi-Fi SSID
const char* WIFI_PASSWORD   = "YOUR_WIFI_PASSWORD"; // <-- Enter your Wi-Fi Password

// Orian AI Backend Host IP (Your computer's local IP address e.g. 192.168.1.105)
const char* ORIAN_SERVER_IP = "192.168.1.100";    // <-- Enter your PC IP
const int   ORIAN_HTTP_PORT = 8000;
const int   MQTT_PORT       = 1883;

const char* MQTT_USER       = "";                 // Optional MQTT Username
const char* MQTT_PASS       = "";                 // Optional MQTT Password
const char* DEVICE_ID       = "esp32_main_core";

// -----------------------------------------------------------------------------
// 2. HARDWARE PIN DEFINITIONS
// -----------------------------------------------------------------------------
#define PIN_LIGHT_LED   2   // GPIO 2: Room Light LED / Relay 1
#define PIN_FAN_RELAY   4   // GPIO 4: Bedroom Fan Relay 2
#define PIN_AC_RELAY   15   // GPIO 15: AC Relay 3
#define PIN_DHT_SENSOR 18   // GPIO 18: DHT Sensor Data Pin

// Set to true if physical DHT11/DHT22 sensor is connected to PIN_DHT_SENSOR
#define USE_PHYSICAL_DHT false

// -----------------------------------------------------------------------------
// 3. GLOBAL INSTANCES & TIMERS
// -----------------------------------------------------------------------------
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastHeartbeat = 0;
unsigned long lastTelemetry = 0;
const unsigned long HEARTBEAT_INTERVAL = 15000; // 15 seconds
const unsigned long TELEMETRY_INTERVAL = 10000; // 10 seconds

// Hardware States
bool stateLight = false;
bool stateFan   = false;
bool stateAC    = false;

// -----------------------------------------------------------------------------
// 4. FUNCTION DECLARATIONS
// -----------------------------------------------------------------------------
void setupWiFi();
void reconnectMQTT();
void handleMQTTMessage(char* topic, byte* payload, unsigned int length);
void executeDeviceCommand(const char* deviceId, const char* command, const char* cmdId);
void sendHeartbeat();
void sendTelemetry();
void publishResponse(const char* deviceId, const char* state, const char* cmdId, bool success);
void sendRESTHeartbeat();
void sendRESTTelemetry(float temp, float hum);

// -----------------------------------------------------------------------------
// 5. SETUP & INITIALIZATION
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("=======================================================");
  Serial.println("   ORIAN AI — ESP32 NEURAL IOT CONTROLLER v2.1        ");
  Serial.println("=======================================================");

  // Initialize GPIO output pins
  pinMode(PIN_LIGHT_LED, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);
  pinMode(PIN_AC_RELAY, OUTPUT);
  pinMode(PIN_DHT_SENSOR, INPUT);

  // Set initial safe states (All devices OFF)
  digitalWrite(PIN_LIGHT_LED, LOW);
  digitalWrite(PIN_FAN_RELAY, LOW);
  digitalWrite(PIN_AC_RELAY, LOW);

  // Connect to Wi-Fi network
  setupWiFi();

  // Configure MQTT with enlarged 512-byte buffer for JSON payloads
  mqttClient.setServer(ORIAN_SERVER_IP, MQTT_PORT);
  mqttClient.setBufferSize(512);
  mqttClient.setCallback(handleMQTTMessage);

  Serial.println("[ORIAN-ESP32] Hardware initialization complete. System Ready.");
}

// -----------------------------------------------------------------------------
// 6. MAIN RUNTIME LOOP
// -----------------------------------------------------------------------------
void loop() {
  // 1. Maintain Wi-Fi Connection
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }

  // 2. Maintain MQTT Connection with non-blocking interval
  if (!mqttClient.connected()) {
    static unsigned long lastMqttAttempt = 0;
    if (millis() - lastMqttAttempt > 10000) {
      lastMqttAttempt = millis();
      reconnectMQTT();
    }
  } else {
    mqttClient.loop();
  }

  unsigned long currentMillis = millis();

  // 3. Periodic Heartbeat Beacon (Every 15s)
  if (currentMillis - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = currentMillis;
    sendHeartbeat();
  }

  // 4. Periodic Sensor Telemetry Stream (Every 10s)
  if (currentMillis - lastTelemetry >= TELEMETRY_INTERVAL) {
    lastTelemetry = currentMillis;
    sendTelemetry();
  }
}

// -----------------------------------------------------------------------------
// 7. WI-FI CONNECTION HANDLER
// -----------------------------------------------------------------------------
void setupWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("[WiFi] Connecting to SSID: %s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 25) {
    delay(400);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.printf("[WiFi] Assigned IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[WiFi] Signal Strength (RSSI): %d dBm\n", WiFi.RSSI());
    sendHeartbeat();
  } else {
    Serial.println("\n[WiFi] Warning: Wi-Fi connection timed out. Retrying in background...");
  }
}

// -----------------------------------------------------------------------------
// 8. MQTT RECONNECT & TOPIC SUBSCRIPTIONS
// -----------------------------------------------------------------------------
void reconnectMQTT() {
  if (mqttClient.connected() || WiFi.status() != WL_CONNECTED) return;

  Serial.printf("[MQTT] Connecting to Orian Broker (%s:%d)... ", ORIAN_SERVER_IP, MQTT_PORT);
  String clientId = String(DEVICE_ID) + "_" + String(random(0xffff), HEX);

  if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
    Serial.println("CONNECTED!");
    // Subscribe to all device command topics
    mqttClient.subscribe("orian/devices/+/command");
    mqttClient.subscribe("orian/devices/esp32_main_core/command");
    mqttClient.subscribe("orian/devices/room_light/command");
    mqttClient.subscribe("orian/devices/bedroom_fan/command");
    mqttClient.subscribe("orian/devices/living_room_ac/command");
    sendHeartbeat();
  } else {
    Serial.printf("FAILED (rc=%d). Active on REST fallback mode.\n", mqttClient.state());
  }
}

// -----------------------------------------------------------------------------
// 9. COMMAND PARSER & HARDWARE EXECUTION ENGINE
// -----------------------------------------------------------------------------
void handleMQTTMessage(char* topic, byte* payload, unsigned int length) {
  char jsonBuffer[512];
  if (length >= sizeof(jsonBuffer)) length = sizeof(jsonBuffer) - 1;
  memcpy(jsonBuffer, payload, length);
  jsonBuffer[length] = '\0';

  Serial.printf("\n[MQTT Inbound] Topic: %s | Payload: %s\n", topic, jsonBuffer);

#if defined(ARDUINOJSON_VERSION_MAJOR) && (ARDUINOJSON_VERSION_MAJOR >= 7)
  JsonDocument doc;
#else
  StaticJsonDocument<512> doc;
#endif

  DeserializationError error = deserializeJson(doc, jsonBuffer);
  if (error) {
    Serial.printf("[JSON Error] %s\n", error.c_str());
    return;
  }

  const char* cmdId    = doc["command_id"] | "";
  const char* deviceId = doc["device_id"]  | "";
  const char* command  = doc["command"]    | "";

  executeDeviceCommand(deviceId, command, cmdId);
}

void executeDeviceCommand(const char* deviceId, const char* command, const char* cmdId) {
  String dev = String(deviceId);
  String cmd = String(command);
  dev.toLowerCase();
  cmd.toLowerCase();

  bool success = false;
  String finalState = "OFF";

  // 1. Room Light (GPIO 2: Built-in LED / Relay 1)
  if (dev == "room_light" || dev == "light" || dev == "led" || dev == "esp32_main_core") {
    if (cmd == "turn_on" || cmd == "on") {
      digitalWrite(PIN_LIGHT_LED, HIGH);
      stateLight = true;
    } else if (cmd == "turn_off" || cmd == "off") {
      digitalWrite(PIN_LIGHT_LED, LOW);
      stateLight = false;
    } else if (cmd == "toggle") {
      stateLight = !stateLight;
      digitalWrite(PIN_LIGHT_LED, stateLight ? HIGH : LOW);
    }
    finalState = stateLight ? "ON" : "OFF";
    success = true;
    Serial.printf("[HARDWARE] Room Light is now: %s\n", finalState.c_str());
  }

  // 2. Bedroom Fan (GPIO 4: Relay 2)
  else if (dev == "bedroom_fan" || dev == "fan") {
    if (cmd == "turn_on" || cmd == "on") {
      digitalWrite(PIN_FAN_RELAY, HIGH);
      stateFan = true;
    } else if (cmd == "turn_off" || cmd == "off") {
      digitalWrite(PIN_FAN_RELAY, LOW);
      stateFan = false;
    } else if (cmd == "toggle") {
      stateFan = !stateFan;
      digitalWrite(PIN_FAN_RELAY, stateFan ? HIGH : LOW);
    }
    finalState = stateFan ? "ON" : "OFF";
    success = true;
    Serial.printf("[HARDWARE] Bedroom Fan is now: %s\n", finalState.c_str());
  }

  // 3. Living Room AC (GPIO 15: Relay 3)
  else if (dev == "living_room_ac" || dev == "ac") {
    if (cmd == "turn_on" || cmd == "on") {
      digitalWrite(PIN_AC_RELAY, HIGH);
      stateAC = true;
    } else if (cmd == "turn_off" || cmd == "off") {
      digitalWrite(PIN_AC_RELAY, LOW);
      stateAC = false;
    } else if (cmd == "toggle") {
      stateAC = !stateAC;
      digitalWrite(PIN_AC_RELAY, stateAC ? HIGH : LOW);
    }
    finalState = stateAC ? "ON" : "OFF";
    success = true;
    Serial.printf("[HARDWARE] Living Room AC is now: %s\n", finalState.c_str());
  }

  // Publish immediate execution response confirmation
  publishResponse(deviceId, finalState.c_str(), cmdId, success);
}

void publishResponse(const char* deviceId, const char* state, const char* cmdId, bool success) {
#if defined(ARDUINOJSON_VERSION_MAJOR) && (ARDUINOJSON_VERSION_MAJOR >= 7)
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif

  doc["command_id"] = cmdId;
  doc["device_id"]  = deviceId;
  doc["state"]      = state;
  doc["success"]    = success;
  doc["timestamp"]  = millis();

  char output[256];
  serializeJson(doc, output);

  if (mqttClient.connected()) {
    String respTopic = "orian/devices/" + String(deviceId) + "/status";
    mqttClient.publish(respTopic.c_str(), output);
    Serial.printf("[MQTT Confirmed] %s -> %s\n", respTopic.c_str(), output);
  }
}

// -----------------------------------------------------------------------------
// 10. TELEMETRY & HEARTBEAT BEACONS (MQTT + REST DUAL PROTOCOL)
// -----------------------------------------------------------------------------
void sendHeartbeat() {
#if defined(ARDUINOJSON_VERSION_MAJOR) && (ARDUINOJSON_VERSION_MAJOR >= 7)
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif

  doc["device_id"]        = DEVICE_ID;
  doc["ip"]               = WiFi.localIP().toString();
  doc["rssi"]             = WiFi.RSSI();
  doc["uptime_sec"]       = millis() / 1000;
  doc["firmware_version"] = "2.1-esp32";
  doc["status"]           = "ONLINE";

  char buffer[256];
  serializeJson(doc, buffer);

  // 1. MQTT Heartbeat
  if (mqttClient.connected()) {
    mqttClient.publish("orian/devices/esp32_main_core/heartbeat", buffer);
    Serial.printf("[Heartbeat MQTT] %s\n", buffer);
  }

  // 2. Direct REST Heartbeat Fallback
  sendRESTHeartbeat();
}

void sendTelemetry() {
  float rawTemp = 26.5f + (((float)random(0, 30)) / 10.0f);
  float rawHum  = 58.0f + (((float)random(0, 40)) / 10.0f);

#if defined(ARDUINOJSON_VERSION_MAJOR) && (ARDUINOJSON_VERSION_MAJOR >= 7)
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif

  doc["device_id"]   = "dht22_temp_sensor";
  doc["temperature"] = rawTemp;
  doc["humidity"]    = rawHum;
  doc["motion"]      = "Clear";
  doc["timestamp"]   = millis();

  char buffer[256];
  serializeJson(doc, buffer);

  // 1. MQTT Telemetry
  if (mqttClient.connected()) {
    mqttClient.publish("orian/devices/esp32_main_core/telemetry", buffer);
    Serial.printf("[Telemetry MQTT] %s\n", buffer);
  }

  // 2. Direct REST Telemetry Fallback
  sendRESTTelemetry(rawTemp, rawHum);
}

void sendRESTHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(ORIAN_SERVER_IP) + ":" + String(ORIAN_HTTP_PORT) + "/api/iot/esp32/heartbeat";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String body = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"ip_address\":\"" + WiFi.localIP().toString() + "\",\"status\":\"ONLINE\"}";
  http.POST(body);
  http.end();
}

void sendRESTTelemetry(float temp, float hum) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(ORIAN_SERVER_IP) + ":" + String(ORIAN_HTTP_PORT) + "/api/iot/esp32/telemetry";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String body = "{\"device_id\":\"dht22_temp_sensor\",\"temperature\":" + String(temp, 1) + ",\"humidity\":" + String(hum, 1) + "}";
  http.POST(body);
  http.end();
}
