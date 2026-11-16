"""BOM for the CAN analog output board, from parts_sub3.json written by aout.py."""
import json, re
from collections import OrderedDict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
parts = json.load(open("parts_sub3.json"))
# LCSC stock from lcsc.com product pages, 2026-11-13 (prior boards: 2026-11-08)
STOCK = {"C1852033": 223, "C221351": 80069, "C2060768": 2904, "C2909805": 8135, "C85085": 32165, "C5383002": 3672,
         "C84817": 90711, "C11338": 25950, "C327215": 700, "C2989618": 6700, "C95204": 499900, "C861589": 22440,
         "C326758": 216940, "C550643": 230, "C916375": 49050, "C474892": 10470, "C2157795": 32150, "C110447": 1980,
         "C189895": 14540, "C2681220": 55150, "C550633": 143140, "C15771": 94370, "C5142280": 6479, "C115962": 282470,
         "C37593": 2802, "C26030": 18600, "C25768": 581300, "C22975": 5306500, "C17714": 277200, "C136020": 2275, "C11341": 24615}
BASIC = {"C17675", "C25744", "C25900", "C25741", "C14663", "C1525", "C13585", "C59461", "C1015", "C19666", "C1554", "C11702",
         "C57112", "C22787", "C25765", "C21190", "C28323", "C1609", "C1588", "C1671", "C25104", "C17872", "C17634",
         "C17902", "C17903", "C20526", "C8545", "C15127", "C8678", "C5446", "C72043", "C25821", "C25857"}
NOTE = {
 "C136020": "Dual 16-bit SPI DAC, powers up at zero scale. $3.72 at 100+",
 "C11341": "2.5 V reference, 3 ppm/C",
 "C19666": "REF5025 output cap (1-50 uF needed for stability)",
 "C550643": "Only 230 in stock: reserve, or use BZX84-C30 (SOT-23) with a footprint change",
 "C327215": "700 in stock; any 0.22 R 1 % 0805 >= 1/8 W works (e.g. UNI-ROYAL 0805W8F220LT5F)",
 "C2989618": "UNI-ROYAL TC0350B4022T5F, 0.1 %, 50 ppm. Sets the output gain",
 "C2060768": "INA240A2DR, gain 50, SOIC-8",
 "C2909805": "Source transistor, SOT-223, 1 A / 80 V",
 "C85085": "Sink transistor, Nexperia BCP53-16,115",
 "C167874": "Same 4.7 uH 4030 as your existing boards; check footprint",
 "C474892": "Cixi Kefa KF350-3.5-2P, 3.5 mm; check footprint against the drawing",
 "C22787": "Do not fit (CAN termination option)",
 "C5142280": "Same MCU as the existing boards",
 "C37593": "Same ADC as the RTD board",
 "C26030": "1206: carries ~10 mA from the op-amp in a short to GND",
 "C17902": "1206 (10k): these see up to 37 V in a short to battery",
 "C17675": "Fold-back sense resistor",
 "C25768": "Fold-back: sets how fast the limit falls with Vce",
 "": "Solder jumper on the PCB, no part",
}
rows = OrderedDict()
for p in parts:
    key = (p["val"], p.get("lcsc") or "", p.get("fp", ""), p.get("dnf", False))
    rows.setdefault(key, []).append(p["ref"])
def refkey(s):
    m = re.match(r"([A-Z]+)(\d+)", s); return (m.group(1), int(m.group(2)))
wb = Workbook(); ws = wb.active; ws.title = "BOM"; F = "Arial"
ws["A1"] = "Dual analog output sub-sheet rev C, 0-12 V / 100 mA: BOM with LCSC / JLCPCB parts"; ws["A1"].font = Font(name=F, bold=True, size=13)
ws["A2"] = ("Stock from lcsc.com product pages on 2026-11-13 (parts shared with the RTD board: 2026-11-08). "
            "JLCPCB's own stock pages need JavaScript and could not be read; LCSC stock is what JLCPCB draws on for global sourcing. "
            "Basic = JLCPCB basic part (no extended-part fee). 'not checked' = common part not looked up this time.")
ws["A2"].font = Font(name=F, size=9, italic=True); ws.merge_cells("A2:H2"); ws["A2"].alignment = Alignment(wrap_text=True); ws.row_dimensions[2].height = 40
hdr = ["Designators", "Qty", "Value", "LCSC #", "Footprint", "Class", "LCSC stock", "Notes"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(4, c, h); cell.font = Font(name=F, bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin = Side(style="thin", color="BFBFBF"); r = 5
for (val, lcsc, fp, dnf), refs in sorted(rows.items(), key=lambda kv: refkey(sorted(kv[1], key=refkey)[0])):
    refs = sorted(refs, key=refkey); st = STOCK.get(lcsc)
    vals = [", ".join(refs), 0 if dnf else f'=LEN(A{r})-LEN(SUBSTITUTE(A{r},",",""))+1', val, lcsc or "(none)",
            fp.split(":")[-1], "Basic" if lcsc in BASIC else ("" if not lcsc else "Extended"),
            st if st else ("basic part" if lcsc in BASIC else ("not checked" if lcsc else "")), NOTE.get(lcsc, "")]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v); cell.font = Font(name=F, size=10); cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)
        cell.alignment = Alignment(vertical="top", wrap_text=c in (1, 5, 8))
    ws.cell(r, 7).number_format = '#,##0'
    if st is not None and st < 1000:
        for c in range(1, 9): ws.cell(r, c).fill = PatternFill("solid", fgColor="FFF2CC")
    r += 1
last = r - 1
ws.cell(r + 1, 6, "Placed parts").font = Font(name=F, bold=True)
ws.cell(r + 1, 7, f"=SUM(B5:B{last})").font = Font(name=F, bold=True)
ws.cell(r + 2, 6, "BOM lines").font = Font(name=F); ws.cell(r + 2, 7, f"=COUNTA(A5:A{last})").font = Font(name=F)
ws.cell(r + 3, 1, "Yellow rows: under 1,000 in stock. Reserve them before ordering.").font = Font(name=F, size=9, italic=True)
for c, wdt in enumerate([34, 6, 20, 12, 36, 9, 13, 62], 1): ws.column_dimensions[get_column_letter(c)].width = wdt
ws.freeze_panes = "A5"
wb.save("analog_out_12v_dual_BOM.xlsx"); print("rows", last - 4)
