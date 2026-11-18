"""
Day 20 · Bee Highways · a soft edge around the pilot area.

Instead of cutting the map at the pilot rectangle, a 2 km ring around it shows the same flowers with less and less detail:
  · the Berlin biotopes in the ring, simplified, with an opacity that fades from 1 at the pilot edge to 0 at 2 km;
  · coarse 120 m hexagons with the biotope forage score (area-weighted), fading the same way: the honeycomb thins out.
  python pipeline/context.py
Output docs/data/context_biotopes.json · docs/data/context_hex.json
"""
import json, math
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Polygon

I, W, D = Path("input"), Path("docs/data"), Path("data")
X0, Y0, X1, Y1 = 389500, 5811000, 396500, 5817000
RING = 2000.0
PIL = box(X0, Y0, X1, Y1)
OUTER = PIL.buffer(RING, join_style=2)


def fade(geom):
    d = PIL.exterior.distance(geom.representative_point()) if not PIL.contains(geom.representative_point()) else 0.0
    return max(0.0, 1 - d / RING)


def main():
    bb = tuple(gpd.GeoSeries([OUTER], crs=25833).to_crs(3857).total_bounds.round())
    bt = gpd.read_file(I / "Biotoptypen.gpkg", bbox=bb, engine="pyogrio").to_crs(25833)
    sc = pd.read_csv(D / "biotope_bee_scores.csv", dtype={"bt_code": str})
    bt = bt.merge(sc[["bt_code", "forage", "rule"]], on="bt_code", how="left")
    bt["forage"] = bt.forage.fillna(0.05); bt["rule"] = bt.rule.fillna("unclassified")
    ring = bt[bt.intersects(OUTER) & ~bt.within(PIL)].copy()
    ring["geometry"] = ring.geometry.intersection(OUTER).difference(PIL)
    ring = ring[~ring.geometry.is_empty]
    import re
    src = Path("pipeline/build_web.py").read_text()
    CAT = eval(re.search(r"CAT = (\{.*?\})\n", src, re.S).group(1))
    ring["cat"] = ring.rule.map(CAT)
    ring["cat"] = ring.cat.where(ring.cat.notna(), np.where(ring.rule.str.startswith("water"), "water", "built"))
    ring["fade"] = [round(fade(gm), 2) for gm in ring.geometry]
    ring = ring[ring.fade > 0.03]
    ring["geometry"] = ring.geometry.simplify(4)
    out = ring[["cat", "forage", "fade", "geometry"]].to_crs(4326)
    out["geometry"] = out.geometry.set_precision(1e-6)
    out.to_file(W / "context_biotopes.json", driver="GeoJSON")
    # coarse hexagons (120 m edge) with area-weighted forage
    E = 120.0; w, h = 1.5 * E, math.sqrt(3) * E
    xb0, yb0, xb1, yb1 = OUTER.bounds
    hexes = []
    for i in range(int((xb1 - xb0) / w) + 2):
        for j in range(int((yb1 - yb0) / h) + 2):
            x = xb0 + i * w; y = yb0 + j * h + (h / 2 if i % 2 else 0)
            hx = Polygon([(x + E * math.cos(k * math.pi / 3), y + E * math.sin(k * math.pi / 3)) for k in range(6)])
            if hx.intersects(OUTER) and not PIL.contains(hx.centroid):
                hexes.append(hx)
    hg = gpd.GeoDataFrame(geometry=hexes, crs=25833)
    hg["id"] = range(len(hg))
    inter = gpd.overlay(hg, ring[["forage", "geometry"]], how="intersection", keep_geom_type=True)
    inter["a"] = inter.area
    agg = inter.groupby("id").apply(lambda d: (d.forage * d.a).sum() / max(hg.geometry[d.name].area, 1), include_groups=False)
    hg["forage"] = hg.id.map(agg).fillna(0)
    hg["fade"] = [round(fade(gm), 2) for gm in hg.geometry]
    hg = hg[(hg.fade > 0.03) & (hg.forage > 0.08)]
    c = hg.geometry.centroid.to_crs(4326)
    (W / "context_hex.json").write_text(json.dumps({"edge": E, "lon": np.round(c.x, 6).tolist(), "lat": np.round(c.y, 6).tolist(),
                                                    "f": np.round(hg.forage, 2).tolist(), "fade": hg.fade.tolist()}, separators=(",", ":")))
    print(len(out), "ring biotopes;", len(hg), "coarse hexes")


if __name__ == "__main__":
    main()
