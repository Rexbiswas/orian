# ORIAN AI — User Operations & Mobile Protection Guide
**Complete Manual for Running Orian AI, Inappropriate Activity Detection, Laptop Protection, and Mobile Alert System**

---

## 📑 Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Quick Start: Launching Orian AI](#2-quick-start-launching-orian-ai)
3. [Connecting Your Mobile Phone (Wi-Fi & Hotspot)](#3-connecting-your-mobile-phone-wi-fi--hotspot)
4. [Pairing & Approving Mobile Devices](#4-pairing--approving-mobile-devices)
5. [How Laptop Protection & Policy Engine Works](#5-how-laptop-protection--policy-engine-works)
6. [How Warnings & Automatic Sleep Work](#6-how-warnings--automatic-sleep-work)
7. [How to Receive & Manage Mobile Alerts](#7-how-to-receive--manage-mobile-alerts)
8. [How to Test the System (3 Testing Methods)](#8-how-to-test-the-system-3-testing-methods)
9. [Security, Privacy & Zero-Surveillance Guarantee](#9-security-privacy--zero-surveillance-guarantee)
10. [REST API & WebSocket Reference](#10-rest-api--websocket-reference)

---

## 1. System Overview & Architecture

Orian AI is an autonomous, privacy-first AI Operating System with built-in **Windows Laptop Protection** and **Real-Time Mobile Push Alerts**.

```
┌────────────────────────────────────────────────────────┐
│                  WINDOWS WORKSTATION                   │
│                                                        │
│  [Activity Monitor] ──► [Policy Engine] ──► [Risk Engine]
│          ▲                     │                │      │
│          │                     ▼                ▼      │
│   (Polls Active Window) [Local Warning]  [HMAC Gateway]│
│                                                 │      │
│                                                 ▼      │
│                                          [Win32 Sleep] │
└──────────────────────────┬─────────────────────────────┘
                           │ Real-Time WebSocket Push (/ws/protection)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   AUTHORIZED MOBILE                    │
│                                                        │
│     [LIVE ALERT CARD] ──► [DETAILS] ──► [OVERRIDE]     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Quick Start: Launching Orian AI

To start Orian AI on your laptop, open two PowerShell terminals:

### Terminal 1: Start Backend (FastAPI)
```powershell
cd "f:\major project\orionAI\backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
> **Note**: Binding to `0.0.0.0` allows your mobile phone on the same Wi-Fi/Hotspot to communicate with the laptop.

### Terminal 2: Start Frontend (Vite)
```powershell
cd "f:\major project\orionAI"
npm run dev -- --host
```
> Vite will show your local network URL (e.g. `http://192.168.1.15:5173`).

---

## 3. Connecting Your Mobile Phone (Wi-Fi & Hotspot)

You can connect your phone via your home Wi-Fi router or directly via your phone's Mobile Hotspot.

### Option A: Home / Office Wi-Fi
1. Connect both your laptop and mobile phone to the **same Wi-Fi network**.
2. On your laptop, run `ipconfig` in PowerShell to find your **IPv4 Address** (e.g. `192.168.1.15`).
3. Open your mobile browser (**Chrome** or **Safari**) and go to:
   ```
   http://<YOUR_LAPTOP_IP>:5173
   ```
   *(Example: `http://192.168.1.15:5173`)*

### Option B: Mobile Hotspot (No External Router)
1. Turn ON **Mobile Hotspot** on your phone.
2. Connect your laptop's Wi-Fi to your phone's hotspot.
3. Check your laptop's IP address with `ipconfig` (usually `192.168.43.x` on Android or `172.20.10.x` on iPhone).
4. On your phone's browser, visit `http://<YOUR_LAPTOP_IP>:5173`.

---

## 4. Pairing & Approving Mobile Devices

Orian uses cryptographic pairing to ensure only authorized devices receive alerts.

### Pairing via the Dashboard UI
1. In Orian AI, tap the **Shield Icon (🛡️)** at the bottom-right to open **ORIAN PROTECTION**.
2. Switch to the **`PAIRED DEVICES`** tab.
3. In **Pair New Mobile Phone**, type your phone name (e.g., `Tecno Spark 20 Pro 5G` or `Owner iPhone`) and tap **`+ PAIR`**.
4. The screen will generate a unique pairing code (e.g. `PAIR-205599`).
5. Tap **`APPROVE`** next to your device in the list to grant full active authorization.

---

## 5. How Laptop Protection & Policy Engine Works

1. **Activity Monitor**:
   - Continuously checks active foreground window titles and processes on Windows.
   - Preserves privacy: **Never captures keystrokes, personal chats, webcam, or full screenshots.**
2. **Whitelist Evaluation**:
   - Developer tools (VS Code, Python, Node, Git, Terminal, Compilers) and authorized cybersecurity labs are automatically whitelisted and remain 100% local.
3. **Policy Engine**:
   - Compares active activity against active **Focus Mode** (`WORK`, `STUDY`, `REST`, `OFF`).
   - Categorizes non-work activities (Gaming, Gambling, Blocked Websites, System Tampering).
4. **Risk Engine**:
   - Calculates dynamic risk level: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

---

## 6. How Warnings & Automatic Sleep Work

When a policy violation is detected during Focus Mode:

```
[Activity Violation Detected]
           │
           ▼
[1. Local Windows Warning Notification Issued]
           │
           ▼
[2. Immediate Push Alert Sent to Mobile Phone]
           │
           ├───────────────────────────────┐
           ▼                               ▼
[Owner clicks OVERRIDE on phone]   [No action taken]
           │                               │
     (App Allowed)                (Grace Period Expires)
                                           │
                                           ▼
                            [3. Cryptographic SLEEP Command Signed]
                                           │
                                           ▼
                            [4. Windows Enters Sleep Mode]
                                           │
                                           ▼
                            [5. Mobile Alert: "Automatic Sleep Executed"]
```

- **Grace Period**: Configurable buffer (e.g., 30–60 seconds) giving the user time to close the app or authorize an override.
- **Controlled Win32 API**: Uses `PowrProf.dll SetSuspendState(0, 1, 0)` with HMAC-SHA256 signature verification. Unrestricted commands or shell injection are mathematically blocked.

---

## 7. How to Receive & Manage Mobile Alerts

Alerts arrive in real time with audio notifications and color-coded risk cards:

### Alert Card Structure
```
┌────────────────────────────────────────────────────────┐
│ 🎮 ORIAN ALERT                             [ MEDIUM ]  │
│ Productivity Warning                       12:05 PM    │
│ ────────────────────────────────────────────────────── │
│ Activity: steam.exe       Policy: Work Hours           │
│ Action:   Warning issued  Device: My Windows Laptop    │
│ ────────────────────────────────────────────────────── │
│ [ DETAILS ]              [ ACKNOWLEDGE ]  [ OVERRIDE ] │
└────────────────────────────────────────────────────────┘
```

### Mobile Actions:
- **`[ DETAILS ]`**: Opens the Section 8 audit log displaying `Event ID`, `Device`, `Category`, `Detection Source`, `Policy`, `Timestamp`, and `Status`.
- **`[ ACKNOWLEDGE ]`**: Marks the alert resolved and stops pending notifications.
- **`[ OVERRIDE ]`**: Requires step-up authentication (Owner Password / TOTP) to override enforcement.

---

## 8. How to Test the System (3 Testing Methods)

### Method 1: Instant Dashboard Test (Recommended)
1. Open the **ORIAN PROTECTION** dashboard (🛡️ icon).
2. Click **`+ TEST WARN`** to simulate a productivity violation.
3. Click **`+ TEST SECURITY`** to simulate a critical tampering alert.
4. Watch the alert card instantly appear on your mobile phone screen.

### Method 2: Real-World Policy Trigger Test
1. Set **Focus Mode** to `WORK`.
2. Open a monitored application (e.g., game or `steam.exe`).
3. Observe the immediate alert delivered to your mobile phone.
4. Let the grace period elapse to observe the automatic sleep enforcement.

### Method 3: Automated 19-Step Scenario Verification Test
Run the deterministic automated verification test in PowerShell:
```powershell
cd "f:\major project\orionAI\backend"
python -m unittest tests.test_protection_e2e_scenario
```
*(Tests complete 19-step lifecycle: Laptop & Mobile registration -> Policy violation -> Windows warning -> Mobile alert -> Auto-sleep -> Audit logging).*

---

## 9. Security, Privacy & Zero-Surveillance Guarantee

| What Orian DOES | What Orian NEVER Does |
| :--- | :--- |
| ✅ Evaluates foreground window process against policy | ❌ No Keyloggers or password recording |
| ✅ Verifies HMAC-SHA256 cryptographic signatures on commands | ❌ No continuous screen capture or streaming |
| ✅ Sends policy-relevant alerts to authorized mobile phones | ❌ No hidden webcam or microphone recording |
| ✅ Enforces step-up authentication for privileged overrides | ❌ No monitoring of private personal messages |
| ✅ Whitelists coding tools and terminal workflows | ❌ Never treats standard programming as malicious |

---

## 10. REST API & WebSocket Reference

### Protection & Dashboard
- `GET /api/protection/dashboard` — Live metrics, focus state, paired devices, and recent alerts.
- `POST /api/protection/emergency-disable` — Owner toggle for master protection.
- `WS /ws/protection` — Live bidirectional WebSocket event channel.

### Mobile Device Management
- `POST /api/mobile/register` — Initiates pairing and generates pairing code.
- `POST /api/mobile/approve` — Owner approves device authorization.
- `GET /api/mobile/devices` — Lists registered mobile phones and status.
- `POST /api/mobile/revoke` — Revokes lost or compromised devices.

### Notifications
- `GET /api/notifications/list` — Query alert history with status and risk filters.
- `GET /api/notifications/{event_id}` — Detailed event data and delivery receipts.
- `POST /api/notifications/{event_id}/acknowledge` — Acknowledge alert.
- `POST /api/notifications/action` — Authenticated owner action (`OWNER_OVERRIDE`, `DISABLE_POLICY`).
- `POST /api/notifications/test` — Trigger simulated test alerts.
