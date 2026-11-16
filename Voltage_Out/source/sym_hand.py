# ------------------------------------------------------------------ extra / replacement symbols
def hpass(name, kind, ref):
    ln = 2.794 if kind == "C" else 1.27
    pins = [("1", "~", "passive", -3.81, 0, 0, ln), ("2", "~", "passive", 3.81, 0, 180, ln)]
    if kind == "R":
        body = ["(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.254) (type default)) (fill (type none)))"]
    elif kind == "FB":
        body = ["(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.254) (type default)) (fill (type outline)))"]
    elif kind == "L":
        body = ["(arc (start -2.54 0) (mid -1.905 0.635) (end -1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))",
                "(arc (start -1.27 0) (mid -0.635 0.635) (end 0 0) (stroke (width 0.254) (type default)) (fill (type none)))",
                "(arc (start 0 0) (mid 0.635 0.635) (end 1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))",
                "(arc (start 1.27 0) (mid 1.905 0.635) (end 2.54 0) (stroke (width 0.254) (type default)) (fill (type none)))"]
    else:
        body = ["(polyline (pts (xy -0.762 2.032) (xy -0.762 -2.032)) (stroke (width 0.508) (type default)) (fill (type none)))",
                "(polyline (pts (xy 0.762 2.032) (xy 0.762 -2.032)) (stroke (width 0.508) (type default)) (fill (type none)))"]
    SYMS[name] = dict(pins=pins, body=body, ref=ref, ref_at=(0, 2.54), val_at=(0, -2.54),
                      bbox=(-2.54, 1.27, 2.54, -1.27), names=False, kind="hpass")
hpass("R_H", "R", "R"); hpass("C_H", "C", "C"); hpass("FB_H", "FB", "FB"); hpass("L_H", "L", "L")

# LED with anode on top (current flows downwards to FGND)
SYMS["LED_DN"] = dict(pins=[("2", "A", "passive", 0, 3.81, 270, 1.27), ("1", "K", "passive", 0, -3.81, 90, 1.27)],
    body=["(polyline (pts (xy -1.27 1.016) (xy 1.27 1.016) (xy 0 -1.016) (xy -1.27 1.016)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.27 -1.016) (xy 1.27 -1.016)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy 1.778 0.508) (xy 2.794 -0.508)) (stroke (width 0.2) (type default)) (fill (type none)))",
          "(polyline (pts (xy 1.778 -0.508) (xy 2.794 -1.524)) (stroke (width 0.2) (type default)) (fill (type none)))"],
    ref="D", ref_at=(2.54, 1.27), val_at=(2.54, -1.27), bbox=(-1.524, 2.54, 1.524, -2.54), names=False, kind="passive")

# P-MOSFET drawn in a horizontal power path; gate at the bottom. order = "DS" (drain left) or "SD" (source left)
def pmos_h(name, order):
    left, right = (("3", "D"), ("2", "S")) if order == "DS" else (("2", "S"), ("3", "D"))
    body = ["(circle (center 0 0.508) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy -1.905 -0.762) (xy 1.905 -0.762)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy -2.032 0) (xy -1.27 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy -0.508 0) (xy 0.508 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy 1.27 0) (xy 2.032 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy -2.54 0) (xy -1.651 0) (xy -1.651 1.524)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy 2.54 0) (xy 1.651 0) (xy 1.651 1.524)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy 0 0) (xy 0 1.524) (xy " + ("1.651" if order == "DS" else "-1.651") + " 1.524)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy 0 0.254) (xy -0.381 0.889) (xy 0.381 0.889) (xy 0 0.254)) (stroke (width 0.2) (type default)) (fill (type outline)))"]
    SYMS[name] = dict(pins=[(left[0], left[1], "passive", -5.08, 0, 0, 2.54), (right[0], right[1], "passive", 5.08, 0, 180, 2.54),
                            ("1", "G", "input", 0, -5.08, 90, 2.54)],
                      body=body, ref="Q", ref_at=(0, 4.318), val_at=(4.0, -3.2), bbox=(-2.794, 3.302, 2.794, -2.286),
                      names=False, kind="qh")
pmos_h("Q_PMOS_DS", "DS"); pmos_h("Q_PMOS_SD", "SD")

# op-amp with the inverting input on top (matches how inverting / I-V stages are drawn)
TRI = ["(polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) (stroke (width 0.254) (type default)) (fill (type background)))"]
def oa2(pm, pp, po):
    return dict(pins=[(pm, "-", "input", -7.62, 2.54, 0, 2.54), (pp, "+", "input", -7.62, -2.54, 0, 2.54), (po, "~", "output", 7.62, 0, 180, 2.54)],
                body=TRI, bbox=(-5.08, 5.08, 5.08, -5.08))
SYMS["OPA2187"] = dict(ref="U", ref_at=(0, 6.35), val_at=(0, -6.35), names=True, kind="ic", units={
    1: oa2("2", "3", "1"), 2: oa2("6", "5", "7"),
    3: dict(pins=[("8", "V+", "power_in", -5.08, 2.54, 0, 2.54), ("4", "V-", "power_in", -5.08, -2.54, 0, 2.54)],
            body=["(rectangle (start -2.54 5.08) (end 2.54 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))"],
            bbox=(-2.54, 5.08, 2.54, -5.08))})

# DAC8812 split into its two multiplying channels + the digital interface
def box(w2, h2): return [f"(rectangle (start {fmt(-w2)} {fmt(h2)}) (end {fmt(w2)} {fmt(-h2)}) (stroke (width 0.254) (type default)) (fill (type background)))"]
def dch(vref, agnd, rfb, iout, ch):
    return dict(pins=[(vref, "VREF" + ch, "input", -10.16, 2.54, 0, 2.54), (agnd, "AGND" + ch, "power_in", -10.16, -2.54, 0, 2.54),
                      (rfb, "RFB" + ch, "passive", 10.16, 2.54, 180, 2.54), (iout, "IOUT" + ch, "output", 10.16, -2.54, 180, 2.54)],
                body=box(7.62, 5.08) + [f'(text "x D{ch}" (at 0 0 0) (effects (font (size 1.524 1.524))))'],
                bbox=(-7.62, 5.08, 7.62, -5.08))
dig = [("13", "VDD", "power_in"), ("11", "~{CS}", "input"), ("16", "CLK", "input"), ("9", "SDI", "input"), ("15", "~{LDAC}", "input"), ("10", "~{RS}", "input")]
SYMS["DAC8812"] = dict(ref="U", ref_at=(0, 10.16), val_at=(0, -10.16), names=True, kind="ic", units={
    1: dch("2", "4", "1", "3", "A"), 2: dch("7", "5", "8", "6", "B"),
    3: dict(pins=[(n, nm, t, -10.16, 6.35 - 2.54 * i, 0, 2.54) for i, (n, nm, t) in enumerate(dig)] +
                 [("14", "MSB", "input", 10.16, 6.35, 180, 2.54), ("12", "DGND", "power_in", 10.16, 3.81, 180, 2.54)],
            body=box(7.62, 8.89), bbox=(-7.62, 8.89, 7.62, -8.89))})

# photorelay: LED pins on top, switch in line left-right
SYMS["TLP172AM"] = dict(
    pins=[("1", "A", "passive", -2.54, 7.62, 270, 2.54), ("2", "K", "passive", 2.54, 7.62, 270, 2.54),
          ("4", "D", "passive", -7.62, -2.54, 0, 2.54), ("3", "D", "passive", 7.62, -2.54, 180, 2.54)],
    body=box(5.08, 5.08) + [
        "(polyline (pts (xy -2.54 5.08) (xy -2.54 3.81)) (stroke (width 0.2) (type default)) (fill (type none)))",
        "(polyline (pts (xy 2.54 5.08) (xy 2.54 3.81) (xy 0 3.81)) (stroke (width 0.2) (type default)) (fill (type none)))",
        "(polyline (pts (xy -3.302 3.81) (xy -1.778 3.81) (xy -2.54 2.54) (xy -3.302 3.81)) (stroke (width 0.2) (type default)) (fill (type none)))",
        "(polyline (pts (xy -3.302 2.54) (xy -1.778 2.54)) (stroke (width 0.2) (type default)) (fill (type none)))",
        "(polyline (pts (xy -2.54 2.54) (xy -2.54 1.778) (xy 0 1.778) (xy 0 3.81)) (stroke (width 0.2) (type default)) (fill (type none)))",
        "(polyline (pts (xy -5.08 -2.54) (xy -2.032 -2.54) (xy 1.524 -1.016)) (stroke (width 0.254) (type default)) (fill (type none)))",
        "(polyline (pts (xy 2.032 -2.54) (xy 5.08 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
        "(polyline (pts (xy -1.27 0.762) (xy -0.254 -0.508)) (stroke (width 0.2) (type default)) (fill (type none)))"],
    ref="K", ref_at=(0, 6.858 + 2.54), val_at=(0, -6.35), bbox=(-5.08, 5.08, 5.08, -5.08), names=False, kind="ic")
SYMS["PWR_FLAG"]["kind"] = "flag"

