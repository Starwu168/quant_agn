from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import numbers

from dsl.schema import MonitorDSL, IndicatorDSL, RuleDSL

@dataclass
class FiredEvent:
    indicator_id: str
    rule_id: str
    rule_op: str
    rule_value: float
    payload: Dict[str, Any]
    template: str
    throttle_sec: int

@dataclass
class IndicatorPlan:
    dsl: IndicatorDSL

@dataclass
class RuntimePlan:
    cfg: MonitorDSL
    indicators: List[IndicatorPlan]

def compile_plan(cfg: dict) -> RuntimePlan:
    dsl = MonitorDSL.model_validate(cfg)
    inds = [IndicatorPlan(i) for i in dsl.indicators if i.enabled]
    return RuntimePlan(cfg=dsl, indicators=inds)

def _is_num(x) -> bool:
    return isinstance(x, numbers.Real)

def eval_rule(out: Dict[str, Any], r: RuleDSL) -> Tuple[bool, Dict[str, Any]]:
    """
    out: dict[str, pd.Series]  (你现有 INDICATORS 输出)
    返回: (fired, payload)
    """
    field = r.field
    if field not in out:
        return False, {}

    s = out[field]
    if s is None or len(s) < 2:
        return False, {}

    v = s.iloc[-1]
    prev = s.iloc[-2]

    # 统一转 float（容错）
    try:
        v_f = float(v)
    except Exception:
        v_f = None
    try:
        prev_f = float(prev)
    except Exception:
        prev_f = None

    if r.op == "<":
        if v_f is None:
            return False, {}
        return v_f < float(r.value), {"field": field, "value": v_f, "threshold": float(r.value)}
    if r.op == ">":
        if v_f is None:
            return False, {}
        return v_f > float(r.value), {"field": field, "value": v_f, "threshold": float(r.value)}
    if r.op == "cross_up":
        if v_f is None or prev_f is None:
            return False, {}
        return prev_f <= float(r.value) and v_f > float(r.value), {"field": field, "value": v_f, "threshold": float(r.value)}
    if r.op == "cross_down":
        if v_f is None or prev_f is None:
            return False, {}
        return prev_f >= float(r.value) and v_f < float(r.value), {"field": field, "value": v_f, "threshold": float(r.value)}

    return False, {}

def resolve_throttle(ind: IndicatorDSL, r: RuleDSL) -> int:
    if r.throttle_sec:
        return int(r.throttle_sec)
    if ind.throttle_sec:
        return int(ind.throttle_sec)
    return 1800

def build_dedup_key(ind: IndicatorDSL, r: RuleDSL, cat: int) -> str:
    return f"{ind.id}:{r.id}:cat={cat}"

@dataclass
class RuntimePlan:
    dsl: MonitorDSL

    @property
    def indicators(self):
        return [p for p in self.dsl.indicators if p.enabled]

    @property
    def anomaly(self):
        return self.dsl.anomaly if (self.dsl.anomaly and self.dsl.anomaly.enabled) else None

def compile_plan(cfg: dict) -> RuntimePlan:
    dsl = MonitorDSL.model_validate(cfg)
    return RuntimePlan(dsl=dsl)
