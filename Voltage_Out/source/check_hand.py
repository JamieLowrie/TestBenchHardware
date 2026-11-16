"""Independent connectivity + hygiene check of the wired schematic, read back from the .kicad_sch file."""
import json, sys
from collections import defaultdict
from kiutils.schematic import Schematic

geo = json.load(open("geom_hand.json"))
sch = Schematic.from_file(sys.argv[1] if len(sys.argv) > 1 else "can_analog_out.kicad_sch")
R = lambda v: round(v, 3)

lib = {}
for ls in sch.libSymbols:
    per_unit = defaultdict(list)
    for u in ls.units:
        for p in u.pins: per_unit[u.unitId].append((p.number, p.position.X, p.position.Y))
    lib[f"{ls.libraryNickname}:{ls.entryName}"] = (per_unit, ls.isPower)

pin_pts = defaultdict(list)       # point -> [(ref, pin)]
global_names = defaultdict(list)  # point -> [net] from power symbols
for s in sch.schematicSymbols:
    ref = next(p.value for p in s.properties if p.key == "Reference")
    val = next(p.value for p in s.properties if p.key == "Value")
    per_unit, is_pwr = lib[f"{s.libraryNickname}:{s.entryName}"]
    pins = per_unit.get(0, []) + per_unit.get(s.unit, [])
    ang = s.position.angle or 0
    for (num, x, y) in pins:
        if ang not in (0,) and (x, y) != (0, 0):
            sys.exit(f"{ref}: rotated symbol with off-origin pin not supported by checker")
        pt = (R(s.position.X + x), R(s.position.Y - y))
        if is_pwr:
            global_names[pt].append(val)
        else:
            pin_pts[pt].append((ref, num))
for pt, lst in pin_pts.items():
    if len(lst) > 1: print("PINS OVERLAP", pt, lst)

wires = [((R(g.points[0].X), R(g.points[0].Y)), (R(g.points[1].X), R(g.points[1].Y))) for g in sch.graphicalItems if g.type == "wire"]
junctions = {(R(j.position.X), R(j.position.Y)) for j in sch.junctions}
labels = defaultdict(list)
for l in list(sch.labels) + list(sch.hierarchicalLabels): labels[(R(l.position.X), R(l.position.Y))].append(l.text)
ncs = {(R(n.position.X), R(n.position.Y)) for n in sch.noConnects}

parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b): parent[find(a)] = find(b)

def on_interior(p, a, b):
    if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]): return True
    if a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]): return True
    return False

errors = 0
endpoints = defaultdict(int)
for a, b in wires:
    union(a, b); endpoints[a] += 1; endpoints[b] += 1
    if a[0] != b[0] and a[1] != b[1]: print("DIAGONAL WIRE", a, b); errors += 1
# anything electrically significant sitting on a wire interior
for a, b in wires:
    for p in set(pin_pts) | set(global_names) | set(endpoints):
        if on_interior(p, a, b):
            print("T/INTERIOR CONTACT (unintended unless label)", p, a, b); errors += 1; union(p, a)
    for p in labels:
        if on_interior(p, a, b): union(p, a)
# collinear overlap between different wires
for i, (a, b) in enumerate(wires):
    for (c, d) in wires[i + 1:]:
        if a[1] == b[1] == c[1] == d[1]:
            if max(min(a[0], b[0]), min(c[0], d[0])) < min(max(a[0], b[0]), max(c[0], d[0])): print("OVERLAP", (a, b), (c, d)); errors += 1
        if a[0] == b[0] == c[0] == d[0]:
            if max(min(a[1], b[1]), min(c[1], d[1])) < min(max(a[1], b[1]), max(c[1], d[1])): print("OVERLAP", (a, b), (c, d)); errors += 1
# junction hygiene: dots exactly where >= 3 items meet
items = defaultdict(int)
for p, n in endpoints.items(): items[p] += n
for p in pin_pts: items[p] += 1
for p in global_names: items[p] += 1
need = {p for p, n in items.items() if n >= 3}
if need - junctions: print("MISSING JUNCTIONS", sorted(need - junctions)); errors += 1
if junctions - need: print("EXTRA JUNCTIONS", sorted(junctions - need)); errors += 1

# global names (power symbols + labels)
names = defaultdict(set)
for p, nets in list(global_names.items()) + list(labels.items()):
    for n in nets: names[n].add(p)
for n, pts in names.items():
    pts = list(pts)
    for p in pts[1:]: union(p, pts[0])

for pt, rp in pin_pts.items():
    if pt in ncs: continue
    if not any(pt in w for w in wires) and pt not in global_names:
        print("UNCONNECTED PIN", rp); errors += 1

intended = {}
for (ref, num, net) in geo["conns"]:
    if net: intended[(ref, num)] = net
groups = defaultdict(set)
for pt, rps in pin_pts.items():
    if pt in ncs: continue
    for rp in rps: groups[find(pt)].add(rp)
net_group = {}
for root, rps in groups.items():
    nets = {intended.get(rp) for rp in rps}
    if len(nets) != 1 or None in nets:
        print("SHORT/UNKNOWN", nets, sorted(rps)); errors += 1; continue
    n = nets.pop()
    if n in net_group: print("NET SPLIT", n, sorted(rps), sorted(groups[net_group[n]])); errors += 1
    net_group[n] = root
    names_here = set()
    for nm, pts in names.items():
        if any(find(p) == root for p in pts): names_here.add(nm)
    if names_here and names_here != {n}: print("NAME MISMATCH", n, names_here); errors += 1
for rp, n in intended.items():
    if n not in net_group: print("MISSING NET", n, rp); errors += 1
print(f"nets {len(net_group)} | pins {sum(len(v) for v in pin_pts.values())} | wires {len(wires)} | junctions {len(junctions)} | power symbols {sum(len(v) for v in global_names.values())} | no-connects {len(ncs)}")
print("ERRORS:", errors)
