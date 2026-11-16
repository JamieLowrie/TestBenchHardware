# ---------------------------------------------------------------- RTD emulator: symbols + parts
# (executed inside gen_rtd.py after the shared symbol helpers)

def diode(name):
    pins = [("1", "K", "passive", 0, 3.81, 270, 1.27), ("2", "A", "passive", 0, -3.81, 90, 1.27)]
    body = ["(polyline (pts (xy -1.27 -1.016) (xy 1.27 -1.016) (xy 0 1.016) (xy -1.27 -1.016)) (stroke (width 0.254) (type default)) (fill (type none)))",
            "(polyline (pts (xy -1.27 1.016) (xy 1.27 1.016)) (stroke (width 0.254) (type default)) (fill (type none)))"]
    if name == "D_Z":
        body.append("(polyline (pts (xy -1.27 1.016) (xy -1.778 0.508)) (stroke (width 0.254) (type default)) (fill (type none)))")
    if name == "LED":
        body.append("(polyline (pts (xy 1.778 0) (xy 2.794 1.016)) (stroke (width 0.2) (type default)) (fill (type none)))")
        body.append("(polyline (pts (xy 1.778 -1.016) (xy 2.794 0)) (stroke (width 0.2) (type default)) (fill (type none)))")
    SYMS[name] = dict(pins=pins, body=body, ref="D", ref_at=(2.54, 1.27), val_at=(2.54, -1.27),
                      bbox=(-1.524, 2.54, 1.524, -2.54), names=False, kind="passive")
diode("D_Z"); diode("D_TVS"); diode("LED")
passive("L", "FB", "L")
SYMS["L"]["body"] = ["(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))",
                     "(polyline (pts (xy -1.016 1.27) (xy 1.016 1.27)) (stroke (width 0.2) (type default)) (fill (type none)))",
                     "(polyline (pts (xy -1.016 0) (xy 1.016 0)) (stroke (width 0.2) (type default)) (fill (type none)))",
                     "(polyline (pts (xy -1.016 -1.27) (xy 1.016 -1.27)) (stroke (width 0.2) (type default)) (fill (type none)))"]
passive("JP", "R", "JP")
SYMS["JP"]["body"] = ["(arc (start 0 0.508) (mid -1.016 1.524) (end 0 2.54) (stroke (width 0.254) (type default)) (fill (type outline)))",
                      "(arc (start 0 -0.508) (mid 1.016 -1.524) (end 0 -2.54) (stroke (width 0.254) (type default)) (fill (type outline)))"]

# P-channel MOSFET: G left, S top, D bottom
SYMS["Q_PMOS"] = dict(
    pins=[("1", "G", "input", -5.08, 0, 0, 2.54), ("2", "S", "passive", 2.54, 5.08, 270, 2.54), ("3", "D", "passive", 2.54, -5.08, 90, 2.54)],
    body=["(polyline (pts (xy -2.54 0) (xy -1.778 0)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.778 1.905) (xy -1.778 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 2.032) (xy -1.016 -2.032)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 1.27) (xy 2.54 1.27) (xy 2.54 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 -1.27) (xy 2.54 -1.27) (xy 2.54 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -1.016 0) (xy 2.54 0) (xy 2.54 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy 0.254 0) (xy -0.508 0.508) (xy -0.508 -0.508) (xy 0.254 0)) (stroke (width 0.2) (type default)) (fill (type outline)))",
          "(circle (center 0.762 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="Q", ref_at=(4.572, 1.27), val_at=(4.572, -1.27), bbox=(-2.54, 2.794, 3.556, -2.794), names=False, kind="passive")

SYMS["XTAL"] = dict(
    pins=[("1", "1", "passive", -5.08, 0, 0, 2.54), ("2", "2", "passive", 5.08, 0, 180, 2.54)],
    body=["(rectangle (start -1.143 1.778) (end 1.143 -1.778) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy -2.032 1.27) (xy -2.032 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))",
          "(polyline (pts (xy 2.032 1.27) (xy 2.032 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))"],
    ref="Y", ref_at=(-10.16, 0), val_at=(0, -3.81), bbox=(-2.54, 2.54, 2.54, -2.54), names=False, kind="ic")

conn("Conn_4_L", ["1", "2", "3", "4"], "L")
ic("MCP16311", [("4", "VIN", "power_in"), ("3", "EN", "input"), ("2", "VCC", "power_out"),
                ("5", "PGND", "power_in"), ("8", "AGND", "power_in"), ("9", "EP", "passive")],
   [("7", "BOOST", "passive"), ("6", "SW", "output"), ("1", "VFB", "input")])
ic("A0515S-1WR3", [("2", "VIN", "power_in"), ("1", "GND", "power_in")],
   [("6", "+VO", "power_out"), ("4", "-VO", "power_out"), ("5", "0V", "power_out")], ref="PS")
ic("HT7533-1", [("2", "VIN", "power_in"), ("1", "GND", "power_in")], [("3", "VOUT", "power_out")], width=12.7)
ic("ISO1042", [("1", "VCC1", "power_in"), ("2", "TXD", "input"), ("3", "RXD", "output"), ("4", "GND1", "power_in")],
   [("8", "VCC2", "power_in"), ("7", "CANH", "bidirectional"), ("6", "CANL", "bidirectional"), ("5", "GND2", "power_in")])
ic("PESD1CAN", [("1", "K1", "passive"), ("2", "K2", "passive")], [("3", "A", "passive")], width=10.16, ref="D")
ic("CH32V203G6U6",
   [("17", "VDD", "power_in"), ("5", "VDDA", "power_in"), ("4", "NRST", "input"), ("1", "BOOT0/PB8", "input"),
    ("2", "PD0/OSC_IN", "input"), ("3", "PD1/OSC_OUT", "output"), ("6", "PA0", "bidirectional"), ("7", "PA1", "bidirectional"),
    ("10", "PA4", "bidirectional"), ("8", "PA2", "bidirectional"), ("9", "PA3", "bidirectional"),
    ("16", "VSS", "power_in"), ("29", "EP", "power_in")],
   [("11", "PA5", "bidirectional"), ("12", "PA6", "bidirectional"), ("13", "PA7", "bidirectional"), ("14", "PB0", "bidirectional"),
    ("15", "PB1", "bidirectional"), ("18", "PA9", "bidirectional"), ("19", "PA10/PA11", "bidirectional"), ("20", "PA12", "bidirectional"),
    ("21", "PA13/SWDIO", "bidirectional"), ("22", "PA14/SWCLK", "bidirectional"), ("23", "PA15", "bidirectional"),
    ("24", "PB3", "bidirectional"), ("25", "PB4", "bidirectional"), ("26", "PB5", "bidirectional"),
    ("27", "PB6", "bidirectional"), ("28", "PB7", "bidirectional")], width=25.4)
ic("DAC8812",
   [("13", "VDD", "power_in"), ("11", "~{CS}", "input"), ("16", "CLK", "input"), ("9", "SDI", "input"),
    ("15", "~{LDAC}", "input"), ("10", "~{RS}", "input"), ("14", "MSB", "input"), ("12", "DGND", "power_in"),
    ("4", "AGNDA", "power_in"), ("5", "AGNDB", "power_in")],
   [("2", "VREFA", "input"), ("1", "RFBA", "passive"), ("3", "IOUTA", "output"),
    ("7", "VREFB", "input"), ("8", "RFBB", "passive"), ("6", "IOUTB", "output")], width=17.78)
ic("ADS1115", [("8", "VDD", "power_in"), ("9", "SDA", "bidirectional"), ("10", "SCL", "input"),
               ("2", "ALERT/RDY", "open_collector"), ("1", "ADDR", "input"), ("3", "GND", "power_in")],
   [("4", "AIN0", "input"), ("5", "AIN1", "input"), ("6", "AIN2", "input"), ("7", "AIN3", "input")], width=17.78)
ic("TLP172AM", [("1", "A", "passive"), ("2", "K", "passive")], [("4", "D", "passive"), ("3", "D", "passive")], width=10.16, ref="K")

TRI = ["(polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) (stroke (width 0.254) (type default)) (fill (type background)))"]
def oa(pp, pm, po):
    return dict(pins=[(pp, "+", "input", -7.62, 2.54, 0, 2.54), (pm, "-", "input", -7.62, -2.54, 0, 2.54), (po, "~", "output", 7.62, 0, 180, 2.54)],
                body=TRI, bbox=(-5.08, 5.08, 5.08, -5.08))
SYMS["OPA2187"] = dict(ref="U", ref_at=(0, 6.35), val_at=(0, -6.35), names=True, kind="ic", units={
    1: oa("3", "2", "1"), 2: oa("5", "6", "7"),
    3: dict(pins=[("8", "V+", "power_in", -5.08, 2.54, 0, 2.54), ("4", "V-", "power_in", -5.08, -2.54, 0, 2.54)],
            body=["(rectangle (start -2.54 5.08) (end 2.54 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))"],
            bbox=(-2.54, 5.08, 2.54, -5.08))})


POWER = {"GND": "gnd", "FGND": "isognd", "+5V_BUS": "rail", "VSYS": "rail", "+15V": "rail", "-15V": "rail", "+3V3F": "rail"}
PWR_BODY = {
    "rail": ["(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))",
             "(polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))"],
    "gnd": ["(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))"],
    "isognd": ["(polyline (pts (xy 0 0) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))",
               "(polyline (pts (xy -1.524 -1.27) (xy 1.524 -1.27)) (stroke (width 0) (type default)) (fill (type none)))",
               "(polyline (pts (xy -1.016 -1.905) (xy 1.016 -1.905)) (stroke (width 0) (type default)) (fill (type none)))",
               "(polyline (pts (xy -0.508 -2.54) (xy 0.508 -2.54)) (stroke (width 0) (type default)) (fill (type none)))"],
}
for net, style in POWER.items():
    up = style == "rail"
    SYMS["PWR_" + net] = dict(pins=[("1", net, "power_in", 0, 0, 90 if up else 270, 0)], body=PWR_BODY[style], ref="#PWR",
                              ref_at=(0, 0), val_at=(0, 3.556 if up else -3.81), bbox=None, names=False, kind="power",
                              net=net, style=style)

