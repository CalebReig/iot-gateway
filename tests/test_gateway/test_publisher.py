import json
import unittest
from unittest.mock import MagicMock, patch

from gateway.publisher import Publisher


class TestPublisher(unittest.TestCase):
    @patch("gateway.publisher.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.publisher.mqtt.Client")
    def test_publish_sensor_data_publishes_only_new_values(
        self, mock_mqtt_client_cls, mock_now_iso
    ):
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        temp = MagicMock()
        temp.name = "temperature"
        temp.unit = "c"
        temp.read.return_value = 22.5
        temp.is_current_new_value.return_value = True

        hum = MagicMock()
        hum.name = "humidity"
        hum.unit = "pct"
        hum.read.return_value = 45.0
        hum.is_current_new_value.return_value = False

        pub = Publisher(
            device_name="gw-1",
            device_source="pi",
            sensors=[temp, hum],
        )

        pub.publish_sensor_data()

        mock_client.connect.assert_called_once()
        mock_client.loop_start.assert_called_once()

        args, kwargs = mock_client.connect.call_args
        host, port = (
            args[0],
            args[1],
        )
        self.assertEqual(kwargs.get("keepalive"), 60)
        self.assertIsInstance(host, str)
        self.assertIsInstance(port, int)

        mock_client.publish.assert_called_once()

        publish_args, publish_kwargs = mock_client.publish.call_args

        topic = publish_args[0]
        payload = publish_args[1]
        qos = publish_kwargs.get(
            "qos", publish_args[2] if len(publish_args) > 2 else None
        )
        retain = publish_kwargs.get(
            "retain", publish_args[3] if len(publish_args) > 3 else None
        )

        self.assertTrue(topic.endswith("/temperature_c"), f"Unexpected topic: {topic}")
        self.assertEqual(qos, 0)
        self.assertEqual(retain, True)

        decoded = json.loads(payload)
        self.assertEqual(decoded["source"], "pi")
        self.assertEqual(decoded["device"], "gw-1")
        self.assertEqual(decoded["sensor"], "temperature_c")
        self.assertEqual(decoded["value"], 22.5)
        self.assertEqual(decoded["ts"], "2026-01-02T12:34:56Z")

        temp.read.assert_called_once()
        hum.read.assert_called_once()

        temp.is_current_new_value.assert_called_once()
        hum.is_current_new_value.assert_called_once()

    @patch("gateway.publisher.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.publisher.mqtt.Client")
    def test_publish_sensor_data_publishes_nothing_if_no_new_values(
        self, mock_mqtt_client_cls, mock_now_iso
    ):
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        s1 = MagicMock()
        s1.name = "temperature"
        s1.unit = "c"
        s1.read.return_value = 22.5
        s1.is_current_new_value.return_value = False

        s2 = MagicMock()
        s2.name = "humidity"
        s2.unit = "pct"
        s2.read.return_value = 45.0
        s2.is_current_new_value.return_value = False

        pub = Publisher(device_name="gw-1", device_source="pi", sensors=[s1, s2])
        pub.publish_sensor_data()

        mock_client.publish.assert_not_called()
        s1.read.assert_called_once()
        s2.read.assert_called_once()

    @patch("gateway.publisher.DateUtil.now_iso", return_value="2026-01-02T12:34:56Z")
    @patch("gateway.publisher.mqtt.Client")
    def test_publish_sensor_data_publishes_multiple_new_values(
        self, mock_mqtt_client_cls, mock_now_iso
    ):
        mock_client = MagicMock()
        mock_mqtt_client_cls.return_value = mock_client

        temp = MagicMock(name="temp_sensor")
        temp.name = "temperature"
        temp.unit = "c"
        temp.read.return_value = 22.5
        temp.is_current_new_value.return_value = True

        cpu = MagicMock(name="cpu_sensor")
        cpu.name = "cpu_temp"
        cpu.unit = "c"
        cpu.read.return_value = 55.2
        cpu.is_current_new_value.return_value = True

        pub = Publisher(device_name="gw-1", device_source="pi", sensors=[temp, cpu])
        pub.publish_sensor_data()

        self.assertEqual(mock_client.publish.call_count, 2)

        topics = [call.args[0] for call in mock_client.publish.call_args_list]
        self.assertTrue(any(t.endswith("/temperature_c") for t in topics))
        self.assertTrue(any(t.endswith("/cpu_temp_c") for t in topics))

        payloads = [
            json.loads(call.args[1]) for call in mock_client.publish.call_args_list
        ]
        sensors = {p["sensor"] for p in payloads}
        self.assertEqual(sensors, {"temperature_c", "cpu_temp_c"})
