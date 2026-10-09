#!/usr/bin/env python3
"""ค้นหาหุ้นไทยที่อยู่ในขาขึ้น

ตัวอย่าง:
  python main.py                         # สแกนรายชื่อตั้งต้น (ดึงจาก Yahoo Finance)
  python main.py --tickers PTT,CPALL,AOT # ระบุเอง
  python main.py --file my_list.txt      # อ่านจากไฟล์ (บรรทัดละ 1 ตัว)
  python main.py --csv-dir ./prices      # ใช้ไฟล์ CSV แทนการดึงออนไลน์
  python main.py --demo                  # ข้อมูลจำลอง (ทดสอบโปรแกรมเท่านั้น)
"""
import argparse
import sys

import pandas as pd

import data
from screener import Params, screen
from tickers import DEFAULT_SYMBOLS, SET_INDEX, to_yahoo


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickers", help="รายชื่อคั่นด้วยจุลภาค เช่น PTT,CPALL")
    ap.add_argument("--file", help="ไฟล์รายชื่อหุ้น บรรทัดละ 1 ตัว")
    ap.add_argument("--csv-dir", help="โฟลเดอร์ไฟล์ <SYMBOL>.csv")
    ap.add_argument("--demo", action="store_true", help="ใช้ข้อมูลจำลอง")
    ap.add_argument("--all", action="store_true", help="แสดงทั้งหมด ไม่เฉพาะที่ผ่านเกณฑ์")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", help="บันทึกผลเป็น CSV")
    ap.add_argument("--min-value", type=float, default=Params.min_value_mb, help="มูลค่าซื้อขายเฉลี่ยขั้นต่ำ (ล้านบาท)")
    ap.add_argument("--min-adx", type=float, default=Params.min_adx)
    ap.add_argument("--line", action="store_true", help="ส่งผลผ่าน LINE (ตั้ง LINE_CHANNEL_ACCESS_TOKEN, LINE_TO)")
    ap.add_argument("--line-dry-run", action="store_true", help="แสดงข้อความ LINE โดยไม่ส่งจริง")
    ap.add_argument("--no-rs", action="store_true", help="ไม่เทียบกับดัชนี SET")
    a = ap.parse_args(argv)

    if a.tickers:
        syms = a.tickers.split(",")
    elif a.file:
        syms = [l.strip() for l in open(a.file, encoding="utf-8") if l.strip() and not l.startswith("#")]
    else:
        syms = DEFAULT_SYMBOLS
    ysyms = [to_yahoo(s) for s in syms]
    want_bench = not a.no_rs

    if a.demo:
        prices = data.synthetic(ysyms + [SET_INDEX])
    elif a.csv_dir:
        prices = data.load_csv_dir(a.csv_dir, ysyms + [SET_INDEX])
    else:
        prices = data.fetch_yfinance(ysyms + ([SET_INDEX] if want_bench else []))
    bench = prices.pop(SET_INDEX, None) if want_bench else None
    prices.pop(SET_INDEX, None)

    missing = [s for s in ysyms if s not in prices]
    if not prices:
        print("ไม่ได้ข้อมูลราคาเลย (ตรวจสอบอินเทอร์เน็ต/ชื่อหุ้น)", file=sys.stderr)
        return 1
    if missing:
        print(f"[warn] ไม่มีข้อมูล {len(missing)} ตัว: {', '.join(m.replace('.BK','') for m in missing)}", file=sys.stderr)
    if want_bench and bench is None:
        print("[warn] ไม่มีข้อมูลดัชนี SET จึงข้ามเกณฑ์ RS", file=sys.stderr)

    p = Params(min_value_mb=a.min_value, min_adx=a.min_adx)
    res = screen(prices, bench, p)
    shown = res if a.all else res[res["uptrend"]]
    shown = shown.head(a.top)

    pd.set_option("display.width", 200)
    fmt = shown.drop(columns=["uptrend"]).copy()
    fmt["failed"] = fmt["failed"].apply(lambda x: ", ".join(x))
    print(f"\nสแกน {len(res)} ตัว ผ่านเกณฑ์ขาขึ้นครบ {int(res['uptrend'].sum())} ตัว\n")
    print(fmt.round(2).to_string(index=False) if len(fmt) else "(ไม่มีหุ้นผ่านเกณฑ์)")
    if a.out:
        res.to_csv(a.out, index=False, encoding="utf-8-sig")
        print(f"\nบันทึกแล้ว: {a.out}")
    if a.line or a.line_dry_run:
        import notify
        msg = notify.format_message(res, a.top)
        if a.line_dry_run:
            print("\n--- LINE (dry run) ---\n" + msg)
        else:
            try:
                notify.send_line(msg)
                print("\nส่ง LINE แล้ว")
            except RuntimeError as e:
                print(f"[error] ส่ง LINE ไม่สำเร็จ: {e}", file=sys.stderr)
                return 2
    print("\n* ผลนี้เป็นเครื่องมือคัดกรองทางเทคนิค ไม่ใช่คำแนะนำการลงทุน")
    return 0


if __name__ == "__main__":
    sys.exit(main())
