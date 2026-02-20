import time
import os
from common.config_yaml import load_yaml
from monitor.notifier_dingtalk import DingTalkNotifier
from tools.symbols.hardcoded_names import SYMBOL_NAME_MAP
from common.logger import get_logger
from common.config import MonitorSettings

from monitor.state_store import *

from tools.tdx_fetcher import TdxFetcher, FetchSpec
from tools.indicators.registry import INDICATORS
from monitor.rule_eval import eval_rule
from monitor.notifier_wecom import *
from monitor.anomaly_engine import AnomalyEngine
from dsl.runtime import compile_plan
from dsl.runtime import *
from dsl.render import render_text
from tools.watchlist.tdx_blk_reader import load_watch_symbols_from_blk

log = get_logger("monitor")


class MonitorService:
    def __init__(self, settings: MonitorSettings):
        self.settings = settings
        self.fetcher = TdxFetcher()
        self.state = StateStore(cooldown_sec=settings.dedup_cooldown_sec)
        self.wecom = WeComWebhookNotifier(getattr(self.settings, "wecom_webhook_url", ""))
        self.dingtalk = DingTalkNotifier(
            getattr(self.settings, "dingtalk_webhook_url", ""),
            getattr(self.settings, "dingtalk_secret", ""),
        )
        self.anomaly = AnomalyEngine(
            lookback_n=self.settings.anomaly_lookback_n,
            vol_ma=self.settings.anomaly_vol_ma,
            ret_thr=self.settings.anomaly_ret_thr,
            vol_thr=self.settings.anomaly_vol_thr,
        )
        self.cfg_path = "C:/Users\qch1763\PycharmProjects\stock_agent\configs\monitor.yaml"
        self._loaded_yaml = load_yaml(self.cfg_path)
        self._apply_yaml(self._loaded_yaml.data)
        self.anomaly = AnomalyEngine(
            lookback_n=..., vol_ma=..., ret_thr=..., vol_thr=...
        )

    def run_forever(self):
        log.info("MonitorService started (interval=%ss).", self.settings.interval_sec)
        while True:
            # ✅ 每轮都检查热加载
            self._maybe_reload_yaml()

            try:
                self._tick()  # 把你现在 _tick 的业务部分挪到这个函数
            except Exception as e:
                log.exception("tick error: %s", e)

            time.sleep(max(1, int(getattr(self.settings, "interval_sec", 5))))

    def _tick(self):
        index_syms = self.settings.index_symbols
        watch_syms = self.settings.watch_symbols
        cats = [0,7]#self.settings.kline_categories
        count = 200

        # 指数
        for sym in index_syms:
            for cat in cats:
                df = self.fetcher.fetch_minute_bars(
                    FetchSpec(symbol=sym, kind="index", count=count, category=cat)
                )
                self._handle_anomaly(kind_label="大盘", sym=sym, cat=cat, df=df)
                self._apply_active_indicators(sym, df, cat)

        # 自选股
        for sym in watch_syms:
            for cat in cats:
                df = self.fetcher.fetch_minute_bars(
                    FetchSpec(symbol=sym, kind="stock", count=count, category=cat)
                )
                self._handle_anomaly(kind_label="自选", sym=sym, cat=cat, df=df)
                self._apply_active_indicators(sym, df, cat)

        log.info("tick ok: index=%d watch=%d cats=%s", len(index_syms), len(watch_syms), cats)
        log.info("kline_categories: %s", self.settings.kline_categories)

    def _apply_active_indicators(self, sym, df, cat):
        if not hasattr(self, "runtime") or self.runtime is None:
            return
        if df is None or df.empty:
            return

        bar_dt = df["datetime"].iloc[-1] if "datetime" in df.columns and len(df) > 0 else None
        name = self.resolve_symbol_name(sym)
        ktxt = self._cat_to_text(cat)

        for ind in self.runtime.indicators:

            # cat 过滤：没配置 cats 则允许所有；配置了则按配置
            if ind.cats and cat not in ind.cats:
                continue

            # min_bars
            if len(df) < int(ind.min_bars):
                continue

            # indicator 函数
            if ind.id not in INDICATORS:
                continue

            out = INDICATORS[ind.id](df, **(ind.params or {}))

            for r in ind.rules:
                fired, payload = eval_rule(out, r)
                if not fired:
                    continue

                # dedup + throttle：sym + cat + indicator + rule
                dedup_key = build_dedup_key(ind, r, cat)
                throttle = resolve_throttle(ind, r)

                if not self.state.can_fire(sym, dedup_key, throttle_sec=throttle):
                    continue

                # 渲染上下文（模板里能用的变量）
                ctx = {
                    "name": name,
                    "symbol": sym,
                    "kline_text": ktxt,
                    "bar_dt": str(bar_dt) if bar_dt is not None else "unknown_dt",
                    "rule_op": r.op,
                    "rule_value": float(r.value),
                    "indicator_id": ind.id,
                    "rule_id": r.id,
                    "field": r.field,
                    "value": payload.get("value"),
                    "threshold": payload.get("threshold"),
                }
                # 把 out 里的最后一个值也塞进去，模板直接用 {duzhan:.2f}
                try:
                    for k, s in out.items():
                        if s is not None and len(s) > 0:
                            ctx[k] = float(s.iloc[-1])
                except Exception:
                    pass

                text = render_text(ind.template or "", ctx)
                if not text.strip():
                    # 没写模板就 fallback
                    text = f"【盯盘提醒】{name} {ktxt} {ctx['bar_dt']}\n{r.field}={payload.get('value')} 触发：{r.op} {r.value}"

                log.warning(text)

                # 推送
                try:
                    #if self.wecom.enabled():
                        #self.wecom.send_text(text)
                    if self.dingtalk.enabled():
                        self.dingtalk.send_text(text)
                except Exception as e:
                    log.error("push failed: %s", e)

                self.state.mark_fired(sym, dedup_key)

    def _handle_anomaly(self, kind_label: str, sym: str, cat: int, df):
        """
        异动提醒（DSL驱动）
        """
        plan = getattr(self, "runtime", None)
        if plan is None or plan.anomaly is None:
            return

        a = plan.anomaly

        # cat 过滤：没配置 cats 则允许所有；配置了则按配置
        if a.cats and int(cat) not in set(a.cats):
            return

        # df 基本校验
        if df is None or df.empty:
            return

        # 用 DSL 的参数确保 anomaly engine 同步（你不想改引擎内部，就这样同步最稳）
        self.anomaly.lookback_n = int(a.lookback_n)
        self.anomaly.vol_ma = int(a.vol_ma)
        self.anomaly.ret_thr = float(a.ret_thr)
        self.anomaly.vol_thr = float(a.vol_thr)

        payload = self.anomaly.detect(df)
        if not payload:
            return

        # 基本信息
        name = self.resolve_symbol_name(sym)
        ktxt = self._cat_to_text(cat)

        # payload 取值（detect() 返回什么就按什么取，缺省给 0/None）
        dt_txt = str(payload.get("dt", "unknown_dt"))
        close = float(payload.get("close", 0.0))
        ret_pct = float(payload.get("ret", 0.0)) * 100.0
        vol_ratio = float(payload.get("vol_ratio", 0.0))

        # ✅ 渲染上下文：给模板用
        ctx = {
            "kind_label": kind_label,  # 大盘 / 自选
            "name": name,
            "symbol": sym,
            "kline_text": ktxt,
            "cat": int(cat),
            "dt": dt_txt,
            "close": close,
            "ret_pct": ret_pct,
            "vol_ratio": vol_ratio,
            "lookback_n": int(a.lookback_n),
            "vol_ma": int(a.vol_ma),
            "ret_thr": float(a.ret_thr),
            "vol_thr": float(a.vol_thr),
        }

        # ✅ 用 DSL 的模板渲染文本；模板为空则 fallback
        template = getattr(a, "template", "") or ""
        text = render_text(template, ctx) if template.strip() else ""
        if not text.strip():
            text = (
                f"【异动提醒-{kind_label}】{name} {ktxt} {dt_txt}\n"
                f"价格={close:.2f} 近{self.anomaly.lookback_n}根涨跌={ret_pct:+.2f}% 放量={vol_ratio:.2f}x"
            )

        # ✅ key 带 sym + cat
        key = f"ANOMALY:{sym}:cat={cat}"

        # ✅ throttle 用 DSL（默认值兜底）
        throttle = int(getattr(a, "throttle_sec", 1800) or 1800)

        # 注意：你项目里 state 的 API 现在有两个：can_fire / can_fire_throttle
        # 你用哪个都行，但参数名要匹配你 StateStore 的实现
        if self.state.can_fire_throttle(sym, key, throttle_sec=throttle):
            log.warning(text)
            try:
                if self.wecom.enabled():
                    self.wecom.send_text(text)
                if self.dingtalk.enabled():
                    self.dingtalk.send_text(text)
            except Exception as e:
                log.error("push failed: %s", e)
            self.state.mark_fired(sym, key)

    @staticmethod
    def _cat_to_text(cat: int) -> str:
    # 按你确认的映射：0 5m,1 15m,2 30m,3 1h,4 日K... 9 日K（你环境）
        mapping = {
            0: "5分钟K",
            1: "15分钟K",
            2: "30分钟K",
            3: "1小时K",
            4: "日K",
            5: "周K",
            6: "月K",
            7: "1分钟K",
            8: "1分钟K",
            9: "日K",
            10:"分时",
        }
        return mapping.get(int(cat), f"cat={cat}")

    @staticmethod
    def resolve_symbol_name(symbol: str) -> str:
        return SYMBOL_NAME_MAP.get(symbol, symbol)

    def _maybe_reload_yaml(self):
        try:
            st = os.stat(self.cfg_path)
            mtime_ns = st.st_mtime_ns
            log.info("yaml_check path=%s mtime_ns=%s last=%s", self.cfg_path, mtime_ns,
                     getattr(self, "_yaml_mtime_ns", None))

            if getattr(self, "_yaml_mtime_ns", None) != mtime_ns:
                self._yaml_mtime_ns = mtime_ns
                loaded = load_yaml(self.cfg_path)
                log.info("yaml_reload keys=%s", list((loaded.data or {}).keys()))
                self._apply_yaml(loaded.data)
                log.info("yaml_applied interval=%s cats=%s watch=%s index=%s",
                         getattr(self.settings, "interval_sec", None),
                         getattr(self.settings, "kline_categories", None),
                         len(getattr(self.settings, "watch_symbols", []) or []),
                         len(getattr(self.settings, "index_symbols", []) or []),
                         )
        except Exception as e:
            log.error("YAML reload failed: %s", e)

    def _apply_yaml(self, cfg: dict):
        # interval
        if "interval_sec" in cfg:
            self.settings.interval_sec = int(cfg["interval_sec"])

        # cats
        if "kline_categories" in cfg:
            self.settings.kline_categories = list(cfg["kline_categories"])

        # watchlist
        wl = cfg.get("watchlist", {}) or {}

        if "indexes" in wl:
            self.settings.index_symbols = list(wl["indexes"])

        # ✅ 新逻辑：优先 watchlist_file，其次才用 stocks 列表
        blk_path = wl.get("watchlist_file") or wl.get("blk_file") or wl.get("file")
        if blk_path:
            try:
                self.settings.watch_symbols = load_watch_symbols_from_blk(str(blk_path))
                log.info("watchlist loaded from blk: %s (n=%d)", blk_path, len(self.settings.watch_symbols))
            except Exception as e:
                log.error("watchlist_file load failed: %s", e)
        elif "stocks" in wl:
            self.settings.watch_symbols = list(wl["stocks"])

        # notify
        nt = cfg.get("notify", {}) or {}
        if "wecom_webhook_url" in nt:
            self.settings.wecom_webhook_url = str(nt["wecom_webhook_url"] or "")
        if "dingtalk_webhook_url" in nt:
            self.settings.dingtalk_webhook_url = str(nt["dingtalk_webhook_url"] or "")
        if "dingtalk_secret" in nt:
            self.settings.dingtalk_secret = str(nt["dingtalk_secret"] or "")

        # 同步更新 notifier（如果你已经有 wecom/dingtalk 对象）
        try:
            if hasattr(self, "wecom"):
                self.wecom.webhook_url = self.settings.wecom_webhook_url
            if hasattr(self, "dingtalk"):
                self.dingtalk.webhook_url = self.settings.dingtalk_webhook_url
                self.dingtalk.secret = self.settings.dingtalk_secret
        except Exception:
            pass

        # ===== DSL: compile runtime plan from YAML =====
        try:
            self._dsl_cfg = cfg
            self.runtime = compile_plan(cfg)
            log.info("dsl compiled: indicators=%d", len(self.runtime.indicators))
        except Exception as e:
            self.runtime = None
            log.error("dsl compile failed: %s", e)


