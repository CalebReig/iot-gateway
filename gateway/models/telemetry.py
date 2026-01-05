from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gateway.utils import DateUtil


@dataclass(frozen=True)
class Telemetry:
    device: str
    sensor: str
    value: float
    ts: datetime

    def __repr__(self):
        return f"Telemetry(device={self.device}, sensor={self.sensor}, value={self.value}, ts={self.ts})"

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> "Telemetry":
        # value required and castable to float
        try:
            value = float(payload["value"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"value must be castable to float: {payload.get('value')}")

        # ts required and ISO8601
        try:
            ts = DateUtil.datetime_from_iso_format(payload["ts"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"Timestamp must be in ISO format: {payload.get('ts')}")

        # device/sensor required
        try:
            device = str(payload["device"])
            sensor = str(payload["sensor"])
        except KeyError as e:
            raise ValueError(f"Missing required field: {e.args[0]}")

        return Telemetry(device=device, sensor=sensor, value=value, ts=ts)
