import numpy as np
import pandas as pd

class AnomalyEngine:
    def __init__(self, lookback_n: int = 3, vol_ma: int = 20, ret_thr: float = 0.01, vol_thr: float = 2.0):
        self.lookback_n = lookback_n
        self.vol_ma = vol_ma
        self.ret_thr = ret_thr
        self.vol_thr = vol_thr

    def detect(self, df: pd.DataFrame) -> dict | None:
        """
        返回 None 表示无异动；否则返回 payload（用于提醒）。
        期待 df 有 datetime/open/high/low/close/vol
        """
        if df is None or df.empty:
            return None
        if len(df) < max(self.lookback_n + 1, self.vol_ma + 1):
            return None

        close = df["close"].astype(float).to_numpy()
        vol = df["vol"].astype(float).to_numpy()

        last = close[-1]
        prev = close[-1 - self.lookback_n]
        ret = last / prev - 1.0

        vol_ma = np.mean(vol[-self.vol_ma:])
        vol_ratio = (vol[-1] / vol_ma) if vol_ma > 1e-9 else 0.0

        if abs(ret) >= self.ret_thr and vol_ratio >= self.vol_thr:
            return {
                "ret": float(ret),
                "vol_ratio": float(vol_ratio),
                "dt": df["datetime"].iloc[-1],
                "close": float(last),
            }
        return None
