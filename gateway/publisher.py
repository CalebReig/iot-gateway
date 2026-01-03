import json

import paho.mqtt.client as mqtt

from gateway.constants import BROKER_HOST, BROKER_PORT, BASE_TOPIC
from gateway.utils import Util, Sensor


class Publisher:
    def __init__(self, device_name: str, device_source: str, sensors: list[Sensor]):
        self.device_name = device_name
        self.device_source = device_source
        self.sensors = sensors

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.mqtt_client.loop_start()

    def _read_sensors(self) -> dict[str, float]:
        sensor_readings = {}
        for sensor in self.sensors:
            sensor_value = sensor.read()
            if sensor.is_current_new_value():
                sensor_readings[f"{sensor.name}_{sensor.unit}"] = sensor_value
        return sensor_readings

    def publish_sensor_data(self):
        now_utc = Util.now_iso()
        sensor_readings = self._read_sensors()
        for sensor_name, sensor_val in sensor_readings.items():
            topic = f"{BASE_TOPIC}/{sensor_name}"
            payload = json.dumps(
                {
                    "source": self.device_source,
                    "device": self.device_name,
                    "sensor": sensor_name,
                    "value": sensor_val,
                    "ts": now_utc,
                }
            )
            self.mqtt_client.publish(topic, payload, qos=0, retain=True)
            print(f"{sensor_name} | {sensor_val} | {now_utc}")
