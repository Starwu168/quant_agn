from pydantic import BaseModel


class MonitorSettings(BaseModel):
    interval_sec: int = 5

    # 盯盘对象（示例：指数 + 自选股）
    index_symbols: list[str] = ["SH000001"]  # 上证/深成/创业板
    watch_symbols: list[str] = [
        "SH510500",  # 中证500ETF
        "SH601179",  # 中国西电
        "SH510300",  # 沪深300ETF
        "SZ159851",  # 金融科技ETF
        "SH513090",  # 香港证券ETF
        "SH515220",  # 煤炭ETF
        "SH600395",  # 盘江股份
        "SH512980",  # 传媒ETF
        "SZ300058",  # 蓝色光标
        "SZ300624",  # 万兴科技
        "SZ300617",  # 安靠智电
        "SH562500",  # 机器人ETF
        "SH515790",  # 光伏ETF
        "SZ159852",  # 软件ETF
        "SZ003005",  # 竞业达
        "SH600759",  # 洲际油气
        "SH512400",  # 有色金属ETF
        "SZ002716",  # 湖南白银
        "SH516020",  # 化工ETF
        "SZ002709",  # 天赐材料
        "SZ300919",  # 中伟新材
        "SZ159206",  # 卫星ETF
        "SH588170",  # 科创半导体ETF
        "SZ300604",  # 长川科技
        "SZ002837",  # 英维克
        "SH589010",  # 科创人工智能ETF
        "SZ159739",  # 云计算ETF
        "SH518880",  # 黄金ETF
        "SH880789",  # 昨成交20（指数类）
        "SH513880",  # 日经225ETF
        "SH511090",  # 30年国债ETF
        "SH880698",  # 宽基ETF（指数类）
        "SZ159570",  # 港股通创新药ETF
        "SH513100",  # 纳指ETF
        "SH515880",  # 通信ETF
    ]

    # 去重/节流：同一条信号最短间隔（秒）
    dedup_cooldown_sec: int = 60



    kline_categories: list[int] = [0,7, 10]  # 默认 5分钟K

    enable_anomaly: bool = True

    # 异动监控参数（先简单可用）
    anomaly_lookback_n: int = 3  # N根bar前
    anomaly_vol_ma: int = 20  # 成交量均值窗口
    anomaly_ret_thr: float = 0.01  # 1% 变化
    anomaly_vol_thr: float = 2.0  # 放量 2倍

    active_indicators: list[dict] = [
        # 顶地图：髑战
        {"name": "DINGDITU_DUZHAN", "params": {}, "rules": [{"op": ">","field":"duzhan","value": 90}, {"op": "<", "field":"duzhan","value": 10}]},

        # MACD 示例：柱子由负转正提醒（你可以随时关掉或改）
        #{"name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9},
         #"rules": [{"op": "cross_up", "field": "macd", "threshold": 0},
                   #{"op": "cross_down", "field": "macd", "threshold": 0},]},


        ]
