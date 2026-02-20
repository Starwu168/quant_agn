from __future__ import annotations
from pathlib import Path
from typing import List, Set

def _normalize_symbol(market_digit: str, code6: str) -> str:
    # 通达信常见：0=深圳(SZ)，1=上海(SH)
    if market_digit == "1":
        return f"SH{code6}"
    if market_digit == "0":
        return f"SZ{code6}"
    # 兜底：未知就原样
    return f"{market_digit}{code6}"

def load_watch_symbols_from_blk(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"blk not found: {path}")

    data = p.read_bytes()
    syms: Set[str] = set()

    # --- 优先按“文本”解析 ---
    try:
        text = data.decode("gbk", errors="ignore")  # 通达信常见GBK
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue

            # 允许：SH600519 / SZ000001
            if (s.startswith("SH") or s.startswith("SZ")) and len(s) >= 8:
                syms.add(s[:8])
                continue

            # 允许：1999999 / 0000001 这种 7 位数字（首位市场 + 6位代码）
            if len(s) >= 7 and s[:7].isdigit():
                market = s[0]
                code6 = s[1:7]
                syms.add(_normalize_symbol(market, code6))
                continue

        if syms:
            return sorted(syms)
    except Exception:
        pass

    # --- 二进制兜底（弱兼容） ---
    # 有些资料提到旧格式可能是“固定长度记录”，这里不强依赖，能解析多少算多少
    # 如果你之后发现你的 .blk 是纯二进制，我们再针对你那份文件做精确解析
    for i in range(0, len(data) - 7, 1):
        chunk = data[i:i+7]
        if chunk.isdigit():
            market = chr(chunk[0])
            code6 = chunk[1:7].decode("ascii", errors="ignore")
            if len(code6) == 6 and code6.isdigit():
                syms.add(_normalize_symbol(market, code6))

    return sorted(syms)
