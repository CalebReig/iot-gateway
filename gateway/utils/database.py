from __future__ import annotations

from abc import ABC, abstractmethod

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from gateway.models import Telemetry


class DataBase(ABC):
    @abstractmethod
    def write_telemetry(self, telemetry: Telemetry) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class InfluxDataBase(DataBase):
    def __init__(self, url: str, org: str, token: str, bucket: str):
        self.url = url
        self.org = org
        self.bucket = bucket

        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def write_telemetry(self, telemetry: Telemetry) -> None:
        data_point = (
            Point("telemetry")
            .tag("device", telemetry.device)
            .tag("sensor", telemetry.sensor)
            .field("value", telemetry.value)
            .time(telemetry.ts, WritePrecision.S)
        )

        self.write_api.write(bucket=self.bucket, org=self.org, record=data_point)

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
