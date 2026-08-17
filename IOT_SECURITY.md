# Orian AI — IoT & ESP32 Hardware Security Architecture

## 1. Physical Device Authentication
Every physical ESP32 controller in Orian AI has a dedicated cryptographic identity:
- **Device ID**: e.g., `esp32_main_core_001`
- **Secret Token**: Generated via `secrets.token_urlsafe(32)`
- **Database Entry**: Persisted in `sec_iot_credentials` and `iot_devices`.

---

## 2. Topic Isolation & Access Control
Devices communicate over strict topic boundaries:
- `orian/devices/{device_id}/command`: Inbound commands addressed to this specific device.
- `orian/devices/{device_id}/status`: Hardware execution confirmation and state telemetry.
- `orian/devices/{device_id}/telemetry`: Sensor streams (DHT11/DHT22 temperature & humidity).
- `orian/devices/{device_id}/heartbeat`: Device alive status and IP beacons.

---

## 3. Replay Attack Protection
Every dispatched command envelope includes:
```json
{
  "request_id": "req_8f1d2938472910a2",
  "device_id": "esp32_main_core_001",
  "command": "turn_on",
  "parameters": {},
  "timestamp": 1786984228.334,
  "expires_at": 1786984288.334,
  "nonce": "c928a417e291",
  "signature": "a7b8c9d0...hmac_sha256"
}
```
- **Replay Window**: Commands older than 60 seconds (or beyond 15s clock skew) are rejected.
- **HMAC Signatures**: ESP32 / backend verifies the signature before executing relays.

---

## 4. Safety Confirmation for High-Power Appliances
Appliances classified with `is_safety_critical=1` (such as AC units, heaters, water heaters) automatically trigger a safety confirmation gate in the Security Gateway before turning on.
