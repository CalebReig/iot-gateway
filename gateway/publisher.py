import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from sense_hat import SenseHat

BROKER_HOST = "localhost"
BROKER_PORT = 1883

GATEWAY_NAME = "gateway01"
BASE_TOPIC = f"sensors/pi/{GATEWAY_NAME}"

PUBLISH_INTERVAL_SEC = 5

sense = SenseHat()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_cpu_temp_c() -> float:
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        return round(int(f.read().strip()) / 1000.0, 2)


def build_payload(sensor: str, value: float):
    return {
        "source": "pi",
        "device": GATEWAY_NAME,
        "sensor": sensor,
        "value": value,
        "ts": now_iso(),
    }


def publish_one(client: mqtt.Client, sensor: str, value: float):
    topic = f"{BASE_TOPIC}/{sensor}"
    payload = json.dumps(build_payload(sensor, value))
    client.publish(topic, payload, qos=0, retain=True)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    while True:
        # Sense HAT sensors
        temp_c = round(sense.get_temperature(), 2)
        humidity = round(sense.get_humidity(), 2)
        pressure_mbar = round(sense.get_pressure(), 2)

        publish_one(client, "temperature_c", temp_c)
        publish_one(client, "humidity_pct", humidity)
        publish_one(client, "pressure_mbar", pressure_mbar)
        publish_one(client, "cpu_temp_c", read_cpu_temp_c())
        
        print(f"T:{temp_c}; H:{humidity}; P:{pressure_mbar}; CPU_T:{read_cpu_temp_c()};")

        time.sleep(PUBLISH_INTERVAL_SEC)


if __name__ == "__main__":
    main()
