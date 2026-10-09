"""ตัวคัดกรองหุ้นขาขึ้น (uptrend) — เกณฑ์สไตล์ Trend Template"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Params:
    min_bars: int = 210                # ต้องมีข้อมูลอย่างน้อยเท่านี้ (SMA200 + slope)
    max_from_high: float = 0.25        # ราคาต้องไม่ต่ำกว่า high 52 สัปดาห์เกิน 25%
    min_above_low: float = 0.30        # ต้องสูงกว่า low 52 สัปดาห์อย่างน้อย 30%
    min_adx: float = 20.0
    rsi_range: tuple[float, float] = (50.0, 80.0)
    min_value_mb: float = 10.0         # มูลค่าซื้อขายเฉลี่ย 20 วัน (ล้านบาท)
    min_rs: float = 0.0                # ผลตอบแทน 6 เดือน เหนือดัชนี (สัดส่วน)


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["High"], df["Low"], df["Close"]
    up, dn = h.diff(), -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = 1 / n
    atr = tr.ewm(alpha=a, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=a, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=a, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=a, adjust=False).mean()


def evaluate(df: pd.DataFrame, bench: pd.DataFrame | None, p: Params) -> dict | None:
    """คืน dict ผลการตรวจ หรือ None หากข้อมูลไม่พอ"""
    if len(df) < p.min_bars:
        return None
    c = df["Close"]
    s50, s150, s200 = sma(c, 50), sma(c, 150), sma(c, 200)
    last = c.iloc[-1]
    hi52, lo52 = c.iloc[-252:].max(), c.iloc[-252:].min()
    r = rsi(c).iloc[-1]
    a = adx(df).iloc[-1]
    value_mb = (c * df["Volume"]).iloc[-20:].mean() / 1e6
    ret6 = last / c.iloc[-126] - 1 if len(c) > 126 else np.nan
    rs = np.nan
    if bench is not None and len(bench) > 126:
        rs = ret6 - (bench["Close"].iloc[-1] / bench["Close"].iloc[-126] - 1)

    checks = {
        "close>SMA50": last > s50.iloc[-1],
        "SMA50>SMA150": s50.iloc[-1] > s150.iloc[-1],
        "SMA150>SMA200": s150.iloc[-1] > s200.iloc[-1],
        "SMA200 rising": s200.iloc[-1] > s200.iloc[-21],
        "near 52w high": last >= hi52 * (1 - p.max_from_high),
        "above 52w low": last >= lo52 * (1 + p.min_above_low),
        "ADX": a >= p.min_adx,
        "RSI": p.rsi_range[0] <= r <= p.rsi_range[1],
        "liquidity": value_mb >= p.min_value_mb,
    }
    if bench is not None:
        checks["RS vs SET"] = bool(rs >= p.min_rs)

    # คะแนนจัดอันดับ: โมเมนตัม 6 เดือน + ความแรงเทรนด์ + ความใกล้ high
    score = (0 if np.isnan(ret6) else ret6 * 100) + a + (last / hi52) * 20
    return {
        "close": last, "ret_6m_%": ret6 * 100, "rs_vs_set_%": rs * 100,
        "rsi": r, "adx": a, "from_52w_high_%": (last / hi52 - 1) * 100,
        "value_mb": value_mb, "passed": sum(checks.values()), "total": len(checks),
        "uptrend": all(checks.values()), "failed": [k for k, v in checks.items() if not v],
        "score": score,
    }


def screen(data: dict[str, pd.DataFrame], bench: pd.DataFrame | None, p: Params) -> pd.DataFrame:
    rows = []
    for sym, df in data.items():
        res = evaluate(df, bench, p)
        if res:
            rows.append({"symbol": sym.replace(".BK", ""), **res})
    cols = ["symbol", "close", "ret_6m_%", "rs_vs_set_%", "rsi", "adx",
            "from_52w_high_%", "value_mb", "passed", "total", "uptrend", "failed", "score"]
    out = pd.DataFrame(rows, columns=cols)
    return out.sort_values(["uptrend", "score"], ascending=False).reset_index(drop=True)
