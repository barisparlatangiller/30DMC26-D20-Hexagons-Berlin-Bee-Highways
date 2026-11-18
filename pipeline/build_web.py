"""
Web layers for Day 20 (MapLibre). Coordinates in WGS84.

  docs/data/biotopes.json   pilot biotopes (forage, nest, rule, name)       docs/data/buildings.json  OSM buildings (h)
  docs/data/trees.bin       float32 × 6: lon, lat, crown, height, value, bloom mask (bit m-1) · trees_meta.json genus list
  docs/data/hex.json        hex centres (lon, lat), obs count, taxa, forage, nest
  docs/data/hexv.bin        uint8: hex × 28 (before small 3–9, before bumble 3–9, after small, after bumble), current percentile
  docs/data/stops.json      candidate stops + chosen 25 · docs/data/obs.json wild-bee observations (pilot) · stats.json
"""
import json, math
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

B, W = Path("build"), Path("docs/data")
HEX = 30.0                                        # hex edge (m), flat-top


def months_mask(s):
    if not isinstance(s, str) or not s:
        return 0
    a, *b = [int(x) for x in s.split("-")]
    m = 0
    for k in range(a, (b[0] if b else a) + 1):
        m |= 1 << (k - 1)
    return m


def wgs(gdf, prec=6):
    g = gdf.to_crs(4326)
    g["geometry"] = g.geometry.set_precision(10 ** -prec)
    return g


def main():
    W.mkdir(parents=True, exist_ok=True)
    g = np.load(B / "grids.npz"); cur = np.load(B / "current.npz")
    X0, Y1, RES = float(g["X0"]), float(g["Y1"]), float(g["RES"])
    NY, NX = g["resist"].shape
    ms = json.load(open(B / "model_stats.json")); meta = json.load(open(B / "meta.json"))
    # ---- hex grid (flat-top), centres inside the pilot
    w, h = 1.5 * HEX, math.sqrt(3) * HEX
    cs = []
    for i in range(int((NX * RES) / w) + 2):
        for j in range(int((NY * RES) / h) + 2):
            x = X0 + i * w; y = Y1 - NY * RES + j * h + (h / 2 if i % 2 else 0)
            if X0 + HEX * 0.5 < x < X0 + NX * RES - HEX * 0.5 and Y1 - NY * RES + HEX * 0.5 < y < Y1 - HEX * 0.5:
                cs.append((x, y))
    cs = np.array(cs)
    # cells → hex (nearest centre via axial rounding)
    yy, xx = np.mgrid[0:NY, 0:NX]
    px, py = X0 + (xx + 0.5) * RES, Y1 - (yy + 0.5) * RES
    from scipy.spatial import cKDTree
    kd = cKDTree(cs)
    _, hid = kd.query(np.c_[px.ravel(), py.ravel()])
    nH = len(cs)
    cnt = np.bincount(hid, minlength=nH).astype(float)
    def hmean(a):
        return np.bincount(hid, weights=a.ravel(), minlength=nH) / np.maximum(cnt, 1)
    vals = []
    for key in ("before", "after"):
        C = cur[key]
        for k in range(C.shape[-1]):
            vals.append(hmean(C[..., k]))
    V = np.stack(vals, 1)                                                 # hex × 28 (before 14, after 14)
    # percentiles relative to BEFORE of the same scenario, so AFTER can grow past it
    P = np.zeros_like(V)
    for k in range(14):
        ref = np.sort(V[:, k])
        P[:, k] = np.searchsorted(ref, V[:, k]) / len(ref)
        P[:, 14 + k] = np.searchsorted(ref, V[:, 14 + k]) / len(ref)
    np.clip(np.round(P * 255), 0, 255).astype("uint8").tofile(W / "hexv.bin")
    fmax = np.max(np.stack([g[f"f{m:02d}"] for m in range(3, 10)]), 0)
    forage_h = hmean(np.clip(fmax, 0, 1)); nest_h = hmean(g["nest"]); pinch_h = hmean(cur["pinch"])
    # observations per hex (within 120 m), taxa
    obs = gpd.read_parquet(B / "obs.parquet")
    ox, oy = obs.geometry.x.values, obs.geometry.y.values
    kdo = cKDTree(np.c_[ox, oy])
    near = kdo.query_ball_point(cs, 120)
    ocnt = np.array([len(n) for n in near]); otax = [sorted(set(obs.taxon.values[n])) for n in near]
    # flower networks for small bees (from model.py): which hexes belong to the largest network before / after the 25 stops
    isl = np.load(B / "islands.npz"); stp = gpd.read_parquet(B / "stops_ranked.parquet"); ch = stp[stp["rank"] > 0]
    kd_ = int(round(ms["hop_m"] / 2 / RES)); R_ST = 2
    big0, big1 = {}, {}
    for key in isl.files:
        lab = isl[key]; n = lab.max()
        Hm = (g["f" + key[1:]] >= ms["patch_forage_min"]) & (g["water"] == 0)
        area = np.bincount(lab[Hm], minlength=n + 1).astype(float)
        par = list(range(n + 1))
        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for _, r_ in ch.iterrows():
            c_ = int((r_.geometry.x - X0) / RES); rr = int((Y1 - r_.geometry.y) / RES)
            w_ = lab[max(0, rr - R_ST - 2 * kd_):rr + R_ST + 2 * kd_ + 1, max(0, c_ - R_ST - 2 * kd_):c_ + R_ST + 2 * kd_ + 1]
            roots = sorted({find(int(i)) for i in np.unique(w_[w_ > 0])})
            for r2 in roots[1:]:
                par[r2] = roots[0]
        tot = {}
        for i in range(1, n + 1):
            tot[find(i)] = tot.get(find(i), 0) + area[i]
        lb = int(np.argmax(area[1:]) + 1) if n else 0
        la = max(tot, key=tot.get) if tot else 0
        root = np.array([find(i) for i in range(n + 1)])
        in0 = (lab == lb) & Hm; in1 = (root[lab] == la) & (lab > 0) & Hm
        big0[key[1:]] = (hmean(in0) > 0.05).astype(int).tolist(); big1[key[1:]] = (hmean(in1) > 0.05).astype(int).tolist()
    ll = gpd.GeoSeries([Point(x, y) for x, y in cs], crs=25833).to_crs(4326)
    hexj = {"edge": HEX, "n": nH, "lon": np.round(ll.x.values, 6).tolist(), "lat": np.round(ll.y.values, 6).tolist(),
            "obs": ocnt.tolist(), "taxa": [len(t) for t in otax], "forage": np.round(forage_h, 2).tolist(), "nest": np.round(nest_h, 2).tolist(),
            "gap": np.round(pinch_h / max(np.percentile(pinch_h, 99.5), 1e-9), 2).clip(0, 1).tolist(),
            "scen": cur["scen"].tolist(), "top_taxa": [t[:6] for t in otax], "big0": big0, "big1": big1}
    (W / "hex.json").write_text(json.dumps(hexj, ensure_ascii=False, separators=(",", ":")))
    # ---- biotopes, buildings
    bt = gpd.read_parquet(B / "biotopes.parquet")
    bt = bt[~bt.geometry.is_empty]
    bt["geometry"] = bt.geometry.simplify(0.6)
    CAT = {"dry grassland / heath": "meadow", "ruderal / tall herbs": "meadow", "meadow": "meadow", "railway land": "meadow", "construction land (often ruderal)": "meadow",
           "part-sealed with joint vegetation": "meadow", "meadow / dry grassland (pre-class.)": "meadow", "herb-rich (pre-class.)": "meadow", "intensive grassland": "lawn", "mown lawn": "lawn",
           "mown (pre-class.)": "lawn", "allotments": "garden", "gardens": "garden", "houses with gardens": "garden", "small houses with gardens": "garden", "garden (pre-class.)": "garden",
           "orchard": "garden", "park": "park", "cemetery": "park", "shrubs / hedges": "park", "woodland": "park", "pine forest": "park", "black-locust stand": "park",
           "trees / shrubs (pre-class.)": "park", "blocks with green courtyards": "yard", "slab / tower blocks with green": "yard"}
    bt["cat"] = bt.rule.map(CAT)
    bt["cat"] = bt.cat.where(bt.cat.notna(), np.where(bt.rule.str.startswith("water"), "water", "built"))
    wgs(bt)[["bt_name", "forage", "nest", "rule", "cat", "geometry"]].to_file(W / "biotopes.json", driver="GeoJSON")
    bl = gpd.read_parquet(B / "buildings.parquet"); bl["geometry"] = bl.geometry.simplify(0.4)
    b2 = wgs(bl)[["h", "geometry"]]; b2["h"] = b2.h.round(1)
    b2.to_file(W / "buildings.json", driver="GeoJSON")
    # ---- trees
    tr = gpd.read_parquet(B / "trees.parquet"); tl = tr.to_crs(4326)
    gen = sorted(tr.genus.fillna("").unique())
    arr = np.c_[tl.geometry.x, tl.geometry.y, tr.crown, tr.height, tr.value, tr.bloom.map(months_mask), tr.genus.map({k: i for i, k in enumerate(gen)})].astype("float64")
    arr[:, :2] = arr[:, :2]
    np.c_[arr[:, 0].astype("float32"), arr[:, 1].astype("float32"), arr[:, 2:].astype("float32")].astype("float32").tofile(W / "trees.bin")
    gv = pd.read_csv("data/tree_genus_bee.csv").set_index("genus")
    de = tr.groupby("genus").art_dtsch.agg(lambda s: s.mode().iat[0] if len(s.mode()) else "").to_dict()
    (W / "trees_meta.json").write_text(json.dumps({"genus": gen, "de": [de.get(k, "") for k in gen]}, ensure_ascii=False))
    # ---- stops, observations
    st = gpd.read_parquet(B / "stops_ranked.parquet").to_crs(4326)
    (W / "stops.json").write_text(json.dumps([{"n": r.name, "lon": round(r.geometry.x, 6), "lat": round(r.geometry.y, 6), "rank": int(r["rank"])} for _, r in st.iterrows()], ensure_ascii=False))
    ob = obs.to_crs(4326)
    show = ~ob.license.str.contains("all rights", case=False, na=True)
    oc = ((obs.geometry.x - X0) / RES).astype(int).clip(0, NX - 1).values; orr = ((Y1 - obs.geometry.y) / RES).astype(int).clip(0, NY - 1).values
    hidden = fmax[orr, oc] < 0.35                                          # bee seen where the biotope map shows few flowers
    (W / "obs.json").write_text(json.dumps([{"t": r.taxon, "d": str(r.date)[:10], "s": r.src, "lon": round(r.geometry.x, 6), "lat": round(r.geometry.y, 6), "u": r.url if s else "", "h": int(hd)}
                                           for (_, r), s, hd in zip(ob.iterrows(), show, hidden)], ensure_ascii=False, separators=(",", ":")))
    # ---- stats
    sc = list(cur["scen"])
    top_hex_obs = int((ocnt > 0).sum())
    hi = P[:, :14].mean(1) >= 0.8
    stats = {**meta, **{k: v for k, v in ms.items() if k != "stops"}, "hex": nH, "hex_with_obs": top_hex_obs,
             "hex_obs_in_highways": float((ocnt[hi] > 0).mean()), "hex_obs_elsewhere": float((ocnt[~hi] > 0).mean()),
             "bbox": list(gpd.GeoSeries([Point(X0, Y1 - NY * RES), Point(X0 + NX * RES, Y1)], crs=25833).to_crs(4326).apply(lambda p: [round(p.x, 5), round(p.y, 5)]))}
    (W / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))
    print(json.dumps({k: stats[k] for k in ("hex", "hex_with_obs", "hex_obs_in_highways", "hex_obs_elsewhere")}, indent=1))
    for f in sorted(W.iterdir()):
        print(f.name, f"{f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
