import unittest
from unittest.mock import MagicMock, patch

from gateway.publisher import sense_and_publish, read_cpu_temp_c, BASE_TOPIC


class TestPublisher(unittest.TestCase):
	@patch("gateway.publisher.SenseHat")
	def test_sense_and_publish(self, mock_sense_cls):
		mock_sense = mock_sense_cls.return_value
		prev_temp_c = 20.0
		mock_sense.get_temperature.return_value = 20.0
		prev_humidity = 40.0
		mock_sense.get_humidity.return_value = 40.0
		prev_pressure_mbar = 1234.0
		mock_sense.get_pressure.return_value = 1000.0
		prev_cpu_temp_c = read_cpu_temp_c()
		
		test_mqtt_client = MagicMock()
		
		new_temp_c, new_humidity, new_pressure_mbar, new_cpu_temp_c = sense_and_publish(test_mqtt_client, prev_temp_c, prev_humidity, prev_pressure_mbar, prev_cpu_temp_c)
		
		self.assertEqual(new_temp_c, prev_temp_c)
		self.assertEqual(new_humidity, prev_humidity)
		self.assertNotEqual(new_pressure_mbar, prev_pressure_mbar)
		self.assertEqual(new_cpu_temp_c, prev_cpu_temp_c)
		
		test_mqtt_client.publish.assert_called_once()
		args, kwargs = test_mqtt_client.publish.call_args
		topic = args[0]
		self.assertEqual(topic, f"{BASE_TOPIC}/pressure_mbar")

