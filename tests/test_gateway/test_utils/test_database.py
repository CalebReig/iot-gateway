import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gateway.models import Telemetry
from gateway.utils.database import DataBase, InfluxDataBase


class TestDataBaseAbstract(unittest.TestCase):
    def test_abstract_methods(self):
        class Impl(DataBase):
            pass

        with self.assertRaises(TypeError):
            Impl()


class TestInfluxDataBase(unittest.TestCase):
    @patch("gateway.utils.database.InfluxDBClient")
    def test_init_creates_client_and_apis(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.write_api.return_value = MagicMock()
        mock_client.query_api.return_value = MagicMock()

        db = InfluxDataBase(
            url="http://localhost:8086",
            org="test-org",
            token="token",
            bucket="test-bucket",
        )

        mock_client_cls.assert_called_once_with(
            url="http://localhost:8086", token="token", org="test-org"
        )
        mock_client.write_api.assert_called_once()
        mock_client.query_api.assert_called_once()
        self.assertEqual(db.bucket, "test-bucket")
        self.assertEqual(db.org, "test-org")

    @patch("gateway.utils.database.InfluxDBClient")
    def test_write_telemetry_writes_point(self, mock_client_cls):
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = MagicMock()
        mock_client_cls.return_value = mock_client

        db = InfluxDataBase(
            url="http://localhost:8086",
            org="test-org",
            token="token",
            bucket="test-bucket",
        )

        ts = datetime(2026, 1, 2, 12, 34, tzinfo=timezone.utc)
        telemetry = Telemetry(device="gw-1", sensor="temperature_c", value=22.5, ts=ts)

        db.write_telemetry(telemetry)

        mock_write_api.write.assert_called_once()
        _, kwargs = mock_write_api.write.call_args
        self.assertEqual(kwargs["bucket"], "test-bucket")
        self.assertEqual(kwargs["org"], "test-org")
        self.assertIsNotNone(kwargs["record"])

    @patch("gateway.utils.database.InfluxDBClient")
    def test_close_calls_client_close(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.write_api.return_value = MagicMock()
        mock_client.query_api.return_value = MagicMock()
        mock_client_cls.return_value = mock_client

        db = InfluxDataBase(
            url="http://localhost:8086",
            org="test-org",
            token="token",
            bucket="test-bucket",
        )

        db.close()
        mock_client.close.assert_called_once()

    @patch("gateway.utils.database.InfluxDBClient")
    def test_close_swallows_exception(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.close.side_effect = RuntimeError("boom")
        mock_client.write_api.return_value = MagicMock()
        mock_client.query_api.return_value = MagicMock()
        mock_client_cls.return_value = mock_client

        db = InfluxDataBase(
            url="http://localhost:8086",
            org="test-org",
            token="token",
            bucket="test-bucket",
        )

        db.close()
