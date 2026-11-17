"""
Day 20 · Bee Highways · score tables (expert-style rules, not measurements).

data/biotope_bee_scores.csv   bt_code → forage (0–1), nest (0–1), bloom months, rule
data/tree_genus_bee.csv       genus → bee value (0–1, nectar + pollen) and bloom months

The biotope scores start from berlin_biotop_ari_habitat_on_siniflandirma.csv (Barış's pre-classification) and add the
urban biotope types it left unclassified (blocks with green courtyards, allotments, railway land, streets …), using key
words of the Berlin biotope names. The tree values follow the usual German bee-forage lists (Bienenweide catalogues):
genus level, rounded, for comparison only.
  python pipeline/scores.py <path to berlin_biotop_ari_habitat_on_siniflandirma.csv>
"""
import re, sys
from pathlib import Path
import pandas as pd

# (pattern on bt_name, forage, nest, bloom months, label); first match wins, order matters
RULES = [
    (r"teilversiegelt|Fugenvegetation|Schotterrasen", 0.15, 0.50, "5-8", "part-sealed with joint vegetation"),
    (r"Spundwand|Steinmauer|Steinpflasterung|Rauhwurf|Kanäle|Ufer", 0.0, 0.0, "", "water / built banks"),
    (r"Bauflächen|Baustelle|Bauerwartung", 0.35, 0.60, "6-9", "construction land (often ruderal)"),
    (r"Güterbahnhöfe|Personenbahnhöfe|Bahnhof", 0.30, 0.40, "5-9", "railway stations"),
    (r"Kleinsiedlung", 0.50, 0.30, "4-9", "small houses with gardens"),
    (r"Kerngebiet|Kirche", 0.08, 0.05, "5-7", "city core / church"),
    (r"^Wege|Weg mit", 0.08, 0.15, "", "paths"),
    (r"Friedhöfe", 0.60, 0.40, "4-9", "cemetery"),
    (r"Sandtrockenrasen|Trockenrasen|Magerrasen|Silbergras|Heide|Calluna", 0.95, 0.95, "4-9", "dry grassland / heath"),
    (r"vegetationsfrei|Rohboden|Sandfläche|Abgrabung|Offensand", 0.10, 0.95, "", "bare soil / sand"),
    (r"Ruderal|Staudenflur|Hochstauden|Brache|Säume|Saum", 0.85, 0.60, "6-9", "ruderal / tall herbs"),
    (r"Streuobst|Obstbaum|Obstwiese", 0.75, 0.40, "4-5", "orchard"),
    (r"Kleingärten|Kleingarten|Grabeland", 0.75, 0.40, "4-9", "allotments"),
    (r"Einzel- und Reihenhaus|Villen|Ziergärten", 0.45, 0.25, "4-9", "houses with gardens"),
    (r"begrünt|Parkbaum|hohem Grünflächenanteil|Hofbegrünung", 0.30, 0.15, "4-8", "blocks with green courtyards"),
    (r"Zeilenbebauung|Großsiedlung|Hochhaus|Großformbebauung", 0.25, 0.15, "4-8", "slab / tower blocks with green"),
    (r"Blockbebauung|Blockrand|Mischgebiet|Dorf", 0.12, 0.08, "5-7", "dense blocks"),
    (r"Industrie|Gewerbe|Handel|Dienstleistung|Ver- und Entsorgung|Gemeinbedarf", 0.08, 0.10, "5-8", "industry / public facilities"),
    (r"Straße|Autobahn|Parkplatz|Verkehrsfläche|Flughafen|Rollfeld|versiegelt|Versiegelt|befestigt|Plätze", 0.03, 0.03, "", "streets / sealed"),
    (r"Feuchtwiese|Frischwiese|Wiese|Grünland|Weide", 0.60, 0.45, "5-8", "meadow"),
    (r"intensiv|Intensiv", 0.30, 0.20, "5-7", "intensive grassland"),
    (r"Friedhof|friedhöfe", 0.60, 0.40, "4-9", "cemetery"),
    (r"Zierrasen|Scherrasen|Trittrasen|Rasen", 0.20, 0.25, "5-6", "mown lawn"),
    (r"Sportplatz|Sportanlage|Spielplatz|Golf", 0.10, 0.15, "", "sports / play"),
    (r"Hausgärten|Ziergärten|Gärten|Garten", 0.60, 0.30, "4-9", "gardens"),
    (r"Park|Grünanlage|Grünfläche", 0.50, 0.30, "4-8", "park"),
    (r"Gleis|Bahnanlage|Bahnbrache|Bahnfläche|Bahngelände|Bahndamm", 0.55, 0.65, "5-9", "railway land"),
    (r"Robinie", 0.55, 0.30, "5-6", "black-locust stand"),
    (r"Gebüsch|Hecke|Feldgehölz|Gehölz|Strauch", 0.50, 0.35, "3-6", "shrubs / hedges"),
    (r"Kiefer", 0.12, 0.30, "", "pine forest"),
    (r"Wald|Forst|Vorwald", 0.25, 0.30, "3-5", "woodland"),
    (r"Acker|Feldflur", 0.30, 0.25, "5-7", "arable"),
    (r"Röhricht|Ried|Moor", 0.20, 0.10, "6-8", "reed / mire"),
    (r"Fluss|Bach|Graben|Kanal|See|Teich|Weiher|Gewässer|Becken|Quelle|Pfuhl", 0.0, 0.0, "", "water"),
]
FALLBACK = {"olasi_otsu_habitat": (0.65, 0.5, "5-8", "herb-rich (pre-class.)"), "oncelikli_inceleme": (0.85, 0.7, "5-9", "meadow / dry grassland (pre-class.)"),
            "bahce_ek_veri_gerekli": (0.55, 0.3, "4-9", "garden (pre-class.)"), "dusuk_veya_yonetim_bagimli": (0.2, 0.2, "5-6", "mown (pre-class.)"),
            "agac_cali_ek_veri_gerekli": (0.3, 0.3, "3-5", "trees / shrubs (pre-class.)")}

# genus → (value 0–1, bloom months); nectar + pollen, rounded from German bee-forage lists
TREES = {
    "Tilia": (1.0, "6-7"), "Robinia": (0.95, "5-6"), "Salix": (1.0, "3-4"), "Styphnolobium": (0.9, "7-8"), "Sophora": (0.9, "7-8"),
    "Tetradium": (1.0, "7-8"), "Euodia": (1.0, "7-8"), "Koelreuteria": (0.8, "7"), "Acer": (0.8, "4-5"), "Prunus": (0.8, "3-5"),
    "Malus": (0.8, "4-5"), "Aesculus": (0.7, "5"), "Castanea": (0.8, "6-7"), "Crataegus": (0.7, "5"), "Sorbus": (0.6, "5-6"),
    "Pyrus": (0.6, "4"), "Amelanchier": (0.6, "4"), "Paulownia": (0.6, "5"), "Catalpa": (0.6, "6-7"), "Ailanthus": (0.7, "6-7"),
    "Ligustrum": (0.6, "6-7"), "Gleditsia": (0.5, "6"), "Cornus": (0.5, "3-4"), "Elaeagnus": (0.5, "5-6"), "Magnolia": (0.4, "4"),
    "Corylus": (0.4, "2-3"), "Ulmus": (0.3, "3"), "Populus": (0.3, "3-4"), "Alnus": (0.3, "2-3"), "Cercis": (0.5, "4-5"),
    "Betula": (0.2, "4"), "Quercus": (0.2, "5"), "Carpinus": (0.15, "4-5"), "Fraxinus": (0.15, "4"), "Liriodendron": (0.6, "6"),
    "Platanus": (0.1, "5"), "Fagus": (0.1, "5"), "Liquidambar": (0.1, "5"), "Celtis": (0.2, "4-5"), "Morus": (0.2, "5"),
    "Pinus": (0.05, ""), "Picea": (0.02, ""), "Taxus": (0.1, "3"), "Ginkgo": (0.0, ""), "Larix": (0.02, ""), "Juglans": (0.2, "5"),
}


def main(src):
    c = pd.read_csv(src, dtype={"bt_code": str})
    out = []
    for r in c.itertuples():
        hit = None
        for pat, f, n, bm, lab in RULES:
            if re.search(pat, r.bt_name, flags=re.I):
                hit = (f, n, bm, lab); break
        if hit is None:
            hit = FALLBACK.get(r.habitat_on_sinifi, (0.05, 0.05, "", "unclassified"))
        # the pre-classification raises herb-rich types that the key words rate low
        if r.habitat_on_sinifi == "oncelikli_inceleme":
            hit = (max(hit[0], 0.8), max(hit[1], 0.6)) + hit[2:]
        out.append({"bt_code": r.bt_code, "bt_name": r.bt_name, "pre_class": r.habitat_on_sinifi, "forage": hit[0], "nest": hit[1], "bloom": hit[2], "rule": hit[3]})
    o = pd.DataFrame(out)
    Path("data").mkdir(exist_ok=True)
    o.to_csv("data/biotope_bee_scores.csv", index=False)
    pd.DataFrame([{"genus": g, "value": v, "bloom": b} for g, (v, b) in TREES.items()]).to_csv("data/tree_genus_bee.csv", index=False)
    print(o.rule.value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv[1])
