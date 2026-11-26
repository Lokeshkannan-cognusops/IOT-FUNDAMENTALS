"""
CognusOps AI Track Internship — Week 1 Thursday Lab
10-Sensor Fleet Simulator & QoS 0 vs QoS 1 Empirical Benchmark

Simulates 10 distinct room sensor nodes (room-01 to room-10) with:
1. Realistic physical baseline variation across rooms.
2. Gaussian measurement noise (DHT22 sensor emulation).
3. Diurnal environmental drift.
4. Stochastic 5% thermal spike / HVAC failure anomaly injection.
5. Comparative benchmarking of QoS 0 vs QoS 1 round-trip performance.
"""

import time
import json
import math
import random
import signal
import sys
import argparse
from typing import Dict, List, Tuple
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
PLANT_NAME  = "lokeshkannan"

running = True

def signal_handler(sig, frame):
    global running
    print("\n[STOP] Received interrupt signal. Stopping fleet...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class SimulatedSensorNode:
    """Represents a virtual room sensor node with physical temperature/humidity modeling."""
    def __init__(self, room_num: int):
        self.room_id = f"room-{room_num:02d}"
        self.device_id = f"fleet-sensor-{self.room_id}"
        self.topic = f"plant/{PLANT_NAME}/{self.room_id}/env"
        
        # Each room has a unique base climate profile
        self.base_temp = 20.0 + (room_num * 0.6)      # 20.6°C to 26.0°C
        self.base_humidity = 48.0 + (room_num * 1.5)  # 49.5% to 63.0%
        self.phase_offset = (room_num * math.pi) / 5.0
        self.seq = 0

    def read_telemetry(self, t_current: float) -> Tuple[Dict, bool]:
        """Generates realistic sensor reading with drift, Gaussian noise, and stochastic spikes."""
        self.seq += 1
        
        # 1. Diurnal thermal drift (slow sinus oscillation)
        drift = 1.2 * math.sin((2 * math.pi * (t_current % 300) / 300) + self.phase_offset)
        
        # 2. Gaussian sensor noise: N(0, sigma^2)
        noise_temp = random.gauss(0, 0.25)
        noise_hum  = random.gauss(0, 0.50)
        
        # 3. Stochastic anomaly injection: 5% probability of thermal runaway / HVAC fault
        is_spike = random.random() < 0.05
        spike_offset = random.uniform(6.5, 12.0) if is_spike else 0.0
        status_flag = "ANOMALY_HEAT_SPIKE" if is_spike else "NORMAL"

        temp = round(self.base_temp + drift + noise_temp + spike_offset, 2)
        hum  = round(max(20.0, min(95.0, self.base_humidity - (drift * 0.5) + noise_hum)), 2)

        payload = {
            "timestamp": int(t_current),
            "device_id": self.device_id,
            "plant": PLANT_NAME,
            "room": self.room_id,
            "seq": self.seq,
            "temperature": temp,
            "humidity": hum,
            "motion": is_spike, # Correlated motion if personnel present during spike
            "status": status_flag
        }
        return payload, is_spike


class FleetManager:
    """Orchestrates the 10-node fleet and benchmarks QoS 0 vs QoS 1."""
    def __init__(self, broker: str = BROKER_HOST, port: int = BROKER_PORT):
        self.broker = broker
        self.port = port
        self.nodes = [SimulatedSensorNode(i) for i in range(1, 11)]
        
        # Timing and latency metrics for benchmark
        self.pending_pubacks: Dict[int, float] = {}
        self.latencies_ms: List[float] = []
        self.published_count = 0
        self.puback_count = 0

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fleet-orchestrator")
        except AttributeError:
            self.client = mqtt.Client(client_id="fleet-orchestrator")

        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[CONNECTED] Fleet orchestrator connected to {self.broker}:{self.port}")
        else:
            print(f"[ERROR] Connection failed with code {rc}")

    def on_publish(self, client, userdata, mid, *args):
        t_recv = time.perf_counter()
        self.puback_count += 1
        if mid in self.pending_pubacks:
            t_sent = self.pending_pubacks.pop(mid)
            rtt_ms = (t_recv - t_sent) * 1000.0
            self.latencies_ms.append(rtt_ms)

    def start(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()
        time.sleep(1)

    def stop(self):
        time.sleep(0.5)
        self.client.loop_stop()
        self.client.disconnect()

    def run_continuous(self, interval: float = 5.0, qos: int = 1, duration: int = 0):
        """Runs the 10 simulated sensor fleet streaming data concurrently."""
        print("==================================================")
        print("  CognusOps AI Track — 10-Device Fleet Simulator  ")
        print(f"  Target Broker: {self.broker}:{self.port} | Interval: {interval}s | QoS: {qos}")
        print("  Nodes: room-01 through room-10 (Gaussian Noise + 5% Anomaly Spikes)")
        print("==================================================")
        
        start_time = time.time()
        cycle = 0

        while running:
            cycle += 1
            now = time.time()
            print(f"\n--- [FLEET CYCLE #{cycle}] Timestamp: {int(now)} | Dispatched 10 Node Telemetries ---")
            
            anomalies_detected = 0
            for node in self.nodes:
                payload, is_spike = node.read_telemetry(now)
                payload["qos"] = qos
                payload_json = json.dumps(payload)
                
                # Highlight spikes in console
                if is_spike:
                    anomalies_detected += 1
                    print(f"  🚨 [{node.room_id}] SPIKE: Temp={payload['temperature']}°C (Status: {payload['status']})")
                else:
                    print(f"  ✓ [{node.room_id}] Temp={payload['temperature']:5.2f}°C, Hum={payload['humidity']:5.2f}%")
                
                self.client.publish(node.topic, payload_json, qos=qos)
            
            if anomalies_detected > 0:
                print(f"  ↳ Warning: {anomalies_detected} thermal anomaly spike(s) triggered in cycle #{cycle}")

            if duration > 0 and (time.time() - start_time) >= duration:
                print(f"\n[DONE] Specified duration of {duration} seconds reached.")
                break

            sleep_slices = int(interval / 0.1)
            for _ in range(sleep_slices):
                if not running:
                    break
                time.sleep(0.1)

    def benchmark_qos(self, test_packets_per_level: int = 50):
        """Runs empirical benchmark comparing QoS 0 vs QoS 1 performance."""
        print("==================================================")
        print("  Empirical MQTT Benchmark: QoS 0 vs QoS 1        ")
        print(f"  Dispatches: {test_packets_per_level} packets per QoS tier across fleet")
        print("==================================================")

        results = {}

        # ----------------- TEST QOS 0 -----------------
        print(f"\n[PHASE 1] Executing QoS 0 (At Most Once / Fire-and-Forget)...")
        qos0_start = time.perf_counter()
        for i in range(test_packets_per_level):
            node = self.nodes[i % len(self.nodes)]
            payload, _ = node.read_telemetry(time.time())
            payload["qos_benchmark"] = 0
            self.client.publish(node.topic, json.dumps(payload), qos=0)
        qos0_duration = (time.perf_counter() - qos0_start) * 1000.0
        
        results["QoS 0"] = {
            "dispatched": test_packets_per_level,
            "acks_received": 0, # QoS 0 has no protocol ACKs
            "total_time_ms": qos0_duration,
            "avg_latency_ms": 0.0, # Zero protocol handshake delay
            "max_latency_ms": 0.0,
            "loss_protection": "None (Fire & Forget)",
            "duplicate_risk": "0% (No retransmission)"
        }
        print(f"  ✓ Dispatched {test_packets_per_level} packets at QoS 0 in {qos0_duration:.2f} ms")

        time.sleep(1.0) # Drain sockets

        # ----------------- TEST QOS 1 -----------------
        print(f"\n[PHASE 2] Executing QoS 1 (At Least Once / Handshake Acknowledged)...")
        self.pending_pubacks.clear()
        self.latencies_ms.clear()
        self.puback_count = 0
        
        qos1_start = time.perf_counter()
        for i in range(test_packets_per_level):
            node = self.nodes[i % len(self.nodes)]
            payload, _ = node.read_telemetry(time.time())
            payload["qos_benchmark"] = 1
            t_send = time.perf_counter()
            msg_info = self.client.publish(node.topic, json.dumps(payload), qos=1)
            self.pending_pubacks[msg_info.mid] = t_send
        
        # Wait for all PUBACKs to arrive (timeout 5s)
        timeout_start = time.time()
        while len(self.pending_pubacks) > 0 and (time.time() - timeout_start) < 5.0:
            time.sleep(0.01)

        qos1_duration = (time.perf_counter() - qos1_start) * 1000.0
        avg_lat = sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0
        max_lat = max(self.latencies_ms) if self.latencies_ms else 0.0
        min_lat = min(self.latencies_ms) if self.latencies_ms else 0.0

        results["QoS 1"] = {
            "dispatched": test_packets_per_level,
            "acks_received": self.puback_count,
            "total_time_ms": qos1_duration,
            "avg_latency_ms": avg_lat,
            "min_latency_ms": min_lat,
            "max_latency_ms": max_lat,
            "loss_protection": "Guaranteed (PUBACK Handshake)",
            "duplicate_risk": "Possible on retransmission timeout"
        }
        print(f"  ✓ Confirmed {self.puback_count}/{test_packets_per_level} PUBACKs in {qos1_duration:.2f} ms")
        print(f"    ↳ Avg RTT: {avg_lat:.2f} ms | Min RTT: {min_lat:.2f} ms | Max RTT: {max_lat:.2f} ms")

        # ----------------- SUMMARY COMPARISON -----------------
        print("\n" + "="*80)
        print("  📊 EMPIRICAL COMPARISON REPORT: MQTT QoS 0 vs QoS 1")
        print("="*80)
        print(f"{'Metric':<30} | {'QoS 0 (Fire & Forget)':<22} | {'QoS 1 (At Least Once)':<22}")
        print("-" * 80)
        print(f"{'Packets Dispatched':<30} | {results['QoS 0']['dispatched']:<22} | {results['QoS 1']['dispatched']:<22}")
        print(f"{'PUBACK Confirmations':<30} | {results['QoS 0']['acks_received']:<22} | {results['QoS 1']['acks_received']:<22}")
        print(f"{'Acknowledgment Rate':<30} | {'N/A (No ACKs in QoS 0)':<22} | {100.0 * results['QoS 1']['acks_received']/test_packets_per_level:<6.1f}%")
        print(f"{'Total Dispatch Time':<30} | {results['QoS 0']['total_time_ms']:<19.2f} ms | {results['QoS 1']['total_time_ms']:<19.2f} ms")
        print(f"{'Avg Round-Trip Latency (RTT)':<30} | {'~0.00 ms (Socket TX)':<22} | {results['QoS 1']['avg_latency_ms']:<19.2f} ms")
        print(f"{'Max Peak Latency':<30} | {'~0.00 ms':<22} | {results['QoS 1']['max_latency_ms']:<19.2f} ms")
        print(f"{'Delivery Guarantee':<30} | {results['QoS 0']['loss_protection']:<22} | {results['QoS 1']['loss_protection']:<22}")
        print(f"{'Duplicate Message Risk':<30} | {results['QoS 0']['duplicate_risk']:<22} | {results['QoS 1']['duplicate_risk']:<22}")
        print("="*80)

        return results


def main():
    parser = argparse.ArgumentParser(description="10-Sensor Simulated Fleet & QoS Benchmark")
    parser.add_argument("--mode", choices=["continuous", "benchmark"], default="continuous", 
                        help="Execution mode: continuous simulation or empirical benchmark")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval between fleet cycles (default: 5.0s)")
    parser.add_argument("--duration", type=int, default=0, help="Run duration in seconds (0 for infinite)")
    parser.add_argument("--qos", type=int, choices=[0, 1], default=1, help="QoS level for continuous mode (default: 1)")
    parser.add_argument("--packets", type=int, default=50, help="Packets per level for benchmark mode (default: 50)")
    args = parser.parse_args()

    fleet = FleetManager(BROKER_HOST, BROKER_PORT)
    fleet.start()

    try:
        if args.mode == "benchmark":
            fleet.benchmark_qos(test_packets_per_level=args.packets)
        else:
            fleet.run_continuous(interval=args.interval, qos=args.qos, duration=args.duration)
    finally:
        fleet.stop()

if __name__ == "__main__":
    main()
