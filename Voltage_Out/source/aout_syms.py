# ---------------------------------------------------------------- symbols specific to the analog-output board
def bjt(name, polarity, nums, mirror=False):
    """nums = dict(B=, C=, E=). NPN: C top, E bottom. PNP: E top, C bottom. Base on the left (or right if mirror)."""
    sx = -1 if mirror else 1
    top, bot = ("C", "E") if polarity == "NPN" else ("E", "C")
    pins = [(nums["B"], "B", "input", sx * -5.08, 0, 0 if not mirror else 180, 2.54),
            (nums[top], top, "passive", sx * 2.54, 5.08, 270, 2.54),
            (nums[bot], bot, "passive", sx * 2.54, -5.08, 90, 2.54)]
    f = lambda x: fmt(sx * x)
    body = [f"(circle (center {f(0.762)} 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))",
            f"(polyline (pts (xy {f(-2.54)} 0) (xy {f(-1.016)} 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
            f"(polyline (pts (xy {f(-1.016)} 1.905) (xy {f(-1.016)} -1.905)) (stroke (width 0.508) (type default)) (fill (type none)))",
            f"(polyline (pts (xy {f(-1.016)} 0.635) (xy {f(2.54)} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
            f"(polyline (pts (xy {f(-1.016)} -0.635) (xy {f(2.54)} -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))"]
    if polarity == "NPN":   # arrow on emitter (bottom), pointing out
        body.append(f"(polyline (pts (xy {f(1.778)} -1.524) (xy {f(2.286)} -2.413) (xy {f(1.27)} -2.286) (xy {f(1.778)} -1.524)) (stroke (width 0.2) (type default)) (fill (type outline)))")
    else:                   # arrow on emitter (top), pointing in
        body.append(f"(polyline (pts (xy {f(-0.254)} 1.27) (xy {f(0.254)} 2.159) (xy {f(0.762)} 1.143) (xy {f(-0.254)} 1.27)) (stroke (width 0.2) (type default)) (fill (type outline)))")
    SYMS[name] = dict(pins=pins, body=body, ref="Q", ref_at=(sx * 4.572 - (3.0 if mirror else 0), 1.27), val_at=(sx * 4.572 - (3.0 if mirror else 0), -1.27),
                      bbox=(-2.54, 2.794, 3.556, -2.794), names=False, kind="passive" if not mirror else "qm")
bjt("Q_NPN_SOT223", "NPN", dict(B="1", C="2", E="3"))
bjt("Q_PNP_SOT223", "PNP", dict(B="1", C="2", E="3"))
bjt("Q_NPN_SOT23_M", "NPN", dict(B="1", E="2", C="3"), mirror=True)
bjt("Q_PNP_SOT23_M", "PNP", dict(B="1", E="2", C="3"), mirror=True)

# N-MOSFET: G left, D top, S bottom (2N7002: 1 G, 2 S, 3 D)
SYMS["Q_NMOS"] = dict(
    pins=[("1", "G", "input", -5.08, 0, 0, 2.54), ("3", "D", "passive", 2.54, 5.08, 270, 2.54), ("2", "S", "passive", 2.54, -5.08, 90, 2.54)],
    body=["(polyline (pts (xy -2.54 0) (xy -1.778 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.778 1.905) (xy -1.778 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 2.032) (xy -1.016 -2.032)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 1.27) (xy 2.54 1.27) (xy 2.54 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 -1.27) (xy 2.54 -1.27) (xy 2.54 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 0) (xy 2.54 0) (xy 2.54 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -0.762 0) (xy 0 0.508) (xy 0 -0.508) (xy -0.762 0)) (stroke (width 0.2) (type default)) (fill (type outline)))",
          "(circle (center 0.762 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="Q", ref_at=(4.572, 1.27), val_at=(4.572, -1.27), bbox=(-2.54, 2.794, 3.556, -2.794), names=False, kind="passive")

# Schottky, anode on top, cathode at the bottom (current flows down)
SYMS["D_SCH_DN"] = dict(pins=[("2", "A", "passive", 0, 3.81, 270, 1.27), ("1", "K", "passive", 0, -3.81, 90, 1.27)],
    body=["(polyline (pts (xy -1.27 1.016) (xy 1.27 1.016) (xy 0 -1.016) (xy -1.27 1.016)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.778 -0.508) (xy -1.778 -1.016) (xy 1.778 -1.016) (xy 1.778 -1.524)) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="D", ref_at=(2.54, 1.27), val_at=(2.54, -1.27), bbox=(-1.778, 2.54, 1.778, -2.54), names=False, kind="passive")
# Schottky horizontal, anode left
SYMS["D_SCH_H"] = dict(pins=[("2", "A", "passive", -3.81, 0, 0, 1.27), ("1", "K", "passive", 3.81, 0, 180, 1.27)],
    body=["(polyline (pts (xy -1.016 1.27) (xy -1.016 -1.27) (xy 1.016 0) (xy -1.016 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy 0.508 1.778) (xy 1.016 1.778) (xy 1.016 -1.778) (xy 1.524 -1.778)) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="D", ref_at=(0, 2.54), val_at=(0, -2.54), bbox=(-2.54, 1.27, 2.54, -1.27), names=False, kind="hpass")
# bidirectional TVS (vertical)
SYMS["D_TVS_BI"] = dict(pins=[("1", "A1", "passive", 0, 3.81, 270, 1.27), ("2", "A2", "passive", 0, -3.81, 90, 1.27)],
    body=["(polyline (pts (xy -1.27 2.286) (xy 1.27 2.286) (xy 0 0) (xy -1.27 2.286)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.27 -2.286) (xy 1.27 -2.286) (xy 0 0) (xy -1.27 -2.286)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.778 0.508) (xy -1.27 0) (xy 1.27 0) (xy 1.778 -0.508)) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="D", ref_at=(2.54, 1.27), val_at=(2.54, -1.27), bbox=(-1.778, 2.54, 1.778, -2.54), names=False, kind="passive")
passive("TH", "R", "TH")
SYMS["TH"]["body"] = ["(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))",
                      "(polyline (pts (xy -2.032 -2.54) (xy -2.032 -1.778) (xy 2.032 1.778)) (stroke (width 0.2) (type default)) (fill (type none)))"]

ic("LMR51420", [("3", "VIN", "power_in"), ("5", "EN", "input"), ("1", "GND", "power_in")],
   [("6", "CB", "passive"), ("2", "SW", "output"), ("4", "FB", "input")])
ic("MT3608", [("5", "IN", "power_in"), ("4", "EN", "input"), ("2", "GND", "power_in")],
   [("1", "SW", "output"), ("3", "FB", "input"), ("6", "NC", "no_connect")])
ic("TPS60403", [("2", "IN", "power_in"), ("4", "GND", "power_in")],
   [("5", "CFLY+", "passive"), ("3", "CFLY-", "passive"), ("1", "OUT", "power_out")])
ic("XC6206", [("3", "VIN", "power_in"), ("1", "GND", "power_in")], [("2", "VOUT", "power_out")], width=12.7)
ic("TJA1044", [("3", "VCC", "power_in"), ("5", "VIO", "power_in"), ("1", "TXD", "input"), ("4", "RXD", "output"),
               ("8", "STB", "input"), ("2", "GND", "power_in"), ("9", "EP", "passive")],
   [("7", "CANH", "bidirectional"), ("6", "CANL", "bidirectional")], width=15.24)
ic("DAC80501", [("1", "VDD", "power_in"), ("5", "SPI2C", "input"), ("6", "SCL", "input"), ("8", "SDA", "bidirectional"),
                ("7", "A0", "input"), ("4", "AGND", "power_in")],
   [("2", "VOUT", "output"), ("10", "VREFIO", "passive"), ("3", "NC", "no_connect"), ("9", "NC", "no_connect")], width=15.24)
ic("INA240", [("6", "VS", "power_in"), ("7", "REF1", "input"), ("8", "IN+", "input"), ("1", "IN-", "input"),
               ("3", "REF2", "input"), ("2", "GND", "power_in")],
   [("5", "OUT", "output"), ("4", "NC", "no_connect")], width=15.24)
ic("ADS1115", [("8", "VDD", "power_in"), ("1", "ADDR", "input"), ("9", "SDA", "bidirectional"), ("10", "SCL", "input"),
               ("2", "ALERT/RDY", "open_collector"), ("3", "GND", "power_in")],
   [("4", "AIN0", "input"), ("5", "AIN1", "input"), ("6", "AIN2", "input"), ("7", "AIN3", "input")], width=17.78)
# single op-amp, inverting input on top, supply pins on the triangle
SYMS["OPA197"] = dict(
    pins=[("4", "-", "input", -7.62, 2.54, 0, 2.54), ("3", "+", "input", -7.62, -2.54, 0, 2.54), ("1", "~", "output", 7.62, 0, 180, 2.54),
          ("5", "V+", "power_in", -2.54, 7.62, 270, 3.81), ("2", "V-", "power_in", -2.54, -7.62, 90, 3.81)],
    body=["(polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) (stroke (width 0.254) (type default)) (fill (type background)))"],
    ref="U", ref_at=(3.81, 6.35), val_at=(5.08, -5.08), bbox=(-5.08, 5.08, 5.08, -5.08), names=True, kind="opa")

POWER = {"GND": "gnd", "VIN": "rail", "+5V": "rail", "+3V3": "rail", "+16V": "rail", "-5V": "rail"}
for net, style in POWER.items():
    up = style == "rail"
    SYMS["PWR_" + net] = dict(pins=[("1", net, "power_in", 0, 0, 90 if up else 270, 0)], body=PWR_BODY[style], ref="#PWR",
                              ref_at=(0, 0), val_at=(0, 3.556 if up else -3.81), bbox=None, names=False, kind="power",
                              net=net, style=style)

SYMS["XTAL"]["ref_at"] = (0, 3.81); SYMS["XTAL"]["val_at"] = (0, -3.81)
