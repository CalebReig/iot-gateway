import unittest
from unittest.mock import MagicMock, patch

from gateway.subscriber import Subscriber


class TestSubscriber(unittest.TestCase):
    @patch("gateway.subscriber.mqtt.Client")
    def test_init_wires_mqtt_and_connects(self, mock_mqtt_client_cls):
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        sub = Subscriber(db=mock_db, enable_db_writes=True)

        mock_mqtt_client_cls.assert_called_once()
        args, kwargs = mock_mqtt_client_cls.call_args
        self.assertEqual(len(args), 1)

        self.assertIsNotNone(args[0])

        self.assertEqual(mock_client.on_connect, sub._on_connect)
        self.assertEqual(mock_client.on_message, sub._on_message)

        mock_client.connect.assert_called_once()
        c_args, c_kwargs = mock_client.connect.call_args
        self.assertEqual(c_kwargs.get("keepalive"), 60)

        mock_client.loop_forever.assert_not_called()

    @patch("gateway.subscriber.mqtt.Client")
    def test_start_calls_loop_forever_and_closes_db(self, mock_mqtt_client_cls):
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        sub = Subscriber(db=mock_db, enable_db_writes=True)
        sub.start()

        mock_client.loop_forever.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("gateway.subscriber.mqtt.Client")
    def test_start_closes_db_even_if_loop_forever_raises(self, mock_mqtt_client_cls):
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.loop_forever.side_effect = RuntimeError("boom")
        mock_mqtt_client_cls.return_value = mock_client

        sub = Subscriber(db=mock_db, enable_db_writes=True)

        with self.assertRaises(RuntimeError):
            sub.start()

        mock_db.close.assert_called_once()

    def test_on_connect_subscribes(self):
        sub = Subscriber.__new__(Subscriber)
        mock_client = MagicMock()

        with patch("gateway.subscriber.TOPIC_FILTER", "sensors/#"):
            sub._on_connect(mock_client, None, None, 0, None)

        mock_client.subscribe.assert_called_once_with("sensors/#")

    @patch("gateway.subscriber.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.subscriber.Telemetry.from_payload")
    def test_on_message_db_write_happy_path(self, mock_from_payload, mock_now_iso):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = True
        sub.db = MagicMock()

        telemetry_obj = MagicMock()
        mock_from_payload.return_value = telemetry_obj

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"ts":"2026-01-02T12:34:00Z","device":"gw-1","sensor":"temperature_c","value":22.5}'

        sub._on_message(None, None, msg)

        mock_from_payload.assert_called_once()
        sub.db.write_telemetry.assert_called_once_with(telemetry_obj)

    @patch("gateway.subscriber.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.subscriber.Telemetry.from_payload")
    def test_on_message_db_write_disabled_does_not_write(
        self, mock_from_payload, mock_now_iso
    ):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = False
        sub.db = MagicMock()

        telemetry_obj = MagicMock()
        mock_from_payload.return_value = telemetry_obj

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"ts":"2026-01-02T12:34:00Z","device":"gw-1","sensor":"temperature_c","value":22.5}'

        sub._on_message(None, None, msg)

        mock_from_payload.assert_called_once()
        sub.db.write_telemetry.assert_not_called()

    @patch("gateway.subscriber.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    def test_on_message_invalid_json_returns_and_does_not_write(self, mock_now_iso):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = True
        sub.db = MagicMock()

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b"not-json"

        sub._on_message(None, None, msg)

        sub.db.write_telemetry.assert_not_called()

    @patch("gateway.subscriber.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch(
        "gateway.subscriber.Telemetry.from_payload",
        side_effect=ValueError("bad payload"),
    )
    def test_on_message_bad_payload_returns_and_does_not_write(
        self, mock_from_payload, mock_now_iso
    ):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = True
        sub.db = MagicMock()

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"device":"gw-1","sensor":"temperature_c","value":"nope"}'

        sub._on_message(None, None, msg)

        sub.db.write_telemetry.assert_not_called()

    @patch("gateway.subscriber.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.subscriber.Telemetry.from_payload")
    def test_on_message_db_write_failure_is_caught(
        self, mock_from_payload, mock_now_iso
    ):
        sub = Subscriber.__new__(Subscriber)
        sub.enable_db_writes = True
        sub.db = MagicMock()

        telemetry_obj = MagicMock()
        mock_from_payload.return_value = telemetry_obj
        sub.db.write_telemetry.side_effect = RuntimeError("db down")

        msg = MagicMock()
        msg.topic = "sensors/gw-1/temperature_c"
        msg.payload = b'{"ts":"2026-01-02T12:34:00Z","device":"gw-1","sensor":"temperature_c","value":22.5}'

        # should not raise
        sub._on_message(None, None, msg)

        sub.db.write_telemetry.assert_called_once_with(telemetry_obj)
