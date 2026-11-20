# IoT Fundamentals — Sensor to MQTT Publisher (ESP32)

> **CognusOps AI Track 6-Week Internship — Week 1 Deliverable**  
> **Author**: Lokeshkannan U  
> **Topic**: Embedded MicroPython, DHT22 Sensor, Wokwi Simulation, and MQTT Telemetry Pipeline

---

## 📌 Project Overview

This repository contains the Week 1 lab deliverable for the CognusOps AI Track Internship. It implements an end-to-end IoT sensor pipeline:
1. An **ESP32 microcontroller** running **MicroPython** in the **Wokwi** simulator.
2. Digital temperature and relative humidity sensing via a **DHT22** sensor on GPIO 15.
3. Event-driven JSON serialization with **delta-reporting** (deadband filtering) to publish telemetry only when ambient conditions change.
4. Transmission over an **MQTT v3.1.1** broker (Eclipse Mosquitto / HiveMQ) to local subscriber terminals.

---

## 🏗️ Repository Structure

```
IOT-FUNDAMENTALS/
├── .github/
│   └── pull_request_template.md    # Standard PR template for mentor review
├── docs/
│   └── architecture_diagram.md     # 1-page 4-layer IoT architecture documentation
├── src/
│   ├── main.py                     # MicroPython firmware logic (Wi-Fi, MQTT, DHT22 loop)
│   ├── diagram.json                # Wokwi circuit schematic (ESP32 DevKitC V4 + DHT22)
│   ├── wokwi.toml                  # Simulator & RFC2217 port configuration
│   ├── mosquitto.conf              # Mosquitto broker configuration
│   └── wokwi-project.txt           # Upstream simulation reference link
├── .gitignore
└── README.md                       # Main lab documentation
```

---

## ⚙️ Circuit & Hardware Connections

| Component | Pin | ESP32 Pin | Purpose |
| :--- | :--- | :--- | :--- |
| **DHT22 Sensor** | VCC | `3V3` | 3.3V Power Supply |
| **DHT22 Sensor** | GND | `GND` | Ground Reference |
| **DHT22 Sensor** | SDA (Data) | `GPIO 15` | 1-Wire Digital Communication |
| **ESP32 UART0** | TX / RX | Serial Monitor | Debug console & REPL |

---

## 🚀 How to Run the Project

### 1. Start the Local Mosquitto Broker
In a terminal, navigate to the project directory and start Mosquitto using the provided configuration:
```powershell
cd src
mosquitto -v -c mosquitto.conf
```
*The broker will listen on `0.0.0.0:1883` and accept incoming connections from the Wokwi gateway.*

### 2. Start the MQTT Subscriber
In a second terminal, listen to the weather topic:
```powershell
mosquitto_sub -h 127.0.0.1 -t "wokwi-weather" -v
```

### 3. Run the Wokwi Simulation
1. In VS Code, press `Ctrl + Shift + P` $\rightarrow$ `Wokwi: Start IoT Gateway`.
2. Open `src/diagram.json` and click the green **Play** button.
3. In a third terminal, execute the firmware via `mpremote`:
   ```powershell
   python -m mpremote connect port:rfc2217://localhost:4000 run src/main.py
   ```

---

## 📊 Telemetry Output

When the DHT22 temperature or humidity values change, the ESP32 publishes an MQTT payload:

```json
{
  "temp": 24.5,
  "humidity": 42.0
}
```

**Terminal Subscriber Log**:
```text
wokwi-weather {"temp": 24.5, "humidity": 42.0}
```

---

## 📜 Deliverables
- [x] Functional MicroPython publisher code (`src/main.py`)
- [x] Wokwi circuit schematic and setup (`src/diagram.json`, `src/wokwi.toml`)
- [x] Local Mosquitto broker setup (`src/mosquitto.conf`)
- [x] One-page Architecture Diagram & Use Case Analysis (`docs/architecture_diagram.md`)
