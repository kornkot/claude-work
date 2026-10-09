"""ส่งผลสแกนผ่าน LINE Messaging API (LINE Notify ปิดบริการแล้ว)

ตั้งค่าผ่าน environment variable:
  LINE_CHANNEL_ACCESS_TOKEN  channel access token (long-lived) ของ Messaging API channel
  LINE_TO                    userId / groupId ปลายทาง (ถ้าไม่ตั้ง จะ broadcast ให้ผู้ติดตามบอททุกคน)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pandas as pd

API = "https://api.line.me/v2/bot/message/"
MAX_LEN = 4800  # LINE จำกัด 5000 ตัวอักษรต่อข้อความ


def format_message(res: pd.DataFrame, top: int = 15) -> str:
    hits = res[res["uptrend"]].head(top)
    head = f"📈 หุ้นไทยขาขึ้น {int(res['uptrend'].sum())}/{len(res)} ตัว"
    if hits.empty:
        return head + "\n(ไม่มีหุ้นผ่านเกณฑ์)"
    lines = [head]
    for i, (_, r) in enumerate(hits.iterrows(), 1):
        lines.append(f"{i}. {r['symbol']} {r['close']:.2f} | 6M {r['ret_6m_%']:+.1f}% | "
                     f"RSI {r['rsi']:.0f} ADX {r['adx']:.0f}")
    lines.append("\n* ไม่ใช่คำแนะนำการลงทุน")
    return "\n".join(lines)


def _chunks(text: str, size: int = MAX_LEN) -> list[str]:
    out, cur = [], ""
    for line in text.split("\n"):
        if cur and len(cur) + len(line) + 1 > size:
            out.append(cur)
            cur = ""
        cur += ("\n" if cur else "") + line
    return out + [cur] if cur else out


def send_line(text: str, token: str | None = None, to: str | None = None) -> None:
    token = token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    to = to or os.environ.get("LINE_TO")
    if not token:
        raise RuntimeError("ไม่พบ LINE_CHANNEL_ACCESS_TOKEN")
    endpoint = "push" if to else "broadcast"
    # push/broadcast รับได้สูงสุด 5 ข้อความต่อครั้ง
    msgs = [{"type": "text", "text": c} for c in _chunks(text)][:5]
    body = {"messages": msgs}
    if to:
        body["to"] = to
    req = urllib.request.Request(
        API + endpoint, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LINE API error {e.code}: {e.read().decode(errors='replace')}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"เชื่อมต่อ LINE ไม่ได้: {e.reason}") from e
