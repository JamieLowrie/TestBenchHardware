# ---------------------------------------------------------------- emission (exec'd from hand.py)
# all parts used?
used = {k for k in PLACE}
missing = [k for k in NETS if k not in used]
if missing: sys.exit(f"not placed: {missing}")

# split wires wherever an endpoint / pin / power point lies in the interior of another wire (intended T)
pin_pts = {}
for key, pl in PLACE.items():
    for (n, nm, t, px, py, ang, ln) in pins_of(key):
        pin_pts[(round(pl["x"] + px, 4), round(pl["y"] - py, 4))] = (key, n)
pts = set(pin_pts) | {(x, y) for (_, x, y, _) in PWR}
for a, b in WIRES: pts |= {a, b}
def interior(p, a, b):
    if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]): return True
    if a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]): return True
    return False
changed = True
while changed:
    changed = False
    for i, (a, b) in enumerate(WIRES):
        for p in pts:
            if interior(p, a, b):
                WIRES[i:i + 1] = [(a, p), (p, b)]; changed = True; break
        if changed: break
WIRES = list(dict.fromkeys(WIRES))
cnt = defaultdict(int)
for a, b in WIRES: cnt[a] += 1; cnt[b] += 1
for p in pin_pts: cnt[p] += 1
for (_, x, y, _) in PWR: cnt[(x, y)] += 1
JUNCS = [p for p, n in cnt.items() if n >= 3]

out = []; w = out.append
w(f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid {q(ROOT)}) (paper {q(globals().get("PAPER", "A2"))})')
w(TITLE_BLOCK)
w('  (lib_symbols')
used_syms = sorted({symof(k) for k in PLACE} | {"PWR_" + n for n in POWER})
for name in used_syms:
    s = SYMS[name]
    is_pwr = s["kind"] == "power"
    hide_names = "" if s["names"] else " hide"
    w(f'    (symbol {q(LIB + ":" + name)}' + (" (power)" if is_pwr else "") + (" (pin_numbers hide)" if is_pwr else "") +
      f' (pin_names (offset {"1.016" if s["names"] else "0"}){hide_names}) (exclude_from_sim no)'
      f' (in_bom {"no" if s["kind"] in ("power", "flag") else "yes"}) (on_board {"no" if s["kind"] in ("power", "flag") else "yes"})')
    w(f'      (property "Reference" {q(s["ref"])} (at {fmt(s["ref_at"][0])} {fmt(s["ref_at"][1])} 0) {FONT_HIDE if is_pwr else FONT})')
    w(f'      (property "Value" {q(s.get("net", name))} (at {fmt(s["val_at"][0])} {fmt(s["val_at"][1])} 0) {FONT})')
    for k in ("Footprint", "Datasheet", "Description"):
        w(f'      (property "{k}" "" (at 0 0 0) {FONT_HIDE})')
    units = s["units"] if "units" in s else None
    if units is None:
        w(f'      (symbol {q(name + "_0_1")} ' + " ".join(s["body"]) + ')')
        units = {1: dict(pins=s["pins"], body=[])}
    for un, ud in units.items():
        pin_s = [f'(pin {ptype} line (at {fmt(x)} {fmt(y)} {ang}) (length {fmt(ln)}) (name {q(pname)} {FONT}) (number {q(num)} {FONT}))'
                 for (num, pname, ptype, x, y, ang, ln) in ud["pins"]]
        w(f'      (symbol {q(name + f"_{un}_1")} ' + " ".join(ud["body"] + pin_s) + ')')
    w('    )')
w('  )')

def emit_symbol(lib_name, ref, val, x, y, rot, props, pins, ref_xy, val_xy, hide_ref=False, bom=True, just="", unit=1, lcsc=None, dnp=False):
    w(f'  (symbol (lib_id {q(LIB + ":" + lib_name)}) (at {fmt(x)} {fmt(y)} {rot}) (unit {unit}) (exclude_from_sim no)'
      f' (in_bom {"yes" if bom else "no"}) (on_board {"yes" if bom else "no"}) (dnp {"yes" if dnp else "no"}) (uuid {q(U())})')
    w(f'    (property "Reference" {q(ref)} (at {fmt(ref_xy[0])} {fmt(ref_xy[1])} 0) (effects (font (size 1.27 1.27)) {just}{" (hide yes)" if hide_ref else ""}))')
    w(f'    (property "Value" {q(val)} (at {fmt(val_xy[0])} {fmt(val_xy[1])} 0) (effects (font (size 1.27 1.27)) {just}))')
    for k, v in props:
        w(f'    (property {q(k)} {q(v)} (at {fmt(x)} {fmt(y)} 0) {FONT_HIDE})')
    if lcsc is not None:
        txt, (lx, ly), show = lcsc
        w(f'    (property "LCSC" {q(txt)} (at {fmt(lx)} {fmt(ly)} 0) (effects (font (size 1.016 1.016)) {just}{"" if show else " (hide yes)"}))')
    for pn in pins:
        w(f'    (pin {q(pn)} (uuid {q(U())}))')
    w(f'    (instances (project {q(PROJECT)} (path {q("/" + ROOT)} (reference {q(ref)}) (unit {unit}))))')
    w('  )')

TXT_POS = {}
for key, pl in PLACE.items():
    p = NETS[key]; name = symof(key); s = SYMS[name]
    X, Y = pl["x"], pl["y"]
    unit = key[1]
    flag = s["kind"] == "flag"
    rx, ry = X + s["ref_at"][0], Y - s["ref_at"][1]
    vx, vy = X + s["val_at"][0], Y - s["val_at"][1]
    just = ""
    if s["kind"] == "passive":
        just = "(justify left)"; lpos = (X + 2.54, Y + 3.81)
    elif s["kind"] == "hpass":
        lpos = (X, vy + 2.03)
    elif s["kind"] == "qh":
        just = "(justify left)"; rx, ry = X + 3.81, Y - 5.08; vx, vy = X + 3.81, Y + 4.32; lpos = (X + 3.81, Y + 6.35)
    else:
        lpos = (vx, vy + 2.29)
    if name == "OPA2187" or name == "DAC8812":
        if unit != 1 and not (name == "DAC8812" and unit == 3): pass
    show_lcsc = bool(p.get("lcsc")) and not p.get("hide_lcsc") and (("units" not in s) or unit == 1)
    props = [("Footprint", p.get("fp", "")), ("Datasheet", ""), ("Description", "")]
    allpins = [pp[0] for pp in pins_of(key)]
    emit_symbol(name, p["ref"], p["val"], X, Y, 0, props, allpins, (rx, ry), (vx, vy), hide_ref=flag, bom=not flag,
                just=just, unit=unit, lcsc=None if flag else (p.get("lcsc") or "", lpos, show_lcsc), dnp=p.get("dnf", False))
    TXT_POS[f"{key[0]}|{key[1]}"] = dict(ref=(rx, ry), val=(vx, vy), lcsc=lpos, just=just, show=show_lcsc)

PWR_OUT = []
for i, (net, x, y, down) in enumerate(PWR):
    s = SYMS["PWR_" + net]
    natural_down = s["style"] != "rail"
    rot = 0 if natural_down == down else 180
    vy = y + 3.81 if down else y - 3.81
    emit_symbol("PWR_" + net, f"#PWR{i+1:03d}", net, x, y, rot, [("Footprint", ""), ("Datasheet", ""), ("Description", "")], ["1"],
                (x, y), (x, vy), hide_ref=True, bom=False)
    PWR_OUT.append((net, x, y, rot, down))
for (a, b) in WIRES:
    w(f'  (wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) (stroke (width 0) (type default)) (uuid {q(U())}))')
for (x, y) in JUNCS:
    w(f'  (junction (at {fmt(x)} {fmt(y)}) (diameter 0) (color 0 0 0 0) (uuid {q(U())}))')
for (net, x, y, ang) in LABELS:
    if net in globals().get("HIER", {}):
        w(f'  (hierarchical_label {q(net)} (shape {HIER[net]}) (at {fmt(x)} {fmt(y)} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {"left" if ang in (0, 90) else "right"})) (uuid {q(U())}))')
        continue
    j = "left bottom" if ang in (0, 90) else "right bottom"
    w(f'  (label {q(net)} (at {fmt(x)} {fmt(y)} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {j})) (uuid {q(U())}))')
for (x, y) in NCS:
    w(f'  (no_connect (at {fmt(x)} {fmt(y)}) (uuid {q(U())}))')
for (x1, y1, x2, y2) in FRAMES:
    w(f'  (rectangle (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)}) (stroke (width 0.254) (type dash) (color 120 120 120 1)) (fill (type none)) (uuid {q(U())}))')
for (x, y, t, sz) in TEXTS:
    w(f'  (text {q(t)} (exclude_from_sim no) (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz})) (justify left bottom)) (uuid {q(U())}))')
w(f'  (text {q(NOTES)} (exclude_from_sim no) (at {fmt(NOTES_AT[0])} {fmt(NOTES_AT[1])} 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid {q(U())}))')
w('  (sheet_instances (path "/" (page "1")))')
w(')')
open(f"{PROJECT}.kicad_sch", "w").write("\n".join(out) + "\n")

libout = ['(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")']
txt = "\n".join(out)
for name in used_syms:
    m = re.search(r'\n    \(symbol "' + re.escape(LIB + ":" + name) + r'"(.*?)\n    \)', txt, re.S)
    libout.append(f'  (symbol {q(name)}' + m.group(1).replace("\n      ", "\n    ") + "\n  )")
libout.append(")")
open(f"{LIB}.kicad_sym", "w").write("\n".join(libout) + "\n")
open("sym-lib-table", "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "AOut")(type "KiCad")(uri "${KIPRJMOD}/AOut.kicad_sym")(options "")(descr "Analog output board symbols"))\n)\n')
json.dump({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}, "sheets": [[ROOT, "Root"]]}, open(f"{PROJECT}.kicad_pro", "w"), indent=2)

conns = []
for key, p in NETS.items():
    for n, net in p["nets"].items(): conns.append((p["ref"], n, net))
geo = dict(parts=[dict(ref=k[0], unit=k[1], x=v["x"], y=v["y"], sym=symof(k), val=NETS[k]["val"], lcsc=NETS[k].get("lcsc", ""),
                       txt=TXT_POS[f"{k[0]}|{k[1]}"]) for k, v in PLACE.items()],
           syms={n: dict(kind=SYMS[n]["kind"], style=SYMS[n].get("style"), names=SYMS[n].get("names"),
                         units={str(u): dict(pins=d["pins"], body=d["body"]) for u, d in SYMS[n]["units"].items()} if "units" in SYMS[n]
                         else {"1": dict(pins=SYMS[n]["pins"], body=SYMS[n]["body"])}) for n in used_syms},
           conns=conns, wires=WIRES, junctions=JUNCS, labels=LABELS, ncs=NCS, pwr=PWR_OUT, frames=FRAMES, texts=TEXTS,
           notes=(NOTES_AT, NOTES))
json.dump(geo, open("geom_hand.json", "w"))
print(f"parts {len(PLACE)} wires {len(WIRES)} junctions {len(JUNCS)} labels {len(LABELS)} power {len(PWR)}")
