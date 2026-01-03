BROKER_HOST = "localhost"
BROKER_PORT = 1883

GATEWAY_NAME = "gateway01"
BASE_TOPIC = f"sensors/pi/{GATEWAY_NAME}"
TOPIC_FILTER = "sensors/#"

PUBLISH_INTERVAL_SEC = 5

ENABLE_DB = True
DB_PATH = "data/telemetry.sqlite3"
