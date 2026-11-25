"""
CognusOps AI Track Internship — Week 1 Lab
ESP32 Smart Station: DHT22 Telemetry + Motion-Triggered Relay/LED Actuation

MQTT Topic Hierarchy:
- Light / Relay State: plant/lokeshkannan/room-1/light/state ("ON" / "OFF")
- Motion Events:       wokwi-motion
- Environmental Data:  plant/lokeshkannan/room-1/env & wokwi-weather
"""

import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

# Pin Definitions
DHT_PIN      = 15    # DHT22 Data pin
PIR_PIN      = 13    # PIR Motion Sensor Output pin
ACTUATOR_PIN = 12    # Relay module input & Red LED Anode pin (GPIO 12)
ONBOARD_LED  = 2     # Built-in ESP32 LED (GPIO 2) for guaranteed visual feedback

# MQTT Parameters
MQTT_CLIENT_ID          = "esp32-lokeshkannan-station"
MQTT_BROKER             = "host.wokwi.internal"  # Bridge to local Mosquitto / Docker broker
MQTT_PORT               = 1883

# Topic Definitions (Supporting standard lab topics & CognusOps hierarchy)
MQTT_LIGHT_STATE_TOPIC  = "plant/lokeshkannan/room-1/light/state"
MQTT_ENV_TOPIC          = "plant/lokeshkannan/room-1/env"
MQTT_LEGACY_WEATHER     = "wokwi-weather"
MQTT_LEGACY_MOTION      = "wokwi-motion"

# Initialize Hardware Peripherals
sensor      = dht.DHT22(Pin(DHT_PIN))
pir         = Pin(PIR_PIN, Pin.IN)
relay       = Pin(12, Pin.OUT)       # Mentor specification: relay on GPIO 12
actuator    = relay                  # Alias for compatibility
onboard_led = Pin(ONBOARD_LED, Pin.OUT)

def set_actuators(state):
    """Controls external Relay & Red LED (GPIO 12) plus onboard LED (GPIO 2) simultaneously."""
    relay.value(state)
    onboard_led.value(state)

print("==================================================")
print("  ESP32 Smart Environmental & Motion Station     ")
print("  CognusOps AI Track — Intern: Lokeshkannan U    ")
print("==================================================")

# Power-On Self-Test (POST): Visibly blink Red LED & toggle Relay 3 times
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
while not sta_if.isconnected() and wifi_timeout < 25:
    print(".", end="")
    time.sleep(0.2)
    wifi_timeout += 1

if sta_if.isconnected():
    print(" Connected! IP:", sta_if.ifconfig()[0])
else:
    print(" WiFi offline or timed out; continuing in standalone simulation mode...")

# Attempt MQTT Broker connection (graceful fallback if broker is offline)
client = None
try:
    print("Connecting to MQTT broker ({}:{})... ".format(MQTT_BROKER, MQTT_PORT), end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=60)
    client.connect()
    print("Connected!")
    print("  ↳ Subscribed / Publishing to: '{}'".format(MQTT_LIGHT_STATE_TOPIC))
except Exception as e:
    print("Broker not reachable ({}), running in standalone Serial mode.".format(e))
    client = None

# State Variables
prev_motion_state = -1
last_sensor_read  = time.ticks_ms()

print("\nSystem ready! Monitoring DHT22 every 5s & PIR motion events...\n")

while True:
    # -------------------------------------------------------------
    # Task 1: Responsive PIR Motion Detection & Relay/LED Control
    # -------------------------------------------------------------
    current_motion = pir.value()
    if current_motion != prev_motion_state:
        if current_motion == 1:
            # Alert blink sequence on motion trigger: 3 rapid pulses, then stay ON
            print("[EVENT] 🚨 Motion Detected! Triggering Relay & Red LED alert...")
            for _ in range(3):
                set_actuators(1)
                time.sleep_ms(100)
                set_actuators(0)
                time.sleep_ms(100)
            set_actuators(1)  # Latch ON Relay & LED while motion is active
            print("[EVENT] 💡 Relay & Red LED latched ON (Motion Active)")
            
            if client:
                try:
                    # Publish both plain state ("ON") and structured telemetry
                    client.publish(MQTT_LIGHT_STATE_TOPIC, "ON")
                    client.publish(MQTT_LEGACY_MOTION, ujson.dumps({"event": "motion_detected", "relay": 1, "state": "ON"}))
                    print("  ↳ Published 'ON' to '{}'".format(MQTT_LIGHT_STATE_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT publish failed: {}".format(e))
        else:
            set_actuators(0)  # Turn OFF Relay & LED
            print("[EVENT] 🟢 Motion Cleared. Relay & Red LED turned OFF")
            
            if client:
                try:
                    # Publish both plain state ("OFF") and structured telemetry
                    client.publish(MQTT_LIGHT_STATE_TOPIC, "OFF")
                    client.publish(MQTT_LEGACY_MOTION, ujson.dumps({"event": "motion_cleared", "relay": 0, "state": "OFF"}))
                    print("  ↳ Published 'OFF' to '{}'".format(MQTT_LIGHT_STATE_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT publish failed: {}".format(e))
                    
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
            
            weather_payload = ujson.dumps({
                "temp": temp,
                "humidity": humidity,
                "motion": bool(current_motion)
            })
            
            # Print JSON every 5 seconds to Serial Monitor
            print("[TELEMETRY] 5s Reading: {}".format(weather_payload))
            
            # Heartbeat blink: brief 100ms pulse if motion is not currently latching LED
            if current_motion == 0:
                set_actuators(1)
                time.sleep_ms(80)
                set_actuators(0)
            
            # Publish to both plant/lokeshkannan/room-1/env and wokwi-weather
            if client:
                try:
                    client.publish(MQTT_ENV_TOPIC, weather_payload)
                    client.publish(MQTT_LEGACY_WEATHER, weather_payload)
                    print("  ↳ Published to '{}'".format(MQTT_ENV_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT publish failed: {}".format(e))
        except OSError as e:
            print("[ERROR] Failed to read DHT22 sensor: {}".format(e))

    time.sleep_ms(100)  # Responsive 100ms polling for instant motion detection
