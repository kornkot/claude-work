"""แหล่งข้อมูลราคา: yfinance (จริง), โฟลเดอร์ CSV, และข้อมูลจำลองสำหรับทดสอบ"""
from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import pandas as pd

COLS = ["Open", "High", "Low", "Close", "Volume"]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[[c for c in COLS if c in df.columns]].dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.sort_index()


def fetch_yfinance(symbols: Iterable[str], period: str = "2y") -> dict[str, pd.DataFrame]:
    try:
        import yfinance as yf
    except ImportError as e:  # pragma: no cover
        raise SystemExit("ต้องติดตั้ง yfinance ก่อน: pip install yfinance") from e
    symbols = list(symbols)
    raw = yf.download(symbols, period=period, interval="1d", auto_adjust=True,
                      group_by="ticker", threads=True, progress=False)
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        try:
            sub = raw[s] if len(symbols) > 1 else raw
            sub = _clean(sub)
        except KeyError:
            continue
        if not sub.empty:
            out[s] = sub
    return out


def load_csv_dir(path: str, symbols: Iterable[str]) -> dict[str, pd.DataFrame]:
    """อ่านไฟล์ <path>/<SYMBOL>.csv ที่มีคอลัมน์ Date,Open,High,Low,Close,Volume"""
    out = {}
    for s in symbols:
        base = s.replace(".BK", "").replace("^", "")
        f = os.path.join(path, f"{base}.csv")
        if os.path.exists(f):
            out[s] = _clean(pd.read_csv(f, index_col=0, parse_dates=True))
    return out


def synthetic(symbols: Iterable[str], days: int = 500, seed: int = 7) -> dict[str, pd.DataFrame]:
    """ข้อมูลจำลอง: หุ้นแต่ละตัวสุ่มแนวโน้ม (ขึ้น/ลง/ไซด์เวย์) เพื่อทดสอบโปรแกรมเท่านั้น"""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    out = {}
    for s in symbols:
        drift = rng.choice([0.0012, 0.0, -0.0008])
        vol = rng.uniform(0.012, 0.025)
        close = 50 * np.exp(np.cumsum(rng.normal(drift, vol, days)))
        spread = close * rng.uniform(0.003, 0.012, days)
        out[s] = pd.DataFrame({
            "Open": close * (1 + rng.normal(0, 0.003, days)),
            "High": close + spread, "Low": close - spread, "Close": close,
            "Volume": rng.integers(1_000_000, 30_000_000, days).astype(float),
        }, index=idx)
    return out
