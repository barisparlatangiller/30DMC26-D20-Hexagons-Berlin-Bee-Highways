"""
Day 20 · Bee Highways · connectivity as electric current (circuit theory, as in Circuitscape; McRae et al. 2008).

The pilot (7 × 6 km) is a 10 m grid of resistors: sealed ground, tall buildings and cells without flowers resist a flying bee
(build/grids.npz → resist). Pairs of flower-rich cells are connected one at a time (+1 A in, −1 A out), and the current
through every cell is summed: where many bee trips have to squeeze through, the current is high (a "highway"), where
two flower patches have no good way between them, it is low (a "missing link").
One factorisation of the grid (scipy splu), then thousands of pairs as right-hand sides. Every pair is reweighted for
  · two bee guilds: small solitary bees (typical foraging range 300 m) and bumblebees (1 km);
  · seven months (March–September): a pair counts as much as both ends are in flower that month.
Then "bee stops": 25 flowering stops at bus and tram stops where many bee paths cross poor ground; the grid is solved
again with them (BEFORE / AFTER).
  python pipeline/model.py
Output build/current.npz, build/stops_ranked.parquet, build/model_stats.json
"""
import json, math, time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import scipy.sparse as sp
import scipy.sparse.linalg as sla
from scipy import ndimage as ndi

B = Path("build")
MONTHS = list(range(3, 10))
GUILDS = {"small": 300.0, "bumble": 1000.0}
NPAIRS = 3600
BATCH = 40
rng = np.random.default_rng(2020)


def edges(NY, NX):
    idx = np.arange(NY * NX).reshape(NY, NX)
    E = []
    for a, b, w in ((idx[:, :-1], idx[:, 1:], 1.0), (idx[:-1, :], idx[1:, :], 1.0),
                    (idx[:-1, :-1], idx[1:, 1:], 1 / math.sqrt(2)), (idx[:-1, 1:], idx[1:, :-1], 1 / math.sqrt(2))):
        E.append((a.ravel(), b.ravel(), np.full(a.size, w)))
    i = np.concatenate([e[0] for e in E]); j = np.concatenate([e[1] for e in E]); w = np.concatenate([e[2] for e in E])
    return i, j, w


def factor(r, I, J, Wd):
    N = r.size
    c = Wd * 2 / (r.ravel()[I] + r.ravel()[J])
    A = sp.csr_matrix((np.r_[c, c], (np.r_[I, J], np.r_[J, I])), shape=(N, N))
    L = (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsc()[1:, 1:]          # node 0 grounded
    return sla.splu(L, permc_spec="COLAMD"), c


def solve_pairs(lu, c, I, J, N, S, T, Wt):
    """current density per cell summed over pairs, weighted per scenario (Wt: pairs × scenarios); also effective resistance"""
    E = len(I)
    inc = sp.csr_matrix((np.full(2 * E, 0.5), (np.r_[I, J], np.r_[np.arange(E), np.arange(E)])), shape=(N, E))
    acc = np.zeros((N, Wt.shape[1]), "float32"); reff = np.zeros(len(S))
    for k0 in range(0, len(S), BATCH):
        s, t = S[k0:k0 + BATCH], T[k0:k0 + BATCH]; k = len(s)
        b = np.zeros((N, k)); b[s, np.arange(k)] = 1; b[t, np.arange(k)] = -1
        v = np.zeros((N, k)); v[1:] = lu.solve(b[1:])
        reff[k0:k0 + k] = v[s, np.arange(k)] - v[t, np.arange(k)]
        ie = np.abs(v[I] - v[J]) * c[:, None]                                  # edge currents
        cur = inc @ ie
        acc += (cur @ Wt[k0:k0 + k]).astype("float32")
    return acc, reff


def main():
    t0 = time.time()
    g = np.load(B / "grids.npz")
    NY, NX = g["resist"].shape; N = NY * NX; RES = float(g["RES"]); X0, Y1 = float(g["X0"]), float(g["Y1"])
    F = {m: g[f"f{m:02d}"] for m in MONTHS}
    fmax = np.max(np.stack(list(F.values())), 0)
    water = g["water"] > 0
    H = (fmax >= 0.35) & ~water                                                # flower-rich cells: pair ends
    hr, hc = np.nonzero(H)
    print(f"grid {NX}×{NY}, flower-rich cells {H.sum():,} ({H.mean() * 100:.0f}%)", flush=True)
    # ---- pairs: s uniform in H; t uniform in H within 600 m (half) or 2 km (half) → importance weights
    ii = np.cumsum(np.cumsum(np.pad(H, ((1, 0), (1, 0))).astype(np.int64), 0), 1)
    def count(r, c, rad):
        k = int(rad / RES); r0, r1 = np.clip(r - k, 0, NY), np.clip(r + k + 1, 0, NY); c0, c1 = np.clip(c - k, 0, NX), np.clip(c + k + 1, 0, NX)
        return ii[r1, c1] - ii[r0, c1] - ii[r1, c0] + ii[r0, c0]
    S, T = [], []
    while len(S) < NPAIRS:
        k = rng.integers(0, len(hr)); rad = 600 if rng.random() < 0.5 else 2000
        for _ in range(50):
            j = rng.integers(0, len(hr))
            if j != k and abs(hr[j] - hr[k]) * RES <= rad and abs(hc[j] - hc[k]) * RES <= rad and (hr[j], hc[j]) != (hr[k], hc[k]):
                break
        else:
            continue
        # cheaper: draw within the square window directly
        S.append(k); T.append(j)
    S, T = np.array(S), np.array(T)
    sr, sc_, tr_, tc_ = hr[S], hc[S], hr[T], hc[T]
    d = np.hypot(sr - tr_, sc_ - tc_) * RES
    q = 0.5 * (np.maximum(np.abs(sr - tr_), np.abs(sc_ - tc_)) * RES <= 600) / np.maximum(count(sr, sc_, 600), 1) + 0.5 / np.maximum(count(sr, sc_, 2000), 1)
    scen = [(gname, m) for gname in GUILDS for m in MONTHS]
    Wt = np.zeros((NPAIRS, len(scen)))
    for k_, (gname, m) in enumerate(scen):
        Wt[:, k_] = np.clip(F[m][sr, sc_], 0, 1) * np.clip(F[m][tr_, tc_], 0, 1) * np.exp(-d / GUILDS[gname]) / q
    Wt /= Wt.sum(0, keepdims=True)
    sidx, tidx = sr * NX + sc_, tr_ * NX + tc_
    print(f"pairs {NPAIRS}: median distance {np.median(d):.0f} m", flush=True)
    I, J, Wd = edges(NY, NX)
    lu, c = factor(g["resist"], I, J, Wd)
    print(f"[{time.time() - t0:.0f} s] factorised", flush=True)
    cur0, reff0 = solve_pairs(lu, c, I, J, N, sidx, tidx, Wt)
    print(f"[{time.time() - t0:.0f} s] solved BEFORE", flush=True)
    del lu
    C0 = cur0.reshape(NY, NX, -1)
    # ---- missing links: much current forced through poor ground (high resistance, few flowers)
    cmean = C0.mean(-1)
    poor = np.clip((g["resist"] - 3) / 8, 0, 1) * (1 - np.clip(fmax, 0, 1))
    pinch = ndi.gaussian_filter(cmean / np.percentile(cmean, 99) * poor, 2)
    # ---- flower islands for small solitary bees: rich patches (forage ≥ 0.5) whose gap is ≤ 100 m form one network
    #      (union of patches dilated by 50 m). A bee stop (30 m × 30 m of flowers, April–September) joins every network
    #      within 100 m of it. Greedy pick of 25 bus / tram stops that raise the equivalent connected area (ECA, Saura et al.)
    #      the most, summed over April–September.
    st = gpd.read_parquet(B / "stops.parquet").reset_index(drop=True)
    st["c"] = ((st.geometry.x - X0) / RES).astype(int).clip(0, NX - 1); st["r"] = ((Y1 - st.geometry.y) / RES).astype(int).clip(0, NY - 1)
    HOP, THR, R_ST = 100.0, 0.5, 2
    kd = int(round(HOP / 2 / RES))
    net = {}
    for m in MONTHS[1:]:
        Hm = (F[m] >= THR) & ~water
        lab, n = ndi.label(ndi.binary_dilation(Hm, iterations=kd), structure=np.ones((3, 3)))
        area = np.bincount(lab[Hm], minlength=n + 1).astype(float) * RES * RES / 1e4      # ha of flower cells per network
        reach = []
        for r_, c_ in zip(st.r, st.c):                                                     # networks within 100 m of the stop
            w = lab[max(0, r_ - R_ST - 2 * kd):r_ + R_ST + 2 * kd + 1, max(0, c_ - R_ST - 2 * kd):c_ + R_ST + 2 * kd + 1]
            reach.append(set(np.unique(w[w > 0]).tolist()))
        net[m] = {"lab": lab, "area": area, "reach": reach}
    def eca(m, parent):
        a = net[m]["area"]; tot = {}
        for i in range(1, len(a)):
            r = i
            while parent[m][r] != r:
                r = parent[m][r]
            tot[r] = tot.get(r, 0) + a[i]
        return math.sqrt(sum(v * v for v in tot.values()))
    parent = {m: list(range(len(net[m]["area"]))) for m in net}
    def find(m, i):
        while parent[m][i] != i:
            parent[m][i] = parent[m][parent[m][i]]; i = parent[m][i]
        return i
    def comp_area(m):
        a = net[m]["area"]; tot = {}
        for i in range(1, len(a)):
            r = find(m, i); tot[r] = tot.get(r, 0) + a[i]
        return tot
    eca0 = {m: eca(m, parent) for m in net}
    largest0 = {m: max(comp_area(m).values()) for m in net}
    chosen = []
    for it in range(25):
        best, bg = None, 0.0
        tots = {m: comp_area(m) for m in net}
        for k in range(len(st)):
            if k in chosen or any(math.hypot(st.geometry.x[k] - st.geometry.x[j], st.geometry.y[k] - st.geometry.y[j]) < 200 for j in chosen):
                continue
            gsum = 0.0
            for m in net:
                roots = {find(m, i) for i in net[m]["reach"][k]}
                if len(roots) > 1:
                    a = [tots[m][r] for r in roots]
                    gsum += (sum(a) ** 2 - sum(x * x for x in a))
            if gsum > bg:
                best, bg = k, gsum
        if best is None:
            break
        chosen.append(best)
        for m in net:
            roots = sorted({find(m, i) for i in net[m]["reach"][best]})
            for r in roots[1:]:
                parent[m][r] = roots[0]
    eca1 = {m: eca(m, parent) for m in net}
    largest1 = {m: max(comp_area(m).values()) for m in net}
    st["rank"] = 0; st.loc[chosen, "rank"] = np.arange(1, len(chosen) + 1)
    pin3 = ndi.uniform_filter(pinch, 7); st["score"] = pin3[st.r, st.c]
    islands = {f"{m:02d}": {"eca_before": round(eca0[m], 1), "eca_after": round(eca1[m], 1), "largest_before": round(largest0[m], 1),
                            "largest_after": round(largest1[m], 1), "networks": int(len(net[m]["area"]) - 1)} for m in net}
    print(json.dumps(islands, indent=0), flush=True)
    # island labels per month for the web (network id per cell, before)
    np.savez_compressed(B / "islands.npz", **{f"m{m:02d}": net[m]["lab"].astype("int32") for m in net})
    # AFTER: each stop gets 30 m × 30 m of flowering plants: resistance like a meadow, flowers April–September
    r1 = g["resist"].copy(); F1 = {m: F[m].copy() for m in MONTHS}
    yy, xx = np.mgrid[-2:3, -2:3]
    for k in chosen:
        r_, c_ = st.r[k], st.c[k]
        rr, cc = np.clip(r_ + yy, 0, NY - 1), np.clip(c_ + xx, 0, NX - 1)
        r1[rr, cc] = np.minimum(r1[rr, cc], 1.8)
        for m in MONTHS:
            if m >= 4:
                F1[m][rr, cc] = np.maximum(F1[m][rr, cc], 0.8)
    lu1, c1 = factor(r1, I, J, Wd)
    cur1, reff1 = solve_pairs(lu1, c1, I, J, N, sidx, tidx, Wt)
    del lu1
    C1 = cur1.reshape(NY, NX, -1)
    print(f"[{time.time() - t0:.0f} s] solved AFTER", flush=True)
    # effective-resistance improvement for pairs, per scenario (weighted)
    imp = {f"{gname}_{m:02d}": round(float(1 - (Wt[:, k] * reff1).sum() / (Wt[:, k] * reff0).sum()), 4) for k, (gname, m) in enumerate(scen)}
    near = [k for k in range(NPAIRS) if any(math.hypot((sc_[k] + tc_[k]) / 2 - st.c[j], (sr[k] + tr_[k]) / 2 - st.r[j]) * RES < 600 for j in chosen)]
    np.savez_compressed(B / "current.npz", before=C0.astype("float32"), after=C1.astype("float32"), pinch=pinch.astype("float32"), scen=np.array([f"{a}_{m:02d}" for a, m in scen]))
    st.to_parquet(B / "stops_ranked.parquet")
    stats = {"islands": islands, "hop_m": HOP, "patch_forage_min": THR, "pairs": NPAIRS, "median_pair_m": float(np.median(d)), "flower_cells_share": float(H.mean()), "reff_improvement": imp,
             "reff_improvement_near_stops": float(1 - reff1[near].mean() / reff0[near].mean()) if near else None, "n_near": len(near),
             "stops": [{"rank": int(st["rank"][k]), "name": st.name[k], "x": float(st.geometry.x[k]), "y": float(st.geometry.y[k]), "score": float(st.score[k])} for k in chosen]}
    json.dump(stats, open(B / "model_stats.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k != "stops"}, indent=1)); print([s["name"] for s in stats["stops"]][:12])
    print(f"done {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
