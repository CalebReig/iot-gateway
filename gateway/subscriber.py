import json
import os
import sqlite3
import time

import paho.mqtt.client as mqtt

from gateway.constants import BROKER_HOST, BROKER_PORT, TOPIC_FILTER, DB_PATH
from gateway.utils import Util


class Subscriber:
    def __init__(self, enable_db_writes: bool = True, db_path: str = DB_PATH):
        self.enable_db_writes = enable_db_writes
        self.db_path = db_path

        self.conn = self._get_db(self.db_path) if self.enable_db_writes else None
        self.cur = self.conn.cursor() if self.conn else None

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    def start(self) -> None:
        self.mqtt_client.loop_forever()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[mqtt] connected reason_code={reason_code} subscribing={TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER)

    def _on_message(self, client, userdata, msg):
        ts_local = time.strftime("%Y-%m-%d %H:%M:%S")
        received_ts = Util.now_iso()

        raw = msg.payload.decode(errors="replace")
        data = self._parse_payload(raw)

        print(f"[{ts_local}] {msg.topic} -> {raw}")

        if not self.enable_db_writes or not self.cur:
            return

        payload_ts = data.get("ts")
        device = data.get("device")
        sensor = data.get("sensor")
        value_real, value_text = self._extract_value_fields(data)

        self.cur.execute(
            """
            INSERT INTO telemetry
              (received_ts, topic, payload_ts, device, sensor, value_real, value_text, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                received_ts,
                msg.topic,
                payload_ts,
                device,
                sensor,
                value_real,
                value_text,
                raw,
            ),
        )

        self.conn.commit()

    def _get_db(self, db_path: str) -> sqlite3.Connection:
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_ts TEXT NOT NULL,
                topic TEXT NOT NULL,
                payload_ts TEXT,
                device TEXT,
                sensor TEXT,
                value_real REAL,
                value_text TEXT,
                raw_json TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON telemetry(received_ts);")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_topic_time ON telemetry(topic, received_ts);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_device_time ON telemetry(device, received_ts);"
        )
        conn.commit()
        return conn

    def _parse_payload(self, raw: str) -> dict:
        try:
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else {"value": obj}
        except json.JSONDecodeError:
            return {"value": raw}

    def _extract_value_fields(self, data: dict) -> tuple[float | None, str | None]:
        value = data.get("value")
        value_real: float | None = None
        value_text: str | None = None

        if isinstance(value, (int, float)):
            value_real = float(value)
        else:
            try:
                value_real = float(value)
            except (TypeError, ValueError):
                value_text = None if value is None else str(value)

        return value_real, value_text
