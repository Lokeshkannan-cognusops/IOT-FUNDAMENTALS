# IoT Fundamentals — ESP32 Sensor & Actuator Station with MQTT

> **CognusOps AI Track 6-Week Internship — Week 1 Lab Deliverable**  
> **Author**: Lokeshkannan U (`Lokeshkannan-cognusops`)  
> **Topic**: Embedded MicroPython, DHT22 Telemetry, PIR Motion Actuation, Wokwi Simulation, and MQTT Telemetry Pipeline

---

## 📌 Project Overview

This repository houses the Week 1 lab deliverables for the CognusOps AI Track Internship. It implements an end-to-end intelligent IoT sensing and actuation node:
1. **ESP32 Microcontroller** running **MicroPython** in the **Wokwi** simulation environment.
2. **Periodic Environmental Telemetry**: Continuous ambient temperature and relative humidity sensing via a **DHT22 sensor** on `GPIO 15`, transmitting JSON telemetry every 5 seconds over Serial and MQTT (`wokwi-weather`).
3. **Motion Detection & Event Actuation**: Real-time human presence detection via a **PIR Motion Sensor** on `GPIO 13`, triggering immediate actuation of an **Electromechanical Relay** and a **Red Indicator LED** on `GPIO 12`, publishing instantaneous state change events (`wokwi-motion`).
4. **Boot-Time Power-On Self-Test (POST)**: The firmware executes an automated 3-pulse blink diagnostic on GPIO 12 to verify actuator continuity and relay switching upon cold boot.
5. **Local MQTT Telemetry Pipeline**: Built-in support for local Eclipse Mosquitto broker integration using Wokwi IoT Gateway bridge (`host.wokwi.internal:1883`) with standalone graceful fallback.

---

## 🏗️ Repository Structure

```
IOT-FUNDAMENTALS/
├── .github/
│   └── pull_request_template.md        # Standard PR review template
├── docs/
│   ├── architecture_diagram.md         # Monday 4-layer IoT architecture documentation
│   └── hardware_comparison_notes.md    # Tuesday hardware comparison (Sensors, Actuators, Arduino vs ESP32 vs RPi)
├── src/
│   ├── main.py                         # MicroPython firmware logic (DHT22 loop + PIR motion trigger + POST)
│   ├── diagram.json                    # Wokwi circuit schematic (ESP32 DevKitC V4, DHT22, PIR, Relay, LED)
│   ├── wokwi.toml                      # Simulator firmware & RFC2217 port binding
│   ├── mosquitto.conf                  # Mosquitto broker listener configuration
│   └── wokwi-project.txt               # Wokwi simulation reference
├── .gitignore
└── README.md                           # Main lab documentation
```

---

## ⚙️ Circuit Schematic & Pin Interconnects

The circuit connects the ESP32 DevKitC V4 to two sensors (DHT22, PIR) and two actuators (5V Relay, Red LED via 220Ω current-limiting resistor):

```
                                  ┌────────────────────────┐
                                  │      ESP32 DevKit      │
                                  │                        │
         DHT22 (Pin 15) ◄─────────┤ GPIO 15         3V3    ├─────────► VCC (DHT22, PIR)
         PIR Out (Pin 13) ────────► GPIO 13         5V     ├─────────► VCC (Relay)
    Relay IN / LED (Pin 12) ◄─────┤ GPIO 12         GND.1  ├─────────► GND (All components)
                                  └────────────────────────┘
```

| Component | Component Pin | ESP32 Pin | Logic Level | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **DHT22 Sensor** | VCC | `3V3` | $3.3\text{V}$ DC | Digital power supply |
| **DHT22 Sensor** | SDA (Data) | `GPIO 15` | $3.3\text{V}$ Logic | 1-Wire bidirectional telemetry |
| **DHT22 Sensor** | GND | `GND.1` | Ground | System common ground |
| **PIR Motion Sensor** | VCC | `3V3` | $3.3\text{V}$ DC | Sensor power |
| **PIR Motion Sensor** | OUT | `GPIO 13` | $3.3\text{V}$ Logic | Active-HIGH binary motion signal |
| **PIR Motion Sensor** | GND | `GND.1` | Ground | System common ground |
| **5V Relay Module** | VCC | `5V` | $5.0\text{V}$ DC | Coil supply voltage |
| **5V Relay Module** | IN | `GPIO 12` | $3.3\text{V}$ Logic | Active-HIGH transistor trigger |
| **5V Relay Module** | GND | `GND.1` | Ground | System common ground |
| **Red LED** | Anode ($A$) | `GPIO 12` | $3.3\text{V}$ Logic | Actuation indicator |
| **220Ω Resistor ($R_1$)** | Pin 1 $\rightarrow$ Pin 2 | `led1:C` $\rightarrow$ `GND.1` | — | Current-limiting protection |

---

## 🚀 How to Run & Verify the Lab

### Way 1: In VS Code with Wokwi Extension & Local Mosquitto

1. **Start the Mosquitto Broker**:
   ```powershell
   & "C:\Program Files\Mosquitto\mosquitto.exe" -v -c "src\mosquitto.conf"
   ```
2. **Start the MQTT Subscriber (monitoring all topics)**:
   ```powershell
   & "C:\Program Files\Mosquitto\mosquitto_sub.exe" -h 127.0.0.1 -t "#" -v
   ```
3. **Start the Wokwi Simulation**:
   - Open `src/diagram.json` in VS Code and click the green **Play** button (or `Ctrl+Shift+P` $\rightarrow$ `Wokwi: Start Simulation`).
4. **Execute Firmware via `mpremote`**:
   ```powershell
   python -m mpremote connect port:rfc2217://localhost:4000 run src/main.py
   ```
   *(Alternatively, copy permanently to internal flash: `python -m mpremote connect port:rfc2217://localhost:4000 fs cp src/main.py :main.py` followed by `python -m mpremote connect port:rfc2217://localhost:4000 reset`)*

---

### Way 2: In Wokwi Web Browser (Zero Setup)

1. Open [Wokwi Web](https://wokwi.com).
2. Select **ESP32** $\rightarrow$ **MicroPython**.
3. Replace `diagram.json` with the contents of [`src/diagram.json`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot%20Fundamentals/IOT-FUNDAMENTALS/src/diagram.json).
4. Replace `main.py` with the contents of [`src/main.py`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot Fundamentals/IOT-FUNDAMENTALS/src/main.py).
5. Click **Start Simulation**:
   - Observe the **Red LED & Relay blink 3 times** during startup self-test.
   - Click the **PIR sensor** and click **Simulate motion** $\rightarrow$ watch the Relay trigger and the Red LED latch ON with real-time Serial output.
   - Adjust the **DHT22 temperature & humidity sliders** $\rightarrow$ observe JSON telemetry printed every 5 seconds.

---

## 📊 Telemetry & Event Outputs

### 1. Serial Monitor Logs
```text
==================================================
  ESP32 Smart Environmental & Motion Station     
  Week 1 Tuesday Lab — CognusOps AI Track        
==================================================

[INIT] Starting Actuator Test: Blinking Red LED & Relay 3 times...
[INIT] Red LED & Relay self-test PASSED (Hardware OK)

Connecting to WiFi................ Connected! IP: 10.0.1.15
Connecting to MQTT broker (host.wokwi.internal:1883)... Connected!

System ready! Monitoring DHT22 every 5s & PIR motion events...

[EVENT] 🚨 Motion Detected! Triggering Relay & Red LED alert...
[EVENT] 💡 Relay & Red LED latched ON (Motion Active)
[TELEMETRY] 5s Reading: {"temp": 28.4, "humidity": 65.2, "motion": true}
  ↳ Published to MQTT topic 'wokwi-weather'

[EVENT] 🟢 Motion Cleared. Relay & Red LED turned OFF
[TELEMETRY] 5s Reading: {"temp": 28.4, "humidity": 65.2, "motion": false}
  ↳ Published to MQTT topic 'wokwi-weather'
```

### 2. MQTT Subscriber Messages
```text
wokwi-motion {"event": "motion_detected", "relay": 1}
wokwi-weather {"temp": 28.4, "humidity": 65.2, "motion": true}
wokwi-motion {"event": "motion_cleared", "relay": 0}
wokwi-weather {"temp": 28.4, "humidity": 65.2, "motion": false}
```

---

## 📜 Deliverables Summary
- [x] **Monday Deliverable**: 4-Layer IoT Architecture & System Analysis ([`docs/architecture_diagram.md`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot%20Fundamentals/IOT-FUNDAMENTALS/docs/architecture_diagram.md))
- [x] **Tuesday Deliverable 1**: Multi-sensor circuit schematic with DHT22, PIR, Relay, and LED ([`src/diagram.json`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot%20Fundamentals/IOT-FUNDAMENTALS/src/diagram.json))
- [x] **Tuesday Deliverable 2**: Responsive MicroPython firmware with 5s DHT22 loop, PIR motion event actuation, and boot self-test ([`src/main.py`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot%20Fundamentals/IOT-FUNDAMENTALS/src/main.py))
- [x] **Tuesday Deliverable 3**: Comprehensive Hardware Comparison & Selection Matrix ([`docs/hardware_comparison_notes.md`](file:///c:/Users/loalo/OneDrive/Documents/cognusops/Week%201/Iot%20Fundamentals/IOT-FUNDAMENTALS/docs/hardware_comparison_notes.md))
- [x] **Tuesday Deliverable 4**: GitHub PR tracking feature branch `feat/week-1-sensor-to-mqtt` with stand-up update text.
