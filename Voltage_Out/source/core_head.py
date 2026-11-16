"""KiCad 8 schematic for the isolated CAN-to-N-type thermocouple emulator, fully wired.
Signals are drawn as orthogonal wires (auto-routed on a 1.27 mm grid); supplies use power symbols."""
import uuid, json, heapq, re, sys
from collections import defaultdict

PROJECT = "thermocouple_emulator"
LIB = "TCEmu"
ROOT = str(uuid.uuid4())
G = 2.54
S = 1.27  # routing grid


def U(): return str(uuid.uuid4())
def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
def q(s): return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) (hide yes))"

# ================================================================ symbols
SYMS = {}
def ic(name, left, right, width=15.24, ref="U"):
    n = max(len(left), len(right))
    top = G * ((n - 1) // 2 + (1 if n % 2 == 0 else 0))
    pins = []
    for i, (num, pname, ptype) in enumerate(left):
        pins.append((num, pname, ptype, -width / 2 - G, top - i * G, 0, G))
    for i, (num, pname, ptype) in enumerate(right):
        pins.append((num, pname, ptype, width / 2 + G, top - i * G, 180, G))
    y1, y2 = top + G, top - (n - 1) * G - G
    body = f"(rectangle (start {fmt(-width/2)} {fmt(y1)}) (end {fmt(width/2)} {fmt(y2)}) (stroke (width 0.254) (type default)) (fill (type background)))"
    SYMS[name] = dict(pins=pins, body=[body], ref=ref, ref_at=(0, y1 + 1.27), val_at=(0, y2 - 1.27),
                      bbox=(-width / 2, y1, width / 2, y2), names=True, kind="ic")

def passive(name, kind, ref):
    ln = 2.794 if kind == "C" else 1.27
    pins = [("1", "~", "passive", 0, 3.81, 270, ln), ("2", "~", "passive", 0, -3.81, 90, ln)]
    if kind == "R":
        body = ["(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))"]
    elif kind == "FB":
        body = ["(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type outline)))"]
    else:
        body = ["(polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))",
                "(polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))"]
    SYMS[name] = dict(pins=pins, body=body, ref=ref, ref_at=(2.54, 1.27), val_at=(2.54, -1.27),
                      bbox=(-2.032, 2.54, 2.032, -2.54), names=False, kind="passive")

def conn(name, labels, side):
    n = len(labels)
    pins = []
    for i, lab in enumerate(labels):
        x, ang = (5.08, 180) if side == "R" else (-5.08, 0)
        pins.append((str(i + 1), lab, "passive", x, -i * G, ang, G))
    y1, y2 = 1.27, -(n - 1) * G - 1.27
    body = f"(rectangle (start -2.54 {fmt(y1)}) (end 2.54 {fmt(y2)}) (stroke (width 0.254) (type default)) (fill (type background)))"
    SYMS[name] = dict(pins=pins, body=[body], ref="J", ref_at=(0, y1 + 1.27), val_at=(0, y2 - 1.27),
                      bbox=(-2.54, y1, 2.54, y2), names=True, kind="ic")

passive("R", "R", "R"); passive("C", "C", "C"); passive("FB", "FB", "FB")
conn("Conn_2_R", ["1", "2"], "R"); conn("Conn_4_R", ["1", "2", "3", "4"], "R")
conn("Conn_2_L", ["1", "2"], "L"); conn("Conn_1_L", ["1"], "L")
SYMS["PWR_FLAG"] = dict(pins=[("1", "pwr", "power_out", 0, -2.54, 90, 2.54)],
                        body=["(polyline (pts (xy 0 0) (xy -1.016 1.27) (xy 0 2.54) (xy 1.016 1.27) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none)))"],
                        ref="#FLG", ref_at=(0, 4.0), val_at=(0, 3.3), bbox=(-1.016, 2.54, 1.016, 0), names=False, kind="flag")
