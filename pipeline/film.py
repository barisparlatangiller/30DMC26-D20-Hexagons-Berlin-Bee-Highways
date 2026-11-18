"""
Day 20 film for LinkedIn (1080×1350, ~24 s, top view): the pilot area appears (flowers for bees on the ground, 60,000 trees
one by one), a honeycomb rises above it (cell size = link strength for small wild bees, colour = wild-bee records), the
months sweep from March to September, then 25 bee stops at bus and tram stops join the flower islands.

  python pipeline/film.py
Output build/video/day20_berlin_bee_highways.mp4 · cover.png · still_*.png · outro.png
"""
import json, math, subprocess, time
from pathlib import Path

import numpy as np
import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B, D, OUT = Path("build"), Path("docs/data"), Path("build/video")
W, H, FPS = 1080, 1350, 24
MAP_Y, MAP_H = 196, 1004
X0, Y0, X1, Y1 = 389500, 5811000, 396500, 5817000
BG = (244, 239, 228)
INK, INK2, INK3 = (43, 41, 37), (111, 106, 97), (155, 149, 138)
HONEY_ACC, VIOLET = (185, 120, 18), (138, 122, 196)
HONEY = [(0, (252, 246, 228)), (1, (244, 214, 128)), (3, (232, 176, 60)), (8, (196, 128, 22)), (20, (140, 84, 10))]
MON = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
ST = json.loads((D / "stats.json").read_text())
HJ = json.loads((D / "hex.json").read_text())
HV = np.fromfile(D / "hexv.bin", np.uint8).reshape(HJ["n"], 28) / 255.0


def font(size, bold=False):
    f = subprocess.run(["fc-match", "-f", "%{file}", "Inter:bold" if bold else "Inter:medium"], capture_output=True, text=True).stdout.strip()
    return ImageFont.truetype(f, size)


F = {"q": font(56, True), "qs": font(24, True), "mid": font(36, True), "sm": font(27), "lab": font(21, True), "foot": font(17), "big": font(104, True), "num": font(70, True)}


def ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def honey(n):
    for (a, ca), (b, cb) in zip(HONEY[:-1], HONEY[1:]):
        if n <= b:
            t = (n - a) / (b - a); return tuple(int(c + (d - c) * t) for c, d in zip(ca, cb))
    return HONEY[-1][1]


class View:
    def __init__(self, cx, cy, span):
        self.span, self.px = span, span / W
        self.x0, self.y1 = cx - span / 2, cy + MAP_H * self.px / 2

    def xy(self, x, y):
        return (np.asarray(x) - self.x0) / self.px, (self.y1 - np.asarray(y)) / self.px + MAP_Y

    def lerp(self, o, t):
        cx = (self.x0 + self.span / 2) * (1 - t) + (o.x0 + o.span / 2) * t
        cy = (self.y1 - MAP_H * self.px / 2) * (1 - t) + (o.y1 - MAP_H * o.px / 2) * t
        return View(cx, cy, self.span * (1 - t) + o.span * t)


FULL = View((X0 + X1) / 2, (Y0 + Y1) / 2, 7000)
K2 = 2


def ground_canvas(month):
    """2× canvas of the FULL view: biotopes coloured by forage, buildings, trees for the given month"""
    Wb, Hb = W * K2, MAP_H * K2; pxm = FULL.px / K2
    im = Image.new("RGB", (Wb, Hb), (236, 233, 226)); d = ImageDraw.Draw(im, "RGBA")
    tr = lambda x, y: ((x - FULL.x0) / pxm, (FULL.y1 - y) / pxm)
    bt = gpd.read_parquet(B / "biotopes.parquet")
    import re as _re
    src = Path("pipeline/build_web.py").read_text()
    CAT = eval(_re.search(r"CAT = (\{.*?\})\n", src, _re.S).group(1))
    COLS = {"meadow": (156, 196, 106), "garden": (188, 208, 126), "park": (168, 197, 154), "yard": (212, 220, 182), "lawn": (223, 227, 204), "water": (207, 224, 230)}
    def fcol(rule):
        c = CAT.get(rule) or ("water" if str(rule).startswith("water") else None)
        return COLS.get(c, (236, 232, 224))
    for g, f in zip(bt.geometry, bt.rule):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            d.polygon([tr(*c) for c in p.exterior.coords], fill=fcol(f) + (255,), outline=(255, 255, 255, 120))
            for h in p.interiors:
                d.polygon([tr(*c) for c in h.coords], fill=(236, 233, 226, 255))
    bl = gpd.read_parquet(B / "buildings.parquet")
    for g, h in zip(bl.geometry, bl.h):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            pts = [tr(*c) for c in p.exterior.coords]; o = min(8, h / pxm * 0.18)
            d.polygon([(x + o, y + o) for x, y in pts], fill=(150, 140, 125, 70))
            d.polygon(pts, fill=(246, 243, 237, 255), outline=(214, 208, 198, 255))
    return im


def trees_layer(base, month, alpha=1.0, scale=1.0):
    im = base.copy(); d = ImageDraw.Draw(im, "RGBA"); pxm = FULL.px / K2
    t = gpd.read_parquet(B / "trees.parquet")
    bit = month
    for g, cr, v, bl in zip(t.geometry, t.crown, t.value, t.bloom):
        x, y = (g.x - FULL.x0) / pxm, (FULL.y1 - g.y) / pxm
        a_, *b_ = [int(z) for z in bl.split("-")] if isinstance(bl, str) and bl else [0]
        on = bl and a_ <= month <= (b_[0] if b_ else a_)
        if on and v >= 0.5:
            c = (236, 186, 70)
        elif on and v >= 0.25:
            c = (200, 196, 104)
        else:
            c = (104, 142, 92)
        r = max(1.2, cr / 2 / pxm * scale)
        d.ellipse([x - r + 1.5, y - r + 1.5, x + r + 1.5, y + r + 1.5], fill=(60, 70, 40, int(60 * alpha)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (int(235 * alpha),))
    return im


def crop(big, v):
    s = v.span / FULL.span
    x0, y0 = (v.x0 - FULL.x0) / (FULL.px / K2), (FULL.y1 - v.y1) / (FULL.px / K2)
    return big.resize((W, MAP_H), Image.LANCZOS, box=(x0, y0, x0 + W * K2 * s, y0 + MAP_H * K2 * s))


# hex centres in EPSG:25833
from pyproj import Transformer
_t = Transformer.from_crs(4326, 25833, always_xy=True)
HX, HY = _t.transform(np.array(HJ["lon"]), np.array(HJ["lat"]))
OBS = np.array(HJ["obs"]); GAP = np.array(HJ["gap"])
HCOL = [honey(n) for n in OBS]


GAPTHR = np.sort(GAP)[int(len(GAP) * 0.975)]
JOINED7 = np.array(HJ["big1"]["07"]) & ~np.array(HJ["big0"]["07"]).astype(bool)


HEAT = [(0.3, (247, 236, 210)), (0.55, (241, 204, 110)), (0.8, (222, 156, 46)), (1.0, (166, 98, 14))]


def heat(v):
    for (a, ca), (b, cb) in zip(HEAT[:-1], HEAT[1:]):
        if v <= b:
            t = max(0.0, (v - a) / (b - a)); return tuple(int(c + (d - c) * t) for c, d in zip(ca, cb))
    return HEAT[-1][1]


def hex_scale(v):
    return np.where(v < 0.3, 0, 0.35 + 0.6 * np.power(np.clip((v - 0.3) / 0.7, 0, 1), 1.2))


def draw_hexes(im, v, vals, lift=1.0, alpha=0.85, gaps=0.0, joined=0.0):
    """honeycomb floating above the ground: shadow offset by 'lift', cells sized by vals (0–1)"""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    e = HJ["edge"] / v.px
    px, py = v.xy(HX, HY); py = py - MAP_Y                      # drawn on the map image, not the frame
    sc = hex_scale(vals)
    if joined > 0:
        sc = np.where(JOINED7, np.maximum(sc, 0.62 * joined), sc)
    ang = np.arange(6) * np.pi / 3
    off = 9 * lift
    m = (px > -20) & (px < W + 20) & (py > -20) & (py < MAP_H + 20) & (sc > 0)
    for i in np.nonzero(m)[0]:
        r = e * sc[i]
        pts = [(px[i] + r * math.cos(a), py[i] + r * math.sin(a)) for a in ang]
        if joined > 0 and JOINED7[i]:
            d.polygon(pts, fill=VIOLET + (int(235 * joined),), outline=(255, 255, 255, 140))
        else:
            d.polygon(pts, fill=heat(vals[i]) + (int(255 * alpha * (0.6 + 0.4 * vals[i])),))
    if gaps > 0:
        for i in np.nonzero((GAP >= GAPTHR) & (px > 0) & (px < W) & (py > 0) & (py < MAP_H))[0]:
            pts = [(px[i] + e * 0.98 * math.cos(a), py[i] + e * 0.98 * math.sin(a)) for a in ang]
            d.line(pts + [pts[0]], fill=VIOLET + (int(230 * gaps),), width=2)
    sh = sh.filter(ImageFilter.GaussianBlur(2.5))
    out = Image.alpha_composite(im.convert("RGBA"), sh)
    return Image.alpha_composite(out, ov)


HONEY_C = (220, 154, 44)
PAL = [(127, 167, 184), (165, 140, 191), (143, 176, 138), (201, 154, 138), (159, 165, 201), (184, 176, 122), (134, 181, 168), (190, 150, 175)]
IV = json.loads((D / "interventions.json").read_text())
HW = json.loads((D / "highways.json").read_text())
HISL = np.fromfile(D / "hexisl.bin", "<u2").reshape(HJ["n"], 6)
KCOL = {"stops": (138, 122, 196), "treepits": (79, 143, 90), "schools": (91, 134, 196), "parking": (150, 132, 110)}


def islands_state(m, picks):
    """union-find over the chosen picks → root per island, area per root, largest root"""
    A = IV["area"][m]; par = list(range(len(A)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for p in picks:
        r = [find(i) for i in p["reach"][m]]
        for q in r[1:]:
            par[find(q)] = find(r[0])
    root = [find(i) for i in range(len(A))]; tot = {}
    for i in range(1, len(A)):
        tot[root[i]] = tot.get(root[i], 0) + A[i]
    big = max(tot, key=tot.get)
    return root, tot, big


def draw_islands(im, v, m, state, alpha=1.0, flash=None):
    root, tot, big = state
    k = IV["months"].index(m)
    d = ImageDraw.Draw(im, "RGBA")
    e = HJ["edge"] * 0.93 / v.px
    px, py = v.xy(HX, HY); py = py - MAP_Y
    ang = np.arange(6) * np.pi / 3
    isl = HISL[:, k]
    for i in np.nonzero((isl > 0) & (px > -20) & (px < W + 20) & (py > -20) & (py < MAP_H + 20))[0]:
        r = root[isl[i]]; a_ = tot[r]
        c = HONEY_C if r == big else ((214, 208, 194) if a_ < 3 else PAL[r % len(PAL)])
        al = alpha
        if flash is not None and r == big and flash.get(isl[i]):
            al = min(1.0, alpha * (0.6 + 0.4 * flash[isl[i]]))
        pts = [(px[i] + e * math.cos(t), py[i] + e * math.sin(t)) for t in ang]
        d.polygon(pts, fill=c + (int(232 * al),))
    return im


def draw_highways(im, v, key, t, alpha=1.0, bees=True):
    d = ImageDraw.Draw(im, "RGBA")
    for h in HW[key]:
        x, y = _t.transform(np.array([q[0] for q in h["p"]]), np.array([q[1] for q in h["p"]]))
        px, py = v.xy(x, y); py = py - MAP_Y
        d.line(list(zip(px, py)), fill=(150, 88, 14, int((120 + 110 * h["s"]) * alpha)), width=max(2, int(2 + 7 * h["s"] * (FULL.span / v.span) ** 0.5)), joint="curve")
        if bees and alpha > 0.05:
            seg = np.hypot(np.diff(x), np.diff(y)); L_ = seg.sum(); cum = np.r_[0, np.cumsum(seg)]
            n = 2 + int(6 * h["s"])
            for k in range(n):
                s0 = ((t * 260 + k * L_ / n + hash(h["len"]) % 997) % (L_ + 1e-6))
                for tail in range(6):
                    s_ = s0 - tail * 14
                    if s_ < 0:
                        continue
                    j = min(len(seg) - 1, np.searchsorted(cum, s_) - 1); f = (s_ - cum[j]) / max(seg[j], 1e-6)
                    bx, by = px[j] + (px[j + 1] - px[j]) * f, py[j] + (py[j + 1] - py[j]) * f
                    r = 3.2 - tail * 0.4
                    d.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, 238, 176, int(255 * alpha * (1 - tail / 6))))
    return im


def draw_corridors(im, v, combo, key, beds_xy, alpha=1.0, t=0.0):
    """corridors with the additions: new ones near the beds in violet, with bees"""
    CORR = draw_corridors.__dict__.setdefault("C", json.loads((D / "corridors.json").read_text()))
    d = ImageDraw.Draw(im, "RGBA")
    bx, by = (np.array([b[0] for b in beds_xy]), np.array([b[1] for b in beds_xy])) if beds_xy else (np.zeros(0), np.zeros(0))
    for h in CORR[combo][key]:
        x, y = _t.transform(np.array([q[0] for q in h["p"]]), np.array([q[1] for q in h["p"]]))
        new = h["n"] and len(bx) and np.min(np.hypot(x[:, None] - bx[None], y[:, None] - by[None])) < 300
        px, py = v.xy(x, y); py = py - MAP_Y
        if new:
            d.line(list(zip(px, py)), fill=(124, 104, 196, int(240 * alpha)), width=max(4, int(4 + 6 * h["s"])), joint="curve")
        else:
            d.line(list(zip(px, py)), fill=(150, 88, 14, int((90 + 90 * h["s"]) * 0.6)), width=max(2, int(2 + 5 * h["s"])), joint="curve")
    return im


def icon(d, x, y, kind, r=13, a=255):
    c = KCOL[kind]
    d.ellipse([x - r, y - r, x + r, y + r], fill=c + (a,), outline=(255, 255, 255, a), width=3)
    if kind == "treepits":
        d.ellipse([x - r * 0.42, y - r * 0.6, x + r * 0.42, y + r * 0.2], fill=(255, 255, 255, a)); d.rectangle([x - 1.5, y + 0.1 * r, x + 1.5, y + r * 0.6], fill=(255, 255, 255, a))
    elif kind == "stops":
        d.rounded_rectangle([x - r * 0.35, y - r * 0.55, x + r * 0.35, y + r * 0.2], 2, fill=(255, 255, 255, a)); d.rectangle([x - 1.2, y + 0.2 * r, x + 1.2, y + r * 0.6], fill=(255, 255, 255, a))


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True); fr = OUT / "frames"; fr.mkdir(exist_ok=True)
    for f in fr.glob("*.jpg"):
        f.unlink()
    g0 = ground_canvas(7); T7 = trees_layer(g0, 7)
    base, t7 = crop(g0, FULL), crop(T7, FULL)
    print(f"[{time.time() - t0:.0f} s] canvases", flush=True)
    m = "07"; c = IV["combos"]; b7, tp7 = c["none"][m], c["treepits"][m]
    ST_ = ST
    LBL = [("TEMPELHOFER FELD", 13.401, 52.4735), ("HASENHEIDE", 13.4175, 52.4845), ("NEUKÖLLN", 13.44, 52.479), ("BRITZ", 13.437, 52.448), ("KREUZBERG", 13.395, 52.493), ("TEMPELHOF", 13.388, 52.458)]
    LX, LY = _t.transform(np.array([l[1] for l in LBL]), np.array([l[2] for l in LBL]))

    def compose(mapimg, title, sub, cap=None, labels=1.0, overlay=None):
        im = Image.new("RGB", (W, H), BG); im.paste(mapimg.convert("RGB"), (0, MAP_Y))
        d = ImageDraw.Draw(im, "RGBA")
        if labels > 0:
            px, py = FULL.xy(LX, LY)
            for (n, *_), x, y in zip(LBL, px, py):
                d.text((x, y), n, font=F["lab"], fill=(60, 56, 50, int(230 * labels)), anchor="mm", stroke_width=4, stroke_fill=(255, 253, 248, int(230 * labels)))
        d.rectangle([0, 0, W, MAP_Y], fill=BG)
        d.text((48, 34), "#30DAYMAPCHALLENGE · DAY 20 · HEXAGONS · BERLIN", font=F["qs"], fill=HONEY_ACC)
        d.text((48, 72), title, font=F["q"], fill=INK)
        if sub:
            d.text((48, 142), sub, font=F["sm"], fill=INK2)
        d.rectangle([0, MAP_Y + MAP_H, W, H], fill=BG)
        if cap:
            d.text((48, MAP_Y + MAP_H + 24), cap[0], font=F["mid"], fill=INK)
            if len(cap) > 1:
                d.text((48, MAP_Y + MAP_H + 72), cap[1], font=F["sm"], fill=INK2)
        d.text((48, H - 30), "A model of potential, not measured flight routes · Berlin biotopes 2024 · trees · iNaturalist · GBIF · © OSM · B. Parlatangiller", font=F["foot"], fill=INK3)
        if overlay:
            overlay(d)
        return im

    n = 0
    def save(im):
        nonlocal n; im.save(fr / f"f{n:04d}.jpg", quality=92); n += 1

    def badge(d, val, sub, col=HONEY_ACC):
        d.rounded_rectangle([W - 330, MAP_Y + 22, W - 22, MAP_Y + 132], 20, fill=(255, 253, 248, 236))
        d.text((W - 306, MAP_Y + 32), val, font=F["mid"], fill=col); d.text((W - 306, MAP_Y + 82), sub, font=F["lab"], fill=INK2)

    Q = "Can a wild bee cross Neukölln?"
    state0 = islands_state(m, [])
    T = 0.0
    # A · flowers (2.4 s)
    for k in range(int(FPS * 2.4)):
        a = ease(k / (FPS * 1.2)); T += 1 / FPS
        save(compose(Image.blend(Image.new("RGB", base.size, BG), base, a), Q, "Tempelhofer Feld · Hasenheide · Neukölln", ("Where bees find flowers", "meadows, gardens, parks, green courtyards"), labels=a))
    # B · trees (2.2 s)
    for k in range(int(FPS * 2.2)):
        a = ease(k / (FPS * 1.2)); T += 1 / FPS
        save(compose(Image.blend(base, t7, a), Q, "July", (f"{ST_['trees']:,} trees, one by one", "honey = lime trees in flower")))
    # C · islands (3.4 s)
    for k in range(int(FPS * 3.4)):
        a = ease(k / (FPS * 1.4)); T += 1 / FPS
        img = draw_islands(t7.copy(), FULL, m, state0, alpha=a)
        save(compose(img, Q, "July · small solitary bees", (f"{ST_['islands_n'][m]} separate flower islands", "one colour = one network without a gap over 100 m"),
                     overlay=lambda d: badge(d, f"{b7:.0f} ha", "largest network (honey)")))
    still_isl = img
    # D · highways with bees (3.4 s)
    for k in range(int(FPS * 3.4)):
        a = ease(k / (FPS * 0.8)); T += 1 / FPS
        img = draw_highways(draw_islands(t7.copy(), FULL, m, state0, alpha=0.75), FULL, "small_07", T, alpha=a)
        save(compose(img, Q, "July · small solitary bees", ("Bee highways", "where the model sends the most flower-to-flower trips")))
    compose(img, Q, "July · small solitary bees", ("Bee highways", "where the model sends the most flower-to-flower trips")).save(OUT / "still_highways.png")
    # E · tree pits, one by one (6 s)
    picks = IV["picks"]["treepits"]
    PX, PY = _t.transform(np.array([p["lon"] for p in picks]), np.array([p["lat"] for p in picks]))
    NE = int(FPS * 6.0)
    for k in range(NE):
        T += 1 / FPS
        nk = min(25, int(25 * ease(k / (FPS * 4.6))))
        st = islands_state(m, picks[:nk])
        img = draw_islands(t7.copy(), FULL, m, st, alpha=0.82)
        img = draw_corridors(img, FULL, "treepits", "small_07", list(zip(PX[:nk], PY[:nk])), alpha=min(1.0, nk / 12), t=T)
        val = st[1][st[2]]
        def ov(d, nk=nk, val=val):
            px, py = FULL.xy(PX[:nk], PY[:nk])
            for x, y in zip(px, py):
                icon(d, x, y, "treepits", 12)
            badge(d, f"{val:.0f} ha", f"largest network · {nk} tree pits", col=(79, 143, 90))
        save(compose(img, "What if 25 tree pits flower?", "July · a 30 m × 30 m flower bed at each", ("Islands join, new corridors grow (violet)", f"{b7:.0f} ha → {tp7:.0f} ha largest network"), overlay=ov))
    final = compose(img, "What if 25 tree pits flower?", "July · a 30 m × 30 m flower bed at each", ("Islands join, new corridors grow (violet)", f"{b7:.0f} ha → {tp7:.0f} ha largest network"), overlay=ov)
    final.save(OUT / "still_treepits.png"); last = img
    # F · outro (4.4 s)
    for k in range(int(FPS * 4.4)):
        a = ease(k / (FPS * 0.6))
        dim = Image.blend(last.convert("RGB"), Image.new("RGB", last.size, BG), 0.6 * a)
        def ov(d):
            if k < 3:
                return
            d.rounded_rectangle([40, MAP_Y + 60, W - 40, MAP_Y + 910], 28, fill=(255, 253, 248, 246))
            d.text((W // 2, MAP_Y + 100), "Largest flower network for small wild bees · July", font=F["sm"], fill=INK2, anchor="ma")
            d.text((W // 2, MAP_Y + 150), f"{b7:.0f} → {tp7:.0f} ha", font=F["big"], fill=(79, 143, 90), anchor="ma")
            d.text((W // 2, MAP_Y + 276), "with flower beds at 25 street-tree pits", font=F["sm"], fill=INK, anchor="ma")
            rows = [("treepits", "25 tree pits", c["treepits"][m]), ("parking", "25 car-park edges", c["parking"][m]), ("stops", "25 bus & tram stops", c["stops"][m]), ("schools", "25 school yards", c["schools"][m])]
            for j, (kk, nm, v_) in enumerate(rows):
                y = MAP_Y + 352 + j * 66
                icon(d, 110, y + 16, kk, 15)
                d.text((140, y), nm, font=F["sm"], fill=INK)
                d.rounded_rectangle([140, y + 38, 140 + int(640 * max(0.0, v_ - b7) / max(1, tp7 - b7)) + 4, y + 48], 5, fill=KCOL[kk])
                d.text((W - 70, y + 2), f"+{max(0, v_ - b7):.0f} ha", font=F["lab"], fill=KCOL[kk], anchor="ra")
            d.text((W // 2, MAP_Y + 640), f"{ST_['obs_pilot']:,} wild-bee records, {ST_['taxa_pilot']} taxa", font=F["sm"], fill=INK, anchor="ma")
            d.text((W // 2, MAP_Y + 678), "62% where the map shows few flowers: balconies, tree pits", font=F["sm"], fill=INK2, anchor="ma")
            d.text((W // 2, MAP_Y + 780), "Story mode & every layer in 3D: barisparlatangiller.github.io", font=F["lab"], fill=INK2, anchor="ma")
            d.text((W // 2, MAP_Y + 820), "A model of potential, not measured flight routes", font=F["lab"], fill=INK3, anchor="ma")
        save(compose(dim, "Bee highways: the missing links", "Berlin · Tempelhofer Feld to Neukölln", labels=0, overlay=ov))
    compose(dim, "Bee highways: the missing links", "Berlin · Tempelhofer Feld to Neukölln", labels=0, overlay=ov).save(OUT / "outro.png")
    compose(still_isl, Q, "July · small solitary bees", (f"{ST_['islands_n'][m]} separate flower islands", "one colour = one network without a gap over 100 m"),
            overlay=lambda d: badge(d, f"{b7:.0f} ha", "largest network (honey)")).save(OUT / "cover.png")
    out = OUT / "day20_berlin_bee_highways.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(fr / "f%04d.jpg"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-profile:v", "main", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    print(f"film: {n} frames, {n / FPS:.1f} s, {out.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        FPS = 3
    main()
