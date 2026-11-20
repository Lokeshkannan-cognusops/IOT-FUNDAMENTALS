"""
MicroPython IoT Weather Station for Wokwi with Local Mosquitto Broker (Scenario B)

To view data on your local computer:
1. Start Mosquitto with listener enabled:
     mosquitto -v -c mosquitto.conf
2. Start Wokwi IoT Gateway / Wokwi Bridge (host IP is 10.0.1.2)
3. In a new terminal on your laptop, subscribe to the topic:
     mosquitto_sub -h localhost -t "wokwi-weather" -v

Now click on the DHT22 sensor in the simulation,
change the temperature/humidity, and you will see
the messages published to your local Mosquitto broker!
"""

import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

# MQTT Server Parameters (Scenario B: Local Mosquitto via Wokwi IoT Gateway)
MQTT_CLIENT_ID = "micropython-weather-demo"
# When using Wokwi IoT Gateway in VS Code, use "host.wokwi.internal" to reach your laptop:
MQTT_BROKER    = "host.wokwi.internal"
MQTT_PORT      = 1883         # Default Mosquitto port
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "wokwi-weather"

sensor = dht.DHT22(Pin(15))

print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
  print(".", end="")
  time.sleep(0.1)
print(" Connected!")

print("Connecting to MQTT server {}:{}... ".format(MQTT_BROKER, MQTT_PORT), end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()

print("Connected!")

prev_weather = ""
while True:
  print("Measuring weather conditions... ", end="")
  try:
    sensor.measure() 
    message = ujson.dumps({
      "temp": sensor.temperature(),
      "humidity": sensor.humidity(),
    })
    if message != prev_weather:
      print("Updated!")
      print("Reporting to MQTT topic {}: {}".format(MQTT_TOPIC, message))
      client.publish(MQTT_TOPIC, message)
      prev_weather = message
    else:
      print("No change")
  except OSError as e:
    print("Sensor read error: {}".format(e))
  time.sleep(5)

