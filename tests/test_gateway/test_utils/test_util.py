import unittest
from datetime import datetime, timezone

from gateway.utils import Util


class TestUtil(unittest.TestCase):
    def test_now_iso_returns_iso_utc_string(self):
        value = Util.now_iso()

        parsed = datetime.fromisoformat(value)

        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.tzinfo, timezone.utc)
