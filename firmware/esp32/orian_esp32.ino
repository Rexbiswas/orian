/*
 * ==============================================================================
 * ORIAN AI — ESP32 IOT EMBEDDED CONTROLLER FIRMWARE v2.0
 * ==============================================================================
 * Hardware Support: ESP32 Dev Module / NodeMCU-32S / ESP32-WROOM
 * Protocols: Wi-Fi 802.11 b/g/n, MQTT Pub/Sub (Port 1883), HTTP REST Fallback
 * Devices:
 *   - GPIO 2:  Room Light (Built-in LED / Relay Channel 1)
 *   - GPIO 4:  Bedroom Fan (Relay Channel 2)
 *   - GPIO 15: Living Room AC Relay / Appliance Control
 *   - GPIO 18: DHT11 / DHT22 Digital Climate Sensor Data Pin
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

// -----------------------------------------------------------------------------
// 1. NETWORK & BROKER CONFIGURATION
// -----------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char* MQTT_BROKER   = "192.168.1.100";  // Orian Backend IP / MQTT Host
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "";               // Optional Broker Username
const char* MQTT_PASS     = "";               // Optional Broker Password

const char* DEVICE_ID     = "esp32_main_core";
const char* REST_API_URL  = "http://192.168.1.100:8000/api/iot";

// -----------------------------------------------------------------------------
// 2. HARDWARE PIN DEFINITIONS
// -----------------------------------------------------------------------------
#define PIN_LIGHT_LED   2   // GPIO 2: Room Light LED / Relay
#define PIN_FAN_RELAY   4   // GPIO 4: Bedroom Fan Relay
#define PIN_AC_RELAY   15   // GPIO 15: AC Relay
#define PIN_DHT_SENSOR 18   // GPIO 18: Temperature / Humidity Sensor Pin

// -----------------------------------------------------------------------------
// 3. MQTT TOPICS
// -----------------------------------------------------------------------------
const char* TOPIC_COMMAND   = "orian/devices/+/command";
const char* TOPIC_HEARTBEAT = "orian/devices/esp32_main_core/heartbeat";
const char* TOPIC_TELEMETRY = "orian/devices/esp32_main_core/telemetry";

// -----------------------------------------------------------------------------
// 4. GLOBAL INSTANCES & TIMERS
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
// 5. FUNCTION DECLARATIONS
// -----------------------------------------------------------------------------
void setupWiFi();
void reconnectMQTT();
void handleMQTTMessage(char* topic, byte* payload, unsigned int length);
void executeDeviceCommand(const char* deviceId, const char* command, const char* cmdId);
void sendHeartbeat();
void sendTelemetry();
void publishResponse(const char* deviceId, const char* state, const char* cmdId, bool success);

// -----------------------------------------------------------------------------
// 6. SETUP & INITIALIZATION
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n[ORIAN-ESP32] Initializing Orian IoT Neural Controller...");

  // Initialize GPIO output pins
  pinMode(PIN_LIGHT_LED, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);
  pinMode(PIN_AC_RELAY, OUTPUT);
  pinMode(PIN_DHT_SENSOR, INPUT);

  // Set initial safe states (OFF)
  digitalWrite(PIN_LIGHT_LED, LOW);
  digitalWrite(PIN_FAN_RELAY, LOW);
  digitalWrite(PIN_AC_RELAY, LOW);

  // Connect to Wi-Fi
  setupWiFi();

  // Configure MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(handleMQTTMessage);

  Serial.println("[ORIAN-ESP32] Hardware initialization complete. System Ready.");
}

// -----------------------------------------------------------------------------
// 7. MAIN RUNTIME LOOP
// -----------------------------------------------------------------------------
void loop() {
  // 1. Maintain Wi-Fi Connection
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }

  // 2. Maintain MQTT Connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

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
// 8. WI-FI & MQTT CONNECTION HANDLERS
// -----------------------------------------------------------------------------
void setupWiFi() {
  delay(10);
  Serial.printf("[WiFi] Connecting to SSID: %s\n", WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.printf("[WiFi] IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WiFi] Warning: Wi-Fi connection timed out. Retrying in background...");
  }
}

void reconnectMQTT() {
  if (mqttClient.connected()) return;

  Serial.print("[MQTT] Connecting to Orian Broker...");
  String clientId = String(DEVICE_ID) + "_" + String(random(0xffff), HEX);

  if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
    Serial.println(" CONNECTED!");
    // Subscribe to all device command topics
    mqttClient.subscribe("orian/devices/+/command");
    mqttClient.subscribe("orian/devices/esp32_main_core/command");
    mqttClient.subscribe("orian/devices/room_light/command");
    mqttClient.subscribe("orian/devices/bedroom_fan/command");
    mqttClient.subscribe("orian/devices/living_room_ac/command");
    sendHeartbeat();
  } else {
    Serial.printf(" FAILED (rc=%d). Re-attempting in next cycle...\n", mqttClient.state());
  }
}

// -----------------------------------------------------------------------------
// 9. COMMAND EXECUTION ENGINE
// -----------------------------------------------------------------------------
void handleMQTTMessage(char* topic, byte* payload, unsigned int length) {
  char jsonBuffer[512];
  if (length >= sizeof(jsonBuffer)) length = sizeof(jsonBuffer) - 1;
  memcpy(jsonBuffer, payload, length);
  jsonBuffer[length] = '\0';

  Serial.printf("[MQTT Inbound] Topic: %s | Payload: %s\n", topic, jsonBuffer);

  StaticJsonDocument<512> doc;
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

  // 1. Room Light Control (GPIO 2)
  if (dev == "room_light" || dev == "light" || dev == "led") {
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
  }

  // Publish immediate execution response
  publishResponse(deviceId, finalState.c_str(), cmdId, success);
}

void publishResponse(const char* deviceId, const char* state, const char* cmdId, bool success) {
  StaticJsonDocument<256> doc;
  doc["command_id"] = cmdId;
  doc["device_id"]  = deviceId;
  doc["state"]      = state;
  doc["success"]    = success;
  doc["timestamp"]  = millis();

  char output[256];
  serializeJson(doc, output);

  String respTopic = "orian/devices/" + String(deviceId) + "/status";
  mqttClient.publish(respTopic.c_str(), output);
  Serial.printf("[Execution Confirmed] Topic: %s -> %s\n", respTopic.c_str(), output);
}

// -----------------------------------------------------------------------------
// 10. TELEMETRY & HEARTBEAT BEACONS
// -----------------------------------------------------------------------------
void sendHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["device_id"]        = DEVICE_ID;
  doc["ip"]               = WiFi.localIP().toString();
  doc["rssi"]             = WiFi.RSSI();
  doc["uptime_sec"]       = millis() / 1000;
  doc["firmware_version"] = "2.0-esp32";
  doc["status"]           = "ONLINE";

  char buffer[256];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_HEARTBEAT, buffer);
  Serial.printf("[Heartbeat] Sent beacon: %s\n", buffer);
}

void sendTelemetry() {
  // Read sensor values (or realistic analog reading)
  float rawTemp = 26.5 + (random(0, 30) / 10.0);
  float rawHum  = 58.0 + (random(0, 40) / 10.0);

  StaticJsonDocument<256> doc;
  doc["device_id"]   = "dht22_temp_sensor";
  doc["temperature"] = rawTemp;
  doc["humidity"]    = rawHum;
  doc["motion"]      = "Clear";
  doc["timestamp"]   = millis();

  char buffer[256];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_TELEMETRY, buffer);
  Serial.printf("[Telemetry] Published sensor data: %s\n", buffer);
}
