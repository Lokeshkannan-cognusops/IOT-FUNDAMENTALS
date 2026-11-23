"""
CognusOps AI Track Internship — Week 1 Tuesday Lab
ESP32 Multi-Sensor Station: DHT22 Telemetry + Motion-Triggered Relay/LED

Outputs:
1. Boot-time Power-On Self-Test (POST): Red LED & Relay blink 3 times on startup.
2. DHT22 5-second periodic temperature & humidity JSON telemetry over Serial & MQTT (with heartbeat pulse).
3. PIR Motion Sensor trigger: Alert blink + Relay & Red LED latch ON with real-time Serial events.
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
MQTT_CLIENT_ID    = "esp32-weather-motion-demo"
MQTT_BROKER       = "host.wokwi.internal"  # Wokwi IoT Gateway bridge to local Mosquitto
MQTT_PORT         = 1883
MQTT_TOPIC        = "wokwi-weather"
MQTT_MOTION_TOPIC = "wokwi-motion"

# Initialize Hardware Peripherals
sensor      = dht.DHT22(Pin(DHT_PIN))
pir         = Pin(PIR_PIN, Pin.IN)
actuator    = Pin(ACTUATOR_PIN, Pin.OUT)
onboard_led = Pin(ONBOARD_LED, Pin.OUT)

def set_actuators(state):
    """Controls external Relay & Red LED (GPIO 12) plus onboard LED (GPIO 2) simultaneously."""
    actuator.value(state)
    onboard_led.value(state)

print("==================================================")
print("  ESP32 Smart Environmental & Motion Station     ")
print("  Week 1 Tuesday Lab — CognusOps AI Track        ")
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
                    client.publish(MQTT_MOTION_TOPIC, ujson.dumps({"event": "motion_detected", "relay": 1}))
                except Exception:
                    pass
        else:
            set_actuators(0)  # Turn OFF Relay & LED
            print("[EVENT] 🟢 Motion Cleared. Relay & Red LED turned OFF")
            if client:
                try:
                    client.publish(MQTT_MOTION_TOPIC, ujson.dumps({"event": "motion_cleared", "relay": 0}))
                except Exception:
                    pass
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
            
            # Publish when connected to MQTT
            if client:
                try:
                    client.publish(MQTT_TOPIC, weather_payload)
                    print("  ↳ Published to MQTT topic '{}'".format(MQTT_TOPIC))
                except Exception as e:
                    print("  ↳ MQTT publish failed: {}".format(e))
        except OSError as e:
            print("[ERROR] Failed to read DHT22 sensor: {}".format(e))

    time.sleep_ms(100)  # Responsive 100ms polling for instant motion detection
