# ---------------------------------------------------------------- hand layout of the analog output board (exec'd from aout.py)
OUTD = {0: (-1, 0), 180: (1, 0), 270: (0, -1), 90: (0, 1)}
def pang(ref, num, unit=1):
    for (n, nm, t, px, py, ang, ln) in pins_of((ref, unit)):
        if n == num: return ang
def T(ref, num, net, L=2.54, unit=1):
    """terminate a pin: stub outwards, then a label or power symbol (None -> no-connect)"""
    p = pin(ref, num, unit)
    if net is None: nc(p); return p
    dx, dy = OUTD[pang(ref, num, unit)]
    e = W(p, R_(p, dx * L, dy * L))
    if net in POWER: pw(net, e)
    else: lab(net, e, 0 if dx > 0 else 180 if dx < 0 else (90 if dy < 0 else 270))
    return e
def term(p, net, top):
    if net is None: return
    if net in POWER:
        pw(net, p, down=False) if (top and net == "-5V") else pw(net, p)
    else:
        s = -1 if top else 1
        e = W(p, R_(p, 0, s * 2.54), R_(p, 2.54, s * 2.54)); lab(net, e, 0)
def vt(ref, x, ytop, top=None, bot=None, sym=None):
    put(ref, x, ytop + 3.81, sym=sym)
    term(pin(ref, "1"), top, True); term(pin(ref, "2"), bot, False)
def divider(rt, rb, x, ytop, topnet, mid, c=None):
    vt(rt, x, ytop, topnet, None); vt(rb, x, ytop + 10.16, None, "GND")
    W(pin(rt, "2"), pin(rb, "1"))
    m = (x, ytop + 8.89)
    e = W(m, (x + 15.24, m[1])); lab(mid, e, 0)
    if c: vt(c, x + 12.7, m[1], None, "GND")


def snap(): return (set(PLACE), len(WIRES), len(PWR), len(LABELS), len(NCS), len(FRAMES), len(TEXTS))
def shift_since(s, dx, dy=0):
    keys, nw, np_, nl, nn, nf, nt = s
    for k in set(PLACE) - keys: PLACE[k]["x"] = round(PLACE[k]["x"] + dx, 4); PLACE[k]["y"] = round(PLACE[k]["y"] + dy, 4)
    WIRES[nw:] = [((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)) for a, b in WIRES[nw:]]
    WIRES[nw:] = [(tuple(round(c, 4) for c in a), tuple(round(c, 4) for c in b)) for a, b in WIRES[nw:]]
    PWR[np_:] = [(n, round(x + dx, 4), round(y + dy, 4), d) for n, x, y, d in PWR[np_:]]
    LABELS[nl:] = [(n, round(x + dx, 4), round(y + dy, 4), g) for n, x, y, g in LABELS[nl:]]
    NCS[nn:] = [(round(x + dx, 4), round(y + dy, 4)) for x, y in NCS[nn:]]
    FRAMES[nf:] = [(x1 + dx, y1 + dy, x2 + dx, y2 + dy) for x1, y1, x2, y2 in FRAMES[nf:]]
    TEXTS[nt:] = [(round(x + dx, 4), round(y + dy, 4), t, z) for x, y, t, z in TEXTS[nt:]]
s0 = snap()
# ================================================================== B. +16 V boost, -5 V, 3.3 V
frame(302.26, 30.48, 579.12, 106.68, "A. Output-stage rails from +5V: +16 V boost, -5 V charge pump")
yb = 50.8
pw("+5V", (322.58, yb))
W((322.58, yb), (387.35, yb))
vcap("C201", 327.66, yb); pw("GND", pin("C201", "2"))
put("U201", 360.68, 60.96)
W((345.44, yb), (345.44, 58.42), pin("U201", "5"))
vt("R201", 337.82, 53.34, None, None)
W((337.82, yb), pin("R201", "1")); W(pin("R201", "2"), pin("U201", "4"))
stubpw("GND", pin("U201", "2"), -2.54)
nc(pin("U201", "6"))
put("L201", 391.16, yb, sym="L_H")
W(pin("L201", "2"), (398.78, yb), (398.78, 58.42))
W(pin("U201", "1"), (398.78, 58.42))
put("D201", 403.86, 58.42)
W((398.78, 58.42), pin("D201", "2"))
W(pin("D201", "1"), (445.77, 58.42))
vcap("R202", 411.48, 58.42); vcap("R203", 411.48, 68.58)
W(pin("R202", "2"), pin("R203", "1")); pw("GND", pin("R203", "2"))
W(pin("U201", "3"), (375.92, 60.96), (375.92, 67.31), (411.48, 67.31))
vcap("C202", 421.64, 58.42); vcap("C203", 431.8, 58.42)
pw("GND", pin("C202", "2")); pw("GND", pin("C203", "2"))
put("FB201", 449.58, 58.42, sym="FB_H")
W(pin("FB201", "2"), (467.36, 58.42))
vcap("C204", 459.74, 58.42); pw("GND", pin("C204", "2"))
pw("+16V", (467.36, 58.42))
TEXTS.append((416.56, 53.34, "+15.9 V", 1.27))
TEXTS.append((322.58, 86.36, "MT3608 boost 5 V -> 15.9 V, ~0.3 A available\n(op-amp + 130 mA output stage)", 1.27))
# -5 V
put("U202", 500.38, 55.88)
W(pin("U202", "2"), (477.52, 53.34))
pw("+5V", (485.14, 53.34))
vcap("C205", 477.52, 53.34); pw("GND", pin("C205", "2"))
stubpw("GND", pin("U202", "4"), -2.54)
put("C206", 518.16, 48.26, sym="C_H")
W(pin("U202", "5"), (513.08, 53.34), (513.08, 48.26), pin("C206", "1"))
W(pin("U202", "3"), (523.24, 55.88), (523.24, 48.26), pin("C206", "2"))
W(pin("U202", "1"), (538.48, 58.42))
vcap("C207", 528.32, 58.42); pw("GND", pin("C207", "2"))
pw("-5V", (538.48, 58.42))
TEXTS.append((541.02, 57.15, "-5 V / 60 mA", 1.27))
shift_since(s0, -287.02)

# ================================================================== C. reference + dual DAC
frame(302.26, 30.48, 579.12, 106.68, "C. 2.5 V reference and dual 16-bit DAC (SPI)")
put("U601", 345.44, 63.5)
W(pin("U601", "2"), (322.58, 58.42)); pw("+5V", (327.66, 58.42))
vt("C601", 322.58, 58.42, None, "GND")
nc(pin("U601", "3")); stubpw("GND", pin("U601", "4"), -2.54)
for n in ("5", "1", "7", "8"): nc(pin("U601", n))
put("U602", 408.94, 63.5)
W(pin("U601", "6"), pin("U602", "2"))
vt("C602", 363.22, 58.42, None, "GND"); vt("C604", 373.38, 58.42, None, "GND")
stubpw("+5V", pin("U602", "1"), -5.08)
T("U602", "5", "DAC_SYNC", 7.62); T("U602", "6", "DAC_SCLK", 7.62); T("U602", "7", "DAC_DIN", 7.62)
stubpw("GND", pin("U602", "8"), -2.54)
T("U602", "4", "DAC_A", 7.62); T("U602", "3", "DAC_B", 7.62)
vt("C603", 449.58, 50.8, "+5V", "GND")
TEXTS.append((444.5, 68.58, "C603 at U602 VDD", 1.27))
TEXTS.append((322.58, 86.36, "U601 REF5025: 2.500 V +/-0.05 %, 3 ppm/C.  C602 4.7 uF required for stability.\n"
  "U602 DAC8552: dual 16 bit, VREF = 2.5 V -> 0-2.5 V, powers up at zero scale (both outputs 0 V).\n"
  "SPI mode 1 (CPOL 0, CPHA 1), 24-bit frames, up to 20 MHz.  Control byte: 0x10 = write + load A,\n"
  "0x24 = write + load B, 0x00 then 0x34 = update A and B together.", 1.27))
import re

_s = snap()
CH_TITLE = 'B. Channel A:  Vout = 5.02 x DAC_A = 0-12.55 V,  100 mA source (fold-back limit),  15 mA sink'; SHOW_HOW = True
_code = open("ch_snippet.py").read()

for _a, _b in [('"OUT_INT"', '"OUT_INT_A"'), ('"OUT"', '"AOUT_A"'), ('"LIM_B"', '"LIMB_A"'), ('"DAC_X"', '"DAC_A"'), ('VOUTX', 'VOUTA')]:
    _code = _code.replace(_a, _b)
exec(_code)
shift_since(_s, 0, 0)

_s = snap()
CH_TITLE = 'D. Channel B:  identical to channel A (refs 4xx)'; SHOW_HOW = False
_code = open("ch_snippet.py").read()
_code = re.sub(r'(?<![A-Z0-9])([A-Z]{1,2})3(\d\d)\b', lambda m: m.group(1) + "4" + m.group(2), _code)
for _a, _b in [('"OUT_INT"', '"OUT_INT_B"'), ('"OUT"', '"AOUT_B"'), ('"LIM_B"', '"LIMB_B"'), ('"DAC_X"', '"DAC_B"'), ('VOUTX', 'VOUTB')]:
    _code = _code.replace(_a, _b)
exec(_code)
shift_since(_s, 0, 147.32)
