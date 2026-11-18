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
    def fcol(f):
        stops = [(0, (232, 228, 220)), (0.15, (228, 226, 210)), (0.35, (216, 224, 187)), (0.6, (188, 211, 154)), (0.85, (147, 187, 114)), (1, (122, 166, 93))]
        for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
            if f <= b:
                t = (f - a) / (b - a); return tuple(int(c + (e - c) * t) for c, e in zip(ca, cb))
        return stops[-1][1]
    for g, f in zip(bt.geometry, bt.forage):
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


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True); fr = OUT / "frames"; fr.mkdir(exist_ok=True)
    for f in fr.glob("*.jpg"):
        f.unlink()
    g0 = ground_canvas(7)
    T = {m: trees_layer(g0, m) for m in range(3, 10)}
    print(f"[{time.time() - t0:.0f} s] canvases", flush=True)
    stops = json.loads((D / "stops.json").read_text()); ch = [s for s in stops if s["rank"] > 0]
    SX_, SY_ = _t.transform(np.array([s["lon"] for s in ch]), np.array([s["lat"] for s in ch]))
    I = ST["islands"]
    col = lambda g, m, a: (0 if g == "small" else 7) + (m - 3) + (14 if a else 0)
    LBL = [("TEMPELHOFER FELD", 13.401, 52.4735), ("HASENHEIDE", 13.4175, 52.4845), ("NEUKÖLLN", 13.44, 52.479), ("BRITZ", 13.437, 52.448), ("KREUZBERG", 13.395, 52.493), ("TEMPELHOF", 13.388, 52.458)]
    LX, LY = _t.transform(np.array([l[1] for l in LBL]), np.array([l[2] for l in LBL]))

    def compose(mapimg, title, sub, cap=None, v=FULL, labels=1.0, overlay=None):
        im = Image.new("RGB", (W, H), BG); im.paste(mapimg.convert("RGB"), (0, 0)) if mapimg.size == (W, H) else im.paste(mapimg.convert("RGB"), (0, MAP_Y))
        d = ImageDraw.Draw(im, "RGBA")
        if labels > 0:
            px, py = v.xy(LX, LY)
            for (n, *_), x, y in zip(LBL, px, py):
                if 60 < x < W - 60 and MAP_Y + 30 < y < MAP_Y + MAP_H - 30:
                    d.text((x, y), n, font=F["lab"], fill=(70, 66, 58, int(220 * labels)), anchor="mm", stroke_width=4, stroke_fill=(255, 253, 248, int(220 * labels)))
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

    def badge(d, x, y, txt, sub):
        d.rounded_rectangle([x, y, x + 300, y + 110], 20, fill=(255, 253, 248, 230))
        d.text((x + 20, y + 14), txt, font=F["mid"], fill=VIOLET); d.text((x + 20, y + 62), sub, font=F["lab"], fill=INK2)

    Q = "Where are Berlin's bee highways?"
    base = crop(g0, FULL)
    # A · ground (2.4 s)
    for k in range(int(FPS * 2.4)):
        a = ease(k / (FPS * 1.2))
        img = Image.blend(Image.new("RGB", base.size, BG), base, a)
        save(compose(img, Q, "Tempelhofer Feld · Hasenheide · Neukölln", ("Green = flowers for bees", "Berlin biotope map 2024, every patch scored"), labels=a))
    # B · trees (2.6 s)
    t7 = crop(T[7], FULL)
    for k in range(int(FPS * 2.6)):
        a = ease(k / (FPS * 1.4))
        save(compose(Image.blend(base, t7, a), Q, "Tempelhofer Feld · Hasenheide · Neukölln", (f"{ST['trees']:,} trees, one by one", "honey = in flower in July and good for bees (lime)")))
    # C · honeycomb rises (3.6 s), July, small bees, today
    vals7 = HV[:, col("small", 7, False)]
    for k in range(int(FPS * 3.6)):
        a = ease(k / (FPS * 2.2))
        img = draw_hexes(t7, FULL, vals7 * a, lift=a, alpha=0.66 * a)
        save(compose(img, Q, "July · small solitary bees", ("A honeycomb of bee links", "bigger and darker cell = stronger link for bees")))
    still = compose(draw_hexes(t7, FULL, vals7, gaps=1.0), Q, "July · small solitary bees", ("A honeycomb of bee links", "bigger and darker cell = stronger link for bees"))
    still.save(OUT / "still_honeycomb.png")
    # D · months March → September (6.4 s)
    ND = int(FPS * 6.4)
    for k in range(ND):
        mf = 3 + 6 * k / (ND - 1); m0 = int(math.floor(mf)); f = mf - m0; m1 = min(9, m0 + 1)
        vals = HV[:, col("small", m0, False)] * (1 - f) + HV[:, col("small", m1, False)] * f
        tm = crop(T[m0 if f < 0.5 else m1], FULL)
        mm = m0 if f < 0.5 else m1
        isl = I.get(f"{mm:02d}")
        def ov(d, isl=isl, mm=mm):
            d.rounded_rectangle([W - 330, MAP_Y + 24, W - 24, MAP_Y + 150], 20, fill=(255, 253, 248, 232))
            d.text((W - 306, MAP_Y + 36), MON[mm], font=F["mid"], fill=INK)
            d.text((W - 306, MAP_Y + 86), f"largest network {isl['largest_before']:.0f} ha" if isl else "almost nothing flowers yet", font=F["lab"], fill=HONEY_ACC)
            # month bar
            for i, m in enumerate(range(3, 10)):
                x = W - 306 + i * 40; d.rounded_rectangle([x, MAP_Y + 124, x + 34, MAP_Y + 132], 3, fill=HONEY_ACC if m <= mm else (226, 220, 208))
        save(compose(draw_hexes(tm, FULL, vals), Q, "March to September · small solitary bees", ("The network grows with the flowers", "willow in March, maple in April, lime in July"), overlay=ov))
    # E · bee stops (4.8 s): zoom to the gaps, stops appear, cells grow
    gx = HX[JOINED7].mean(); gy = HY[JOINED7].mean()
    zs = 4600; zh = zs * MAP_H / W; fh = FULL.span * MAP_H / W
    zx = min(max(0.5 * gx + 0.5 * SX_.mean(), FULL.x0 + zs / 2 + 1), FULL.x0 + FULL.span - zs / 2 - 1)
    zy = min(max(0.5 * gy + 0.5 * SY_.mean(), FULL.y1 - fh + zh / 2 + 1), FULL.y1 - zh / 2 - 1)
    ZV = View(zx, zy, zs)
    big7 = T[7]
    NE = int(FPS * 4.8); i7 = I["07"]
    for k in range(NE):
        u = ease(k / (FPS * 1.6)); v = FULL.lerp(ZV, u)
        a = ease((k - FPS * 1.6) / (FPS * 1.8))
        vals = HV[:, col("small", 7, False)] * (1 - a) + HV[:, col("small", 7, True)] * a
        img = draw_hexes(crop(big7, v), v, vals, gaps=1.0 - a * 0.6, joined=max(0.0, a))
        def ov(d, v=v, a=a, k=k):
            px, py = v.xy(SX_, SY_)
            for j, (x, y) in enumerate(zip(px, py)):
                if k > FPS * 1.4 and MAP_Y < y < MAP_Y + MAP_H:
                    r = 9 + 3 * min(1, (k - FPS * 1.4) / 6)
                    d.ellipse([x - r, y - r, x + r, y + r], fill=VIOLET + (230,), outline=(255, 255, 255, 255), width=2)
                    d.text((x, y), str(ch[j]["rank"]), font=F["lab"], fill=(255, 255, 255), anchor="mm")
            la = i7["largest_before"] + (i7["largest_after"] - i7["largest_before"]) * max(0, a)
            badge(d, W - 340, MAP_Y + 24, f"{la:.0f} ha", "largest flower network")
        save(compose(img, Q, "July · + 25 bee stops", ("25 flowering bus and tram stops", "violet: newly joined to the largest flower network"), v=v, labels=1 - u * 0.5, overlay=ov))
    final = img
    compose(final, Q, "July · + 25 bee stops", ("25 flowering bus and tram stops", "violet: newly joined to the largest flower network"), v=ZV, labels=0.5, overlay=ov).save(OUT / "still_stops.png")
    # F · outro (4.2 s)
    for k in range(int(FPS * 4.2)):
        a = ease(k / (FPS * 0.6))
        dim = Image.blend(final.convert("RGB"), Image.new("RGB", final.size, BG), 0.55 * a)
        def ov(d):
            if k < 3:
                return
            d.rounded_rectangle([40, MAP_Y + 70, W - 40, MAP_Y + 900], 28, fill=(255, 253, 248, 245))
            d.text((W // 2, MAP_Y + 112), "Berlin · Tempelhofer Feld to Neukölln · July", font=F["sm"], fill=INK2, anchor="ma")
            d.text((W // 2, MAP_Y + 168), f"{i7['largest_before']:.0f} → {i7['largest_after']:.0f} ha", font=F["big"], fill=VIOLET, anchor="ma")
            d.text((W // 2, MAP_Y + 296), "largest flower network a small wild bee can use,", font=F["sm"], fill=INK, anchor="ma")
            d.text((W // 2, MAP_Y + 332), "with 25 flowering bus and tram stops", font=F["sm"], fill=INK, anchor="ma")
            d.text((W // 2, MAP_Y + 420), f"{ST['obs_pilot']:,}", font=F["num"], fill=HONEY_ACC, anchor="ma")
            d.text((W // 2, MAP_Y + 502), f"wild-bee records, {ST['taxa_pilot']} taxa, compared with the model", font=F["sm"], fill=INK, anchor="ma")
            d.text((W // 2, MAP_Y + 580), f"{ST['trees']:,}", font=F["num"], fill=(104, 142, 92), anchor="ma")
            d.text((W // 2, MAP_Y + 662), "trees mapped one by one, each with its flowering months", font=F["sm"], fill=INK, anchor="ma")
            d.text((W // 2, MAP_Y + 770), "Explore every month in 3D: barisparlatangiller.github.io", font=F["lab"], fill=INK2, anchor="ma")
            d.text((W // 2, MAP_Y + 812), "A model of potential, not measured flight routes", font=F["lab"], fill=INK3, anchor="ma")
        save(compose(dim, "Bee highways: the missing links", "a honeycomb of bee links over Berlin", v=ZV, labels=0, overlay=ov))
    compose(dim, "Bee highways: the missing links", "a honeycomb of bee links over Berlin", v=ZV, labels=0, overlay=ov).save(OUT / "outro.png")
    still.save(OUT / "cover.png")
    out = OUT / "day20_berlin_bee_highways.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(fr / "f%04d.jpg"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-profile:v", "main", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    print(f"film: {n} frames, {n / FPS:.1f} s, {out.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        FPS = 3
    main()
