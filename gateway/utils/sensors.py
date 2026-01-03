from abc import ABC, abstractmethod

from sense_hat import SenseHat


class Sensor(ABC):
    def __init__(
        self,
        name: str,
        unit: str,
        sense_hat: SenseHat | None = None,
        precision: int = 1,
    ):
        self.name = name
        self.unit = unit
        self.sense_hat = sense_hat or SenseHat()
        self.precision = precision
        self.prev_value = 0.0
        self.current_value = 0.0

    def is_current_new_value(self) -> bool:
        return self.prev_value != self.current_value

    def read(self) -> float:
        self.prev_value = self.current_value
        raw = self._read_raw()
        self.current_value = round(raw, self.precision)
        return self.current_value

    @abstractmethod
    def _read_raw(self) -> float:
        raise NotImplementedError


class TemperatureSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__("temperature", "c", **kwargs)

    def _read_raw(self) -> float:
        return self.sense_hat.get_temperature()


class HumiditySensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__("humidity", "pct", **kwargs)

    def _read_raw(self) -> float:
        return self.sense_hat.get_humidity()


class PressureSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__("pressure", "mbar", **kwargs)

    def _read_raw(self) -> float:
        return self.sense_hat.get_pressure()


class CPUSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__("cpu_temp", "c", **kwargs)

    def _read_raw(self) -> float:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read().strip()) / 1000.0
