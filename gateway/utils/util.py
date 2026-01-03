from datetime import datetime, timezone


class Util:
    @staticmethod
    def now_iso():
        return datetime.now(timezone.utc).isoformat()
