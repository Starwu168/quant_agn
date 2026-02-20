from dataclasses import dataclass
from typing import Callable

import pandas as pd
from tools.indicators.dingditu import dingditu_duzhan


@dataclass
class Rule:
    rule_id: str
    desc: str
    check: Callable[[str, pd.DataFrame], tuple[bool, dict]]  # (symbol, df)


def rule_dingditu_duzhan_90_10() -> Rule:
    def _check(symbol: str, df: pd.DataFrame):
        s = dingditu_duzhan(df)
        v = float(s.iloc[-1]) if len(s) else float("nan")

        if v != v:  # NaN
            return False, {"髑战": v, "reason": "NaN"}

        fired = (v > 90.0) or (v < 10.0)
        return fired, {"髑战": v}

    return Rule(
        rule_id="DINGDITU_DUZHAN_90_10",
        desc="顶地图：髑战 > 90 或 < 10",
        check=_check
    )


