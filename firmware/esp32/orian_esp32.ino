/*
 * ==============================================================================
 * ORIAN AI — ESP32 IOT EMBEDDED CONTROLLER FIRMWARE v2.1
 * ==============================================================================
 * Fixed:
 *  - Real DHT11/DHT22 readings instead of random values
 *  - Correct device ID extraction from MQTT topics
 *  - Invalid commands now return success=false
 *  - Safer MQTT reconnect logic
 *  - MQTT Last-Will/availability
 *  - Device status publication
 *  - Configurable relay active level
 *  - HTTP timeouts
 *  - No false "REST fallback" claim for command execution
 *
 * Libraries:
 *  - WiFi (ESP32 core)
 *  - PubSubClient
 *  - ArduinoJson
 *  - HTTPClient (ESP32 core)
 *  - DHT sensor library by Adafruit
 *  - Adafruit Unified Sensor
 */

#include <ArduinoJson.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <WiFi.h>

// -----------------------------------------------------------------------------
// 1. NETWORK CONFIGURATION
// -----------------------------------------------------------------------------
const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char *ORIAN_SERVER_IP = "192.168.1.100";
const uint16_t ORIAN_HTTP_PORT = 8000;
const uint16_t MQTT_PORT = 1883;

const char *MQTT_USER = "";
const char *MQTT_PASS = "";

const char *DEVICE_ID = "esp32_main_core";
const char *FIRMWARE_VERSION = "2.1-esp32";

// -----------------------------------------------------------------------------
// 2. HARDWARE
// -----------------------------------------------------------------------------
#define PIN_LIGHT_LED 2
#define PIN_FAN_RELAY 4
#define PIN_AC_RELAY 15
#define PIN_DHT_SENSOR 18

// Set true if your relay module is active-LOW.
// Most relay modules use LOW = ON. Change this to false if yours is active-HIGH.
const bool RELAY_ACTIVE_LOW = true;

#define DHTTYPE DHT22
// If you have a DHT11, change the line above to:
// #define DHTTYPE DHT11

DHT dht(PIN_DHT_SENSOR, DHTTYPE);

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// -----------------------------------------------------------------------------
// 3. TIMERS
// -----------------------------------------------------------------------------
const unsigned long WIFI_RETRY_INTERVAL = 10000UL;
const unsigned long MQTT_RETRY_INTERVAL = 10000UL;
const unsigned long HEARTBEAT_INTERVAL = 15000UL;
const unsigned long TELEMETRY_INTERVAL = 10000UL;

unsigned long lastWiFiAttempt = 0;
unsigned long lastMqttAttempt = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastTelemetry = 0;

// -----------------------------------------------------------------------------
// 4. DEVICE STATE
// -----------------------------------------------------------------------------
bool stateLight = false;
bool stateFan = false;
bool stateAC = false;

// -----------------------------------------------------------------------------
// 5. FUNCTION DECLARATIONS
// -----------------------------------------------------------------------------
void setupWiFi();
void maintainWiFi();
void reconnectMQTT();
void handleMQTTMessage(char *topic, byte *payload, unsigned int length);

bool executeDeviceCommand(const char *deviceId, const char *command,
                          const char *cmdId, String &finalState,
                          String &errorMessage);

void sendHeartbeat();
void sendTelemetry();
void publishResponse(const char *deviceId, const char *state,
                     const char *cmdId, bool success,
                     const char *errorMessage = nullptr);

void sendRESTHeartbeat();
void sendRESTTelemetry(float temp, float hum);

String extractDeviceIdFromTopic(const char *topic);
bool isKnownDevice(const String &deviceId);
bool isCommand(const String &cmd, const char *a, const char *b = nullptr,
               const char *c = nullptr);

void writeRelay(uint8_t pin, bool on);
void setDeviceState(const String &deviceId, bool on);
bool getDeviceState(const String &deviceId);

// -----------------------------------------------------------------------------
// 6. SETUP
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("=======================================================");
  Serial.println("       ORIAN AI — ESP32 IOT CONTROLLER v2.1           ");
  Serial.println("=======================================================");

  // GPIO
  pinMode(PIN_LIGHT_LED, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);
  pinMode(PIN_AC_RELAY, OUTPUT);

  // Safe startup state
  writeRelay(PIN_LIGHT_LED, false);
  writeRelay(PIN_FAN_RELAY, false);
  writeRelay(PIN_AC_RELAY, false);

  // DHT
  dht.begin();

  // Wi-Fi
  WiFi.mode(WIFI_STA);
  setupWiFi();

  // MQTT
  mqttClient.setServer(ORIAN_SERVER_IP, MQTT_PORT);
  mqttClient.setCallback(handleMQTTMessage);
  mqttClient.setBufferSize(768);
  mqttClient.setKeepAlive(30);

  Serial.println("[ORIAN] Hardware initialization complete.");
}

// -----------------------------------------------------------------------------
// 7. MAIN LOOP
// -----------------------------------------------------------------------------
void loop() {
  maintainWiFi();

  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      unsigned long now = millis();

      if (now - lastMqttAttempt >= MQTT_RETRY_INTERVAL) {
        lastMqttAttempt = now;
        reconnectMQTT();
      }
    } else {
      mqttClient.loop();
    }
  }

  unsigned long now = millis();

  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    sendHeartbeat();
  }

  if (now - lastTelemetry >= TELEMETRY_INTERVAL) {
    lastTelemetry = now;
    sendTelemetry();
  }

  delay(2);
}

// -----------------------------------------------------------------------------
// 8. WIFI
// -----------------------------------------------------------------------------
void setupWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("[WiFi] Connecting to: %s\n", WIFI_SSID);

  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - start < 12000UL) {
    delay(300);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("[WiFi] Connected.");
    Serial.printf("[WiFi] IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[WiFi] RSSI: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println();
    Serial.println("[WiFi] Connection failed. Will retry automatically.");
  }
}

void maintainWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  unsigned long now = millis();

  if (now - lastWiFiAttempt >= WIFI_RETRY_INTERVAL) {
    lastWiFiAttempt = now;
    setupWiFi();
  }
}

// -----------------------------------------------------------------------------
// 9. MQTT
// -----------------------------------------------------------------------------
void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED || mqttClient.connected()) {
    return;
  }

  Serial.printf("[MQTT] Connecting to %s:%u...\n",
                ORIAN_SERVER_IP, MQTT_PORT);

  String clientId =
      String(DEVICE_ID) + "_" + String((uint32_t)ESP.getEfuseMac(), HEX);

  String willTopic =
      String("orian/devices/") + DEVICE_ID + "/status";

  const char *willPayload =
      "{\"device_id\":\"esp32_main_core\",\"status\":\"OFFLINE\"}";

  bool connected;

  if (strlen(MQTT_USER) > 0) {
    connected = mqttClient.connect(
        clientId.c_str(),
        MQTT_USER,
        MQTT_PASS,
        willTopic.c_str(),
        1,
        true,
        willPayload);
  } else {
    connected = mqttClient.connect(
        clientId.c_str(),
        willTopic.c_str(),
        1,
        true,
        willPayload);
  }

  if (!connected) {
    Serial.printf("[MQTT] Failed. rc=%d\n", mqttClient.state());
    return;
  }

  Serial.println("[MQTT] Connected.");

  // Main wildcard subscription.
  // The ESP32 will validate device_id before executing commands.
  if (!mqttClient.subscribe("orian/devices/+/command", 1)) {
    Serial.println("[MQTT] Command subscription failed.");
  }

  sendHeartbeat();
}

// -----------------------------------------------------------------------------
// 10. MQTT COMMAND HANDLER
// -----------------------------------------------------------------------------
void handleMQTTMessage(char *topic, byte *payload, unsigned int length) {
  if (length == 0) {
    return;
  }

  char jsonBuffer[768];

  if (length >= sizeof(jsonBuffer)) {
    Serial.println("[MQTT] Payload too large.");
    return;
  }

  memcpy(jsonBuffer, payload, length);
  jsonBuffer[length] = '\0';

  Serial.printf("\n[MQTT] Topic: %s\n", topic);
  Serial.printf("[MQTT] Payload: %s\n", jsonBuffer);

#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<768> doc;
#endif

  DeserializationError error = deserializeJson(doc, jsonBuffer);

  if (error) {
    Serial.printf("[JSON] Parse error: %s\n", error.c_str());
    return;
  }

  String topicDevice = extractDeviceIdFromTopic(topic);

  const char *payloadDevice = doc["device_id"] | "";
  const char *command = doc["command"] | "";
  const char *cmdId = doc["command_id"] | "";

  String deviceId = strlen(payloadDevice) > 0
                        ? String(payloadDevice)
                        : topicDevice;

  deviceId.toLowerCase();

  if (deviceId.length() == 0) {
    publishResponse(
        DEVICE_ID,
        "UNKNOWN",
        cmdId,
        false,
        "Missing device_id");
    return;
  }

  // Security/correctness check:
  // This ESP32 should only execute commands addressed to itself or
  // explicitly to one of its locally controlled devices.
  if (!isKnownDevice(deviceId)) {
    publishResponse(
        deviceId.c_str(),
        "UNKNOWN",
        cmdId,
        false,
        "Unknown device");
    return;
  }

  if (strlen(command) == 0) {
    publishResponse(
        deviceId.c_str(),
        "UNKNOWN",
        cmdId,
        false,
        "Missing command");
    return;
  }

  String finalState;
  String errorMessage;

  bool success = executeDeviceCommand(
      deviceId.c_str(),
      command,
      cmdId,
      finalState,
      errorMessage);

  publishResponse(
      deviceId.c_str(),
      finalState.c_str(),
      cmdId,
      success,
      success ? nullptr : errorMessage.c_str());
}

// -----------------------------------------------------------------------------
// 11. COMMAND EXECUTION
// -----------------------------------------------------------------------------
bool executeDeviceCommand(const char *deviceId,
                          const char *command,
                          const char *cmdId,
                          String &finalState,
                          String &errorMessage) {
  (void)cmdId;

  String dev(deviceId);
  String cmd(command);

  dev.toLowerCase();
  cmd.toLowerCase();
  cmd.trim();

  if (!isKnownDevice(dev)) {
    finalState = "UNKNOWN";
    errorMessage = "Unknown device";
    return false;
  }

  // Room light / LED
  if (dev == "room_light" || dev == "light" || dev == "led") {
    if (isCommand(cmd, "turn_on", "on")) {
      setDeviceState("room_light", true);
    } else if (isCommand(cmd, "turn_off", "off")) {
      setDeviceState("room_light", false);
    } else if (cmd == "toggle") {
      setDeviceState("room_light", !stateLight);
    } else {
      finalState = stateLight ? "ON" : "OFF";
      errorMessage = "Unsupported light command";
      return false;
    }

    finalState = stateLight ? "ON" : "OFF";

    Serial.printf("[LIGHT] State: %s\n", finalState.c_str());
    return true;
  }

  // Bedroom fan
  if (dev == "bedroom_fan" || dev == "fan") {
    if (isCommand(cmd, "turn_on", "on")) {
      setDeviceState("bedroom_fan", true);
    } else if (isCommand(cmd, "turn_off", "off")) {
      setDeviceState("bedroom_fan", false);
    } else if (cmd == "toggle") {
      setDeviceState("bedroom_fan", !stateFan);
    } else {
      finalState = stateFan ? "ON" : "OFF";
      errorMessage = "Unsupported fan command";
      return false;
    }

    finalState = stateFan ? "ON" : "OFF";

    Serial.printf("[FAN] State: %s\n", finalState.c_str());
    return true;
  }

  // Living room AC relay
  if (dev == "living_room_ac" || dev == "ac") {
    if (isCommand(cmd, "turn_on", "on")) {
      setDeviceState("living_room_ac", true);
    } else if (isCommand(cmd, "turn_off", "off")) {
      setDeviceState("living_room_ac", false);
    } else if (cmd == "toggle") {
      setDeviceState("living_room_ac", !stateAC);
    } else {
      finalState = stateAC ? "ON" : "OFF";
      errorMessage = "Unsupported AC command";
      return false;
    }

    finalState = stateAC ? "ON" : "OFF";

    Serial.printf("[AC] State: %s\n", finalState.c_str());
    return true;
  }

  finalState = "UNKNOWN";
  errorMessage = "No command handler for device";
  return false;
}

// -----------------------------------------------------------------------------
// 12. DEVICE HELPERS
// -----------------------------------------------------------------------------
bool isKnownDevice(const String &deviceId) {
  String dev = deviceId;
  dev.toLowerCase();

  return dev == "esp32_main_core" ||
         dev == "room_light" ||
         dev == "light" ||
         dev == "led" ||
         dev == "bedroom_fan" ||
         dev == "fan" ||
         dev == "living_room_ac" ||
         dev == "ac";
}

bool isCommand(const String &cmd,
               const char *a,
               const char *b,
               const char *c) {
  return cmd == a ||
         (b != nullptr && cmd == b) ||
         (c != nullptr && cmd == c);
}

void writeRelay(uint8_t pin, bool on) {
  if (pin == PIN_LIGHT_LED && !RELAY_ACTIVE_LOW) {
    digitalWrite(pin, on ? HIGH : LOW);
    return;
  }

  if (pin == PIN_LIGHT_LED && RELAY_ACTIVE_LOW) {
    // Built-in LEDs are commonly active-HIGH on ESP32 boards.
    // GPIO2 is treated as a normal LED output here.
    digitalWrite(pin, on ? HIGH : LOW);
    return;
  }

  digitalWrite(pin, RELAY_ACTIVE_LOW
                        ? (on ? LOW : HIGH)
                        : (on ? HIGH : LOW));
}

void setDeviceState(const String &deviceId, bool on) {
  String dev = deviceId;
  dev.toLowerCase();

  if (dev == "room_light" || dev == "light" || dev == "led") {
    stateLight = on;
    writeRelay(PIN_LIGHT_LED, on);
  } else if (dev == "bedroom_fan" || dev == "fan") {
    stateFan = on;
    writeRelay(PIN_FAN_RELAY, on);
  } else if (dev == "living_room_ac" || dev == "ac") {
    stateAC = on;
    writeRelay(PIN_AC_RELAY, on);
  }
}

bool getDeviceState(const String &deviceId) {
  String dev = deviceId;
  dev.toLowerCase();

  if (dev == "room_light" || dev == "light" || dev == "led") {
    return stateLight;
  }

  if (dev == "bedroom_fan" || dev == "fan") {
    return stateFan;
  }

  if (dev == "living_room_ac" || dev == "ac") {
    return stateAC;
  }

  return false;
}

// Extracts:
// orian/devices/room_light/command
//                    ^^^^^^^^^^
String extractDeviceIdFromTopic(const char *topic) {
  String value(topic);

  const String prefix = "orian/devices/";
  const String suffix = "/command";

  if (!value.startsWith(prefix) || !value.endsWith(suffix)) {
    return "";
  }

  value.remove(0, prefix.length());
  value.remove(value.length() - suffix.length());

  value.toLowerCase();
  return value;
}

// -----------------------------------------------------------------------------
// 13. RESPONSE
// -----------------------------------------------------------------------------
void publishResponse(const char *deviceId,
                     const char *state,
                     const char *cmdId,
                     bool success,
                     const char *errorMessage) {
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<384> doc;
#endif

  doc["command_id"] = cmdId ? cmdId : "";
  doc["device_id"] = deviceId ? deviceId : "";
  doc["state"] = state ? state : "UNKNOWN";
  doc["success"] = success;
  doc["timestamp"] = millis();

  if (!success && errorMessage != nullptr) {
    doc["error"] = errorMessage;
  }

  char output[384];
  serializeJson(doc, output, sizeof(output));

  String respTopic =
      String("orian/devices/") + String(deviceId) + "/status";

  if (mqttClient.connected()) {
    bool published =
        mqttClient.publish(respTopic.c_str(), output, true);

    Serial.printf(
        "[MQTT Response] %s -> %s [%s]\n",
        respTopic.c_str(),
        output,
        published ? "OK" : "FAILED");
  } else {
    Serial.println("[MQTT Response] MQTT offline; response not published.");
  }
}

// -----------------------------------------------------------------------------
// 14. HEARTBEAT
// -----------------------------------------------------------------------------
void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<384> doc;
#endif

  doc["device_id"] = DEVICE_ID;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_sec"] = millis() / 1000UL;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["status"] = "ONLINE";
  doc["light"] = stateLight ? "ON" : "OFF";
  doc["fan"] = stateFan ? "ON" : "OFF";
  doc["ac"] = stateAC ? "ON" : "OFF";

  char buffer[384];
  serializeJson(doc, buffer, sizeof(buffer));

  if (mqttClient.connected()) {
    String topic =
        String("orian/devices/") + DEVICE_ID + "/heartbeat";

    mqttClient.publish(topic.c_str(), buffer, true);

    String statusTopic =
        String("orian/devices/") + DEVICE_ID + "/status";

    mqttClient.publish(statusTopic.c_str(), buffer, true);

    Serial.printf("[Heartbeat] %s\n", buffer);
  }

  sendRESTHeartbeat();
}

// -----------------------------------------------------------------------------
// 15. DHT TELEMETRY
// -----------------------------------------------------------------------------
void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("[DHT] Failed to read sensor.");
    return;
  }

#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<384> doc;
#endif

  doc["device_id"] = DEVICE_ID;
  doc["sensor"] = "dht";
  doc["temperature_c"] = temperature;
  doc["humidity_percent"] = humidity;
  doc["light"] = stateLight ? "ON" : "OFF";
  doc["fan"] = stateFan ? "ON" : "OFF";
  doc["ac"] = stateAC ? "ON" : "OFF";
  doc["timestamp"] = millis();

  char buffer[384];
  serializeJson(doc, buffer, sizeof(buffer));

  if (mqttClient.connected()) {
    String topic =
        String("orian/devices/") + DEVICE_ID + "/telemetry";

    mqttClient.publish(topic.c_str(), buffer);

    Serial.printf("[Telemetry] %s\n", buffer);
  }

  sendRESTTelemetry(temperature, humidity);
}

// -----------------------------------------------------------------------------
// 16. REST FALLBACK — TELEMETRY / HEARTBEAT ONLY
// -----------------------------------------------------------------------------
void sendRESTHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;

  String url =
      "http://" + String(ORIAN_SERVER_IP) + ":" +
      String(ORIAN_HTTP_PORT) +
      "/api/iot/esp32/heartbeat";

  if (!http.begin(url)) {
    Serial.println("[REST] Failed to initialize HTTP client.");
    return;
  }

  http.setTimeout(2000);
  http.addHeader("Content-Type", "application/json");

  String body =
      "{\"device_id\":\"" + String(DEVICE_ID) +
      "\",\"ip_address\":\"" + WiFi.localIP().toString() +
      "\",\"status\":\"ONLINE\"}";

  int httpCode = http.POST(body);

  if (httpCode > 0) {
    Serial.printf("[REST Heartbeat] HTTP %d\n", httpCode);
  } else {
    Serial.printf("[REST Heartbeat] Error: %s\n",
                  http.errorToString(httpCode).c_str());
  }

  http.end();
}

void sendRESTTelemetry(float temp, float hum) {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;

  String url =
      "http://" + String(ORIAN_SERVER_IP) + ":" +
      String(ORIAN_HTTP_PORT) +
      "/api/iot/esp32/telemetry";

  if (!http.begin(url)) {
    Serial.println("[REST] Failed to initialize HTTP client.");
    return;
  }

  http.setTimeout(2000);
  http.addHeader("Content-Type", "application/json");

  String body =
      "{\"device_id\":\"" + String(DEVICE_ID) +
      "\",\"temperature\":" + String(temp, 1) +
      ",\"humidity\":" + String(hum, 1) +
      ",\"light\":\"" + String(stateLight ? "ON" : "OFF") +
      "\",\"fan\":\"" + String(stateFan ? "ON" : "OFF") +
      "\",\"ac\":\"" + String(stateAC ? "ON" : "OFF") +
      "\"}";

  int httpCode = http.POST(body);

  if (httpCode > 0) {
    Serial.printf("[REST Telemetry] HTTP %d\n", httpCode);
  } else {
    Serial.printf("[REST Telemetry] Error: %s\n",
                  http.errorToString(httpCode).c_str());
  }

  http.end();
}