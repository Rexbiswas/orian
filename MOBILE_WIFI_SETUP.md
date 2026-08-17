# Orian AI — Mobile Wi-Fi & Hotspot Connection Guide

This guide explains how to connect your mobile phone (Android / iPhone) to your laptop running **Orian AI** over Wi-Fi or Mobile Hotspot.

---

## 📡 Connection Methods

```
 ┌────────────────────────────────────────────────────────┐
 │                   METHOD 1: HOME WI-FI                 │
 │                                                        │
 │     [Mobile Phone] ──(Wi-Fi)──► [Wi-Fi Router]         │
 │                                       ▲                │
 │     [Laptop (Orian AI)] ──────(Wi-Fi)─┘                │
 └────────────────────────────────────────────────────────┘

 ┌────────────────────────────────────────────────────────┐
 │               METHOD 2: MOBILE HOTSPOT (NO ROUTER)     │
 │                                                        │
 │     [Mobile Phone (Hotspot ON)]                        │
 │                 ▲                                      │
 │                 └──────(Direct Wi-Fi)── [Laptop]       │
 └────────────────────────────────────────────────────────┘
```

---

## 🚀 Method 1: Connect via Mobile Hotspot (No External Router Needed)

Use this method when traveling or when you don't have a Wi-Fi router.

### Step 1: Enable Hotspot on Your Phone
1. **Android**: Go to **Settings > Network & Internet > Hotspot & Tethering > Wi-Fi Hotspot** and turn it **ON**.
2. **iPhone**: Go to **Settings > Personal Hotspot** and turn on **Allow Others to Join**.

### Step 2: Connect Laptop to Phone's Hotspot
1. On your laptop, click the **Wi-Fi** icon in the taskbar.
2. Select your phone's Hotspot network and enter the password.

### Step 3: Find Your Laptop's IP Address
1. Open **PowerShell** or **Command Prompt** on your laptop.
2. Type:
   ```powershell
   ipconfig
   ```
3. Locate **Wireless LAN adapter Wi-Fi** and find the **IPv4 Address**:
   - On Android Hotspot, it usually looks like: `192.168.43.xxx` (e.g. `192.168.43.15`)
   - On iPhone Hotspot, it usually looks like: `172.20.10.xxx` (e.g. `172.20.10.2`)

### Step 4: Open Orian AI on Your Phone
Open **Google Chrome**, **Safari**, or **Brave** on your phone and navigate to:

```
http://<YOUR_LAPTOP_IP>:5173
```
*(Example: `http://192.168.43.15:5173`)*

---

## 🏠 Method 2: Connect via Same Home / Office Wi-Fi Router

### Step 1: Connect Both Devices
Ensure both your laptop and mobile phone are connected to the **same Wi-Fi network**.

### Step 2: Check Laptop IP Address
Run in PowerShell on your laptop:
```powershell
ipconfig
```
*(Note the IPv4 address under Wi-Fi, e.g., `192.168.1.4`)*.

### Step 3: Open in Mobile Browser
On your phone's browser, visit:
```
http://192.168.1.4:5173
```

---

## 📲 Install as a Fullscreen Mobile App (PWA)

To make Orian AI look and feel like a native mobile app without the browser address bar:

1. Open `http://<YOUR_LAPTOP_IP>:5173` in **Chrome** (Android) or **Safari** (iOS).
2. Tap the browser menu:
   - **Chrome (Android)**: Tap the **3 vertical dots (⋮)** > **Add to Home screen** / **Install app**.
   - **Safari (iOS)**: Tap the **Share button (⬆)** > **Add to Home Screen**.
3. Orian AI will now launch from your phone's home screen with full fullscreen support, camera eye-tracking, and voice capabilities!

---

## 🤖 Method 3: Run as Native Android App (Capacitor Build)

If you prefer building a standalone Android `.apk`:

1. **Build the web production bundle**:
   ```powershell
   npm run build
   ```

2. **Sync the assets with Capacitor**:
   ```powershell
   npx cap sync android
   ```

3. **Open Android Studio**:
   ```powershell
   npx cap open android
   ```

4. Connect your phone via USB with **USB Debugging** enabled and hit **Run (▶)** in Android Studio.

---

## 🔍 Verifying Backend Health

To verify your phone can communicate with the Python backend server:

Open this URL on your phone:
```
http://<YOUR_LAPTOP_IP>:8000/api/iot/health
```

Expected JSON response:
```json
{
  "success": true,
  "health": {
    "backend_status": "ONLINE",
    "database_status": "HEALTHY",
    "health_score": 100.0
  }
}
```

---

## 🛠️ Troubleshooting & Fixes

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **Page does not load on mobile** | Laptop dev server not running | Ensure `npm run dev:all` or `npm run dev` is active in PowerShell. |
| **Connection Timed Out** | Windows Firewall blocking incoming port 5173 / 8000 | Set your network profile to **Private** in Windows Settings, or run `New-NetFirewallRule -DisplayName "Orian AI" -Direction Inbound -LocalPort 5173,8000 -Protocol TCP -Action Allow`. |
| **Different Subnet** | Phone and laptop are on different networks | Ensure both devices share the exact same Wi-Fi SSID or use Mobile Hotspot. |
| **Microphone / Camera permission blocked** | Non-HTTPS origin restrictions | Go to Chrome settings on phone > Site Settings > Permissions > Allow Camera & Microphone for this local IP. |
