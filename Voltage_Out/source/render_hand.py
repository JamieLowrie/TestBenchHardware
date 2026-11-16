"""PNG/PDF preview of the hand-drawn schematic, drawn from the symbol graphics actually written to the file."""
import json, re, sys, math
TITLE_TXT = sys.argv[3] if len(sys.argv) > 3 else "CAN Analog Output 0-12 V / 100 mA   Rev A   2026-11-13"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arc, Polygon

g = json.load(open(sys.argv[4] if len(sys.argv) > 4 else "geom_hand.json"))
SC = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
import os
PW, PH = (420, 297) if os.environ.get("PAPER") == "A3" else (594, 420)
fig, ax = plt.subplots(figsize=(PW / 25.4 * SC, PH / 25.4 * SC), dpi=150)
ax.set_xlim(5, PW - 5); ax.set_ylim(PH - 5, 5); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(Rectangle((10, 10), PW - 20, PH - 20, fill=False, lw=0.8, ec="#8B0000"))
INK, NET, TXT, PINC = "#840000", "#008400", "#006496", "#840000"
FS = 4.2 * SC  # 1.27 mm text in points at this scale

def nums(s): return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", s)]
def draw_body(item, X, Y):
    fill = "(fill (type background))" in item and "#ffffc2" or ("(fill (type outline))" in item and INK) or "none"
    if item.startswith("(polyline"):
        pts = re.findall(r"\(xy (-?[\d.]+) (-?[\d.]+)\)", item)
        xs = [X + float(a) for a, b in pts]; ys = [Y - float(b) for a, b in pts]
        lw = 1.6 if "width 0.508" in item else 0.9
        if fill != "none" and len(pts) > 2:
            ax.add_patch(Polygon(list(zip(xs, ys)), closed=True, fc=fill, ec=INK, lw=lw * SC))
        else:
            ax.plot(xs, ys, color=INK, lw=lw * SC, solid_capstyle="round")
    elif item.startswith("(rectangle"):
        x1, y1, x2, y2 = nums(item.split("(stroke")[0])[:4]
        ax.add_patch(Rectangle((X + min(x1, x2), Y - max(y1, y2)), abs(x2 - x1), abs(y2 - y1), fc=fill, ec=INK, lw=0.9 * SC))
    elif item.startswith("(circle"):
        cx, cy, r = nums(item.split("(stroke")[0])[:3]
        ax.add_patch(Circle((X + cx, Y - cy), r, fill=False, ec=INK, lw=0.9 * SC))
    elif item.startswith("(arc"):
        sx, sy, mx, my, ex, ey = nums(item.split("(stroke")[0])[:6]
        P = [(X + sx, Y - sy), (X + mx, Y - my), (X + ex, Y - ey)]
        (ax1, ay1), (bx, by), (cx2, cy2) = P
        d = 2 * (ax1 * (by - cy2) + bx * (cy2 - ay1) + cx2 * (ay1 - by))
        ux = ((ax1**2 + ay1**2) * (by - cy2) + (bx**2 + by**2) * (cy2 - ay1) + (cx2**2 + cy2**2) * (ay1 - by)) / d
        uy = ((ax1**2 + ay1**2) * (cx2 - bx) + (bx**2 + by**2) * (ax1 - cx2) + (cx2**2 + cy2**2) * (bx - ax1)) / d
        r = math.hypot(ax1 - ux, ay1 - uy)
        a = [math.atan2(p[1] - uy, p[0] - ux) for p in P]
        ts = [a[0] + t * ((a[2] - a[0]) % (2 * math.pi)) for t in (0, .25, .5, .75, 1)]
        if not any(abs(((t - a[1] + math.pi) % (2 * math.pi)) - math.pi) < 0.6 for t in ts):
            ts = [a[0] - t * ((a[0] - a[2]) % (2 * math.pi)) for t in (0, .25, .5, .75, 1)]
        ts2 = [ts[0] + (ts[-1] - ts[0]) * k / 20 for k in range(21)]
        ax.plot([ux + r * math.cos(t) for t in ts2], [uy + r * math.sin(t) for t in ts2], color=INK, lw=0.9 * SC)
    elif item.startswith("(text"):
        t = re.search(r'\(text "([^"]*)"', item).group(1); x, y = nums(item.split("(at")[1])[:2]
        ax.text(X + x, Y - y, t, fontsize=FS * 1.1, ha="center", va="center", color=INK)

for p in g["parts"]:
    s = g["syms"][p["sym"]]; u = s["units"].get(str(p["unit"])) or s["units"]["1"]
    X, Y = p["x"], p["y"]
    for b in u["body"]: draw_body(b, X, Y)
    tri = p["sym"] == "OPA2187" and p["unit"] in (1, 2)
    for (num, name, ptype, px, py, ang, ln) in u["pins"]:
        tx, ty = X + px, Y - py
        d = {0: (1, 0), 180: (-1, 0), 270: (0, 1), 90: (0, -1)}[ang]
        ax.plot([tx, tx + d[0] * ln], [ty, ty + d[1] * ln], color=PINC, lw=0.8 * SC)
        if s["kind"] in ("power", "flag"): continue
        if s["names"] and name not in ("~",):
            nm = name.replace("~{", "/").replace("}", "")
            ex, ey = tx + d[0] * (ln + 0.6), ty + d[1] * (ln + 0.6)
            if ang == 0: ax.text(ex, ey, nm, fontsize=FS * (1.15 if tri else 0.95), va="center", ha="left", color="#006464")
            elif ang == 180: ax.text(ex, ey, nm, fontsize=FS * 0.95, va="center", ha="right", color="#006464")
            elif ang == 270: ax.text(ex, ey + 0.4, nm, fontsize=FS * 0.8, va="top", ha="center", color="#006464")
        if s["kind"] not in ("passive", "hpass") and not tri:
            if ang in (0, 180): ax.text(tx + d[0] * ln / 2, ty - 0.45, num, fontsize=FS * 0.7, ha="center", va="bottom", color=PINC)
            else: ax.text(tx + 0.45, ty + d[1] * ln / 2, num, fontsize=FS * 0.7, va="center", ha="left", color=PINC)
    if s["kind"] == "flag":
        ax.text(X, Y - 3.0, "PWR_FLAG", fontsize=FS * 0.7, ha="center", color=INK); continue
    t = p["txt"]; ha = "left" if "left" in t["just"] else "center"
    ref = p["ref"] + ("ABC"[p["unit"] - 1] if p["sym"] in ("OPA2187", "DAC8812") else "")
    ax.text(*t["ref"], ref, fontsize=FS * 1.05, ha=ha, va="center", color=TXT, fontweight="bold")
    ax.text(*t["val"], p["val"], fontsize=FS, ha=ha, va="center", color=TXT)
    if t["show"]: ax.text(*t["lcsc"], p["lcsc"], fontsize=FS * 0.75, ha=ha, va="center", color="#7a4b00")

for (net, x, y, rot, down) in g["pwr"]:
    style = g["syms"]["PWR_" + net]["style"]; sg = 1 if down else -1
    if style == "rail":
        ax.plot([x, x], [y, y + sg * 2.54], color=INK, lw=0.8 * SC)
        ax.plot([x - 0.762, x, x + 0.762], [y + sg * 1.27, y + sg * 2.54, y + sg * 1.27], color=INK, lw=0.8 * SC)
    elif style == "gnd":
        ax.plot([x, x, x + 1.27, x, x - 1.27, x], [y, y + sg * 1.27, y + sg * 1.27, y + sg * 2.54, y + sg * 1.27, y + sg * 1.27], color=INK, lw=0.8 * SC)
    else:
        ax.plot([x, x], [y, y + sg * 1.27], color=INK, lw=0.8 * SC)
        for k, hw in ((1.27, 1.524), (1.905, 1.016), (2.54, 0.508)):
            ax.plot([x - hw, x + hw], [y + sg * k] * 2, color=INK, lw=0.8 * SC)
    ax.text(x, y + sg * 3.3, net, fontsize=FS * 0.85, ha="center", va="top" if down else "bottom", color=INK)
for (a, b) in g["wires"]:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=NET, lw=0.9 * SC, solid_capstyle="round")
for (x, y) in g["junctions"]:
    ax.add_patch(Circle((x, y), 0.5, color=NET))
for (net, x, y, ang) in g["labels"]:
    k = dict(fontsize=FS, color="#000")
    if ang == 0: ax.text(x + 0.3, y - 0.3, net, ha="left", va="bottom", **k)
    elif ang == 180: ax.text(x - 0.3, y - 0.3, net, ha="right", va="bottom", **k)
    elif ang == 90: ax.text(x - 0.3, y - 0.3, net, ha="right", va="bottom", rotation=90, **k)
    else: ax.text(x - 0.3, y + 0.3, net, ha="right", va="top", rotation=90, **k)
for (x, y) in g["ncs"]:
    ax.plot([x - 0.8, x + 0.8], [y - 0.8, y + 0.8], color="#0000c8", lw=0.8 * SC)
    ax.plot([x - 0.8, x + 0.8], [y + 0.8, y - 0.8], color="#0000c8", lw=0.8 * SC)
for (x1, y1, x2, y2) in g["frames"]:
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, ec="#787878", lw=0.8 * SC, ls=(0, (6, 4))))
for (x, y, t, sz) in g["texts"]:
    ax.text(x, y, t, fontsize=FS * sz / 1.27, ha="left", va="bottom", color="#000", linespacing=1.3,
            fontweight="bold" if sz > 2 else "normal")
(nx, ny), nt = g["notes"]
ax.text(nx, ny, nt, fontsize=FS * 0.95, ha="left", va="top", family="monospace", color="#000", linespacing=1.35)
ax.text(PW - 172, PH - 15, TITLE_TXT, fontsize=FS * 1.6, color="#000")
out = sys.argv[2] if len(sys.argv) > 2 else "schematic_preview.png"
plt.savefig(out, bbox_inches="tight", pad_inches=0.1)
print("ok", out)
