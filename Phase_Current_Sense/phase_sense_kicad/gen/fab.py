"""Copy final board into the project and generate JLCPCB outputs (gerbers, drill, BOM, CPL, previews).
Run with /usr/bin/python3 (needs pcbnew)."""
import os, sys, csv, json, shutil, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew
from design import PARTS

ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "pcbwork")
PCB = os.path.join(OUT, "phase_sense.kicad_pcb")
def run(*a): subprocess.run(list(a), check=True, capture_output=True)

# project file + board
d = json.load(open(os.path.join(WORK, "final.kicad_pro")))
d["meta"]["filename"] = "phase_sense.kicad_pro"
d["sheets"] = [["e0bd0f26-c5a1-5d45-800f-4f195a0cbe1f", ""]]
json.dump(d, open(os.path.join(OUT, "phase_sense.kicad_pro"), "w"), indent=2)
shutil.copy(os.path.join(WORK, "final.kicad_pcb"), PCB)
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase_sense.kicad_dru"), os.path.join(OUT, "phase_sense.kicad_dru"))

# consistency check board <-> design
b = pcbnew.LoadBoard(PCB); err = 0
for p in PARTS:
    fp = b.FindFootprintByReference(p["ref"])
    err += fp.GetPath().AsString() != "/" + p["uuid"]
    for pad in fp.Pads(): err += pad.GetNetname() != (p["pins"].get(pad.GetNumber()) or "")
print("board vs schematic mismatches:", err)

# gerbers + drill
g = os.path.join(OUT, "fab", "gerbers")
shutil.rmtree(g, ignore_errors=True); os.makedirs(g)
run("kicad-cli", "pcb", "export", "gerbers", "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,Edge.Cuts",
    "--subtract-soldermask", "-o", g + "/", PCB)
run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute",
    "--excellon-units", "mm", "-o", g + "/", PCB)
z = os.path.join(OUT, "fab", "gerbers_JLCPCB.zip")
if os.path.exists(z): os.remove(z)
run("zip", "-j", "-q", z, *glob.glob(g + "/*"))

# BOM + CPL (all parts with an LCSC number; THT terminals included)
run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "-o", "/tmp/pos.csv", PCB)
pos = {r["Ref"]: r for r in csv.DictReader(open("/tmp/pos.csv"))}
fpd = {fp.GetReference(): fp for fp in b.GetFootprints()}
groups = {}
for p in PARTS:
    if p["lcsc"] and not p.get("dnp"):
        groups.setdefault((p["value"], p["fp"].split(":")[1], p["lcsc"]), []).append(p["ref"])
with open(os.path.join(OUT, "fab", "BOM_JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (v, fpn, l), refs in sorted(groups.items(), key=lambda x: x[1][0]):
        w.writerow([v, ",".join(sorted(refs)), fpn, l])
with open(os.path.join(OUT, "fab", "CPL_JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for p in PARTS:
        if not p["lcsc"] or p.get("dnp"): continue
        if p["ref"] in pos:
            r = pos[p["ref"]]; x, y, rot = float(r["PosX"]), float(r["PosY"]), float(r["Rot"])
        else:                                   # THT parts are not in the KiCad pos file
            fp = fpd[p["ref"]]
            x, y = pcbnew.ToMM(fp.GetPosition().x), -pcbnew.ToMM(fp.GetPosition().y)
            rot = fp.GetOrientationDegrees()
        w.writerow([p["ref"], f"{x:.3f}mm", f"{y:.3f}mm", "Top", f"{rot:.0f}"])

# previews
pv = os.path.join(OUT, "previews"); os.makedirs(pv, exist_ok=True)
run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(pv, "phase_sense_schematic.pdf"), os.path.join(OUT, "phase_sense.kicad_sch"))
for name, layers in (("pcb_top", "F.Cu,F.SilkS,Edge.Cuts,F.Mask"), ("pcb_bottom", "B.Cu,B.SilkS,Edge.Cuts")):
    run("kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2",
        "--exclude-drawing-sheet", "-o", f"/tmp/{name}.svg", PCB)
    run("rsvg-convert", "-w", "1800", "-b", "#0b2a16", f"/tmp/{name}.svg", "-o", os.path.join(pv, f"{name}.png"))
print(open(os.path.join(OUT, "fab", "BOM_JLCPCB.csv")).read())
