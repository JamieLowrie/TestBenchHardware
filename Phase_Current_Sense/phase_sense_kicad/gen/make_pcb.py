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
BAND = (51.0, 59.6)                              # In1 crossing band: no phase vias here
LVBOT = 66.4
LANE = {n: BAND[0] + 0.6 + 0.7 * i for i, n in
        enumerate(("+3.3VA", "IA", "IB", "IC", "VA", "VB", "VC", "FAULT_N", "GS0", "GS1"))}
LVIA = {"+3.3VA": 1.3, "I": 5.9, "V": 6.6, "FAULT_N": 2.3, "GS0": 4.4, "GS1": 3.6}   # lane-via X offset from the sensor centre
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
    # GAIN_SEL straps (0402, vertical) right of the sensor's LV pins 14/16
    # GAIN_SEL straps (0402, vertical) in the free slots of the right column; pins 14/16 reach them on In1
    # tops of all four = GAIN_SEL net; bottoms: GND (x 5.3) / 3V3 (x 6.6)
pos["J8"] = (TDC, TY_T, 0)
pos["J1"] = (51.0, 50.6, 0)                              # 2x7 header in a small pocket left of strip C
pos["Q1"] = (52.6, 46.6, 0)                              # sensor power switch
pos["R2"] = (49.5, 46.6, 90)
pos["R3"] = (48.4, 62.6, 90)
pos["R4"] = (48.4, 66.0, 90)
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
    if p.get("dnp"):
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
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
        track("+3.3VA", a_, c_, w=0.3, lock=True)
    # GAIN_SEL bus: pins 16/14 -> vias under the body -> In1 straight down -> vias above the band -> B.Cu to the lane vias
    u = lambda du, dv: (cx + du, CY + dv)
    p16, p14 = padpos(f"U{k}", "16"), padpos(f"U{k}", "14")
    track("GS0", p16, (cx + 3.3, p16[1]), w=0.25, lock=True); track("GS0", (cx + 3.3, p16[1]), u(2.9, -3.9), w=0.25, lock=True)
    track("GS1", p14, u(2.9, p14[1] - CY), w=0.25, lock=True)
    for n_, top, jog in (("GS0", u(2.9, -3.9), u(LVIA["GS0"], -2.4)), ("GS1", u(2.9, p14[1] - CY), u(LVIA["GS1"], p14[1] - CY + 0.7))):
        bv = (jog[0], BAND[0] - 0.2)
        xvia(n_, top); xvia(n_, bv)
        track(n_, top, jog, w=0.25, lock=True, layer="In1"); track(n_, jog, bv, w=0.25, lock=True, layer="In1")
        track(n_, bv, (bv[0], LANE[n_]), w=0.25, lock=True, layer="B")
    # +3.3VA: two In1 drops from the local rail straight into the 3V3 lane (top lane, so nothing to cross)
    r1a, c1a = padpos(f"R{k}1", "1"), padpos(f"C{k}1", "1")
    for vv, pp in (((cx + 0.9, r1a[1] - 0.8), r1a), ((cx + 5.75, c1a[1] + 1.15), c1a)):
        xvia("+3.3VA", vv); track("+3.3VA", pp, vv, w=0.25, lock=True)
        track("+3.3VA", vv, (vv[0], LANE["+3.3VA"]), w=0.25, lock=True, layer="In1")
    # VIOUT: pin 12 -> via under the body -> In1 -> via above R{k}3
    p12, r3 = padpos(f"U{k}", "12"), padpos(f"R{k}3", "1")
    track(f"VIOUT_{X}", p12, (cx + 2.6, p12[1]), w=0.25, lock=True); xvia(f"VIOUT_{X}", (cx + 2.6, p12[1]))
    for a_, c_ in (((cx + 2.6, p12[1]), (r3[0], p12[1] + 0.975)), ((r3[0], p12[1] + 0.975), (r3[0], r3[1] - 0.9))):
        track(f"VIOUT_{X}", a_, c_, w=0.25, lock=True, layer="In1")
    xvia(f"VIOUT_{X}", (r3[0], r3[1] - 0.9)); track(f"VIOUT_{X}", (r3[0], r3[1] - 0.9), r3, w=0.25, lock=True)
    # FAULT_N: pin 9 -> via under the body -> In1 straight down -> via above the band -> B.Cu to its lane via
    p9 = padpos(f"U{k}", "9"); fv1, fv2 = (cx + 2.9, p9[1]), (cx + LVIA["FAULT_N"], BAND[0] - 0.2)
    track("FAULT_N", p9, fv1, w=0.25, lock=True); xvia("FAULT_N", fv1); xvia("FAULT_N", fv2)
    for a_, c_ in ((fv1, (fv2[0], fv1[1] + 0.6)), ((fv2[0], fv1[1] + 0.6), fv2)):
        track("FAULT_N", a_, c_, w=0.25, lock=True, layer="In1")
    track("FAULT_N", fv2, (fv2[0], LANE["FAULT_N"]), w=0.25, lock=True, layer="B")
    # IX: C{k}3 pad 1 -> F.Cu channel between the two part columns -> its In1 lane via
    c3 = padpos(f"C{k}3", "1"); iy = LANE[f"I{X}"]; ix = cx + LVIA["I"]
    for a_, c_ in ((c3, (ix, c3[1] + 0.775)), ((ix, c3[1] + 0.775), (ix, iy))):
        track(f"I{X}", a_, c_, w=0.25, lock=True)
# GND stitching (F / In2 / B)
for X in "ABC":
    cx = CX[X]; sr = STRIP[X][1]
    for p_ in ((cx + 2.8, 65.4), (cx + 5.0, 65.4), (cx + 1.6, CY - 3.0), (cx + 6.6, BAND[1] - 0.4),
               ):
        xvia("GND", p_)
for p_ in ((54.5, 12.0), (54.5, 22.0), (54.5, 32.0), (54.5, 40.0), (49.0, 44.9), (49.4, 67.7), (54.4, 67.7)):
    xvia("GND", p_)

# In1 lanes across the band: one per LV net, 0.7 mm pitch, a via into each LV area that uses it
USE = {X: ("+3.3VA", f"I{X}", f"V{X}", "FAULT_N", "GS0", "GS1") for X in "ABC"}
for n, y_ in LANE.items():
    xs = []
    for X in "CBA":
        if n in USE[X]:
            xs.append(CX[X] + LVIA[n if n in LVIA else n[0]])
    track(n, (57.2, y_), (max(xs), y_), w=0.25, lock=True, layer="In1")
    for x_ in xs: xvia(n, (x_, y_))

_r1 = padpos("R1", "2"); _fx = CX["C"] + LVIA["FAULT_N"]        # FAULT_N pull-up -> lane via
for a_, c_ in ((_r1, (_r1[0], _r1[1] - 0.9)), ((_r1[0], _r1[1] - 0.9), (_fx, _r1[1] - 1.5)),
               ((_fx, _r1[1] - 1.5), (_fx, LANE["FAULT_N"]))):
    track("FAULT_N", a_, c_, w=0.25, lock=True)

# J1 / Q1 -> lane starts, all on In1 (lanes start at X 57.2 inside the band)
LX = 57.2
def ipath(net_, pts, w=0.25):
    for a_, c_ in zip(pts, pts[1:]): track(net_, a_, c_, w=w, lock=True, layer="In1")
qd = padpos("Q1", "3")
track("+3.3VA", qd, (54.6, qd[1]), w=0.3, lock=True); xvia("+3.3VA", (54.6, qd[1]))
ipath("+3.3VA", [(54.6, qd[1]), (56.1, qd[1] + 1.5), (56.1, LANE["+3.3VA"] - 0.5), (56.6, LANE["+3.3VA"]), (LX, LANE["+3.3VA"])], 0.3)
j = {n: padpos("J1", n) for n in ("2", "3", "4", "5", "6", "7", "8")}
ipath("IA", [j["2"], (55.4, j["2"][1]), (55.4, LANE["IA"] - 0.4), (55.8, LANE["IA"]), (LX, LANE["IA"])])
ipath("IB", [j["3"], (j["3"][0] + 1.27, j["3"][1] - 1.27), (54.8, j["3"][1] - 1.27), (54.8, LANE["IB"] - 0.4),
             (55.2, LANE["IB"]), (LX, LANE["IB"])])
ipath("IC", [j["4"], (j["4"][0] + 0.56, LANE["IC"]), (LX, LANE["IC"])])
ipath("VA", [j["5"], (j["5"][0] + 1.27, j["5"][1] - 1.27), (LX, j["5"][1] - 1.27)])
ipath("VB", [j["6"], (j["6"][0] + 0.96, LANE["VB"]), (LX, LANE["VB"])])
ipath("VC", [j["7"], (j["7"][0] + 1.27, j["7"][1] - 1.27), (54.7, j["7"][1] - 1.27), (54.7 + (j["7"][1] - 1.27 - LANE["VC"]), LANE["VC"]),
             (LX, LANE["VC"])])
ipath("FAULT_N", [j["8"], (55.0, j["8"][1]), (55.0 + (j["8"][1] - LANE["FAULT_N"]), LANE["FAULT_N"]), (LX, LANE["FAULT_N"])])
# GS0 / GS1 from the series resistors R3 / R4 (bus side = pad 2)
r3b, r4b = padpos("R3", "2"), padpos("R4", "2")
g0v, g1v = (r3b[0] - 0.7, r3b[1] - 0.6), (r4b[0] - 0.7, r4b[1] - 0.6)
track("GS0", r3b, g0v, w=0.25, lock=True); xvia("GS0", g0v)
track("GS1", r4b, g1v, w=0.25, lock=True); xvia("GS1", g1v)
gy0 = j["8"][1] + 1.27                      # gap below pins 7/8
x0_ = 55.0 + (gy0 - (j["8"][1])) + 0.0
ipath("GS0", [g0v, (g0v[0] + (g0v[1] - gy0), gy0), (54.9, gy0), (54.9 + (gy0 - LANE["GS0"]), LANE["GS0"])])
if 54.9 + (gy0 - LANE["GS0"]) > LX: pass
gy1 = j["8"][1] + 3 * 1.27                  # gap below pins 9/10 -> 11/12
ipath("GS1", [g1v, (g1v[0] + (g1v[1] - gy1), gy1), (54.6, gy1), (54.6 + 3.0, gy1 - 3.0),
              (54.6 + 3.0 + (gy1 - 3.0 - LANE["GS1"]), LANE["GS1"])])

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
DCS = [(SPLIT_X + 0.2, 0.5), (68.0, 0.5), (68.0, 9.8), (55.3, 9.8), (55.3, 44.4), (SPLIT_X + 0.2, 44.4)]   # DC- -> J1 strip
JPAD = rect(47.4, 44.2, 55.3, 68.4)
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
    rule_area(rect(0, 0, 47.2, H), ALL)                                       # controller side
    rule_area(rect(47.2, 0, 56.0, 44.0), ALL); rule_area(rect(47.2, 68.6, 56.0, H), ALL)
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
    if not (43.0 < y < 69.0): line(SPLIT_X, y, SPLIT_X, min(y + 1.5, H - 1.0), pcbnew.F_SilkS, 0.15)
    y += 3.0
silk("CONTROLLER AREA", 25.0, 36.0, 1.5, bold=True)
silk("(X < 53.6 mm)", 25.0, 38.6, 1.2, bold=True)
silk("3-PH SENSE  ACS37002  rev H", 25.0, 41.2, 0.8)
CM = pcbnew.Cmts_User
for r_ in BLOCKS: rect_outline(*r_, CM, 0.1)
for r_ in POSTS:  rect_outline(*r_, CM, 0.2)
rect_outline(*PLATFORM, CM, 0.05)
def note(t, x, y): silk(t, x, y, 0.8, layer=CM)
note("block", 49.5, 19.0)
note("box post: max 3.3 mm", 49.45, 13.0); note("box post: max 3.3 mm", 49.45, 69.6)
note("centre platform 0.5 mm below PCB (Y 21.5-61.2): no lead protrusion", 25.0, 44.0)
note("open wiring strips: Y<10.5 and Y>72.3 (terminals only here)", 25.0, 45.4)
pin = ["1 3V3", "2 IA", "3 IB", "4 IC", "5 VA", "6 VB", "7 VC", "8 FLT", "9 GND", "10 GND", "11 GS0", "12 GS1", "13 SOFF", "14 GND"]
for i, t in enumerate(pin):
    silk(t, 44.0 - (0 if i % 2 == 0 else 6.0), 50.6 + (i // 2) * 2.54, 0.8, layer=pcbnew.B_SilkS)
silk("J1 (pin 1 square, top-left)", 41.0, 47.0, 0.8, layer=pcbnew.B_SilkS, bold=True)
silk("1", pos["J1"][0] - 1.8, pos["J1"][1], 0.8)

pcbnew.SaveBoard(OUT, b)
if DSN:
    print("dsn export", pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
print("saved", OUT, "vias", len(vias))
