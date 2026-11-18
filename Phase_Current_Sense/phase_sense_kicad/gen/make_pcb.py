"""CamdenBoss CDIB/6(ST)/L2 lower PCB 99.0 x 82.8 mm, rev F, 4 layers.
Sensor circuit pushed to the right; the controller gets X < ~53.8.
Top-right window (Y < 10.5): DC- (nearest the middle), C IN, B IN, A IN.  Bottom-right window: C OUT, B OUT, A OUT.

Layers: F.Cu / B.Cu = phase copper (both layers, via-stitched) + LV parts & GND;
        In1.Cu = LV signal routing (crosses under the phase strips in a via-free band, Y 49.4-56.6);
        In2.Cu = GND only under the LV areas, the J1 pocket, the DC- strip and the crossing band.
usage: make_pcb.py out.kicad_pcb [route.dsn]
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from design import PARTS
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union

FPDIR = "/usr/share/kicad/footprints"
PROJ_FP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "phase_sense.pretty")
OUT = sys.argv[1]
DSN = len(sys.argv) > 2
mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
LAY = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}

W, H = 99.0, 82.8
OUTLINE = [(1, 0), (W - 1, 0), (W, 1), (W, H - 1), (W - 1, H), (1, H), (0, H - 1), (0, 1)]
SPLIT_X = 53.6                                   # controller | sensor (J1 pocket excepted)
TY_T, TY_B = 5.8, 77.0
TDC = 64.0                                       # DC- terminal (nearest the middle)
TIN = {"C": 73.5, "B": 83.0, "A": 94.2}
TOUT = {"C": 65.5, "B": 80.0, "A": 94.2}
STRIP = {"C": (56.1, 69.7), "B": (70.5, 84.1), "A": (84.9, 98.5)}
CX = {X: STRIP[X][0] + 6.2 for X in "ABC"}
CY = 29.0
BAND = (51.0, 58.2)                              # In1 crossing band: no phase vias here
LVBOT = 66.4
PILLARS = {"H1": (6.995, 66.405), "H2": (91.995, 16.405)}
H2K_F, H2K_IN = 4.0, 2.4                         # copper keep-away around the H2 screw: top (head) / other layers
BLOCKS = [(42.2, 0.0, 56.7, 21.7)]
POSTS = [(45.7, 0.0, 53.2, 11.7), (45.7, 70.7, 53.2, 82.8)]
PLATFORM = (0.0, 21.5, W, 61.2)

def rect(x1, y1, x2, y2): return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
def coords(g):
    """shapely (multi)polygon -> list of exterior rings"""
    gs = [g] if g.geom_type == "Polygon" else list(g.geoms)
    return [[(round(x, 3), round(y, 3)) for x, y in list(p.exterior.coords)[:-1]] for p in gs if p.area > 0.05]

# ---- phase copper --------------------------------------------------------------------------------
def in_poly(X):
    sl, sr = STRIP[X]; cx = CX[X]; f = (cx - 3.3, CY - 5.3, CY - 0.3)
    if X == "C":
        p = [(68.8, 0.5), (78.2, 0.5), (78.2, 12.0), (69.7, 22.0), (69.7, f[1]), (f[0], f[1]), (f[0], f[2]),
             (sl, f[2]), (sl, 10.6), (68.8, 10.6)]
    elif X == "B":
        p = [(79.0, 0.5), (88.6, 0.5), (88.6, 10.6), (84.5, 10.6), (84.5, 21.0), (84.1, 22.0), (84.1, f[1]),
             (f[0], f[1]), (f[0], f[2]), (sl, f[2]), (sl, 22.0), (79.0, 12.0)]
    else:
        p = [(89.4, 0.5), (98.5, 0.5), (98.5, f[1]), (f[0], f[1]), (f[0], f[2]), (sl, f[2]), (sl, 22.0),
             (85.3, 21.0), (85.3, 11.4), (89.4, 11.4)]
    return Polygon(p)
def out_poly(X):
    sl, sr = STRIP[X]; cx = CX[X]
    return Polygon([(sl, CY + 0.3), (cx - 3.3, CY + 0.3), (cx - 3.3, CY + 5.3), (cx + 0.0, CY + 5.3), (cx + 0.0, 67.0),
                    (sr, 67.0), (sr, 82.3), (sl, 82.3)])
RING = {"F": Point(*PILLARS["H2"]).buffer(H2K_F, 32), "B": Point(*PILLARS["H2"]).buffer(H2K_IN, 32)}
HVZ = []   # (net, layer, poly)
HVG = {}   # shapely geometry per net (union of layers) for keepouts / via checks
for X in "ABC":
    for n, g in ((f"P{X}_IN", in_poly(X)), (f"P{X}_OUT", out_poly(X))):
        HVG[n] = g
        for L in ("F", "B"):
            for ring in coords(g.difference(RING[L])):
                HVZ.append((n, L, ring))

b = pcbnew.NewBoard(OUT)
b.SetCopperLayerCount(4)
ds = b.GetDesignSettings()
ds.SetCopperLayerCount(4)
b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)          # In2 = GND plane; the router keeps off it
ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.2)
ds.m_ViasMinSize = mm(0.6); ds.m_MinThroughDrill = mm(0.3); ds.m_CopperEdgeClearance = mm(0.4)
nc = ds.m_NetSettings.m_DefaultNetClass
nc.SetClearance(mm(0.2)); nc.SetTrackWidth(mm(0.25)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    return nets[name]
def line(x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2)); s.SetLayer(layer); s.SetWidth(mm(w)); b.Add(s)
def rect_outline(x1, y1, x2, y2, layer, w=0.1):
    for a, c in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        line(*a, *c, layer=layer, w=w)
for a, c in zip(OUTLINE, OUTLINE[1:] + OUTLINE[:1]):
    line(*a, *c)

# ---------------------------------------------------------------- placement
pos = {}
for X in "ABC":
    k = "ABC".index(X) + 1; cx = CX[X]
    pos[f"U{k}"] = (cx, CY, 0)
    pos[f"J{2*k}"] = (TIN[X], TY_T, 0)
    pos[f"J{2*k+1}"] = (TOUT[X], TY_B, 0)
    c1, c2 = cx + 2.4, cx + 5.9
    r0 = CY + 6.6
    pos[f"C{k}1"] = (c2, r0, 0); pos[f"C{k}2"] = (c1, r0, 0)
    pos[f"R{k}1"] = (c1, r0 + 2.6, 0); pos[f"R{k}2"] = (c2, r0 + 2.6, 0)
    pos[f"R{k}3"] = (c1, r0 + 5.2, 0); pos[f"C{k}3"] = (c2, r0 + 5.2, 0)
    pos[f"R{k}4"] = (c1, r0 + 8.6, 0)                    # pad 1 (left) = motor-side tap
    pos[f"R{k}5"] = (c1, r0 + 11.2, 180)                 # pad 1 (right) = VMID
    pos[f"R{k}6"] = (c1, r0 + 13.8, 0); pos[f"C{k}4"] = (c2, r0 + 13.8, 0)
pos["J8"] = (TDC, TY_T, 0)
pos["J1"] = (51.0, 50.6, 0)                              # 2x5 header in a small pocket left of strip C
pos["R1"] = (CX["C"] + 2.4, 60.6, 0)
pos["C1"] = (CX["C"] + 2.4, 63.0, 0)
pos["H1"] = (*PILLARS["H1"], 0); pos["H2"] = (*PILLARS["H2"], 0)

fps = {}
HV_NETS = set(HVG)
for p in PARTS:
    lib, name = p["fp"].split(":")
    libdir = PROJ_FP if lib == "phase_sense" else f"{FPDIR}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(libdir, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(p["ref"]); fp.SetValue(p["value"])
    fp.SetPath(pcbnew.KIID_PATH("/" + p["uuid"]))
    if p["lcsc"]: fp.SetProperty("LCSC", p["lcsc"])
    x, y, r = pos[p["ref"]]
    b.Add(fp); fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
    hv_div = p["ref"][0] == "R" and len(p["ref"]) == 3 and p["ref"][-1] == "4"
    for pad in fp.Pads():
        n = p["pins"].get(pad.GetNumber())
        skip = DSN and n and (n in HV_NETS or hv_div)
        if n and not skip: pad.SetNet(net(n))
    fp.Value().SetVisible(False)
    if p["ref"].startswith(("J", "H", "R", "C")): fp.Reference().SetVisible(False)
    fps[p["ref"]] = fp
for k in (1, 2, 3):
    r = fps[f"U{k}"].Reference(); r.SetTextSize(V(0.8, 0.8)); r.SetTextThickness(mm(0.15))
    x, y, _ = pos[f"U{k}"]; r.SetPosition(V(x + 1.0, y)); r.SetTextAngleDegrees(90)

# ---------------------------------------------------------------- phase zones + stitching vias
def zone(netname, pts, layer, clearance=0.6, prio=1):
    z = pcbnew.ZONE(b); z.SetLayer(layer)
    if netname: z.SetNet(net(netname))
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in pts: ol.Append(mm(x), mm(y))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetLocalClearance(mm(clearance)); z.SetMinThickness(mm(0.25)); z.SetAssignedPriority(prio)
    b.Add(z); return z
vias = []
legs = []
for tx, ty in [(TIN[X], TY_T) for X in "ABC"] + [(TOUT[X], TY_B) for X in "ABC"] + [(TDC, TY_T)]:
    legs += [(tx + dx, ty + dy) for dx in (-2.5, 2.5) for dy in (-2.5, 2.5)]
if not DSN:
    for (n, L, poly) in HVZ:
        zone(n, poly, LAY[L])
    both = {n: unary_union([Polygon(p) for (m, L, p) in HVZ if m == n and L == "F"]).intersection(
               unary_union([Polygon(p) for (m, L, p) in HVZ if m == n and L == "B"])) for n in HVG}
    def ok_spot(x, y, n):
        if BAND[0] - 0.6 < y < BAND[1] + 0.6: return False
        if min(math.hypot(x - a, y - c) for a, c in legs) < 2.6: return False
        if math.hypot(x - PILLARS["H2"][0], y - PILLARS["H2"][1]) < H2K_F + 0.6: return False
        for X in "ABC":
            if abs(x - CX[X]) < 6.2 and abs(y - CY) < 5.6: return False
        pt = Point(x, y)
        return both[n].contains(pt) and both[n].exterior.distance(pt) > 0.9 if both[n].geom_type == "Polygon" else \
            any(g.contains(pt) and g.exterior.distance(pt) > 0.9 for g in both[n].geoms)
    for n in HVG:
        y = 1.5
        while y < 82.0:
            x = 56.6
            while x < 98.2:
                if ok_spot(x, y, n): vias.append((n, round(x, 2), round(y, 2), 0.8, 0.4))
                x += 2.0
            y += 2.0
    for X in "ABC":
        sl = STRIP[X][0]; cx = CX[X]
        for vx in (sl + 0.8, sl + 2.0, sl + 3.2, sl + 4.4):
            vias.append((f"P{X}_IN", vx, CY - 6.1, 0.8, 0.4))
            vias.append((f"P{X}_OUT", vx, CY + 6.1, 0.8, 0.4))
        for vx in (cx - 1.8, cx - 0.4):
            vias.append((f"P{X}_OUT", vx, CY + 6.1, 0.8, 0.4))
        vias.append((f"P{X}_IN", TIN[X], TY_T, 0.8, 0.4)); vias.append((f"P{X}_OUT", TOUT[X], TY_B, 0.8, 0.4))
uv = []
for v_ in sorted(vias, key=lambda q: -q[3]):
    if all(math.hypot(v_[1] - q[1], v_[2] - q[2]) > 1.3 for q in uv): uv.append(v_)
vias = uv
for (n, x, y, d, dr) in vias:
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(dr)); v.SetNet(net(n)); b.Add(v)

# ---------------------------------------------------------------- pre-routes
def padpos(ref, num):
    for pd in fps[ref].Pads():
        if pd.GetNumber() == num:
            q = pd.GetPosition(); return (round(pcbnew.ToMM(q.x), 4), round(pcbnew.ToMM(q.y), 4))
explicit = []
xvias = []
def track(netname, a, c_, w=0.3, lock=False, layer="F"):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c_)); t.SetWidth(mm(w))
    t.SetLayer(LAY[layer]); t.SetNet(net(netname)); t.SetLocked(lock); b.Add(t)
    explicit.append([netname, a[0], a[1], c_[0], c_[1]])
def xvia(netname, p_):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(*p_)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net(netname))
    v.SetLocked(True); b.Add(v); xvias.append(list(p_))
for X in "ABC":
    k = "ABC".index(X) + 1; cx = CX[X]
    p1 = padpos(f"R{k}4", "1")
    if not DSN:
        track(f"P{X}_OUT", (cx - 0.4, p1[1]), p1, w=0.4)
    track(f"VMID_{X}", padpos(f"R{k}4", "2"), padpos(f"R{k}5", "1"), lock=True)
    track(f"V{X}", padpos(f"R{k}5", "2"), padpos(f"R{k}6", "1"), lock=True)
    # VCC: pin 10 -> round the outside of pin 9 -> decoupling cap C{k}1
    _p10 = padpos(f"U{k}", "10"); _c1 = padpos(f"C{k}1", "1")
    for a_, c_ in ((_p10, (cx + 6.2, _p10[1])), ((cx + 6.2, _p10[1]), (cx + 6.2, CY + 5.6)), ((cx + 6.2, CY + 5.6), _c1)):
        track("+3V3", a_, c_, w=0.3, lock=True)
# GND stitching (F / In2 / B)
for X in "ABC":
    cx = CX[X]; sr = STRIP[X][1]
    for p_ in ((cx + 2.8, 65.4), (cx + 5.0, 65.4), (sr - 0.7, CY - 4.0), (cx + 6.6, BAND[1] - 0.4),
               (cx + 4.45, CY + 5.6)):
        xvia("GND", p_)
for p_ in ((54.5, 12.0), (54.5, 22.0), (54.5, 32.0), (54.5, 42.0), (50.0, 46.8), (49.4, 61.8), (54.4, 61.8)):
    xvia("GND", p_)

# In1 lanes across the band: one per LV net, 0.7 mm pitch, a via into each LV area that uses it
LANE = {n: BAND[0] + 0.6 + 0.7 * i for i, n in enumerate(("+3V3", "IA", "IB", "IC", "VA", "VB", "VC", "FAULT_N"))}
USE = {"C": ("+3V3", "IC", "VC", "FAULT_N"), "B": ("+3V3", "IB", "VB", "FAULT_N"), "A": ("+3V3", "IA", "VA", "FAULT_N")}
for n, y_ in LANE.items():
    xs = []
    for X in "CBA":
        if n in USE[X]:
            xs.append(CX[X] + 2.0 + USE[X].index(n) * 1.3)
    track(n, (56.6, y_), (max(xs), y_), w=0.25, lock=True, layer="In1")
    for x_ in xs: xvia(n, (x_, y_))

_r1 = padpos("R1", "2"); _fx = CX["C"] + 2.0 + 3 * 1.3          # FAULT_N pull-up -> lane via
for a_, c_ in ((_r1, (_r1[0] + 1.0, _r1[1] - 1.0)), ((_r1[0] + 1.0, _r1[1] - 1.0), (_fx, _r1[1] - 2.7)),
               ((_fx, _r1[1] - 2.7), (_fx, LANE["FAULT_N"]))):
    track("FAULT_N", a_, c_, w=0.25, lock=True)
_j1 = padpos("J1", "1")   # 3V3: pin 1 over the top of pin 2, down into its lane
track("+3V3", _j1, (_j1[0] + 1.27, _j1[1] - 1.27), w=0.25, lock=True)
track("+3V3", (_j1[0] + 1.27, _j1[1] - 1.27), (54.8, _j1[1] - 1.27), w=0.25, lock=True)
xvia("+3V3", (54.8, _j1[1] - 1.27))
track("+3V3", (54.8, _j1[1] - 1.27), (56.6, LANE["+3V3"]), w=0.25, lock=True, layer="In1")

# ---------------------------------------------------------------- GND pours, keepouts
def rule_area(poly, layers=("F", "B"), nopour=False, vias=False):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for L in layers: ls.AddLayer(LAY[L])
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(not vias); z.SetDoNotAllowCopperPour(nopour)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in poly: ol.Append(mm(x), mm(y))
    b.Add(z)
LV = {X: rect(CX[X] + 0.8, CY - 4.8, STRIP[X][1], LVBOT) for X in "ABC"}
DCS = [(SPLIT_X + 0.2, 0.5), (68.0, 0.5), (68.0, 9.8), (55.3, 9.8), (55.3, 47.4), (SPLIT_X + 0.2, 47.4)]   # DC- -> J1 strip
JPAD = rect(48.4, 46.0, 55.3, 62.6)
CROSS = rect(48.4, BAND[0], W - 0.5, BAND[1])
GND = {"F": [LV["C"], LV["B"], LV["A"], DCS, JPAD],
       "B": [LV["C"], LV["B"], LV["A"], DCS, JPAD],
       "In2": [LV["C"], LV["B"], LV["A"], DCS, JPAD, CROSS]}
if DSN:
    for (n, L, poly) in HVZ:
        rule_area(coords(Polygon(poly).buffer(0.55, join_style=2))[0], (L,))
    hv_all = unary_union(list(HVG.values())).buffer(0.6, join_style=2)
    for ring in coords(hv_all.difference(sbox(0, BAND[0], W, BAND[1]))):    # In1: only cross in the band
        rule_area(ring, ("In1",))
    for L, r_ in (("F", H2K_F), ("B", H2K_IN), ("In1", H2K_IN)):
        rule_area(coords(Point(*PILLARS["H2"]).buffer(r_, 24))[0], (L,))
    ALL = ("F", "In1", "B")
    rule_area(rect(0, 0, 48.2, H), ALL)                                       # controller side
    rule_area(rect(48.2, 0, 56.0, 45.8), ALL); rule_area(rect(48.2, 62.8, 56.0, H), ALL)
    rule_area(rect(W - 0.9, 0, W, H), ALL)
    for X in "ABC":
        y4 = pos[f"R{'ABC'.index(X) + 1}4"][1]
        rule_area(rect(CX[X] - 0.7, y4 - 0.9, CX[X] + 3.2, y4 + 0.9), ("F",))
else:
    rule_area(coords(Point(*PILLARS["H2"]).buffer(H2K_F, 24))[0], ("F",), nopour=True)
    rule_area(coords(Point(*PILLARS["H2"]).buffer(H2K_IN, 24))[0], ("In1", "In2", "B"), nopour=True)
    json.dump({"explicit": explicit, "xvias": xvias, "gnd_polys": GND},
              open(os.path.join(os.path.dirname(os.path.abspath(OUT)), "explicit_tracks.json"), "w"))

# ---------------------------------------------------------------- silkscreen + mechanical notes
def silk(t, x, y, size=1.0, layer=pcbnew.F_SilkS, bold=False, ang=0):
    tx = pcbnew.PCB_TEXT(b); tx.SetText(t); tx.SetPosition(V(x, y)); tx.SetLayer(layer)
    tx.SetTextSize(V(size, size)); tx.SetTextThickness(mm(size * (0.2 if bold else 0.15)))
    tx.SetTextAngleDegrees(ang)
    if layer == pcbnew.B_SilkS: tx.SetMirrored(True)
    b.Add(tx)
for X in "ABC":
    silk(f"{X} IN", TIN[X], 0.95, 0.8, bold=True); silk(f"{X} OUT", TOUT[X], 81.85, 0.8, bold=True)
silk("DC-", TDC, 0.95, 0.8, bold=True)
silk("FROM DRIVE", 77.0, 11.2, 0.9, bold=True); silk("TO MOTOR", 77.0, 71.6, 0.9, bold=True)
y = 1.0
while y < H - 1.0:
    if not (45.0 < y < 62.0): line(SPLIT_X, y, SPLIT_X, min(y + 1.5, H - 1.0), pcbnew.F_SilkS, 0.15)
    y += 3.0
silk("CONTROLLER AREA", 25.0, 36.0, 1.5, bold=True)
silk("(X < 53.6 mm)", 25.0, 38.6, 1.2, bold=True)
silk("3-PH SENSE  ACS37002  rev F", 25.0, 41.2, 0.8)
CM = pcbnew.Cmts_User
for r_ in BLOCKS: rect_outline(*r_, CM, 0.1)
for r_ in POSTS:  rect_outline(*r_, CM, 0.2)
rect_outline(*PLATFORM, CM, 0.05)
def note(t, x, y): silk(t, x, y, 0.8, layer=CM)
note("block", 49.5, 19.0)
note("box post: max 3.3 mm", 49.45, 13.0); note("box post: max 3.3 mm", 49.45, 69.6)
note("centre platform 0.5 mm below PCB (Y 21.5-61.2): no lead protrusion", 25.0, 44.0)
note("open wiring strips: Y<10.5 and Y>72.3 (terminals only here)", 25.0, 45.4)
pin = ["1 3V3", "2 IA", "3 IB", "4 IC", "5 VA", "6 VB", "7 VC", "8 FLT", "9 GND", "10 GND"]
for i, t in enumerate(pin):
    silk(t, 44.0 - (0 if i % 2 == 0 else 5.5), 49.0 + (i // 2) * 2.54, 0.8, layer=pcbnew.B_SilkS)
silk("J1 (pin 1 square, top-left)", 41.0, 46.6, 0.8, layer=pcbnew.B_SilkS, bold=True)
silk("1", pos["J1"][0] - 1.8, pos["J1"][1], 0.8)

pcbnew.SaveBoard(OUT, b)
if DSN:
    print("dsn export", pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
print("saved", OUT, "vias", len(vias))
