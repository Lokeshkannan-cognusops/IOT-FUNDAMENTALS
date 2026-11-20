## CognusOps AI Track Internship — Lab Submission

### Lab Information
- **Week**: Week 1 · IoT Fundamentals
- **Topic**: Sensor-to-MQTT Publisher with MicroPython & Wokwi
- **Intern Name**: Lokeshkannan U

---

### Description & Objectives Completed
- [x] Simulated an ESP32 microcontroller with a DHT22 temperature and humidity sensor in Wokwi.
- [x] Developed MicroPython firmware (`main.py`) reading sensor telemetry on GPIO 15.
- [x] Implemented JSON payload formatting and delta-reporting (deadband filter) to optimize network bandwidth.
- [x] Configured and verified local Mosquitto MQTT broker (`0.0.0.0:1883`) and subscription feed (`wokwi-weather`).
- [x] Documented complete 4-layer IoT architecture and data flow in `docs/architecture_diagram.md`.

---

### Testing & Verification
- **Wi-Fi Connectivity**: Simulated ESP32 successfully connected to `Wokwi-GUEST`.
- **MQTT Connectivity**: Handshake with local Mosquitto broker verified over TCP.
- **Telemetry Verification**:
  ```text
  Connecting to WiFi....... Connected!
  Connecting to MQTT server host.wokwi.internal:1883... Connected!
  Measuring weather conditions... Updated!
  Reporting to MQTT topic wokwi-weather: {"temp": 24.0, "humidity": 40.0}
  ```
- **Subscriber Output**: Verified live incoming messages in `mosquitto_sub`:
  ```text
  wokwi-weather {"temp": 24.0, "humidity": 40.0}
  ```

---

### Deliverables Included
1. `src/main.py`: MicroPython firmware source code.
2. `src/diagram.json`: Circuit schematic & pin connection definitions for Wokwi.
3. `src/wokwi.toml`: Simulator configuration.
4. `src/mosquitto.conf`: Mosquitto broker configuration.
5. `docs/architecture_diagram.md`: 1-page architecture diagram and use-case breakdown.
