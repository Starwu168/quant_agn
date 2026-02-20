from common.config import MonitorSettings
from tools.tdx_fetcher import TdxFetcher, FetchSpec
from tools.indicators.dingditu import dingditu_duzhan

fetcher = TdxFetcher()

# 上证指数
df_idx = fetcher.fetch_minute_bars(FetchSpec(symbol="SH000001", kind="index", count=200,category= 2))
s_idx = dingditu_duzhan(df_idx)
print("SH000001 髑战(last) =", float(s_idx.iloc[-1]), "category=", df_idx.attrs.get("tdx_category"))

# 自选股里随便选一个
settings = MonitorSettings()
sym = settings.watch_symbols[2]
df = fetcher.fetch_minute_bars(FetchSpec(symbol=sym, kind="stock", count=200,category= 2))
s = dingditu_duzhan(df)
print(sym, "髑战(last) =", float(s.iloc[-1]), "category=", df.attrs.get("tdx_category"))

