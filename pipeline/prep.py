"""
Day 20 · Bee Highways · Berlin pilot (Tempelhofer Feld, Hasenheide, northern Neukölln): 7 × 6 km, EPSG:25833.

Inputs (input/): Biotoptypen.gpkg, Versiegelung_*.gpkg, baumbestand_*.gpkg, Grunanlagen.gpkg, observations-817068.csv (iNaturalist),
gbif_berlin.csv (GBIF bees, Berlin), osm_pilot.gpkg (buildings, stops, lines) + data/biotope_bee_scores.csv, data/tree_genus_bee.csv
Output (build/): grids.npz (10 m: forage per month, nest, sealed, building height, resistance, water), *.parquet for the web,
obs.parquet (wild-bee observations), stops.parquet
  python pipeline/prep.py
"""
import json, re, time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import box
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage as ndi

I, B, D = Path("input"), Path("build"), Path("data")
X0, Y0, X1, Y1 = 389500, 5811000, 396500, 5817000
RES = 10
NX, NY = (X1 - X0) // RES, (Y1 - Y0) // RES
TF = from_origin(X0, Y1, RES, RES)
PIL = box(X0, Y0, X1, Y1)
BB3857 = None
MONTHS = list(range(3, 10))          # March … September


def months(s):
    if not isinstance(s, str) or not s:
        return set()
    a, *b = [int(x) for x in s.split("-")]
    return set(range(a, (b[0] if b else a) + 1))


def read(f, layer=None, **kw):
    g = gpd.read_file(I / f, layer=layer, bbox=PIL_3857, engine="pyogrio", **kw)
    return g.to_crs(25833)


def ras(geoms_vals, fill=0, dtype="float32", merge="replace"):
    return features.rasterize(geoms_vals, out_shape=(NY, NX), transform=TF, fill=fill, dtype=dtype,
                              merge_alg=features.MergeAlg.add if merge == "add" else features.MergeAlg.replace)


def frac(geoms, sub=5):
    """area fraction per 10 m cell (rasterised at 2 m)"""
    a = features.rasterize(((g, 1) for g in geoms), out_shape=(NY * sub, NX * sub), transform=from_origin(X0, Y1, RES / sub, RES / sub), dtype="uint8")
    return a.reshape(NY, sub, NX, sub).mean(axis=(1, 3)).astype("float32")


def main():
    global PIL_3857
    t0 = time.time()
    B.mkdir(exist_ok=True)
    PIL_3857 = tuple(gpd.GeoSeries([PIL], crs=25833).to_crs(3857).total_bounds.round())
    # ---- biotopes → forage / nest / bloom
    bt = read("Biotoptypen.gpkg")
    bt = bt[bt.intersects(PIL)].copy()
    sc = pd.read_csv(D / "biotope_bee_scores.csv", dtype={"bt_code": str})
    bt = bt.merge(sc[["bt_code", "forage", "nest", "bloom", "rule"]], on="bt_code", how="left")
    bt["forage"] = bt.forage.fillna(0.05); bt["nest"] = bt.nest.fillna(0.05); bt["rule"] = bt.rule.fillna("unclassified")
    bt["geometry"] = bt.geometry.intersection(PIL)
    print(f"biotopes {len(bt):,}", flush=True)
    order = bt.sort_values("forage")                       # later (higher) wins on shared edges
    forage_b = ras(zip(order.geometry, order.forage))
    nest_b = ras(zip(order.geometry, order.nest))
    water = ras(((g, 1) for g, r in zip(bt.geometry, bt.rule) if r.startswith("water")), dtype="uint8")
    bloom = {m: ras(((g, 1.0) for g, b in zip(order.geometry, order.bloom) if m in months(b)), dtype="float32") for m in MONTHS}
    # ---- sealing (blocks + streets, 2021): sealed share, ground-nesting is impossible there
    vb = read("Versiegelung_derblockundblockteif.gpkg"); vs = read("Versiegelung_derstraenflachen.gpkg")
    sealed = ras(list(zip(vs.geometry, vs.vg.fillna(80).astype(float) / 100)) + list(zip(vb.geometry, vb.vg_2021.fillna(50).astype(float) / 100)))
    print(f"[{time.time() - t0:.0f} s] sealing", flush=True)
    # ---- buildings (OSM): footprint fraction + height
    bl = gpd.read_file(I / "osm_pilot.gpkg", layer="buildings").to_crs(25833)
    bl = bl[bl.intersects(PIL)].copy()
    def tag(t, k):
        m = re.search(rf'"{k}"=>"([0-9.]+)', t if isinstance(t, str) else ""); return float(m.group(1)) if m else np.nan
    lv = bl.other_tags.map(lambda t: tag(t, "building:levels")); hh = bl.other_tags.map(lambda t: tag(t, "height"))
    bl["h"] = np.where(hh.notna(), hh, np.where(lv.notna(), lv * 3.2 + 1.5, np.where(bl.building.isin(["garage", "garages", "shed", "kiosk", "roof", "carport"]), 3.0, 14.0)))
    bl["h"] = bl.h.clip(2.5, 120)
    bfrac = frac(bl.geometry)
    bh = ras(zip(bl.geometry, bl.h))
    print(f"[{time.time() - t0:.0f} s] buildings {len(bl):,}", flush=True)
    # ---- trees: crowns as forage, per month
    gv = pd.read_csv(D / "tree_genus_bee.csv").set_index("genus")
    trees = []
    for f in ("baumbestand_strassen.gpkg", "baumbestand_anlagenbume.gpkg"):
        t = read(f); t = t[t.within(PIL)].copy(); t["src"] = "street" if "strassen" in f else "park"; trees.append(t)
    tr = pd.concat(trees, ignore_index=True)
    tr["crown"] = pd.to_numeric(tr.kronedurch, errors="coerce")
    hgt = pd.to_numeric(tr.baumhoehe, errors="coerce")
    tr["crown"] = tr.crown.where(tr.crown.between(1, 30), (hgt * 0.55).clip(2, 14)).fillna(5.0)
    tr["height"] = hgt.where(hgt.between(2, 45), tr.crown * 1.5).fillna(8.0)
    tr["genus"] = tr.gattung.fillna("").str.split().str[0].str.capitalize()
    tr["value"] = tr.genus.map(gv.value).fillna(0.1)
    tr["bloom"] = tr.genus.map(gv.bloom).fillna("4-6")
    print(f"[{time.time() - t0:.0f} s] trees {len(tr):,}; top genera {tr.genus.value_counts().head(8).to_dict()}", flush=True)
    xs, ys = tr.geometry.x.values, tr.geometry.y.values
    tf = {}
    for m in MONTHS:
        on = tr.bloom.map(lambda b: m in months(b)).values
        g = np.zeros((NY, NX), "float32")
        c = ((xs - X0) / RES).astype(int); r = ((Y1 - ys) / RES).astype(int)
        ok = on & (c >= 0) & (c < NX) & (r >= 0) & (r < NY)
        area = np.pi * (tr.crown.values / 2) ** 2
        np.add.at(g, (r[ok], c[ok]), (tr.value.values * area)[ok] / (RES * RES))
        tf[m] = ndi.gaussian_filter(g, 0.8)                      # crowns spill over neighbouring cells
    # ---- monthly forage: biotope × in bloom (+ a little outside the peak) + flowering crowns
    fm = {}
    for m in MONTHS:
        fm[m] = np.clip(forage_b * (0.25 + 0.75 * bloom[m]) * (1 - 0.8 * bfrac) + np.clip(tf[m], 0, 1.2), 0, 1.5).astype("float32")
    nest = (nest_b * (1 - sealed) * (1 - bfrac)).astype("float32")
    # ---- resistance to flying through a cell: sealed ground, tall buildings and lack of flowers slow bees down
    fmax = np.max(np.stack([fm[m] for m in MONTHS]), axis=0)
    hb = np.clip(bh / 25, 0, 1.5) * bfrac
    resist = (1 + 5 * sealed + 6 * hb + 3 * (1 - np.clip(fmax, 0, 1)) + 1.5 * water).astype("float32")
    np.savez_compressed(B / "grids.npz", **{f"f{m:02d}": fm[m] for m in MONTHS}, forage_b=forage_b, nest=nest, sealed=sealed, bfrac=bfrac, bh=bh,
                        resist=resist, water=water, X0=X0, Y1=Y1, RES=RES)
    # ---- observations: wild bees only (no honey bee), accurate locations
    ob = pd.read_csv(I / "observations-817068.csv", low_memory=False)
    ob = ob[(ob.scientific_name != "Apis mellifera") & (ob.coordinates_obscured != True) & (ob.public_positional_accuracy.fillna(9999) <= 100)]
    ob = gpd.GeoDataFrame({"src": "iNaturalist", "taxon": ob.scientific_name, "date": ob.observed_on, "grade": ob.quality_grade, "license": ob.license.fillna("all rights reserved"),
                           "url": ob.url, "acc": ob.public_positional_accuracy}, geometry=gpd.points_from_xy(ob.longitude, ob.latitude), crs=4326).to_crs(25833)
    gb = pd.read_csv(I / "gbif_berlin.csv", low_memory=False)
    gb = gb[(gb.genus != "Apis") & (gb.datasetKey != "50c9509d-22c7-4a22-a47d-8c48425ef4a7") & (gb.coordinateUncertaintyInMeters.fillna(0) <= 100)]
    gb = gpd.GeoDataFrame({"src": "GBIF", "taxon": gb.species.fillna(gb.genus), "date": gb.eventDate.astype(str).str[:10], "grade": gb.basisOfRecord,
                           "license": gb.license, "url": "https://www.gbif.org/occurrence/" + gb.gbifID.astype(str), "acc": gb.coordinateUncertaintyInMeters},
                          geometry=gpd.points_from_xy(gb.decimalLongitude, gb.decimalLatitude), crs=4326).to_crs(25833)
    obs = pd.concat([ob, gb], ignore_index=True)
    obs_p = obs[obs.within(PIL)].copy()
    print(f"[{time.time() - t0:.0f} s] wild-bee observations: Berlin {len(obs):,}, pilot {len(obs_p):,} ({obs_p.src.value_counts().to_dict()}), taxa {obs_p.taxon.nunique()}", flush=True)
    obs.to_parquet(B / "obs_berlin.parquet"); obs_p.to_parquet(B / "obs.parquet")
    # ---- candidate "bee stops": bus / tram stops (one per 25 m)
    st = gpd.read_file(I / "osm_pilot.gpkg", layer="stops").to_crs(25833)
    st = st[st.within(PIL)].copy()
    st["name"] = st.name.fillna("")
    st["k"] = (st.geometry.x // 25).astype(int).astype(str) + "_" + (st.geometry.y // 25).astype(int).astype(str)
    st = st.drop_duplicates("k")[["name", "geometry"]]
    st.to_parquet(B / "stops.parquet")
    print(f"stops {len(st):,}")
    # ---- web layers
    bt[["bt_code", "bt_name", "forage", "nest", "rule", "geometry"]].to_parquet(B / "biotopes.parquet")
    bl[["h", "building", "geometry"]].to_parquet(B / "buildings.parquet")
    tr[["genus", "art_dtsch", "art_bot", "crown", "height", "value", "bloom", "src", "pflanzjahr", "geometry"]].to_parquet(B / "trees.parquet")
    json.dump({"biotopes": len(bt), "buildings": len(bl), "trees": len(tr), "obs_pilot": len(obs_p), "obs_berlin": len(obs), "stops": len(st),
               "taxa_pilot": int(obs_p.taxon.nunique())}, open(B / "meta.json", "w"))
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
