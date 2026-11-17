# Bee Highways · Berlin

**#30DayMapChallenge 2026 · Day 20 · Hexagons**

**Where do Berlin's wild bees find flowers, where are the gaps between them, and which flowering stops would close them?**

👉 **Live map:** https://barisparlatangiller.github.io/30DMC26-D20-Hexagons-Berlin-Bee-Highways/ · [Türkçe](https://barisparlatangiller.github.io/30DMC26-D20-Hexagons-Berlin-Bee-Highways/tr.html)

A pilot area of 7 × 6 km around Tempelhofer Feld, Hasenheide and northern Neukölln, mapped in detail: every biotope patch scored for flowers and nesting ground, every street and park tree with its flowering months, every building. Above the city floats a honeycomb of 30 m cells:

- **cell size** = how strongly the cell links flower patches for bees (circuit theory: thousands of flower-to-flower trips through a 10 m resistance grid);
- **cell colour** = how many wild bees people have actually recorded within 120 m (iNaturalist, GBIF; no honey bee);
- **violet rings** = missing links, where many bee paths have to cross sealed ground.

Switch between small solitary bees (≈ 300 m range) and bumblebees (≈ 1 km), slide through the months from March to September, and add **25 bee stops**: flowering beds at bus and tram stops, chosen one by one where they join the most flower networks for small bees.

## Pipeline

```
python pipeline/scores.py <berlin_biotop_ari_habitat_on_siniflandirma.csv>   # biotope + tree-genus score tables (data/)
python pipeline/prep.py        # 10 m grids: forage per month, nesting, sealing, buildings, resistance; observations; stops
python pipeline/model.py       # circuit current (before / after), flower islands and the 25 bee stops
python pipeline/build_web.py   # web layers (docs/data)
python pipeline/make_html.py   # docs/index.html + docs/tr.html
python pipeline/film.py        # LinkedIn film
```

Inputs not in the repo (`input/`): Berlin Biotoptypen 2024, Versiegelung 2021, Baumbestand, Grünanlagen (Geoportal Berlin), the iNaturalist export, and the GBIF download and OSM extract fetched by `.github/workflows/fetch.yml`.

## Limits

A model of potential, not measured nectar or verified flight routes. Scores are expert-style rules. Records cluster where people walk; no record does not mean no bees. Wild bees differ widely by species.

## Data & licences

Biotoptypen, Versiegelung, Baumbestand, Grünanlagen © Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin (dl-de/zero-2-0) · iNaturalist observations (licence per record) · GBIF.org occurrence download doi:10.15468/dl.w965pw (CC BY-NC 4.0) · © OpenStreetMap contributors (ODbL) · basemap © CARTO.

Barış Parlatangiller · built with AI assistance (Claude, Anthropic)
