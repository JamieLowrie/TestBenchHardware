"""CAN analog output board: 0-12 V / 100 mA, protected, CH32V203 + TJA1044. Hand-laid KiCad 8 schematic."""
import sys
exec(open("core_head.py").read())
PROJECT = "analog_out_12v_b"; LIB = "AOut"
exec(open("sym_rtd.py").read())
exec(open("sym_hand.py").read())
exec(open("aout_syms.py").read())

def P(ref, sym, val, lcsc, fp, nets, unit=None, dnf=False):
    d = dict(ref=ref, sym=sym, val=val, lcsc=lcsc, fp=fp, nets=nets, dnf=dnf)
    if unit: d["unit"] = unit
    return d
F = dict(R4="Resistor_SMD:R_0402_1005Metric", R6="Resistor_SMD:R_0603_1608Metric", R8="Resistor_SMD:R_0805_2012Metric",
         R12="Resistor_SMD:R_1206_3216Metric", C4="Capacitor_SMD:C_0402_1005Metric", C6="Capacitor_SMD:C_0603_1608Metric",
         C8="Capacitor_SMD:C_0805_2012Metric", C12="Capacitor_SMD:C_1206_3216Metric", SOT23="Package_TO_SOT_SMD:SOT-23",
         SOT236="Package_TO_SOT_SMD:SOT-23-6", SOT235="Package_TO_SOT_SMD:SOT-23-5", SOT223="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
         SOD523="Diode_SMD:D_SOD-523", SMA="Diode_SMD:D_SMA", SMB="Diode_SMD:D_SMB", L4030="Inductor_SMD:L_Changjiang_FNR4030S",
         GH4="Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal", FB8="Inductor_SMD:L_0805_2012Metric")
R10K, R100K, R4K7, R1K = "C25744", "C25741", "C25900", "C11702"
C100N, C100N4, C10U50, C22U, C1U = "C14663", "C1525", "C13585", "C59461", "C28323"
parts = [
    # ---------------- A. input protection + 5 V buck
    P("U201", "MT3608", "MT3608", "C84817", F["SOT236"], {"5": "+5V", "4": "BOOST_EN", "2": "GND", "1": "BOOST_SW", "3": "BOOST_FB", "6": None}),
    P("R201", "R", "100k", R100K, F["R4"], {"1": "+5V", "2": "BOOST_EN"}),
    P("C201", "C", "22u", C22U, F["C6"], {"1": "+5V", "2": "GND"}),
    P("L201", "L", "4.7uH 3.2A", "C167874", F["L4030"], {"1": "+5V", "2": "BOOST_SW"}),
    P("D201", "D_SCH_H", "SS34", "C8678", F["SMA"], {"2": "BOOST_SW", "1": "+16V_RAW"}),
    P("R202", "R", "255k 1%", "C25857", F["R6"], {"1": "+16V_RAW", "2": "BOOST_FB"}),
    P("R203", "R", "10k 1%", R10K, F["R4"], {"1": "BOOST_FB", "2": "GND"}),
    P("C202", "C", "10u 50V", C10U50, F["C12"], {"1": "+16V_RAW", "2": "GND"}),
    P("C203", "C", "10u 50V", C10U50, F["C12"], {"1": "+16V_RAW", "2": "GND"}),
    P("FB201", "FB", "100R@100M", "C1015", F["FB8"], {"1": "+16V_RAW", "2": "+16V"}),
    P("C204", "C", "10u 50V", C10U50, F["C12"], {"1": "+16V", "2": "GND"}),
    P("U202", "TPS60403", "TPS60403DBVR", "C11338", F["SOT235"], {"2": "+5V", "4": "GND", "5": "CP_FLYP", "3": "CP_FLYN", "1": "-5V"}),
    P("C205", "C", "1u", C1U, F["C8"], {"1": "+5V", "2": "GND"}),
    P("C206", "C", "1u", C1U, F["C8"], {"1": "CP_FLYP", "2": "CP_FLYN"}),
    P("C207", "C", "1u", C1U, F["C8"], {"1": "-5V", "2": "GND"}),
    P("U301", "DAC80501", "DAC80501ZDGSR", "C1852033", "Package_SO:MSOP-10_3x3mm_P0.5mm",
      {"1": "+3V3", "5": "+3V3", "6": "I2C_SCL", "8": "I2C_SDA", "7": "GND", "4": "GND", "2": "DAC_OUT", "10": "DAC_REF", "3": None, "9": None}),
    P("C301", "C", "100n", C100N, F["C6"], {"1": "+3V3", "2": "GND"}),
    P("C302", "C", "100n", C100N, F["C6"], {"1": "DAC_REF", "2": "GND"}),
    P("R301", "R_H", "2k", "C22975", F["R6"], {"1": "DAC_OUT", "2": "DAC_F"}),
    P("C303", "C", "3n3 C0G", "C1609", F["C6"], {"1": "DAC_F", "2": "GND"}),
    P("U302", "OPA197", "OPA197IDBVR", "C221351", F["SOT235"], {"4": "FB_N", "3": "DAC_F", "1": "OA", "5": "+16V", "2": "-5V"}),
    P("C304", "C", "100n 50V", C100N, F["C6"], {"1": "+16V", "2": "GND"}),
    P("C305", "C", "100n", C100N, F["C6"], {"1": "-5V", "2": "GND"}),
    P("R302", "R_H", "40k2 0.1%", "C2989618", F["R6"], {"1": "OUT", "2": "FB_N"}),
    P("R303", "R_H", "10k 0.1%", "C95204", F["R6"], {"1": "GND", "2": "FB_N"}),
    P("C306", "C_H", "47p C0G", "C1671", F["C6"], {"1": "FB_N", "2": "OA"}),
    P("Q301", "Q_NPN_SOT223", "BCP56-16", "C2909805", F["SOT223"], {"1": "B1", "2": "+16V", "3": "E1"}),
    P("R307", "R_H", "1k5", "C26030", F["R12"], {"1": "OA", "2": "B1"}),
    P("R308", "R", "4R7", "C17675", F["R8"], {"1": "E1", "2": "E1B"}),
    P("Q305", "Q_NPN_SOT23_M", "MMBT3904", "C20526", F["SOT23"], {"1": "LIM_B", "2": "E1B", "3": "B1"}),
    P("D301", "D_SCH_DN", "SS34", "C8678", F["SMA"], {"2": "E1B", "1": "OUT_INT"}),
    P("Q302", "Q_PNP_SOT223", "BCP53-16", "C85085", F["SOT223"], {"1": "B2", "3": "E2", "2": "-5V"}),
    P("R309", "R_H", "10k 1206", "C17902", F["R12"], {"1": "OA", "2": "B2"}),
    P("R310", "R", "47R", "C17714", F["R8"], {"1": "OUT_INT", "2": "E2"}),
    P("Q306", "Q_PNP_SOT23_M", "MMBT3906", "C916375", F["SOT23"], {"1": "E2", "2": "OUT_INT", "3": "B2"}),
    P("R311", "R_H", "10k 1206", "C17902", F["R12"], {"1": "OA", "2": "OUT_INT"}),
    P("R312", "R", "10k 1206", "C17902", F["R12"], {"1": "OUT_INT", "2": "-5V"}),
    P("C307", "C", "1n 50V", "C1588", F["C6"], {"1": "OUT_INT", "2": "GND"}),
    P("R315", "R_H", "1k", R1K, F["R4"], {"1": "LIM_B", "2": "E1"}),
    P("R316", "R", "22k", "C25768", F["R4"], {"1": "+16V", "2": "LIM_B"}),
    P("R317", "R", "4k7 DNF", R4K7, F["R4"], {"1": "+3V3", "2": "I2C_SCL"}, dnf=True),
    P("R318", "R", "4k7 DNF", R4K7, F["R4"], {"1": "+3V3", "2": "I2C_SDA"}, dnf=True),
    P("R314", "R_H", "10R 1206", "C17903", F["R12"], {"1": "OUT_INT", "2": "OUT"}),
    P("D302", "D_TVS_BI", "SMBJ33CA", "C110447", F["SMB"], {"1": "OUT", "2": "GND"}),
    P("J301", "Conn_2_L", "AOUT", "C474892", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
      {"1": "OUT", "2": "GND"}),
    # ---------------- F. monitoring
    # ---------------- D. MCU + CAN
]
for p in parts:
    if p["ref"] in ("D301", "R310", "Q305", "Q306", "R308", "R315", "R307"): p["hide_lcsc"] = True
NETS = {(p["ref"], p.get("unit", 1)): p for p in parts}

exec(open("place_helpers.py").read())
def pw(net, p, down=None):
    style = POWER[net]
    if down is None: down = style != "rail" or net.startswith("-")
    PWR.append((net, p[0], p[1], down))

exec(open("sub2_layout.py").read())

TITLE_BLOCK = ('  (title_block (title "Analog output 0-12 V / 100 mA (sub-sheet)") (date "2026-11-13") (rev "B")'
               ' (comment 1 "Needs +5V, +3V3, GND from the core supply sheet. I2C to the MCU sheet via hierarchical labels")'
               ' (comment 2 "Check SOT-223, inductor and terminal footprints against the chosen parts before layout"))')
NOTES_AT = (299.72, 35.56)
HIER = {"I2C_SCL": "input", "I2C_SDA": "bidirectional"}
PAPER = "A3"
NOTES = """NOTES
1. Sub-sheet. Power from the global symbols +5V (~0.4 A peak),
   +3V3 (~2 mA) and GND; rename them if your core sheet differs.
   +16V and -5V are made on this sheet.
2. Only interface: I2C_SCL / I2C_SDA (hierarchical labels).
   DAC80501 at 0x48 (A0 = GND). It powers up at 0 V.
3. Vout = DAC x (1 + R302/R303) = DAC x 5.02. DAC in 0-2.5 V mode
   (GAIN reg 0x04 = 0x0101) -> 0-12.55 V, 0.19 mV/LSB.
4. Source 100 mA up to 12 V (loads >= 120 R). Fold-back limit:
   ~120 mA at 12 V, ~25 mA into a short. Sink 15 mA to 0.000 V.
5. Protection is all hardware: short to GND or to a battery up to
   32 V is safe indefinitely. No monitoring, no firmware action.
6. Speed (simulated): 1-12 V step settles to 0.1 % in ~47 us,
   100 mV step to +/-1 mV in ~32 us. Clean into 10 nF on the pin;
   for 100 nF and above ramp the DAC (or add series R).
7. Accuracy: feedback from the terminal, 0.1 % gain resistors,
   OPA197 25 uV offset. Gain error < 0.2 % before calibration."""

exec(open("hand_emit.py").read())
json.dump([{k: v for k, v in p.items() if k != "nets"} for p in parts if not p["ref"].startswith("#")], open("parts_sub2.json", "w"))
