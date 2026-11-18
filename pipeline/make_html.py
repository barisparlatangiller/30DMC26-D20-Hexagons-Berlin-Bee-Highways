"""docs/index.html (EN) + docs/tr.html (TR): story mode + explore panel. python pipeline/make_html.py"""
import json
from pathlib import Path

V = "4"
ST = json.loads(Path("docs/data/stats.json").read_text())
C = ST["combos"]

S = {
 "en": dict(
  title="Bee Highways · Berlin", desc="Can a wild bee cross Neukölln? Flower islands, bee highways and the missing links between Tempelhofer Feld, Hasenheide and Neukölln, and what 25 flower beds in tree pits, at bus stops, school yards or car parks would join.",
  load="Counting flowers…", story="Story", explore="Explore", skip="Skip to the map", prev="Previous",
  ph="Explore the bee network", lead="Switch additions on and off and watch the flower islands join. Click an island to see only its network.",
  month="Month", bee="Highways for", small="Small solitary bees", smallE="≈ 300 m", bumble="Bumblebees", bumbleE="≈ 1 km",
  gNet="Bee network", lIsl="Flower islands", lIslE="one colour = one network for small bees (gaps ≤ 100 m)", lHw="Bee highways", lHwE="busiest flower-to-flower routes (circuit model)",
  lFlow="Bees moving", lFlowE="animated along the highways", lBr="Possible bridges", lBrE="where one flower bed would join islands",
  gAdd="What if we add flowers here?", gAddE="Each: the 25 places that join the most network, a 30 m × 30 m flower bed (April–September). The number: extra hectares of the largest network.",
  gFl="Flowers on the ground", gFlE="Berlin biotope map 2024, scored for bees",
  gObs="Real bees", lRec="Wild-bee records", lRecE="iNaturalist + GBIF, no honey bee", lHid="…where the map shows few flowers", lHidE="balconies, front gardens, tree pits",
  gCity="City", lTrees="Trees (3D)", lTreesE="honey = in flower and good for bees", lBld="Buildings", lBldE="OSM, 3D when zoomed in", lAdds="Show all candidate places", lAddsE="small icons, also when switched off",
  method="Method", m_1="<b>Flowers.</b> Each of Berlin's 1,675 biotope types gets a forage score (0–1) and flowering months; urban types (courtyards, allotments, railway land, streets) included. Street and park trees add flowers by genus and month (bee-forage lists).",
  m_2="<b>Islands.</b> Cells with rich flowers (score ≥ 0.5 that month) whose gap is 100 m or less form one network: a typical hop for small solitary bees. Each 30 m hexagon takes the island it mostly lies on.",
  m_3="<b>Highways.</b> The 10 m grid is a network of resistors: sealed ground (Berlin sealing map 2021), tall buildings (OSM) and flowerless cells slow a bee down. 3,600 flower pairs are connected one at a time and the current is summed per cell (circuit theory, as in Circuitscape), weighted by month and range (300 m small bees, 1 km bumblebees). The strongest 8% of current, skeletonised, are the highways.",
  m_4="<b>Additions.</b> For each kind (628 bus and tram stops, 6,879 street-tree pits, 157 school and nursery yards, 768 car parks), a 30 m × 30 m flower bed joins every island within 100 m of it. The 25 places that raise the equivalent connected area most over April–September are picked one by one.",
  limits="Limits", l_1="A model of potential, not measured nectar or verified flight routes. Scores are expert-style rules and need checking on the ground; wild bees differ widely by species.",
  l_2="Records cluster where people walk; no record does not mean no bees. 62% of records lie where the biotope map shows few flowers: the map misses balconies, front gardens and tree pits.",
  sources="Sources", r_1="Biotoptypen 2024, Versiegelung 2021, Baumbestand, Grünanlagen: Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin, Geoportal Berlin (dl-de/zero-2-0).",
  r_2="Wild-bee observations: iNaturalist (Anthophila, Berlin, export 17 Nov 2026, licence per record); GBIF.org (17 Nov 2026) <a href=\"https://doi.org/10.15468/dl.w965pw\">doi:10.15468/dl.w965pw</a>, CC BY-NC 4.0.",
  r_3="Buildings, stops, school yards, car parks: © OpenStreetMap contributors, ODbL. Basemap © CARTO.",
  r_4="McRae, B. H. et al. (2008) Ecology 89: 2712–2724 (circuit theory). Saura, S. et al. (2011) Ecol. Indicators 11: 407–416 (equivalent connected area).",
  foot="Barış Parlatangiller · <a href=\"https://barisparlatangiller.github.io/\">all 30 maps</a> · <a href=\"https://github.com/barisparlatangiller/30DMC26-D20-Hexagons-Berlin-Bee-Highways\">code &amp; method</a> · built with AI assistance (Claude, Anthropic)",
  other="tr.html", otherL="TR"),
 "tr": dict(
  title="Arı Otoyolları · Berlin", desc="Bir yabani arı Neukölln'ü geçebilir mi? Tempelhofer Feld, Hasenheide ve Neukölln arasında çiçek adaları, arı otoyolları ve eksik halkalar; ağaç diplerine, otobüs duraklarına, okul bahçelerine ya da otoparklara konacak 25 çiçek yatağının neleri birleştireceği.",
  load="Çiçekler sayılıyor…", story="Hikâye", explore="Keşfet", skip="Haritaya geç", prev="Geri",
  ph="Arı ağını keşfedin", lead="Eklemeleri açıp kapatın ve çiçek adalarının birleşmesini izleyin. Yalnızca ağını görmek için bir adaya tıklayın.",
  month="Ay", bee="Otoyollar", small="Küçük yalnız arılar", smallE="≈ 300 m", bumble="Bombus arıları", bumbleE="≈ 1 km",
  gNet="Arı ağı", lIsl="Çiçek adaları", lIslE="bir renk = küçük arılar için bir ağ (boşluk ≤ 100 m)", lHw="Arı otoyolları", lHwE="en yoğun çiçekten çiçeğe rotalar (devre modeli)",
  lFlow="Hareket eden arılar", lFlowE="otoyollar boyunca animasyon", lBr="Olası köprüler", lBrE="tek bir çiçek yatağının adaları birleştireceği yerler",
  gAdd="Buraya çiçek eklesek ne olur?", gAddE="Her biri: ağı en çok birleştiren 25 yer, 30 m × 30 m'lik bir çiçek yatağı (Nisan–Eylül). Sayı: en büyük ağa eklenen hektar.",
  gFl="Zemindeki çiçekler", gFlE="Berlin biyotop haritası 2024, arılar için puanlandı",
  gObs="Gerçek arılar", lRec="Yabani arı kayıtları", lRecE="iNaturalist + GBIF, bal arısı hariç", lHid="…haritanın az çiçek gösterdiği yerde", lHidE="balkonlar, ön bahçeler, ağaç dipleri",
  gCity="Şehir", lTrees="Ağaçlar (3B)", lTreesE="bal rengi = çiçekte ve arılar için iyi", lBld="Binalar", lBldE="OSM, yaklaşınca 3B", lAdds="Tüm aday yerleri göster", lAddsE="küçük simgeler, kapalıyken de",
  method="Yöntem", m_1="<b>Çiçekler.</b> Berlin'in 1.675 biyotop tipinin her biri bir besin puanı (0–1) ve çiçeklenme ayları aldı; kentsel tipler (avlular, hobi bahçeleri, demiryolu alanları, sokaklar) dahil. Sokak ve park ağaçları cinse ve aya göre çiçek ekler (arı bitkisi listeleri).",
  m_2="<b>Adalar.</b> Zengin çiçekli hücreler (o ay puan ≥ 0,5) aralarındaki boşluk 100 m veya daha azsa tek bir ağ oluşturur: küçük yalnız arılar için tipik bir sıçrama. Her 30 m'lik altıgen çoğunlukla üzerinde durduğu adayı alır.",
  m_3="<b>Otoyollar.</b> 10 m'lik grid bir direnç ağıdır: kaplı zemin (Berlin 2021), yüksek binalar (OSM) ve çiçeksiz hücreler arıyı yavaşlatır. 3.600 çiçek çifti tek tek bağlanır ve akım hücre başına toplanır (devre teorisi, Circuitscape'teki gibi); aya ve menzile göre ağırlıklandırılır (küçük arılar 300 m, bombus 1 km). Akımın en güçlü %8'i iskeletlenerek otoyollar elde edilir.",
  m_4="<b>Eklemeler.</b> Her tür için (628 otobüs ve tramvay durağı, 6.879 sokak ağacı dibi, 157 okul ve kreş bahçesi, 768 otopark) 30 m × 30 m'lik bir çiçek yatağı 100 m içindeki her adayı birleştirir. Nisan–Eylül boyunca eşdeğer bağlantılı alanı en çok artıran 25 yer tek tek seçilir.",
  limits="Sınırlar", l_1="Bu bir potansiyel modeli; ölçülmüş nektar ya da doğrulanmış uçuş rotası değildir. Puanlar uzman tarzı kurallardır ve arazide doğrulanmalıdır; yabani arılar türe göre çok farklıdır.",
  l_2="Kayıtlar insanların yürüdüğü yerlerde yoğunlaşır; kayıt olmaması arı olmadığı anlamına gelmez. Kayıtların %62'si biyotop haritasının az çiçek gösterdiği yerlerde: harita balkonları, ön bahçeleri ve ağaç diplerini kaçırıyor.",
  sources="Kaynaklar", r_1="Biotoptypen 2024, Versiegelung 2021, Baumbestand, Grünanlagen: Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin, Geoportal Berlin (dl-de/zero-2-0).",
  r_2="Yabani arı gözlemleri: iNaturalist (Anthophila, Berlin, 17 Kasım 2026, kayıt bazında lisans); GBIF.org (17 Kasım 2026) <a href=\"https://doi.org/10.15468/dl.w965pw\">doi:10.15468/dl.w965pw</a>, CC BY-NC 4.0.",
  r_3="Binalar, duraklar, okul bahçeleri, otoparklar: © OpenStreetMap katkıcıları, ODbL. Altlık © CARTO.",
  r_4="McRae, B. H. vd. (2008) Ecology 89: 2712–2724 (devre teorisi). Saura, S. vd. (2011) Ecol. Indicators 11: 407–416 (eşdeğer bağlantılı alan).",
  foot="Barış Parlatangiller · <a href=\"https://barisparlatangiller.github.io/\">30 haritanın tümü</a> · <a href=\"https://github.com/barisparlatangiller/30DMC26-D20-Hexagons-Berlin-Bee-Highways\">kod ve yöntem</a> · yapay zekâ desteğiyle hazırlandı (Claude, Anthropic)",
  other="index.html", otherL="EN"),
}

for lang, t in S.items():
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title>
<meta name="description" content="{t['desc']}">
<meta property="og:title" content="{t['title']}">
<meta property="og:description" content="{t['desc']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<link href="style.css?v={V}" rel="stylesheet">
</head>
<body class="story-on">
<div id="map"></div>
<header class="top">
  <nav class="modes"><button id="m-story" class="on">{t['story']}</button><button id="m-explore">{t['explore']}</button></nav>
  <a class="pill lang" href="{t['other']}">{t['otherL']}</a>
</header>

<section class="story card" id="story" aria-live="polite">
  <div class="kick" id="s-kick"></div>
  <h1 id="s-title"></h1>
  <p id="s-text"></p>
  <div class="s-key" id="s-key"></div>
  <div class="s-nav"><button class="ghost" id="s-prev" aria-label="{t['prev']}">←</button><div class="dots" id="s-dots"></div><button class="go" id="s-next"></button></div>
  <button class="skip" id="s-skip">{t['skip']}</button>
</section>

<aside class="panel card" id="panel">
  <h2 class="ph">{t['ph']}</h2>
  <p class="lead">{t['lead']}</p>
  <div id="kpi"></div>
  <div class="sl"><span>{t['month']}</span><input type="range" id="month" min="4" max="9" step="1" value="7"><b id="monthV">July</b></div>

  <h3>{t['gAdd']}</h3>
  <div class="adds" id="adds"></div>
  <p class="hint">{t['gAddE']}</p>

  <h3>{t['gNet']}</h3>
  <div class="toggles">
    <label><input type="checkbox" data-s="islands" checked><span>{t['lIsl']}</span><em>{t['lIslE']}</em></label>
    <label><input type="checkbox" data-s="highways" checked><span>{t['lHw']}</span><em>{t['lHwE']}</em></label>
    <label><input type="checkbox" data-s="flow" checked><span>{t['lFlow']}</span><em>{t['lFlowE']}</em></label>
    <label><input type="checkbox" data-s="bridges" checked><span>{t['lBr']}</span><em>{t['lBrE']}</em></label>
  </div>
  <div class="seg" id="guild"><button data-g="small" class="on">{t['small']}<em>{t['smallE']}</em></button><button data-g="bumble">{t['bumble']}<em>{t['bumbleE']}</em></button></div>

  <h3>{t['gFl']}</h3>
  <div class="toggles flowers" id="flowers"></div>
  <p class="hint">{t['gFlE']}</p>

  <h3>{t['gObs']}</h3>
  <div class="toggles">
    <label><input type="checkbox" data-s="records"><span>{t['lRec']}</span><em>{t['lRecE']}</em></label>
    <label><input type="checkbox" data-s="hidden"><span>{t['lHid']}</span><em>{t['lHidE']}</em></label>
  </div>

  <h3>{t['gCity']}</h3>
  <div class="toggles">
    <label><input type="checkbox" data-s="trees" checked><span>{t['lTrees']}</span><em>{t['lTreesE']}</em></label>
    <label><input type="checkbox" data-s="bld" checked><span>{t['lBld']}</span><em>{t['lBldE']}</em></label>
    <label><input type="checkbox" data-s="adds" checked><span>{t['lAdds']}</span><em>{t['lAddsE']}</em></label>
  </div>

  <details class="howto"><summary>{t['method']}</summary><p>{t['m_1']}</p><p>{t['m_2']}</p><p>{t['m_3']}</p><p>{t['m_4']}</p></details>
  <details class="howto"><summary>{t['limits']}</summary><p>{t['l_1']}</p><p>{t['l_2']}</p></details>
  <details class="howto"><summary>{t['sources']}</summary><ol class="refs"><li>{t['r_1']}</li><li>{t['r_2']}</li><li>{t['r_3']}</li><li>{t['r_4']}</li></ol></details>
  <footer class="foot"><p>{t['foot']}</p></footer>
</aside>
<div id="load" class="loading">{t['load']}</div>
<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://cdn.jsdelivr.net/npm/deck.gl@9.0.38/dist.min.js"></script>
<script src="app.js?v={V}"></script>
</body>
</html>
"""
    Path("docs/" + ("index.html" if lang == "en" else "tr.html")).write_text(html)
print("ok")
