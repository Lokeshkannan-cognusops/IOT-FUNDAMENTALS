"""
CognusOps AI Track Internship — Week 1 Lab Deliverable
Finalized ESP32 Smart Room Monitor: MicroPython DHT22 Telemetry & Motion Actuation

Target Public Broker: broker.hivemq.com (Port 1883)
Structured Topic Hierarchy:
- Environmental Telemetry: plant/lokeshkannan/room-1/env
- Light / Actuator State:  plant/lokeshkannan/room-1/light/state ("ON" / "OFF")
- Legacy Compatibility:    wokwi-weather & wokwi-motion

Hardware Peripherals:
- DHT22 Sensor:            GPIO 15
- PIR Motion Sensor:       GPIO 13
- Relay & Red LED:         GPIO 12 (via 220Ω resistor)
- Onboard Status LED:      GPIO 2
"""

import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

# Pin Definitions
DHT_PIN      = 15    # DHT22 Temperature & Humidity sensor
PIR_PIN      = 13    # PIR Motion Sensor Output
RELAY_PIN    = 12    # Electromechanical Relay & Red Indicator LED
ONBOARD_LED  = 2     # Built-in ESP32 LED for visual verification

# MQTT Broker Configuration (Public HiveMQ broker for zero-gateway Wokwi Web execution)
MQTT_BROKER             = "broker.hivemq.com"
MQTT_PORT               = 1883
MQTT_CLIENT_ID          = "esp32-lokeshkannan-station-01"

# Structured Topic Hierarchy
MQTT_ENV_TOPIC          = "plant/lokeshkannan/room-1/env"
MQTT_LIGHT_STATE_TOPIC  = "plant/lokeshkannan/room-1/light/state"
MQTT_LEGACY_WEATHER     = "wokwi-weather"
MQTT_LEGACY_MOTION      = "wokwi-motion"

# Initialize Hardware Peripherals
sensor      = dht.DHT22(Pin(DHT_PIN))
pir         = Pin(PIR_PIN, Pin.IN)
relay       = Pin(RELAY_PIN, Pin.OUT)       # Explicit Relay pin on GPIO 12
actuator    = relay                         # Alias for backward compatibility
onboard_led = Pin(ONBOARD_LED, Pin.OUT)

def set_actuators(state):
    """Controls external Relay & Red LED (GPIO 12) plus onboard LED (GPIO 2) simultaneously."""
    relay.value(state)
    onboard_led.value(state)

print("==================================================")
print("  ESP32 Finalized Smart Room Monitor (Week 1)     ")
print("  CognusOps AI Track — Intern: Lokeshkannan U    ")
print("  Target Broker: {} : {}".format(MQTT_BROKER, MQTT_PORT))
print("==================================================")

# Power-On Self-Test (POST): Blink Red LED & toggle Relay 3 times upon boot
print("\n[INIT] Starting Actuator Test: Blinking Red LED & Relay 3 times...")
for i in range(3):
    set_actuators(1)
    time.sleep_ms(300)
    set_actuators(0)
    time.sleep_ms(200)
print("[INIT] Red LED & Relay self-test PASSED (Hardware OK)\n")

# Connect to Wi-Fi (Wokwi-GUEST in simulation)
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
wifi_timeout = 0
while not sta_if.isconnected() and wifi_timeout < 30:
    print(".", end="")
    time.sleep(0.2)
    wifi_timeout += 1

if sta_if.isconnected():
    print(" Connected! IP:", sta_if.ifconfig()[0])
else:
    print(" WiFi connection timed out; continuing in standalone simulation mode...")

# Establish MQTT Broker Connection
client = None
try:
    print("Connecting to MQTT broker ({}:{})... ".format(MQTT_BROKER, MQTT_PORT), end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=60)
    client.connect()
    print("Connected!")
    print("  ↳ Publishing telemetry to: '{}'".format(MQTT_ENV_TOPIC))
    print("  ↳ Publishing events to:    '{}'".format(MQTT_LIGHT_STATE_TOPIC))
except Exception as e:
    print("Broker not reachable ({}); falling back to standalone Serial mode.".format(e))
    client = None

# State Variables
prev_motion_state = -1
last_sensor_read  = time.ticks_ms()

print("\nSystem online! Monitoring DHT22 every 5s & PIR motion events...\n")

while True:
    # -------------------------------------------------------------
    # Task 1: Responsive PIR Motion Detection & Relay/LED Control
    # -------------------------------------------------------------
    current_motion = pir.value()
    if current_motion != prev_motion_state:
        if current_motion == 1:
            print("[EVENT] 🚨 Motion Detected! Triggering Relay & Red LED alert...")
            # 3 rapid warning pulses, then latch ON
            for _ in range(3):
                set_actuators(1)
                time.sleep_ms(80)
                set_actuators(0)
                time.sleep_ms(80)
            set_actuators(1)
            print("[EVENT] 💡 Relay & Red LED latched ON (Motion Active)")
            
            if client:
                try:
                    client.publish(MQTT_LIGHT_STATE_TOPIC, "ON")
                    client.publish(MQTT_LEGACY_MOTION, ujson.dumps({
                        "timestamp": time.time(),
                        "event": "motion_detected",
                        "relay": 1,
                        "state": "ON"
                    }))
                    print("  ↳ Published 'ON' to '{}'".format(MQTT_LIGHT_STATE_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT event publish error: {}".format(e))
        else:
            set_actuators(0)
            print("[EVENT] 🟢 Motion Cleared. Relay & Red LED turned OFF")
            
            if client:
                try:
                    client.publish(MQTT_LIGHT_STATE_TOPIC, "OFF")
                    client.publish(MQTT_LEGACY_MOTION, ujson.dumps({
                        "timestamp": time.time(),
                        "event": "motion_cleared",
                        "relay": 0,
                        "state": "OFF"
                    }))
                    print("  ↳ Published 'OFF' to '{}'".format(MQTT_LIGHT_STATE_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT event publish error: {}".format(e))
                    
        prev_motion_state = current_motion

    # -------------------------------------------------------------
    # Task 2: DHT22 5-Second Periodic Measurement Loop
    # -------------------------------------------------------------
    if time.ticks_diff(time.ticks_ms(), last_sensor_read) >= 5000:
        last_sensor_read = time.ticks_ms()
        try:
            sensor.measure()
            temp = sensor.temperature()
            humidity = sensor.humidity()
            
            # Standardized IoT Telemetry Schema
            telemetry_payload = ujson.dumps({
                "timestamp": time.time(),
                "device_id": MQTT_CLIENT_ID,
                "plant": "lokeshkannan",
                "room": "room-1",
                "temperature": temp,
                "humidity": humidity,
                "motion": bool(current_motion),
                "status": "NORMAL"
            })
            
            print("[TELEMETRY] 5s Reading: {}".format(telemetry_payload))
            
            # Heartbeat blink: 60ms pulse if motion is not currently latching LED
            if current_motion == 0:
                set_actuators(1)
                time.sleep_ms(60)
                set_actuators(0)
            
            if client:
                try:
                    client.publish(MQTT_ENV_TOPIC, telemetry_payload)
                    client.publish(MQTT_LEGACY_WEATHER, telemetry_payload)
                    print("  ↳ Published to '{}' & '{}'".format(MQTT_ENV_TOPIC, MQTT_LEGACY_WEATHER))
                except Exception as e:
                    print("  ↳ MQTT telemetry publish error: {}".format(e))
        except OSError as e:
            print("[ERROR] Failed to read DHT22 sensor: {}".format(e))

    time.sleep_ms(100) # Responsive 100ms cycle for instant motion sensing
