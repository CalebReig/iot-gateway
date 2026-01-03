import unittest
from unittest.mock import MagicMock, patch

from gateway.utils import (
    Sensor,
    TemperatureSensor,
    HumiditySensor,
    PressureSensor,
    CPUSensor,
)


class TestSensorBase(unittest.TestCase):
    def test_sensor_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Sensor("x", "y")

    def test_read_updates_prev_and_current_and_rounds(self):
        class FakeSensor(Sensor):
            def __init__(self, **kwargs):
                super().__init__("fake", "u", **kwargs)

            def _read_raw(self) -> float:
                return 1.234

        s = FakeSensor(sense_hat=MagicMock(), precision=1)

        v1 = s.read()
        self.assertEqual(v1, 1.2)
        self.assertEqual(s.prev_value, 0.0)
        self.assertEqual(s.current_value, 1.2)
        self.assertTrue(s.is_current_new_value())

        v2 = s.read()
        self.assertEqual(v2, 1.2)
        self.assertEqual(s.prev_value, 1.2)
        self.assertEqual(s.current_value, 1.2)
        self.assertFalse(s.is_current_new_value())


class TestSenseHatSensors(unittest.TestCase):
    def test_temperature_sensor_reads_from_sense_hat(self):
        sense_hat = MagicMock()
        sense_hat.get_temperature.return_value = 22.56

        s = TemperatureSensor(sense_hat=sense_hat, precision=1)
        v = s.read()

        self.assertEqual(v, 22.6)
        sense_hat.get_temperature.assert_called_once()

    def test_humidity_sensor_reads_from_sense_hat(self):
        sense_hat = MagicMock()
        sense_hat.get_humidity.return_value = 45.04

        s = HumiditySensor(sense_hat=sense_hat, precision=1)
        v = s.read()

        self.assertEqual(v, 45.0)
        sense_hat.get_humidity.assert_called_once()

    def test_pressure_sensor_reads_from_sense_hat(self):
        sense_hat = MagicMock()
        sense_hat.get_pressure.return_value = 1013.26

        s = PressureSensor(sense_hat=sense_hat, precision=1)
        v = s.read()

        self.assertEqual(v, 1013.3)
        sense_hat.get_pressure.assert_called_once()


class TestCPUSensor(unittest.TestCase):
    def test_cpu_sensor_reads_from_sysfs_and_converts_to_c(self):
        m = unittest.mock.mock_open(read_data="55000\n")
        with patch("builtins.open", m):
            s = CPUSensor(sense_hat=MagicMock(), precision=1)
            v = s.read()

        self.assertEqual(v, 55.0)
        m.assert_called_once_with("/sys/class/thermal/thermal_zone0/temp", "r")
