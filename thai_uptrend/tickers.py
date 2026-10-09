"""รายชื่อหุ้นไทยตั้งต้น (กลุ่มใหญ่/สภาพคล่องสูงใน SET50/SET100 โดยประมาณ)

องค์ประกอบดัชนีเปลี่ยนทุกครึ่งปี จึงควรอัปเดตเอง หรือส่งรายชื่อผ่าน --tickers / --file
Yahoo Finance ใช้ suffix ".BK" สำหรับตลาดหลักทรัพย์แห่งประเทศไทย
"""

SET_INDEX = "^SET.BK"

DEFAULT_SYMBOLS = """
ADVANC AOT AWC BAM BANPU BBL BCP BDMS BEM BGRIM BH BJC BTS CBG CENTEL CCET CHG
COM7 CPALL CPF CPN CRC DELTA EA EGCO GLOBAL GPSC GULF HMPRO INTUCH IVL JMART JMT
KBANK KCE KKP KTB KTC LH MINT MTC OR OSP PTT PTTEP PTTGC RATCH SAWAD SCB SCC SCGP
SPALI STA STGT TASCO TCAP THANI TIDLOR TISCO TOP TRUE TTB TU VGI WHA
""".split()


def to_yahoo(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.startswith("^") or s.endswith(".BK"):
        return s
    return f"{s}.BK"
