"""export DSN for secondary-only routing, or import SES + finish board.
  route.py export base.kicad_pcb out.dsn
  route.py finish base.kicad_pcb in.ses final.kicad_pcb"""
import sys, math, re, os
import pcbnew
mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
W, H = 88.0, 60.0
PRIMARY = ("PA_IN", "PA_OUT", "PB_IN", "PB_OUT", "PC_IN", "PC_OUT")

def rule_area(b, pts):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(mm(x), mm(y))
    b.Add(z)

def export(base, dsn):
    b = pcbnew.LoadBoard(base)
    for z in [b.GetArea(i) for i in range(b.GetAreaCount())]: b.Remove(z)
    for t in list(b.GetTracks()): b.Remove(t)
    zero = b.FindNet("") or b.GetNetInfo().GetNetItem(0)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in PRIMARY: p.SetNet(zero)
    rule_area(b, [(0, 0), (W, 0), (W, 26.3), (0, 26.3)])   # whole HV side + under package body
    ok = pcbnew.ExportSpecctraDSN(b, dsn); print("dsn", ok)

def parse_sexp(s):
    tok = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s); st = [[]]
    for t in tok:
        if t == "(": st.append([])
        elif t == ")": x = st.pop(); st[-1].append(x)
        else: st[-1].append(t.strip('"'))
    return st[0][0]

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def finish(base, ses, out):
    b = pcbnew.LoadBoard(base)
    s = parse_sexp(open(ses).read())
    routes = find(s, "routes")[0]
    res = find(routes, "resolution")[0]; div = float(res[2])            # e.g. um 10
    unit = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[res[1]]
    k = unit / div
    netmap = {b.GetNetInfo().GetNetItem(i).GetNetname(): b.GetNetInfo().GetNetItem(i)
              for i in range(b.GetNetCount())}
    import json, os
    meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(base)), "explicit_tracks.json")))
    ex = meta["explicit"]
    def on_seg(pt, e):
        (x1, y1, x2, y2) = e[1:5]; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
        if L == 0: return math.hypot(pt[0] - x1, pt[1] - y1) < 0.02
        t = ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / L
        if t < -0.001 or t > 1.001: return False
        return math.hypot(pt[0] - x1 - t * dx, pt[1] - y1 - t * dy) < 0.02
    def is_explicit(n, a, b_):
        return any(e[0] == n and on_seg(a, e) and on_seg(b_, e) for e in ex)
    nt = nv = 0
    for n in find(find(routes, "network_out")[0], "net"):
        net = netmap[n[1]]
        for w in find(n, "wire"):
            path = find(w, "path")[0]
            layer = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu}[path[1]]
            width = float(path[2]) * k
            c = [float(v) * k for v in path[3:]]
            pts = [(c[i], -c[i + 1]) for i in range(0, len(c), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if is_explicit(n[1], (x1, y1), (x2, y2)): continue
                if abs(x1 - x2) + abs(y1 - y2) < 0.01: continue
                t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2))
                t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(net); b.Add(t); nt += 1
        for v in find(n, "via"):
            x, y = float(v[2]) * k, -float(v[3]) * k
            if any(abs(x - q[0]) < 0.05 and abs(y - q[1]) < 0.05 for q in meta.get("xvias", [])): continue
            via = pcbnew.PCB_VIA(b); via.SetPosition(V(x, y)); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3))
            via.SetNet(net); b.Add(via); nv += 1
    print("tracks", nt, "vias", nv)
    # GND pour: explicit polygons per layer (from make_pcb), or board minus HV areas (older layouts)
    gnd = b.FindNet("GND")
    def add_gnd(L, pts):
        z = pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(gnd); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in pts: ol.Append(mm(x), mm(y))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL); z.SetLocalClearance(mm(0.2))
        z.SetMinThickness(mm(0.18)); z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetAssignedPriority(0); b.Add(z)
    for Lname, polys in meta["gnd_polys"].items():
        for pts in polys:
            add_gnd({"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu}[Lname], pts)
    # prune dangling copper (non-GND): vias/tracks whose ends touch nothing else of their net
    def P(v): return (round(pcbnew.ToMM(v.x), 3), round(pcbnew.ToMM(v.y), 3))
    while not os.environ.get("NOPRUNE"):
        items = [t for t in b.GetTracks() if not t.IsLocked() and t.GetNetname() not in ("GND",) and not t.GetNetname().startswith("P")]
        pads = {}
        for fp in b.GetFootprints():
            for pd in fp.Pads():
                pads.setdefault(pd.GetNetname(), []).append(pd)
        def touches(pt, net, layer, me):
            x, y = pt
            for pd in pads.get(net, []):
                if pd.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))): return True
            for o in b.GetTracks():
                if o.m_Uuid.AsString() == me.m_Uuid.AsString() or o.GetNetname() != net: continue
                if o.GetClass() == "PCB_VIA":
                    if math.hypot(*(a - c for a, c in zip(P(o.GetPosition()), pt))) < pcbnew.ToMM(o.GetWidth()) / 2 + 0.01 and (layer is None or True): return True
                else:
                    if layer is not None and o.GetLayer() != layer: continue
                    if pt in (P(o.GetStart()), P(o.GetEnd())): return True
                    a_, c_ = P(o.GetStart()), P(o.GetEnd()); dx, dy = c_[0] - a_[0], c_[1] - a_[1]; L = dx * dx + dy * dy
                    if L > 0:
                        u = ((pt[0] - a_[0]) * dx + (pt[1] - a_[1]) * dy) / L
                        if 0 <= u <= 1 and math.hypot(pt[0] - a_[0] - u * dx, pt[1] - a_[1] - u * dy) < 0.02: return True
            return False
        dead = []
        for t in items:
            if t.GetClass() == "PCB_VIA":
                n = sum(1 for o in b.GetTracks() if o.m_Uuid.AsString() != t.m_Uuid.AsString() and o.GetClass() != "PCB_VIA" and o.GetNetname() == t.GetNetname()
                        and P(t.GetPosition()) in (P(o.GetStart()), P(o.GetEnd())))
                if n <= 1 and not any(pd.HitTest(t.GetPosition()) for pd in pads.get(t.GetNetname(), [])): dead.append(t)
            else:
                if not (touches(P(t.GetStart()), t.GetNetname(), t.GetLayer(), t) and touches(P(t.GetEnd()), t.GetNetname(), t.GetLayer(), t)):
                    dead.append(t)
        if not dead: break
        for t in dead: b.Remove(t)
        print("pruned", len(dead))
    # vias that join fewer than two layers are useless: drop them
    for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() not in ("GND",)
              and not t.GetNetname().startswith("P") and not os.environ.get("NOPRUNE")]:
        vp = P(v.GetPosition()); layers = set()
        for o in b.GetTracks():
            if o.GetClass() != "PCB_VIA" and o.GetNetname() == v.GetNetname():
                a_, c_ = P(o.GetStart()), P(o.GetEnd()); dx, dy = c_[0] - a_[0], c_[1] - a_[1]; L2 = dx * dx + dy * dy
                u = 0 if L2 == 0 else ((vp[0] - a_[0]) * dx + (vp[1] - a_[1]) * dy) / L2
                if -0.001 <= u <= 1.001 and math.hypot(vp[0] - a_[0] - u * dx, vp[1] - a_[1] - u * dy) < 0.02:
                    layers.add(o.GetLayer())
        for pd in pads.get(v.GetNetname(), []):
            if pd.HitTest(v.GetPosition()): layers.add(-1); layers.add(-2)
        if len(layers) < 2:
            b.Remove(v); print("drop unused via", vp)
    # trim lane ends left dangling by dropped vias back to the last point something connects
    def seg_t(pt, t):
        a_, c_ = P(t.GetStart()), P(t.GetEnd()); dx, dy = c_[0] - a_[0], c_[1] - a_[1]; L = dx * dx + dy * dy
        if L == 0: return None
        u = ((pt[0] - a_[0]) * dx + (pt[1] - a_[1]) * dy) / L
        if -0.001 <= u <= 1.001 and math.hypot(pt[0] - a_[0] - u * dx, pt[1] - a_[1] - u * dy) < 0.02: return u
        return None
    for t in [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA" and t.IsLocked() and t.GetNetname() != "GND"
              and not os.environ.get("NOPRUNE")]:
        n = t.GetNetname(); us = []
        for o in b.GetTracks():
            if o.m_Uuid.AsString() == t.m_Uuid.AsString() or o.GetNetname() != n: continue
            pts = [P(o.GetPosition())] if o.GetClass() == "PCB_VIA" else ([P(o.GetStart()), P(o.GetEnd())] if o.GetLayer() == t.GetLayer() else [])
            for q in pts:
                u = seg_t(q, t)
                if u is not None: us.append(u)
            if o.GetClass() != "PCB_VIA" and o.GetLayer() == t.GetLayer():
                for u_, q in ((0.0, P(t.GetStart())), (1.0, P(t.GetEnd()))):
                    if seg_t(q, o) is not None: us.append(u_)
        for pd in pads.get(n, []):
            for u in (0.0, 1.0):
                q = t.GetStart() if u == 0 else t.GetEnd()
                if pd.HitTest(q) and pd.IsOnLayer(t.GetLayer()): us.append(u)
        if not us: continue
        lo, hi = max(0.0, min(us)), min(1.0, max(us))
        a_, c_ = P(t.GetStart()), P(t.GetEnd())
        if hi < 0.999 or lo > 0.001:
            na = (a_[0] + lo * (c_[0] - a_[0]), a_[1] + lo * (c_[1] - a_[1])); nc = (a_[0] + hi * (c_[0] - a_[0]), a_[1] + hi * (c_[1] - a_[1]))
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(na[0]), pcbnew.FromMM(na[1]))); t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(nc[0]), pcbnew.FromMM(nc[1])))
            print("trimmed", n, a_, c_, "->", na, nc)
    for t in [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLength() < pcbnew.FromMM(0.01)]:
        b.Remove(t)
    # T-junctions: split a segment wherever another track of its net ends on its middle (KiCad wants end-to-end)
    changed = True
    while changed:
        changed = False
        segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
        ends = [(t.GetNetname(), t.GetLayer(), P(q)) for t in segs for q in (t.GetStart(), t.GetEnd())]
        for t in segs:
            a_, c_ = P(t.GetStart()), P(t.GetEnd())
            for n, L, q in ends:
                if n != t.GetNetname() or L != t.GetLayer() or q in (a_, c_): continue
                u = seg_t(q, t)
                if u is not None and 0.01 < u < 0.99:
                    t2 = pcbnew.PCB_TRACK(b); t2.SetLayer(t.GetLayer()); t2.SetWidth(t.GetWidth()); t2.SetNet(t.GetNet())
                    t2.SetLocked(t.IsLocked())
                    qv = pcbnew.VECTOR2I(pcbnew.FromMM(q[0]), pcbnew.FromMM(q[1]))
                    t2.SetStart(qv); t2.SetEnd(t.GetEnd()); t.SetEnd(qv); b.Add(t2)
                    changed = True; break
            if changed: break
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(out, b); print("saved", out)

if __name__ == "__main__":
    if sys.argv[1] == "export": export(sys.argv[2], sys.argv[3])
    else: finish(sys.argv[2], sys.argv[3], sys.argv[4])
