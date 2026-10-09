# Thai Stock Uptrend Finder

คัดกรองหุ้นไทย (SET) ที่อยู่ในขาขึ้นด้วยเกณฑ์ Trend Template:

1. ราคา > SMA50 > SMA150 > SMA200
2. SMA200 ชี้ขึ้น (เทียบ 20 วันก่อน)
3. ราคาอยู่ห่างจาก high 52 สัปดาห์ไม่เกิน 25% และสูงกว่า low 52 สัปดาห์ ≥ 30%
4. ADX ≥ 20 (เทรนด์มีแรง), RSI อยู่ช่วง 50–80 (ไม่อ่อนแรง/ไม่ร้อนเกิน)
5. มูลค่าซื้อขายเฉลี่ย 20 วัน ≥ 10 ล้านบาท
6. ผลตอบแทน 6 เดือนเหนือดัชนี SET (Relative Strength)

เรียงอันดับด้วยคะแนนจากโมเมนตัม 6 เดือน + ADX + ความใกล้ high

## ใช้งาน
```bash
pip install -r requirements.txt
python main.py                          # สแกนรายชื่อตั้งต้น
python main.py --tickers PTT,CPALL,AOT
python main.py --file list.txt --out result.csv
python main.py --all                    # ดูทั้งหมดพร้อมเหตุผลที่ไม่ผ่าน
python main.py --csv-dir ./prices       # ใช้ CSV (Date,Open,High,Low,Close,Volume)
python main.py --demo                   # ข้อมูลจำลองเพื่อทดสอบ
```
ปรับเกณฑ์ได้ใน `Params` (screener.py) ปรับรายชื่อหุ้นใน `tickers.py`
ข้อมูลจาก Yahoo Finance (suffix `.BK`) อาจล่าช้า/คลาดเคลื่อนได้ — ไม่ใช่คำแนะนำการลงทุน

## แจ้งเตือนผ่าน LINE
ใช้ LINE Messaging API (LINE Notify ปิดบริการแล้ว) สร้างช่อง Messaging API ที่ LINE Developers Console แล้วออก channel access token
```bash
export LINE_CHANNEL_ACCESS_TOKEN=xxxx
export LINE_TO=Uxxxxxxxx      # userId หรือ groupId; ไม่ตั้ง = broadcast ให้ผู้ติดตามบอททุกคน
python main.py --line          # สแกนแล้วส่งผล
python main.py --demo --line-dry-run   # ดูข้อความโดยไม่ส่ง
```
ตั้งเวลารันอัตโนมัติด้วย cron เช่น `30 17 * * 1-5 cd /path/thai_uptrend && python main.py --line` (หลังตลาดปิด)
