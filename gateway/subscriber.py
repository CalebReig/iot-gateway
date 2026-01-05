import json

import paho.mqtt.client as mqtt

from gateway.constants import BROKER_HOST, BROKER_PORT, TOPIC_FILTER
from gateway.models import Telemetry
from gateway.utils import DateUtil
from gateway.utils.database import DataBase


class Subscriber:
    def __init__(
        self, db: DataBase, enable_db_writes: bool = True, mqtt_host: str = BROKER_HOST
    ):
        self.enable_db_writes = enable_db_writes
        self.db = db

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.connect(mqtt_host, BROKER_PORT, keepalive=60)

    def start(self) -> None:
        try:
            self.mqtt_client.loop_forever()
        finally:
            if self.db:
                self.db.close()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[mqtt] connected reason_code={reason_code} subscribing={TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER)

    def _on_message(self, client, userdata, msg):
        recieved_ts = DateUtil.now_iso()
        raw_msg = msg.payload.decode(errors="replace")
        try:
            payload = json.loads(raw_msg)
            telemetry = Telemetry.from_payload(payload)
        except Exception as e:
            print(f"[{recieved_ts}] [drop] topic={msg.topic} err={e} raw={raw_msg}")
            return

        print(f"[{recieved_ts}] {msg.topic} -> {telemetry}")

        if not self.enable_db_writes:
            return
        try:
            self.db.write_telemetry(telemetry)
        except Exception as e:
            print(f"[{recieved_ts}] [db] write failed err={e}")
