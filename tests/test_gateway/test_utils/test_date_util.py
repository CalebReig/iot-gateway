import unittest
from datetime import datetime, timezone

from gateway.utils import DateUtil


class TestDateUtil(unittest.TestCase):
    def test_now_iso_returns_iso_utc_string(self):
        value = DateUtil.now_iso()

        parsed = datetime.fromisoformat(value)

        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_datetime_from_iso_format(self):
        value = DateUtil.now_iso()
        dt = DateUtil.datetime_from_iso_format(value)

        self.assertEqual(type(dt), datetime)
        self.assertEqual(dt.tzinfo, timezone.utc)
