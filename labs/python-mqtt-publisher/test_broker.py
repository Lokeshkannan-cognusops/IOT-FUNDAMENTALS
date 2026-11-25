"""
CognusOps AI Track Internship — Week 1 Wednesday Lab
Broker Smoke Test: Verifies local Eclipse Mosquitto broker connectivity using paho-mqtt.
"""

import time
import json
import sys
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC       = "plant/room-1/test"
PAYLOAD     = "broker_ok"

connected = False
published = False

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        connected = True
        print(f"[SUCCESS] Connected to local Mosquitto broker at {BROKER_HOST}:{BROKER_PORT}")
        print(f"  ↳ Publishing test message to topic '{TOPIC}'...")
        res = client.publish(TOPIC, PAYLOAD)
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"  ↳ Successfully queued publish: '{PAYLOAD}'")
        else:
            print(f"  ↳ Publish failed with code {res.rc}")
    else:
        print(f"[ERROR] Connection failed with result code {rc}")

def on_publish(client, userdata, mid, *args):
    global published
    published = True
    print(f"[CONFIRMED] Message mid={mid} delivered to broker.")

# Create MQTT client (compatible with paho-mqtt 2.x and 1.x)
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python-smoke-tester")
except AttributeError:
    client = mqtt.Client(client_id="python-smoke-tester")

client.on_connect = on_connect
client.on_publish = on_publish

print("==================================================")
print("  CognusOps AI Track — Local MQTT Broker Smoke Test")
print("==================================================")
print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}...")

try:
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    
    # Wait for connect & publish
    timeout = 5
    start = time.time()
    while not published and (time.time() - start) < timeout:
        time.sleep(0.1)
        
    client.loop_stop()
    client.disconnect()
    
    if connected:
        print("\n[RESULT] ✅ Smoke test PASSED: Mosquitto is active and accepting MQTT traffic!")
        sys.exit(0)
    else:
        print("\n[RESULT] ❌ Smoke test FAILED: Could not connect to broker.")
        sys.exit(1)
        
except Exception as e:
    print(f"\n[EXCEPTION] Failed to connect: {e}")
    sys.exit(1)
