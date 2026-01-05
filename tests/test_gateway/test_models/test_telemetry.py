import unittest
from datetime import datetime, timezone

from gateway.models import Telemetry


class TestTelemetry(unittest.TestCase):
    def test_repr(self):
        ts = datetime(2026, 1, 2, 12, 34, tzinfo=timezone.utc)
        s = repr(Telemetry(device="gw-1", sensor="temperature_c", value=22.5, ts=ts))
        self.assertIn("Telemetry(device=gw-1", s)
        self.assertIn("sensor=temperature_c", s)
        self.assertIn("value=22.5", s)
        self.assertIn("ts=", s)

    def test_from_payload_ok(self):
        t = Telemetry.from_payload(
            {
                "device": "gw-1",
                "sensor": "temperature_c",
                "value": 22.5,
                "ts": "2026-01-02T12:34:00Z",
            }
        )
        self.assertEqual(t.device, "gw-1")
        self.assertEqual(t.sensor, "temperature_c")
        self.assertEqual(t.value, 22.5)
        self.assertEqual(t.ts.isoformat(), "2026-01-02T12:34:00+00:00")
        self.assertEqual(t.ts.tzinfo, timezone.utc)

    def test_from_payload_value_casts(self):
        t = Telemetry.from_payload(
            {
                "device": "gw-1",
                "sensor": "humidity_pct",
                "value": "12.3",
                "ts": "2026-01-02T12:34:00Z",
            }
        )
        self.assertEqual(t.value, 12.3)

    def test_from_payload_bad_value(self):
        cases = [
            (
                {"device": "gw-1", "sensor": "t", "ts": "2026-01-02T12:34:00Z"},
                r"value must be castable to float",
            ),
            (
                {
                    "device": "gw-1",
                    "sensor": "t",
                    "value": "nope",
                    "ts": "2026-01-02T12:34:00Z",
                },
                r"value must be castable to float: nope",
            ),
            (
                {
                    "device": "gw-1",
                    "sensor": "t",
                    "value": None,
                    "ts": "2026-01-02T12:34:00Z",
                },
                r"value must be castable to float",
            ),
        ]
        for payload, pat in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, pat):
                    Telemetry.from_payload(payload)  # type: ignore[arg-type]

    def test_from_payload_bad_ts(self):
        cases = [
            (
                {"device": "gw-1", "sensor": "t", "value": 1.0},
                r"Timestamp must be in ISO format",
            ),
            (
                {"device": "gw-1", "sensor": "t", "value": 1.0, "ts": "nope"},
                r"Timestamp must be in ISO format: nope",
            ),
        ]
        for payload, pat in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, pat):
                    Telemetry.from_payload(payload)

    def test_from_payload_missing_device_or_sensor(self):
        cases = [
            (
                {"sensor": "t", "value": 1.0, "ts": "2026-01-02T12:34:00Z"},
                r"Missing required field: device",
            ),
            (
                {"device": "gw-1", "value": 1.0, "ts": "2026-01-02T12:34:00Z"},
                r"Missing required field: sensor",
            ),
        ]
        for payload, pat in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, pat):
                    Telemetry.from_payload(payload)

    def test_from_payload_stringifies_device_and_sensor(self):
        t = Telemetry.from_payload(
            {"device": 123, "sensor": 456, "value": 1, "ts": "2026-01-02T12:34:00Z"}
        )
        self.assertEqual(t.device, "123")
        self.assertEqual(t.sensor, "456")
