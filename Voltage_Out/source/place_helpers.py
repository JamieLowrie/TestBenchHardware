# ------------------------------------------------------------------ placement
PLACE = {}
def put(ref, x, y, sym=None, unit=1):
    for v in (x, y):
        assert abs(round(v / 1.27) * 1.27 - v) < 1e-6, (ref, x, y)
    PLACE[(ref, unit)] = dict(x=round(x, 4), y=round(y, 4), sym=sym)
def symof(key):
    p = NETS[key]; s = PLACE[key]["sym"] or p["sym"]
    return s
def pins_of(key):
    s = SYMS[symof(key)]
    return s["units"][key[1]]["pins"] if "units" in s else s["pins"]
def pin(ref, num, unit=1):
    key = (ref, unit)
    X, Y = PLACE[key]["x"], PLACE[key]["y"]
    for (n, nm, t, px, py, ang, ln) in pins_of(key):
        if n == num: return (round(X + px, 4), round(Y - py, 4))
    raise KeyError((ref, num, unit))

WIRES, PWR, LABELS, NCS, FRAMES, TEXTS = [], [], [], [], [], []
def W(*pts):
    pts = [tuple(round(c, 4) for c in p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        assert a[0] == b[0] or a[1] == b[1], ("diagonal", a, b)
        if a != b: WIRES.append((a, b))
    return pts[-1]
def R_(p, dx=0, dy=0): return (round(p[0] + dx, 4), round(p[1] + dy, 4))
def pw(net, p, down=None):
    """power symbol at p. down=True -> body below (gnd style); default by style"""
    style = POWER[net]
    if down is None: down = style != "rail" or net == "-15V"
    PWR.append((net, p[0], p[1], down))
def stubpw(net, p, dx=0, dy=0, down=None):
    e = W(p, R_(p, dx, dy)); pw(net, e, down); return e
def lab(net, p, ang=0): LABELS.append((net, p[0], p[1], ang))
def stublab(net, p, dx, dy=0):
    e = W(p, R_(p, dx, dy))
    ang = 0 if dx > 0 else 180 if dx < 0 else (90 if dy < 0 else 270)
    lab(net, e, ang); return e
def nc(p): NCS.append(p)
def frame(x1, y1, x2, y2, title):
    FRAMES.append((x1, y1, x2, y2)); TEXTS.append((x1 + 2.54, y1 + 5.08, title, 2.54))
def vcap(ref, x, ytop, unit=1):   # vertical passive whose pin1 sits at (x, ytop)
    put(ref, x, ytop + 3.81, unit=unit)

