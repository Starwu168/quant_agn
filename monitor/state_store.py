import time

class StateStore:
    def __init__(self, cooldown_sec: int = 60):
        self.cooldown_sec = cooldown_sec
        self._last_ts = {}  # (sym, key) -> unix_time

    def can_fire(self, sym: str, key: str, throttle_sec: int | None = None) -> bool:
        """
        throttle_sec:
          - None: 使用 self.cooldown_sec
          - int:  使用给定限流秒数（例如 1800=30分钟）
        """
        k = (sym, key)
        last = self._last_ts.get(k)
        now = time.time()

        window = self.cooldown_sec if throttle_sec is None else int(throttle_sec)

        if last is None:
            return True
        return (now - last) >= window

    def mark_fired(self, sym: str, key: str) -> None:
        self._last_ts[(sym, key)] = time.time()


class PrevCloseCache:
    def __init__(self, ttl_sec=60):
        self.ttl = ttl_sec
        self.data = {}  # (sym)->(ts, prev_close)

    def get(self, sym):
        item = self.data.get(sym)
        if not item:
            return None
        ts, val = item
        if time.time() - ts > self.ttl:
            return None
        return val

    def set(self, sym, val):
        self.data[sym] = (time.time(), val)

