"""
Day 20 · Bee Highways · corridors that react to the additions.

For every combination of the four kinds of additions (16, incl. none), the circuit model (model.py) is solved again with the
25 flower beds of each switched-on kind: their cells get meadow-like resistance and flowers (April–September), and they
become flower sources themselves (extra pairs from every bed to flower-rich cells within 1 km). The current is traced to
lines with a threshold fixed by the "none" case, so new corridors appear where the beds connect into the network; lines
that were not a highway before are flagged as new.
  python pipeline/corridors.py
Output docs/data/corridors.json {combo: {scenario: [{s, p, len, n}]}}   (combo = "stops+treepits" …, "none")
"""
import itertools, json, math, sys, time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
from shapely.geometry import LineString
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).parent))
from model import edges, factor, solve_pairs, GUILDS          # noqa: E402

B, W = Path("build"), Path("docs/data")
MONTHS = list(range(3, 10))
KINDS = ["stops", "treepits", "schools", "parking"]
NBASE, NBED = 1500, 14
TF = Transformer.from_crs(25833, 4326, always_xy=True)
rng = np.random.default_rng(2021)


def trace(c, thr, ref99, water, X0, Y1, RES, before=None, bthr=None):
    mask = ndi.binary_opening(c >= thr, iterations=1)
    sk = skeletonize(mask)
    nb = ndi.convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
    node = sk & (nb != 2)
    pts = set(zip(*np.nonzero(sk)))
    def nbrs(p):
        r, cc = p
        return [(r + dr, cc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and (r + dr, cc + dc) in pts]
    used, lines = set(), []
    for s in [tuple(p) for p in zip(*np.nonzero(node))] + list(pts):
        for n1 in nbrs(s):
            e = (min(s, n1), max(s, n1))
            if e in used:
                continue
            path = [s, n1]; used.add(e); prev, cur = s, n1
            while not node[cur] and len(path) < 4000:
                nx_ = [q for q in nbrs(cur) if q != prev and (min(cur, q), max(cur, q)) not in used]
                if not nx_:
                    break
                q = nx_[0]; used.add((min(cur, q), max(cur, q))); prev, cur = cur, q; path.append(cur)
            if len(path) >= 6:
                lines.append(path)
    out = []
    for path in lines:
        rr = np.array([p[0] for p in path]); cc = np.array([p[1] for p in path])
        ls = LineString(np.c_[X0 + (cc + 0.5) * RES, Y1 - (rr + 0.5) * RES]).simplify(8)
        if ls.length < 80:
            continue
        new = int(before is not None and np.mean(before[rr, cc] < bthr) > 0.5)
        lon, lat = TF.transform(*np.array(ls.coords).T)
        out.append({"s": round(float(min(1.0, np.mean(c[rr, cc]) / ref99)), 3), "p": np.round(np.c_[lon, lat], 6).tolist(), "len": round(ls.length), "n": new})
    return out


def main():
    t0 = time.time()
    g = np.load(B / "grids.npz")
    NY, NX = g["resist"].shape; N = NY * NX; RES = float(g["RES"]); X0, Y1 = float(g["X0"]), float(g["Y1"])
    F = {m: g[f"f{m:02d}"] for m in MONTHS}
    water = g["water"] > 0
    H = (np.max(np.stack(list(F.values())), 0) >= 0.35) & ~water
    hr, hc = np.nonzero(H)
    IV = json.loads((W / "interventions.json").read_text())
    beds = {}
    for k in KINDS:
        x, y = TF.transform(np.array([p["lon"] for p in IV["picks"][k]]), np.array([p["lat"] for p in IV["picks"][k]]), direction="INVERSE")
        beds[k] = list(zip(((Y1 - y) / RES).astype(int).clip(0, NY - 1), ((x - X0) / RES).astype(int).clip(0, NX - 1)))
    # base pairs: as in model.py (uniform s, t within 600 m or 2 km), importance weights per scenario
    S, T = [], []
    while len(S) < NBASE:
        k = rng.integers(0, len(hr)); rad = 600 if rng.random() < 0.5 else 2000
        for _ in range(60):
            j = rng.integers(0, len(hr))
            if j != k and abs(hr[j] - hr[k]) * RES <= rad and abs(hc[j] - hc[k]) * RES <= rad:
                S.append(k); T.append(j); break
    S, T = np.array(S), np.array(T)
    scen = [(gn, m) for gn in GUILDS for m in MONTHS]
    def weights(sr, sc, tr, tc, Fm, q):
        d = np.hypot(sr - tr, sc - tc) * RES
        Wt = np.zeros((len(sr), len(scen)))
        for k_, (gn, m) in enumerate(scen):
            Wt[:, k_] = np.clip(Fm[m][sr, sc], 0, 1) * np.clip(Fm[m][tr, tc], 0, 1) * np.exp(-d / GUILDS[gn]) / q
        return Wt
    sr, sc, tr, tc = hr[S], hc[S], hr[T], hc[T]
    q0 = np.full(len(S), 1.0 / len(S))
    Wb = weights(sr, sc, tr, tc, F, q0); norm = Wb.sum(0, keepdims=True)
    I, J, Wd = edges(NY, NX)
    yy, xx = np.mgrid[-2:3, -2:3]
    res, ref = {}, {}
    combos = [c for n in range(0, 5) for c in itertools.combinations(KINDS, n)]
    for combo in combos:
        name = "+".join(combo) or "none"
        r1 = g["resist"].copy(); F1 = {m: F[m].copy() for m in MONTHS}
        bs = [b for k in combo for b in beds[k]]
        for r_, c_ in bs:
            rr, cc = np.clip(r_ + yy, 0, NY - 1), np.clip(c_ + xx, 0, NX - 1)
            r1[rr, cc] = np.minimum(r1[rr, cc], 1.8)
            for m in MONTHS:
                if m >= 4:
                    F1[m][rr, cc] = np.maximum(F1[m][rr, cc], 0.8)
        # pairs: base + from every bed to flower-rich cells within 1 km
        es, et = [], []
        for r_, c_ in bs:
            near = np.nonzero((np.abs(hr - r_) * RES <= 1000) & (np.abs(hc - c_) * RES <= 1000))[0]
            for j in rng.choice(near, min(NBED, len(near)), replace=False):
                es.append((r_, c_)); et.append(j)
        Wt = weights(sr, sc, tr, tc, F1, q0)
        S_idx, T_idx = sr * NX + sc, tr * NX + tc
        if es:
            er = np.array([e[0] for e in es]); ec = np.array([e[1] for e in es]); etr, etc_ = hr[np.array(et)], hc[np.array(et)]
            We = weights(er, ec, etr, etc_, F1, np.full(len(es), 1.0 / len(S)))
            Wt = np.vstack([Wt, We]); S_idx = np.r_[S_idx, er * NX + ec]; T_idx = np.r_[T_idx, etr * NX + etc_]
        Wt = Wt / norm                                                   # same scale as "none"
        lu, c = factor(r1, I, J, Wd)
        cur, _ = solve_pairs(lu, c, I, J, N, S_idx, T_idx, Wt); del lu
        C = cur.reshape(NY, NX, -1)
        out = {}
        for k_, (gn, m) in enumerate(scen):
            key = f"{gn}_{m:02d}"; cs = ndi.gaussian_filter(C[..., k_], 1.5)
            if name == "none":
                ref[key] = (np.percentile(cs[~water], 92), np.percentile(cs[~water], 99.5), cs)
            thr, r99, c0 = ref[key]
            out[key] = trace(cs, thr, r99, water, X0, Y1, RES, before=None if name == "none" else c0, bthr=thr)
        res[name] = out
        print(f"[{time.time() - t0:.0f} s] {name}: {sum(len(v) for v in out.values())} lines, new in small_07: {sum(l['n'] for l in out['small_07'])}", flush=True)
        (W / "corridors.json").write_text(json.dumps(res, separators=(",", ":")))
    print(f"done {time.time() - t0:.0f} s, {(W / 'corridors.json').stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
