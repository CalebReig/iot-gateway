import json
import os
import sqlite3
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# MQTT
BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_FILTER = os.getenv("MQTT_TOPIC", "sensors/#")

# SQLite (set ENABLE_DB=0 to disable writing)
ENABLE_DB = os.getenv("ENABLE_DB", "1") == "1"
DB_PATH = os.getenv("DB_PATH", "data/telemetry.sqlite3")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def ensure_db(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_topic_time ON telemetry(topic, received_ts);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_device_time ON telemetry(device, received_ts);")
    conn.commit()
    return conn


def parse_payload(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # If publisher sends non-JSON, wrap it
        return {"value": raw}


def extract_value_fields(data: dict):
    value = data.get("value")
    value_real = None
    value_text = None

    if isinstance(value, (int, float)):
        value_real = float(value)
    else:
        try:
            value_real = float(value)
        except (TypeError, ValueError):
            value_text = None if value is None else str(value)

    return value_real, value_text


def main():
    conn = ensure_db(DB_PATH) if ENABLE_DB else None
    cur = conn.cursor() if conn else None

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"[mqtt] connected reason_code={reason_code} subscribing={TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER)

    def on_message(client, userdata, msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        received_ts = now_iso()

        raw = msg.payload.decode(errors="replace")
        data = parse_payload(raw)

        # Print for visibility
        print(f"[{ts}] {msg.topic} -> {raw}")

        if not ENABLE_DB:
            return

        payload_ts = data.get("ts")
        device = data.get("device")
        sensor = data.get("sensor")
        value_real, value_text = extract_value_fields(data)

        cur.execute(
            """
            INSERT INTO telemetry
              (received_ts, topic, payload_ts, device, sensor, value_real, value_text, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (received_ts, msg.topic, payload_ts, device, sensor, value_real, value_text, raw),
        )
        conn.commit()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
