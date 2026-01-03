import unittest
from unittest.mock import MagicMock, patch

from gateway.subscriber import Subscriber


class TestSubscriber(unittest.TestCase):
    @patch("gateway.subscriber.mqtt.Client")
    @patch("gateway.subscriber.Subscriber._get_db")
    def test_init_wires_mqtt_and_connects(self, mock_get_db, mock_mqtt_client_cls):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        sub = Subscriber(enable_db_writes=True, db_path=":memory:")

        mock_get_db.assert_called_once()
        mock_conn.cursor.assert_called_once()

        self.assertEqual(mock_client.on_connect, sub._on_connect)
        self.assertEqual(mock_client.on_message, sub._on_message)
        mock_client.connect.assert_called_once()
        mock_client.loop_forever.assert_not_called()

    @patch("gateway.subscriber.mqtt.Client")
    @patch("gateway.subscriber.Subscriber._get_db")
    def test_start_calls_loop_forever(self, mock_get_db, mock_mqtt_client_cls):
        mock_get_db.return_value = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        sub = Subscriber(enable_db_writes=True, db_path=":memory:")
        sub.start()

        mock_client.loop_forever.assert_called_once()

    def test_on_connect_subscribes(self):
        sub = Subscriber.__new__(Subscriber)
        mock_client = MagicMock()

        with patch("gateway.subscriber.TOPIC_FILTER", "sensors/#"):
            sub._on_connect(mock_client, None, None, 0, None)

        mock_client.subscribe.assert_called_once_with("sensors/#")

    @patch("gateway.subscriber.Util.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.subscriber.time.strftime", return_value="2026-01-02 04:34:56")
    def test_on_message_db_write_happy_path(self, mock_strftime, mock_now_iso):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = True
        sub.conn = MagicMock()
        sub.cur = MagicMock()

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"ts":"2026-01-02T12:34:00Z","device":"gw-1","sensor":"temperature_c","value":22.5}'

        sub._on_message(None, None, msg)

        sub.cur.execute.assert_called_once()
        args, _ = sub.cur.execute.call_args

        sql = args[0]
        params = args[1]

        self.assertIn("INSERT INTO telemetry", sql)
        self.assertEqual(params[0], "2026-01-02T12:34:56Z")
        self.assertEqual(params[1], "sensors/gw-1/temperature_c")
        self.assertEqual(params[2], "2026-01-02T12:34:00Z")
        self.assertEqual(params[3], "gw-1")
        self.assertEqual(params[4], "temperature_c")
        self.assertEqual(params[5], 22.5)
        self.assertIsNone(params[6])
        self.assertEqual(params[7], msg.payload.decode(errors="replace"))

        sub.conn.commit.assert_called_once()

    @patch("gateway.subscriber.Util.now_iso", return_value="2026-01-02T12:34:56Z")
    def test_on_message_db_write_disabled_does_not_write(self, mock_now_iso):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = False
        sub.conn = MagicMock()
        sub.cur = MagicMock()

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"device":"gw-1","sensor":"temperature_c","value":22.5}'

        sub._on_message(None, None, msg)

        sub.cur.execute.assert_not_called()
        sub.conn.commit.assert_not_called()

    def test_parse_payload_valid_json_dict(self):
        sub = Subscriber.__new__(Subscriber)
        data = sub._parse_payload('{"a":1}')
        self.assertEqual(data, {"a": 1})

    def test_parse_payload_valid_json_non_dict(self):
        sub = Subscriber.__new__(Subscriber)
        data = sub._parse_payload('"hello"')
        self.assertEqual(data, {"value": "hello"})

    def test_parse_payload_invalid_json(self):
        sub = Subscriber.__new__(Subscriber)
        data = sub._parse_payload("not-json")
        self.assertEqual(data, {"value": "not-json"})

    def test_extract_value_fields_numeric(self):
        sub = Subscriber.__new__(Subscriber)
        value_real, value_text = sub._extract_value_fields({"value": 12.3})
        self.assertEqual(value_real, 12.3)
        self.assertIsNone(value_text)

    def test_extract_value_fields_numeric_string(self):
        sub = Subscriber.__new__(Subscriber)
        value_real, value_text = sub._extract_value_fields({"value": "12.3"})
        self.assertEqual(value_real, 12.3)
        self.assertIsNone(value_text)

    def test_extract_value_fields_non_numeric_string(self):
        sub = Subscriber.__new__(Subscriber)
        value_real, value_text = sub._extract_value_fields({"value": "ok"})
        self.assertIsNone(value_real)
        self.assertEqual(value_text, "ok")
