"""
Day 20 · Bee Highways · the network for the story and the explore mode.

1. Flower islands (small solitary bees): rich flower cells (forage ≥ 0.5) whose gap is ≤ 100 m form one network (model.py
   logic, per month April–September). Each 30 m hex takes the island it mostly lies on → docs/data/hexisl.bin
2. Interventions, four kinds, 25 best places each (greedy, equivalent connected area summed over April–September):
   bus & tram stops · tree pits (street trees) · school & kindergarten yards · car parks. Every pick stores, per month, the
   islands it touches, so the browser can merge islands live for any combination (union-find) → docs/data/interventions.json
3. Bee highways as lines: the strongest current corridors (model.py, before), skeletonised and traced to polylines with
   their strength, per guild and month → docs/data/highways.json; also short "bridges" from every pick to the islands it joins.
  python pipeline/network.py
"""
import json, math, time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize
from shapely.geometry import LineString
from pyproj import Transformer

B, W, I = Path("build"), Path("docs/data"), Path("input")
MONTHS = list(range(4, 10))
HOP, THR, R_ST, NPICK = 100.0, 0.5, 2, 25
TF = Transformer.from_crs(25833, 4326, always_xy=True)


def main():
    t0 = time.time()
    g = np.load(B / "grids.npz"); cur = np.load(B / "current.npz")
    X0, Y1, RES = float(g["X0"]), float(g["Y1"]), float(g["RES"]); NY, NX = g["resist"].shape
    water = g["water"] > 0
    kd = int(round(HOP / 2 / RES))
    HJ = json.loads((W / "hex.json").read_text())
    hx, hy = TF.transform(np.array(HJ["lon"]), np.array(HJ["lat"]), direction="INVERSE")
    nH = HJ["n"]
    yy, xx = np.mgrid[0:NY, 0:NX]
    _, hid = cKDTree(np.c_[hx, hy]).query(np.c_[(X0 + (xx + 0.5) * RES).ravel(), (Y1 - (yy + 0.5) * RES).ravel()])
    hid = hid.reshape(NY, NX)
    ncell = np.bincount(hid.ravel(), minlength=nH)
    # ---- islands per month
    LAB, AREA = {}, {}
    hexisl = np.zeros((nH, len(MONTHS)), np.int32)
    for k, m in enumerate(MONTHS):
        Hm = (g[f"f{m:02d}"] >= THR) & ~water
        lab, n = ndi.label(ndi.binary_dilation(Hm, iterations=kd), structure=np.ones((3, 3)))
        lab = np.where(Hm, lab, 0)
        LAB[m] = (lab, ndi.label(ndi.binary_dilation(Hm, iterations=kd), structure=np.ones((3, 3)))[0])
        AREA[m] = np.bincount(lab.ravel(), minlength=n + 1).astype(float) * RES * RES / 1e4
        # hex → island with most flower cells in it (if ≥ 15 % of the hex flowers)
        df = pd.DataFrame({"h": hid[Hm], "l": lab[Hm]})
        if len(df):
            top = df.groupby(["h", "l"]).size().reset_index(name="c").sort_values("c").drop_duplicates("h", keep="last")
            ok = top.c.values >= 0.15 * ncell[top.h.values]
            hexisl[top.h.values[ok], k] = top.l.values[ok]
    print(f"[{time.time() - t0:.0f} s] islands; hexes with an island (July): {(hexisl[:, 3] > 0).sum():,}", flush=True)
    # ---- intervention candidates (EPSG:25833 points)
    PIL = (389500, 5811000, 396500, 5817000)
    def inside(gs):
        return gs[(gs.x > PIL[0]) & (gs.x < PIL[2]) & (gs.y > PIL[1]) & (gs.y < PIL[3])]
    cand = {}
    st = gpd.read_parquet(B / "stops.parquet"); cand["stops"] = [(p.x, p.y, n) for p, n in zip(st.geometry, st.name)]
    tr = gpd.read_parquet(B / "trees.parquet"); tr = tr[tr.src == "street"]
    k40 = (tr.geometry.x // 40).astype(int).astype(str) + "_" + (tr.geometry.y // 40).astype(int).astype(str)
    tr = tr.loc[~k40.duplicated()]
    cand["treepits"] = [(p.x, p.y, (a or g_ or "")) for p, a, g_ in zip(tr.geometry, tr.art_dtsch, tr.genus)]
    ar = gpd.read_file(I / "osm_pilot.gpkg", layer="areas").to_crs(25833)
    sc_ = ar[ar.amenity.isin(["school", "kindergarten"])].copy(); sc_["rp"] = sc_.geometry.representative_point()
    cand["schools"] = [(p.x, p.y, (n if isinstance(n, str) else a)) for p, n, a in zip(sc_.rp, sc_.name, sc_.amenity)]
    pk = ar[(ar.amenity == "parking")].copy(); pk = pk[pk.geometry.area >= 300]; pk["rp"] = pk.geometry.representative_point()
    cand["parking"] = [(p.x, p.y, (n if isinstance(n, str) else "")) for p, n in zip(pk.rp, pk.name)]
    for kk in cand:
        cand[kk] = [c for c in cand[kk] if PIL[0] < c[0] < PIL[2] and PIL[1] < c[1] < PIL[3]]
    print({k: len(v) for k, v in cand.items()}, flush=True)
    # reach: islands within 100 m of a 30 m bed at the candidate, per month
    def reach(x, y):
        c_, r_ = int((x - X0) / RES), int((Y1 - y) / RES); out = {}
        for m in MONTHS:
            lab = LAB[m][0]; w = lab[max(0, r_ - R_ST - 2 * kd):r_ + R_ST + 2 * kd + 1, max(0, c_ - R_ST - 2 * kd):c_ + R_ST + 2 * kd + 1]
            out[m] = sorted(set(np.unique(w[w > 0]).tolist()))
        return out
    picks = {}
    for kind, cl in cand.items():
        R = [reach(x, y) for x, y, _ in cl]
        par = {m: np.arange(len(AREA[m])) for m in MONTHS}
        def find(m, i):
            p = par[m]
            while p[i] != i:
                p[i] = p[p[i]]; i = p[i]
            return i
        chosen = []
        for it in range(NPICK):
            tot = {}
            for m in MONTHS:
                roots = np.array([find(m, i) for i in range(len(AREA[m]))]); tot[m] = np.bincount(roots, weights=AREA[m], minlength=len(AREA[m]))
            best, bg = None, 0.0
            for j, rr in enumerate(R):
                if j in chosen or any(math.hypot(cl[j][0] - cl[q][0], cl[j][1] - cl[q][1]) < 200 for q in chosen):
                    continue
                gs = 0.0
                for m in MONTHS:
                    roots = {find(m, i) for i in rr[m]}
                    if len(roots) > 1:
                        a = [tot[m][r] for r in roots]; gs += sum(a) ** 2 - sum(v * v for v in a)
                if gs > bg:
                    best, bg = j, gs
            if best is None:
                break
            chosen.append(best)
            for m in MONTHS:
                roots = sorted({find(m, i) for i in R[best][m]})
                for r in roots[1:]:
                    par[m][r] = roots[0]
        picks[kind] = [{"rank": q + 1, "x": cl[j][0], "y": cl[j][1], "name": str(cl[j][2] or ""), "reach": {f"{m:02d}": R[j][m] for m in MONTHS}} for q, j in enumerate(chosen)]
        print(f"[{time.time() - t0:.0f} s] {kind}: {len(chosen)} picks", flush=True)
    # combined results (browser recomputes the same; stored for the text and the film)
    def merged(kinds, m):
        par = list(range(len(AREA[m])))
        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for kind in kinds:
            for p in picks[kind]:
                rr = sorted({find(i) for i in p["reach"][f"{m:02d}"]})
                for r in rr[1:]:
                    par[r] = rr[0]
        tot = {}
        for i in range(1, len(AREA[m])):
            tot[find(i)] = tot.get(find(i), 0) + AREA[m][i]
        return max(tot.values()) if tot else 0
    combos = {}
    for kinds in ([], ["stops"], ["treepits"], ["schools"], ["parking"], ["stops", "treepits", "schools", "parking"]):
        combos["+".join(kinds) or "none"] = {f"{m:02d}": round(merged(kinds, m), 1) for m in MONTHS}
    print(json.dumps(combos, indent=0), flush=True)
    # ---- bridges: from a pick to the nearest flower cell of each island it joins
    for kind in picks:
        for p in picks[kind]:
            c_, r_ = int((p["x"] - X0) / RES), int((Y1 - p["y"]) / RES); br = {}
            for m in MONTHS:
                lab = LAB[m][0]; r0, c0 = max(0, r_ - 2 * kd - R_ST), max(0, c_ - 2 * kd - R_ST)
                w = lab[r0:r_ + R_ST + 2 * kd + 1, c0:c_ + R_ST + 2 * kd + 1]; segs = []
                if len(p["reach"][f"{m:02d}"]) > 1:
                    for isl in p["reach"][f"{m:02d}"]:
                        rr, cc = np.nonzero(w == isl)
                        if len(rr):
                            d = (rr + r0 - r_) ** 2 + (cc + c0 - c_) ** 2; q = int(np.argmin(d))
                            lon, lat = TF.transform(X0 + (cc[q] + c0 + 0.5) * RES, Y1 - (rr[q] + r0 + 0.5) * RES)
                            segs.append([round(lon, 6), round(lat, 6)])
                br[f"{m:02d}"] = segs
            p["bridges"] = br
            p["lon"], p["lat"] = [round(v, 6) for v in TF.transform(p["x"], p["y"])]
            del p["x"], p["y"]
    island_area = {f"{m:02d}": np.round(AREA[m], 2).tolist() for m in MONTHS}
    hexisl.astype("<u2").tofile(W / "hexisl.bin")
    (W / "interventions.json").write_text(json.dumps({"months": [f"{m:02d}" for m in MONTHS], "picks": picks, "area": island_area, "combos": combos}, ensure_ascii=False, separators=(",", ":")))
    # ---- highways as lines (current, before), per scenario
    scen = list(cur["scen"]); C = cur["before"]
    hw = {}
    for k, name in enumerate(scen):
        c = ndi.gaussian_filter(C[..., k], 1.5)
        thr = np.percentile(c[~water], 92)
        mask = ndi.binary_opening(c >= thr, iterations=1)
        sk = skeletonize(mask)
        # trace: break at junctions, follow chains
        nb = ndi.convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
        node = sk & (nb != 2)
        seen = np.zeros_like(sk); lines = []
        pts = set(zip(*np.nonzero(sk)))
        def nbrs(p):
            r, cc = p
            return [(r + dr, cc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and (r + dr, cc + dc) in pts]
        starts = [tuple(p) for p in zip(*np.nonzero(node))] + [p for p in pts]
        used_edges = set()
        for s in starts:
            for n1 in nbrs(s):
                e = (min(s, n1), max(s, n1))
                if e in used_edges:
                    continue
                path = [s, n1]; used_edges.add(e); prev, curp = s, n1
                while not node[curp] and len(path) < 4000:
                    nx_ = [q for q in nbrs(curp) if q != prev and (min(curp, q), max(curp, q)) not in used_edges]
                    if not nx_:
                        break
                    q = nx_[0]; used_edges.add((min(curp, q), max(curp, q))); prev, curp = curp, q; path.append(curp)
                if len(path) >= 6:
                    lines.append(path)
        out = []
        for path in lines:
            rr = np.array([p[0] for p in path]); cc = np.array([p[1] for p in path])
            xs, ys = X0 + (cc + 0.5) * RES, Y1 - (rr + 0.5) * RES
            ls = LineString(np.c_[xs, ys]).simplify(8)
            if ls.length < 80:
                continue
            s_ = float(np.mean(c[rr, cc]) / np.percentile(c[~water], 99.5))
            lon, lat = TF.transform(*np.array(ls.coords).T)
            out.append({"s": round(min(1.0, s_), 3), "p": np.round(np.c_[lon, lat], 6).tolist(), "len": round(ls.length)})
        hw[name] = out
    (W / "highways.json").write_text(json.dumps(hw, separators=(",", ":")))
    print(f"highways: {{k: len(v) for k, v in hw.items()}}"[:0], {k: len(v) for k, v in hw.items()})
    ST = json.loads((W / "stats.json").read_text()); ST["combos"] = combos
    ST["islands_n"] = {f"{m:02d}": int((AREA[m] > 0).sum() - 1) for m in MONTHS}
    (W / "stats.json").write_text(json.dumps(ST, ensure_ascii=False, indent=1))
    for f in ("hexisl.bin", "interventions.json", "highways.json"):
        print(f, f"{(W / f).stat().st_size / 1e6:.2f} MB")
    print(f"done {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
