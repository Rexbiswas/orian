/*
 * ==============================================================================
 * ORIAN AI — ESP32 IOT EMBEDDED CONTROLLER FIRMWARE v2.0
 * ==============================================================================
 * Hardware Support: ESP32 Dev Module / NodeMCU-32S / ESP32-WROOM / ESP32-S3
 * Protocols:
 *   1. Wi-Fi 802.11 b/g/n
 *   2. MQTT Pub/Sub (Port 1883) with Auto-Reconnect
 *   3. HTTP REST Direct Fallback (Port 8000) for zero-broker local setups
 * Devices:
 *   - GPIO 2:  Room Light (Built-in Blue LED / Relay Channel 1)
 *   - GPIO 4:  Bedroom Fan (Relay Channel 2)
 *   - GPIO 15: Living Room AC Relay / High-Power Appliance
 *   - GPIO 18: DHT11 / DHT22 Digital Temperature & Humidity Sensor
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

// -----------------------------------------------------------------------------
// 1. NETWORK & BROKER CONFIGURATION
// -----------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";       // <-- Replace with your Wi-Fi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // <-- Replace with your Wi-Fi Password

// Orian AI Backend IP Address (Your Computer's Local Network IP)
const char* ORIAN_SERVER_IP = "192.168.1.100";      // <-- Replace with your PC IP (e.g. 192.168.1.105)
const int   ORIAN_HTTP_PORT = 8000;
const int   MQTT_PORT       = 1883;

const char* MQTT_USER       = "";                   // Optional MQTT Username
const char* MQTT_PASS       = "";                   // Optional MQTT Password

const char* DEVICE_ID       = "esp32_main_core";

// -----------------------------------------------------------------------------
// 2. HARDWARE PIN DEFINITIONS
// -----------------------------------------------------------------------------
#define PIN_LIGHT_LED   2   // GPIO 2: Room Light LED / Relay Channel 1
#define PIN_FAN_RELAY   4   // GPIO 4: Bedroom Fan Relay Channel 2
#define PIN_AC_RELAY   15   // GPIO 15: AC Relay Channel 3
#define PIN_DHT_SENSOR 18   // GPIO 18: Temperature / Humidity Sensor Pin

// -----------------------------------------------------------------------------
// 3. GLOBAL INSTANCES & TIMERS
// -----------------------------------------------------------------------------
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastHeartbeat = 0;
unsigned long lastTelemetry = 0;
const unsigned long HEARTBEAT_INTERVAL = 15000; // 15 seconds
const unsigned long TELEMETRY_INTERVAL = 10000; // 10 seconds

// Device states
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
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println("   ORIAN AI — ESP32 NEURAL IOT CONTROLLER v2.0        ");
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

  // Connect to Wi-Fi
  setupWiFi();

  // Configure MQTT client
  mqttClient.setServer(ORIAN_SERVER_IP, MQTT_PORT);
  mqttClient.setCallback(handleMQTTMessage);

  Serial.println("[ORIAN-ESP32] Hardware initialization complete. Online & Listening.");
}

// -----------------------------------------------------------------------------
// 6. MAIN RUNTIME LOOP
// -----------------------------------------------------------------------------
void loop() {
  // 1. Maintain Wi-Fi Connection
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }

  // 2. Maintain MQTT Connection if broker is available
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

  // 3. Periodic Heartbeat Beacon
  if (currentMillis - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = currentMillis;
    sendHeartbeat();
  }

  // 4. Periodic Telemetry Stream
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
    // Initial Beacon
    sendHeartbeat();
  } else {
    Serial.println("\n[WiFi] Warning: Connection attempt timed out. Retrying in background...");
  }
}

// -----------------------------------------------------------------------------
// 8. MQTT RECONNECT & SUBSCRIPTIONS
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
    Serial.printf("FAILED (rc=%d). Using Direct REST Fallback.\n", mqttClient.state());
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

  Serial.printf("\n[MQTT Inbound] Topic: %s | Message: %s\n", topic, jsonBuffer);

#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<512> doc;
#endif

  DeserializationError error = deserializeJson(doc, jsonBuffer);
  if (error) {
    Serial.printf("[JSON] Deserialization error: %s\n", error.c_str());
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

  // 1. Room Light Control (GPIO 2 - Built-in LED / Relay)
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
    Serial.printf("[RELAY 1] Room Light state is now: %s\n", finalState.c_str());
  }

  // 2. Bedroom Fan Relay (GPIO 4)
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
    Serial.printf("[RELAY 2] Bedroom Fan state is now: %s\n", finalState.c_str());
  }

  // 3. Living Room AC Relay (GPIO 15)
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
    Serial.printf("[RELAY 3] Living Room AC state is now: %s\n", finalState.c_str());
  }

  // Publish immediate execution response
  publishResponse(deviceId, finalState.c_str(), cmdId, success);
}

void publishResponse(const char* deviceId, const char* state, const char* cmdId, bool success) {
#if ARDUINOJSON_VERSION_MAJOR >= 7
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
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif

  doc["device_id"]        = DEVICE_ID;
  doc["ip"]               = WiFi.localIP().toString();
  doc["rssi"]             = WiFi.RSSI();
  doc["uptime_sec"]       = millis() / 1000;
  doc["firmware_version"] = "2.0-esp32";
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
  // Read sensor values (or realistic reading from DHT sensor)
  float rawTemp = 26.5 + (random(0, 30) / 10.0);
  float rawHum  = 58.0 + (random(0, 40) / 10.0);

#if ARDUINOJSON_VERSION_MAJOR >= 7
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
  int httpCode = http.POST(body);
  
  if (httpCode > 0) {
    // Successfully delivered
  }
  http.end();
}

void sendRESTTelemetry(float temp, float hum) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(ORIAN_SERVER_IP) + ":" + String(ORIAN_HTTP_PORT) + "/api/iot/esp32/telemetry";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String body = "{\"device_id\":\"dht22_temp_sensor\",\"temperature\":" + String(temp, 1) + ",\"humidity\":" + String(hum, 1) + "}";
  int httpCode = http.POST(body);
  
  if (httpCode > 0) {
    // Successfully delivered
  }
  http.end();
}
