from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

OpType = Literal["<", ">", "cross_up", "cross_down"]

class RuleDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    field: str
    op: OpType
    value: float | int
    throttle_sec: int = 1800

class IndicatorDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    enabled: bool = True
    display_name: str = ""
    cats: List[int] = Field(default_factory=list)
    min_bars: int = 80
    params: Dict[str, Any] = Field(default_factory=dict)
    throttle_sec: Optional[int] = None
    rules: List[RuleDSL] = Field(default_factory=list)
    template: str = ""

class MonitorDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    interval_sec: int = 5
    kline_categories: List[int] = Field(default_factory=list)
    indicators: List[IndicatorDSL] = Field(default_factory=list)

    # ✅ 兼容你 YAML 顶层结构：允许它存在，但 DSL 不解析也不会报错
OpType = Literal["<", ">", "cross_up", "cross_down"]

class AnomalyDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    enabled: bool = True
    cats: List[int] = Field(default_factory=list)     # 不填=所有cat都做
    lookback_n: int = 6
    vol_ma: int = 20
    ret_thr: float = 0.03
    vol_thr: float = 2.0
    throttle_sec: int = 1800
    template: str = (
        "【异动提醒-{kind_label}】{name} {kline_text} {dt}\n"
        "价格={close:.2f} 近{lookback_n}根涨跌={ret_pct:+.2f}% 放量={vol_ratio:.2f}x"
    )

class RuleDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    field: str
    op: OpType
    value: float | int
    throttle_sec: int = 1800

class IndicatorDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    enabled: bool = True
    cats: List[int] = Field(default_factory=list)
    min_bars: int = 80
    params: Dict[str, Any] = Field(default_factory=dict)
    throttle_sec: Optional[int] = None
    rules: List[RuleDSL] = Field(default_factory=list)
    template: str = ""

class MonitorDSL(BaseModel):
    model_config = ConfigDict(extra="ignore")
    interval_sec: int = 5
    kline_categories: List[int] = Field(default_factory=list)
    indicators: List[IndicatorDSL] = Field(default_factory=list)
    anomaly: Optional[AnomalyDSL] = None
