# Orian Android App - Language & Technical Analysis

This document provides a comprehensive analysis of the programming languages and technical stack used to build the **Orian Android Application** (located in the [android](file:///f:/major%20project/orionAI/android) directory).

---

## 📊 Programming Languages Breakdown

The Orian Android app is a **hybrid/cross-platform application** powered by **Capacitor**. It uses a combination of web technologies for the user interface and native languages for platform-level background tasks.

| Role | Language / Tech | Primary Usage & Components |
|---|---|---|
| **Frontend / App UI** | **TypeScript / JavaScript** | Core application logic, React 19 views, Framer Motion animations, user interactions, and state management (Zustand). |
| **Native Integration** | **Java** | Native Android container (`MainActivity`), background/foreground services (`WakeWordService`), microphone permissions, and Speech API. |
| **Build Configuration** | **Groovy (Gradle)** | Compilation recipes, dependency management, SDK level overrides, and Capacitor build configurations. |

### 📋 List of Languages to Build the App

To develop, configure, and compile the **Orian Android App**, the following programming and configuration languages are required:

1. **Java (JDK 17)**:
   - **Usage**: Used to compile and run the native Android container and custom services.
   - **Key files**: [MainActivity.java](file:///f:/major%20project/orionAI/android/app/src/main/java/com/orian/ai/MainActivity.java) and [WakeWordService.java](file:///f:/major%20project/orionAI/android/app/src/main/java/com/orian/ai/WakeWordService.java).
2. **TypeScript (TS) / JavaScript (JS)**:
   - **Usage**: Used for developing the entire frontend logic, React components, and state management.
   - **Key files**: Frontend files under [src/](file:///f:/major%20project/orionAI/src).
3. **HTML5 & CSS3 (Tailwind CSS)**:
   - **Usage**: Used to build the application layout, structure, styles, and responsive layout interfaces.
4. **Groovy (Gradle)**:
   - **Usage**: Used for Android build system configurations, dependency declarations, and signing configs.
   - **Key files**: [build.gradle](file:///f:/major%20project/orionAI/android/build.gradle) and [settings.gradle](file:///f:/major%20project/orionAI/android/settings.gradle).

---

## 🛠️ Detailed Component Analysis

### 1. Web Layer (TypeScript / React)
The user interface of the app runs inside a native WebView wrapper powered by Capacitor.
* **Source Path:** [src/](file:///f:/major%20project/orionAI/src) (top-level directory)
* **Framework:** React 19 + Vite + Tailwind CSS.
* **Build Artifact:** Compiled into the `dist/` directory, which is packaged as assets inside the Android application via Capacitor (`webDir: 'dist'`).

### 2. Native Wrapper Layer (Java)
For features that require direct access to Android operating system capabilities, native Java code is used.
* **MainActivity ([MainActivity.java](file:///f:/major%20project/orionAI/android/app/src/main/java/com/orian/ai/MainActivity.java)):**
  - Written in **Java**.
  - Inherits from `com.getcapacitor.BridgeActivity`.
  - Handles runtime microphone permission requests.
  - Controls lifecycle events and handles incoming wake-word intents.
* **WakeWordService ([WakeWordService.java](file:///f:/major%20project/orionAI/android/app/src/main/java/com/orian/ai/WakeWordService.java)):**
  - Written in **Java**.
  - Implements a foreground/background Android Service (`android.app.Service`).
  - Utilizes the native Google Speech Recognition API (`android.speech.SpeechRecognizer`) to continuously monitor microphone input.
  - Matches spoken trigger phrases ("hello orian" or "orian") to wake up the app dynamically.

### 3. Build & Build Scripting (Groovy)
The build settings are configured using Gradle files:
* **Settings & Gradle files:**
  - `android/build.gradle` (Groovy DSL)
  - `android/app/build.gradle` (Groovy DSL)
  - `android/settings.gradle` (Groovy DSL)

---

## 📡 Bridge Interaction (Java ⇆ React)

The communication between the Java native service and the React web application is handled through Capacitor's WebView injection mechanism:
1. When the Java-based foreground service (`WakeWordService`) hears the wake word:
   ```java
   intent.putExtra("wakeWordTriggered", true);
   ```
2. The `MainActivity` captures this intent and executes custom JavaScript in the web runtime:
   ```java
   this.bridge.getWebView().evaluateJavascript(
       "window.dispatchEvent(new CustomEvent('nativeWakeWordTriggered'));", 
       null
   );
   ```
3. The React app (in TypeScript) listens for the `nativeWakeWordTriggered` custom window event to trigger speech synthesis or voice activation.

---

## ⚠️ Important Note: Missing Local Files
> [!WARNING]
> While performing the analysis, it was detected that the native Android app directory (`android/app`) files have been deleted locally in your working directory (e.g. `MainActivity.java`, `WakeWordService.java`, and `build.gradle`).
>
> However, these files **are fully tracked in Git** under the `main` branch.
>
> If you wish to restore the deleted native files locally, you can run the following command in your terminal:
> ```powershell
> git restore android/app/
> ```
