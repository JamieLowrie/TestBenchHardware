"""Human-readable schematic: real wires, left->right flow, labels only between blocks."""
import copy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from design import PARTS, uid
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.schitems import (SchematicSymbol, LocalLabel, Connection, NoConnect, Junction,
                                    SymbolProjectInstance, SymbolProjectPath, Text, PolyLine,
                                    HierarchicalSheetInstance)
from kiutils.items.common import Position, Property, Effects, Font, Justify, Stroke, TitleBlock

PROJ = "phase_sense"
OUT = sys.argv[1]
SYMDIR = "/usr/share/kicad/symbols"
G = 2.54
def g(n): return round(n * G, 3)
byref = {p["ref"]: p for p in PARTS}

# ---------------------------------------------------------------- library handling
libs = {}
def libsym(lib_id):
    nick, name = lib_id.split(":")
    path = os.path.join(os.path.dirname(OUT), f"{PROJ}.kicad_sym") if nick == PROJ else f"{SYMDIR}/{nick}.kicad_sym"
    if path not in libs: libs[path] = SymbolLib.from_file(path)
    return next(s for s in libs[path].symbols if s.entryName == name)

sch = Schematic.create_new()
sch.version = 20230121; sch.generator = "eeschema"
sch.uuid = uid("root-sheet")
sch.paper.paperSize = "A3"
sch.titleBlock = TitleBlock(title="3-Channel Motor Phase Current Sense (ACS37002, +/-66.7 A)",
                            date="2026-11-17", revision="E",
                            comments={1: "Output: 1.65 V @ 0 A, 19.8 mV/A, ratiometric to 3V3",
                                      2: "RC 1k/10n -> fc 16 kHz; OCF threshold ~77 A (VOC = 0.77 V)",
                                      3: "For CH32V203 12-bit ADC, VDDA = same 3V3 rail"})
sch.sheetInstances = [HierarchicalSheetInstance(instancePath="/", page="1")]
added = set()
def ensure_lib(lib_id):
    if lib_id in added: return
    s = copy.deepcopy(libsym(lib_id)); s.libraryNickname, s.entryName = lib_id.split(":")
    sch.libSymbols.append(s); added.add(lib_id)

def eff(just=None, hide=False, size=1.27, bold=False):
    e = Effects(font=Font(height=size, width=size, bold=bold), hide=hide)
    if just: e.justify = Justify(horizontally=just)
    return e

# ---------------------------------------------------------------- placement
placed = {}
def xf(lx, ly, rot, mirror):
    x, y = lx, -ly                                   # lib y-up -> sheet y-down
    for _ in range((rot // 90) % 4): x, y = y, -x    # CCW on screen
    if mirror == "y": x = -x
    return x, y

def place(lib_id, ref, value, x, y, fp="", lcsc="", su=None, rot=0, mirror=None,
          rpos=None, vpos=None, rjust="left", vjust="left", show_ref=True, show_val=True):
    ensure_lib(lib_id)
    nick, name = lib_id.split(":")
    s = SchematicSymbol(libraryNickname=nick, entryName=name, position=Position(x, y, rot), unit=1,
                        inBom=not ref.startswith("#"), onBoard=True, uuid=su or uid("sym-" + ref))
    if mirror: s.mirror = mirror
    fa = 90 if rot in (90, 270) else 0
    s.properties = [
        Property(key="Reference", value=ref, id=0, position=Position(*(rpos or (x + 2.54, y - 1.27)), fa), effects=eff(rjust, hide=not show_ref)),
        Property(key="Value", value=value, id=1, position=Position(*(vpos or (x + 2.54, y + 1.27)), fa), effects=eff(vjust, hide=not show_val)),
        Property(key="Footprint", value=fp, id=2, position=Position(x, y, 0), effects=eff(hide=True)),
        Property(key="Datasheet", value="~", id=3, position=Position(x, y, 0), effects=eff(hide=True)),
    ]
    if lcsc: s.properties.append(Property(key="LCSC", value=lcsc, id=4, position=Position(x, y, 0), effects=eff(hide=True)))
    pins = [p for u in libsym(lib_id).units for p in u.pins]
    s.pins = {p.number: uid(f"pin-{ref}-{p.number}") for p in pins}
    s.instances = [SymbolProjectInstance(name=PROJ, paths=[SymbolProjectPath(sheetInstancePath=f"/{sch.uuid}", reference=ref, unit=1)])]
    sch.schematicSymbols.append(s)
    ends = {}
    for p in pins:
        dx, dy = xf(p.position.X, p.position.Y, rot, mirror)
        ends[p.number] = (round(x + dx, 3), round(y + dy, 3))
    placed[ref] = ends
    return ends

def part(ref, x, y, **kw):
    p = byref[ref]
    return place(p["lib"], ref, p["value"], x, y, p["fp"], p["lcsc"], su=p["uuid"], **kw)

def pe(ref, num): return placed[ref][num]

pwr = [0]
def power(net, x, y):
    pwr[0] += 1
    ref = f"#PWR{pwr[0]:03d}"
    if net == "GND":
        place("power:GND", ref, "GND", x, y, show_ref=False, vpos=(x, y + 4.4), vjust=None)
    else:
        place("power:+3V3", ref, "+3V3", x, y, show_ref=False, vpos=(x, y - 3.6), vjust=None)

# ---------------------------------------------------------------- wiring
segs = []
def W(*pts):
    for a, b in zip(pts, pts[1:]):
        segs.append((tuple(map(lambda v: round(v, 3), a)), tuple(map(lambda v: round(v, 3), b))))

def label(net, x, y, d="right"):
    ang = {"right": 0, "up": 90, "left": 180, "down": 270}[d]
    just = "right" if d in ("left", "down") else "left"
    sch.labels.append(LocalLabel(text=net, position=Position(x, y, ang), effects=eff(just), uuid=uid(f"lbl-{net}-{x}-{y}")))

def nc(ref, num):
    x, y = pe(ref, num); sch.noConnects.append(NoConnect(position=Position(x, y), uuid=uid(f"nc-{ref}-{num}")))

def text(t, x, y, size=1.27, bold=False):
    for i, line in enumerate(t.split("\n")):
        sch.texts.append(Text(text=line, position=Position(x, round(y + i * size * 1.75, 3), 0),
                              effects=eff("left", size=size, bold=bold), uuid=uid(f"t{line}{x}{y}")))

def box(x1, y1, x2, y2):
    sch.graphicalItems.append(PolyLine(points=[Position(x1, y1), Position(x2, y1), Position(x2, y2), Position(x1, y2), Position(x1, y1)],
                                       stroke=Stroke(width=0.2, type="dash"), uuid=uid(f"box{x1}{y1}")))

def finish_wires():
    pts = {p for s in segs for p in s} | {p for e in placed.values() for p in e.values()}
    out = []
    for a, b in segs:
        cut = [a, b]
        for p in pts:
            if p in (a, b): continue
            if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]): cut.append(p)
            if a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]): cut.append(p)
        cut = sorted(set(cut), key=lambda q: (q[0], q[1]))
        out += list(zip(cut, cut[1:]))
    count = {}
    for a, b in out:
        sch.graphicalItems.append(Connection(type="wire", points=[Position(*a), Position(*b)], stroke=Stroke(width=0), uuid=uid(f"w{a}{b}")))
        for p in (a, b): count[p] = count.get(p, 0) + 1
    for p, n in count.items():
        if n >= 3: sch.junctions.append(Junction(position=Position(*p), diameter=0, uuid=uid(f"j{p}")))

# ---------------------------------------------------------------- one sensor channel
def channel(k, X, x0, y0):
    U, Jin, Jout = f"U{k}", f"J{2*k}", f"J{2*k+1}"
    Cb, Rh, Rl, Cv, Rf, Cf = f"C{k}1", f"R{k}1", f"R{k}2", f"C{k}2", f"R{k}3", f"C{k}3"
    box(x0 - g(18.5), y0 - g(15), x0 + g(23), y0 + g(19))
    text(f"PHASE {X} CURRENT SENSOR", x0 - g(18), y0 - g(13.5), 2.0, bold=True)
    part(U, x0, y0, rpos=(x0 - 10.16, y0 - 13.97), vpos=(x0 - 12.7, y0 + 13.97))

    # ---- primary: lugs -> IP+ bus, IP- bus -> lug
    xb, xl = x0 - g(7), x0 - g(12)
    for lug, pins, yj, net, txt in ((Jin, "1234", y0 - g(2.5), f"P{X}_IN", "FROM DRIVE"),
                                     (Jout, "5678", y0 + g(2.5), f"P{X}_OUT", "TO MOTOR")):
        ys = []
        for n in pins:
            px, py = pe(U, n); W((px, py), (xb, py)); ys.append(py)
        W((xb, min(ys)), (xb, max(ys)))
        part(lug, xl - g(2), yj, mirror="y", rpos=(xl - g(2.5), yj - g(1)), rjust="right", show_val=False)
        W(pe(lug, "1"), (xb, yj))
        label(net, xl + g(1), yj)
        text(f"{txt}, M4 T44001", xl - g(5), yj + g(1.2), 1.0)

    # ---- 3V3 rail with VCC bypass and VOC divider feed
    rail = y0 - g(11)
    vx, vy = pe(U, "10")
    W((vx, vy), (vx, rail))
    power("+3V3", vx, rail)
    part(Cb, x0 + g(6), rail + g(1.5))
    W((vx, rail), pe(Cb, "1"))
    W(pe(Cb, "2"), (pe(Cb, "2")[0], pe(Cb, "2")[1] + G)); power("GND", pe(Cb, "2")[0], pe(Cb, "2")[1] + G)

    # ---- VOC divider (sets overcurrent threshold)
    xd = x0 + g(16)
    ox, oy = pe(U, "11")
    part(Rh, xd, oy - g(1.5))
    part(Rl, xd, oy + g(1.5))
    part(Cv, xd + g(4), oy + g(1.5))
    W((pe(Cb, "1")), (xd, rail), pe(Rh, "1"))
    W((ox, oy), (xd + g(4), oy))
    label(f"VOC_{X}", ox + g(5), oy)
    for c in (Rl, Cv):
        b = pe(c, "2"); W(b, (b[0], b[1] + G)); power("GND", b[0], b[1] + G)
    nc(U, "13")

    # ---- VIOUT -> RC filter -> ADC output
    ix, iy = pe(U, "12")
    part(Rf, x0 + g(10), iy, rot=90, rpos=(x0 + g(10), iy - 2.2), vpos=(x0 + g(10), iy + 2.4), rjust=None, vjust=None)
    part(Cf, x0 + g(13), iy + g(1.5))
    W((ix, iy), pe(Rf, "1"))
    label(f"VIOUT_{X}", ix + g(0.5), iy)
    W(pe(Rf, "2"), (x0 + g(14.5), iy))
    label(f"I{X}", x0 + g(14.5), iy)
    b = pe(Cf, "2"); W(b, (b[0], b[1] + G)); power("GND", b[0], b[1] + G)

    # ---- OCF (open drain, wired-OR)
    fx, fy = pe(U, "9")
    W((fx, fy), (fx + g(2), fy)); label("FAULT_N", fx + g(2), fy)

    # ---- GAIN_SEL_0/1 + GND tied together
    gx = x0 + g(6)
    gys = []
    for n in ("16", "14", "15"):
        px, py = pe(U, n); W((px, py), (gx, py)); gys.append(py)
    W((gx, min(gys)), (gx, max(gys)), (gx, max(gys) + G)); power("GND", gx, max(gys) + G)
    text("GAIN_SEL=00 -> +/-66.7 A", gx + g(1.5), max(gys) + g(1.8), 1.0)

    # ---- phase voltage divider (needs board GND linked to drive DC-)
    Rt1, Rt2, Rb, Cd = f"R{k}4", f"R{k}5", f"R{k}6", f"C{k}4"
    yd = y0 + g(14)
    text(f"PHASE {X} VOLTAGE: V{X} = V(P{X}_OUT) x 2.7k / 96.7k  (100 V -> 2.79 V, FS 118 V), fc ~2.8 kHz",
         x0 - g(17.5), yd - g(3.5), 1.0)
    part(Rt1, x0 - g(10), yd, rot=90, rpos=(x0 - g(10), yd - 2.2), vpos=(x0 - g(10), yd + 2.4), rjust=None, vjust=None)
    part(Rt2, x0 - g(4), yd, rot=90, rpos=(x0 - g(4), yd - 2.2), vpos=(x0 - g(4), yd + 2.4), rjust=None, vjust=None)
    part(Rb, x0 + g(2), yd + g(1.5))
    part(Cd, x0 + g(6), yd + g(1.5))
    W((x0 - g(15), yd), pe(Rt1, "1")); label(f"P{X}_OUT", x0 - g(15), yd, "left")
    W(pe(Rt1, "2"), pe(Rt2, "1")); label(f"VMID_{X}", pe(Rt1, "2")[0] + g(0.5), yd)
    W(pe(Rt2, "2"), (x0 + g(9), yd)); label(f"V{X}", x0 + g(9), yd)
    for c in (Rb, Cd):
        b = pe(c, "2"); W(b, (b[0], b[1] + G)); power("GND", b[0], b[1] + G)
    text("2 x 47k in series: 150 V rating", x0 - g(12), yd + g(2.2), 1.0)

for k, X in enumerate("ABC", start=1):
    channel(k, X, g(24 + (k - 1) * 43), g(25))

# ---------------------------------------------------------------- MCU interface block
x0, y0 = g(22), g(62)
box(x0 - g(14), y0 - g(11), x0 + g(46), y0 + g(14))
text("MCU INTERFACE  (controller lives on the same PCB, X < 42 mm)", x0 - g(13.5), y0 - g(9.5), 2.0, bold=True)
part("J1", x0, y0, rpos=(x0 - 1.27, y0 - g(5.5)), vpos=(x0 - 1.27, y0 + g(6.5)))
p1 = pe("J1", "1"); W(p1, (p1[0] - g(3), p1[1]), (p1[0] - g(3), p1[1] - g(2))); power("+3V3", p1[0] - g(3), p1[1] - g(2))
for n in "2345678":
    net = byref["J1"]["pins"][n]
    px, py = pe("J1", n); W((px, py), (px - g(5), py)); label(net, px - g(5), py, "left")
ga, gb = pe("J1", "9"), pe("J1", "10")
W(ga, (ga[0] - g(2), ga[1]), (gb[0] - g(2), gb[1]), (gb[0] - g(2), gb[1] + g(2))); W(gb, (gb[0] - g(2), gb[1]))
power("GND", gb[0] - g(2), gb[1] + g(2))
text("IA/IB/IC, VA/VB/VC -> CH32V203 ADC inputs\nFAULT_N -> TIM1_BKIN or GPIO (active low, ~77 A)\nJ1 is optional: wire the labels to the MCU and delete J1", x0 + g(4), y0 - g(3), 1.27)
part("J8", x0 + g(8), y0 + g(9), rpos=(x0 + g(7), y0 + g(7.5)), show_val=False)
j8 = pe("J8", "1"); W(j8, (j8[0] - g(1), j8[1]), (j8[0] - g(1), j8[1] + g(2))); power("GND", j8[0] - g(1), j8[1] + g(2))
text("J8: DRIVE DC- LINK (M4 T44001)\nRequired for VA/VB/VC: ties this\nboard's GND to the drive's DC-.", x0 + g(10), y0 + g(8.4), 1.27)

# pull-up and bulk cap
xr = x0 + g(20)
part("R1", xr, y0)
a, b = pe("R1", "1"), pe("R1", "2")
W(a, (a[0], a[1] - g(2))); power("+3V3", a[0], a[1] - g(2))
W(b, (b[0], b[1] + g(2))); label("FAULT_N", b[0], b[1] + g(2), "down")
part("C1", xr + g(8), y0)
a, b = pe("C1", "1"), pe("C1", "2")
W(a, (a[0], a[1] - g(2))); power("+3V3", a[0], a[1] - g(2))
W(b, (b[0], b[1] + g(2))); power("GND", b[0], b[1] + g(2))
text("3V3 bulk", xr + g(8) + 2.54, y0 + 3.6, 1.0)
text("OCF pull-up\n(wired-OR)", xr + 2.54, y0 + 3.6, 1.0)
# power flags
for i, net in enumerate(["+3V3", "GND"]):
    fx, fy = xr + g(16 + i * 5), y0
    up = net != "GND"
    place("power:PWR_FLAG", f"#FLG{i+1:02d}", "PWR_FLAG", fx, fy, rot=180 if up else 0, show_ref=False,
          vpos=(fx, fy + 4.6 if up else fy - 4.6), vjust=None)
    power(net, fx, fy)
place("Mechanical:MountingHole", "H1", "M3", x0 + g(36), y0 + g(6), byref["H1"]["fp"], su=byref["H1"]["uuid"])
place("Mechanical:MountingHole", "H2", "M3", x0 + g(41), y0 + g(6), byref["H2"]["fp"], su=byref["H2"]["uuid"])

# ---------------------------------------------------------------- notes
text("DESIGN NOTES\n"
     "1. Drive (IN) -> IP+ ... IP- -> motor (OUT), 0.85 mOhm. VIOUT = 1.65 V + 19.8 mV/A for drive->motor current.\n"
     "2. VIOUT -> 1k / 10n RC (fc ~16 kHz) -> I[A/B/C] -> MCU ADC. The 1k isolates the 10n (VIOUT max load 6 nF).\n"
     "3. VOC = 3.3 V x 10k/(33k+10k) = 0.767 V -> OCF trips at ~116 % FS (~77 A). OCF is open-drain; all three wired-OR on FAULT_N.\n"
     "4. GAIN_SEL_1/0 tied low = range +/-66.7 A (internal 1M pull-downs; tied for noise immunity). VREF unused.\n"
     "5. Power the sensors from the SAME 3V3 as the MCU VDDA: output is ratiometric, supply drift cancels.\n"
     "6. Thermal: 60 A DC = ~3 W per sensor (too much for SOIC-16). ~30 A RMS continuous with 2 oz copper.\n"
     "7. Spacing: phase copper >= 0.5 mm from all other nets (DRC rule). NOTE: with J8 linked, board GND = drive DC- (not isolated).\n"
     "8. Phase voltage: 47k+47k / 2.7k (C25819/C13167), 22n -> fc ~2.8 kHz. 28.9 mV per ADC count, 118 V full scale.",
     g(74), g(51), 1.5, )
sch.texts[-10].effects.font.bold = True

finish_wires()
sch.to_file(OUT)
print("wrote", OUT, len(sch.schematicSymbols), "symbols", len(sch.graphicalItems), "graphics")
