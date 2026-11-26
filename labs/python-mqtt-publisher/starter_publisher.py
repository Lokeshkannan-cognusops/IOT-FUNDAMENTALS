"""
CognusOps AI Track Internship — Week 1 Thursday Lab
Starter MQTT Publisher: Streams room temperature & humidity JSON every 5 seconds with QoS=1.
"""

import time
import json
import sys
import random
import signal
import argparse
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC       = "plant/lokeshkannan/room-1/env"
CLIENT_ID   = "python-starter-room-1"

running = True
publish_count = 0
acknowledged_count = 0

def signal_handler(sig, frame):
    global running
    print("\n[STOP] Received shutdown signal. Disconnecting gracefully...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[SUCCESS] Connected to Mosquitto broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[ERROR] Connection failed with result code {rc}")

def on_publish(client, userdata, mid, *args):
    global acknowledged_count
    acknowledged_count += 1
    print(f"  [ACK CONFIRMED] PUBACK received from broker for message mid={mid} (Total ACKs: {acknowledged_count})")

def on_disconnect(client, userdata, *args):
    print("[INFO] Disconnected from MQTT broker.")

def main():
    global running, publish_count
    parser = argparse.ArgumentParser(description="Week 1 Starter MQTT Publisher (QoS 1)")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to publish (0 for infinite loop)")
    parser.add_argument("--interval", type=float, default=5.0, help="Publish interval in seconds (default: 5.0)")
    args = parser.parse_args()

    # Create MQTT client with Paho 2.x API compatibility
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    except AttributeError:
        client = mqtt.Client(client_id=CLIENT_ID)

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    print("==================================================")
    print("  CognusOps AI Track — Python Starter MQTT Publisher")
    print(f"  Target: {BROKER_HOST}:{BROKER_PORT} | Topic: {TOPIC} | QoS: 1")
    print("==================================================")
    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}...")

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[ERROR] Could not connect to broker: {e}")
        sys.exit(1)

    time.sleep(1) # Allow connection to establish

    base_temp = 24.0
    base_humidity = 55.0

    try:
        while running:
            publish_count += 1
            # Add small realistic sensor jitter
            temp = round(base_temp + random.uniform(-0.8, 0.8), 2)
            humidity = round(base_humidity + random.uniform(-2.0, 2.0), 2)
            
            payload = {
                "timestamp": int(time.time()),
                "device_id": CLIENT_ID,
                "plant": "lokeshkannan",
                "room": "room-1",
                "temperature": temp,
                "humidity": humidity,
                "motion": False,
                "qos": 1,
                "seq": publish_count
            }
            
            payload_json = json.dumps(payload)
            print(f"\n[PUBLISH #{publish_count}] Sending to '{TOPIC}' (QoS=1):")
            print(f"  Payload: {payload_json}")
            
            # Publish with QoS = 1
            msg_info = client.publish(TOPIC, payload_json, qos=1)
            if msg_info.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"  [ERROR] Failed to queue publish. Code: {msg_info.rc}")

            if args.count > 0 and publish_count >= args.count:
                print(f"\n[DONE] Reached target count of {args.count} messages.")
                break

            # Sleep in small slices to respond promptly to Ctrl+C
            sleep_slices = int(args.interval / 0.1)
            for _ in range(sleep_slices):
                if not running:
                    break
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[STOP] Keyboard interrupt received.")
    finally:
        # Give remaining ACKs time to process
        time.sleep(1.0)
        client.loop_stop()
        client.disconnect()
        print(f"\n[SUMMARY] Finished. Messages dispatched: {publish_count}, PUBACKs received: {acknowledged_count}")

if __name__ == "__main__":
    main()
