from pydantic import BaseModel


class MonitorSettings(BaseModel):
    interval_sec: int = 5

    # 盯盘对象（示例：指数 + 自选股）
    index_symbols: list[str] = ["SH000001", "SZ399001", "SZ399006"]  # 上证/深成/创业板
    watch_symbols: list[str] = ["SZ000001", "SH600519","SZ300058"]

    # 去重/节流：同一条信号最短间隔（秒）
    dedup_cooldown_sec: int = 60
