from __future__ import annotations
from dataclasses import dataclass
import time
import random
from tools.tdx_client import PyTdxClient
import time


@dataclass
class Bar:
    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketSource:
    """
    行情数据源统一接口：
    - get_recent_bars(symbol, n): 返回最近 n 根 bar（用于计算指标）
    - get_last_price(symbol): 返回最新价（用于展示/触发）
    """

    def get_recent_bars(self, symbol: str, n: int) -> list[Bar]:
        raise NotImplementedError

    def get_last_price(self, symbol: str) -> float:
        raise NotImplementedError


class MockMarketSource(MarketSource):
    """
    先用假数据让监控系统跑起来。
    下一阶段你把这里换成：
    - 读取通达信导出的分钟数据
    - 或 pytdx 实时行情
    """
    def __init__(self):
        self._seed = {}

    def _base(self, symbol: str) -> float:
        if symbol not in self._seed:
            self._seed[symbol] = 10 + random.random() * 50
        return self._seed[symbol]

    def get_recent_bars(self, symbol: str, n: int) -> list[Bar]:
        base = self._base(symbol)
        now = time.time()
        bars = []
        price = base
        for i in range(n):
            # 模拟波动
            price = max(0.1, price + random.uniform(-0.5, 0.5))
            o = price + random.uniform(-0.2, 0.2)
            c = price + random.uniform(-0.2, 0.2)
            h = max(o, c) + random.uniform(0, 0.3)
            l = min(o, c) - random.uniform(0, 0.3)
            v = random.uniform(1e5, 5e5)
            bars.append(Bar(ts=now - (n - 1 - i) * 60, open=o, high=h, low=l, close=c, volume=v))
        return bars

    def get_last_price(self, symbol: str) -> float:
        return self.get_recent_bars(symbol, 1)[-1].close

class PyTdxMarketSource(MarketSource):
    """
    用 pytdx 拉分钟K：
    - 股票：get_security_bars
    - 指数：get_index_bars
    """
    def __init__(self):
        self.client = PyTdxClient(timeout=10)
        self.client.connect_best()

    @staticmethod
    def _parse_symbol(symbol: str):
        # 约定：SH600519 / SZ000001 / SH000001(指数)
        market = 1 if symbol.startswith("SH") else 0
        code = symbol[2:]
        return market, code

    def get_recent_bars(self, symbol: str, n: int) -> list[Bar]:
        self.client.ensure_connected()
        market, code = self._parse_symbol(symbol)

        # 先用“分钟K”类别尝试（pytdx 社区常用 9/8/7 有差异，先用9）
        category = 9

        # 指数：用 get_index_bars；股票：get_security_bars
        if symbol.startswith("SH000") or symbol.startswith("SZ399") or code.startswith("000001") and symbol.startswith("SH"):
            raw = self.client.api.get_index_bars(category, market, code, 0, n)
        else:
            raw = self.client.api.get_security_bars(category, market, code, 0, n)

        if not raw:
            return []

        bars = []
        for r in raw:
            # r 一般包含: open, close, high, low, vol, amount, year, month, day, hour, minute
            ts = time.time()
            if "year" in r and "month" in r and "day" in r and "hour" in r and "minute" in r:
                # 这里先不严格转本地时间，MVP阶段用 time.time 占位也能跑
                pass

            bars.append(Bar(
                ts=ts,
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r.get("vol", r.get("volume", 0.0)))
            ))
        return bars

    def get_last_price(self, symbol: str) -> float:
        bars = self.get_recent_bars(symbol, 1)
        return bars[-1].close if bars else float("nan")