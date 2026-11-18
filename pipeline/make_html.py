"""docs/index.html (EN) + docs/tr.html (TR). python pipeline/make_html.py"""
import json
from pathlib import Path

V = "2"
ST = json.loads(Path("docs/data/stats.json").read_text())
I7 = ST["islands"]["07"]
NUM = lambda x, tr: (f"{x:,.0f}".replace(",", ".") if tr else f"{x:,.0f}")

S = {
 "en": dict(
  title="Bee Highways · Berlin", desc="Where do Berlin's wild bees find flowers, where are the gaps between them, and which 25 flowering bus stops would close them? A 3D honeycomb over Tempelhofer Feld, Hasenheide and Neukölln.",
  load="Counting flowers…", eyebrow="#30DayMapChallenge · Day 20 · Hexagons · Berlin", h1="Bee highways: the missing links",
  lede="Between Tempelhofer Feld, Hasenheide and Neukölln, every flower patch, lime tree and garden is on this map. Zoomed out, a <b>honeycomb on the ground</b> shows where wild bees can travel from flower to flower: <b>bigger and darker cells, stronger links</b>. Zoom in and it gives way to every tree and building. Dark dots are real wild-bee records.",
  s1=f"ha: the largest flower network a small wild bee can use in July, up from {NUM(I7['largest_before'], False)} ha with 25 bee stops",
  s2=f"wild-bee records in the pilot area, {ST['taxa_pilot']} taxa (iNaturalist + GBIF, no honey bee)",
  s3=f"lime, maple, black locust and other trees mapped one by one ({NUM(ST['trees'], False)} in total)",
  bee="Which bee?", small="Small solitary bee", smallE="hops ≤ 100 m, forages ~300 m", bumble="Bumblebee", bumbleE="forages ~1 km",
  month="Month", before="Today", after="+ 25 bee stops",
  layers="Layers", lHex="Honeycomb", lHexE="size and colour = link strength", lTrees="Trees (3D)", lTreesE="honey = in flower and good for bees",
  lBld="Buildings", lBldE="OSM", lObs="Wild-bee records", lObsE="iNaturalist, GBIF", lStops="Bee stops", lStopsE="25 proposed flowering stops", lGround="Ground: flowers for bees", lGroundE="Berlin biotope map 2024",
  lift="Height", hexop="Opacity", views="Views", vAll="Pilot area", vFeld="Tempelhofer Feld", vHasen="Hasenheide", vTop="Top view",
  stopsT="25 bee stops", stopsH="Bus and tram stops where a 30 m × 30 m flower bed would join the most flower networks for small bees (greedy, April–September). Click to fly there.",
  legT="How to read the honeycomb", leg1="Bigger cell: stronger link for bees (circuit model)", leg2="Darker honey: more bee traffic", leg5="Wild-bee record (iNaturalist, GBIF)", zoomH="Zoom out: the network as a honeycomb. Zoom in: every tree, trunk and building.", leg3="Violet outline: missing link, bee paths cross poor ground", leg4="Violet cell (+ 25 bee stops): newly joined to the largest flower network",
  none="little", many="a lot",
  howto="How to read this map",
  h_1="The <b>ground</b> is the Berlin biotope map: the greener, the more flowers for bees. Streets and roofs are pale.",
  h_2="<b>Trees</b> are drawn one by one from the street and park tree register. They turn <b>honey-coloured</b> in the months they flower, if they are good for bees (lime in June–July, black locust in May, maple in April …).",
  h_3="Zoomed out, the <b>honeycomb</b> lies on the ground: cells 30 m wide, <b>bigger and darker where the model sends more bee traffic</b>. Dark dots are wild bees people have actually recorded. Violet rings: the missing links. Zoom in and the honeycomb fades into the detailed city.",
  h_4="Switch the <b>bee</b>, the <b>month</b> and <b>today / + 25 bee stops</b> to see the network change.",
  method="Method", m_1="<b>Flowers and nests.</b> Every one of the 1,675 biotope types gets a forage and a nesting score (0–1) and its flowering months, starting from a pre-classification and adding the urban types (green courtyards, allotments, railway land, streets). Street and park trees add flowers by genus and month (bee-forage lists). Sealed ground (Berlin sealing map 2021) and buildings (OSM) remove nesting ground.",
  m_2="<b>Links.</b> The 10 m grid becomes a network of resistors: sealed ground, tall buildings and cells without flowers slow a bee down. 3,600 pairs of flower-rich cells are connected one at a time and the current through every cell is summed (circuit theory, as in Circuitscape). Each pair counts as much as both ends flower that month and as the bee's range allows (300 m for small solitary bees, 1 km for bumblebees).",
  m_3="<b>Bee stops.</b> For small bees, flower patches whose gap is 100 m or less form one network. Each candidate bus or tram stop gets a 30 m × 30 m flower bed (April–September); the 25 that join the most network area are chosen one by one (equivalent connected area). The circuit model is then run again with them.",
  limits="Limits", l_1="This is a <b>model of potential</b>, not measured nectar or verified flight routes. Scores are expert-style rules and need checking on the ground. Wild bees differ by species: some need one plant, some sand, some dead wood.",
  l_2="No record does not mean no bees: records cluster where people walk (parks, Tempelhofer Feld). Locations accurate to 100 m or better only; obscured records and the honey bee are left out. Records without an open licence are counted but not shown as points.",
  sources="Sources",
  r_1="Biotoptypen 2024, Versiegelung 2021, Baumbestand (Straßen- und Anlagenbäume), Grünanlagen: Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin, Geoportal Berlin (dl-de/zero-2-0).",
  r_2="Wild-bee observations: iNaturalist (Anthophila, Berlin, export 17 Nov 2026), licences per record; GBIF.org (17 Nov 2026) occurrence download <a href=\"https://doi.org/10.15468/dl.w965pw\">doi:10.15468/dl.w965pw</a>, CC BY-NC 4.0.",
  r_3="Buildings and stops: © OpenStreetMap contributors, ODbL. Basemap © CARTO.",
  r_4="Method: McRae, B. H. et al. (2008) Using circuit theory to model connectivity in ecology, evolution, and conservation. Ecology 89: 2712–2724. Saura, S. et al. (2011) Network analysis to assess landscape connectivity trends. Ecol. Indicators 11: 407–416.",
  foot="Barış Parlatangiller · <a href=\"https://barisparlatangiller.github.io/\">all 30 maps</a> · <a href=\"https://github.com/barisparlatangiller/30DMC26-D20-Hexagons-Berlin-Bee-Highways\">code &amp; method</a> · built with AI assistance (Claude, Anthropic)",
  other="tr.html", otherL="TR"),
 "tr": dict(
  title="Arı Otoyolları · Berlin", desc="Berlin'in yabani arıları çiçekleri nerede buluyor, aralarındaki boşluklar nerede ve hangi 25 çiçekli otobüs durağı bu boşlukları kapatır? Tempelhofer Feld, Hasenheide ve Neukölln üzerinde 3B bir petek.",
  load="Çiçekler sayılıyor…", eyebrow="#30DayMapChallenge · Gün 20 · Altıgenler · Berlin", h1="Arı otoyolları: eksik halkalar",
  lede="Tempelhofer Feld, Hasenheide ve Neukölln arasında her çiçek alanı, her ıhlamur ve her bahçe bu haritada. Uzaktan bakınca <b>zemindeki petek</b>, yabani arıların çiçekten çiçeğe nereden geçebildiğini gösteriyor: <b>hücre ne kadar büyük ve koyuysa bağlantı o kadar güçlü</b>. Yaklaşınca petek kayboluyor, her ağaç ve bina ortaya çıkıyor. Koyu noktalar gerçek yabani arı kayıtları.",
  s1=f"ha: küçük bir yabani arının Temmuz'da kullanabildiği en büyük çiçek ağı; 25 arı durağıyla {NUM(I7['largest_before'], True)} ha'dan bu değere çıkıyor",
  s2=f"pilot bölgede yabani arı kaydı, {ST['taxa_pilot']} takson (iNaturalist + GBIF, bal arısı hariç)",
  s3=f"ıhlamur, akçaağaç, akasya ve diğer ağaçlar tek tek ({NUM(ST['trees'], True)} ağaç)",
  bee="Hangi arı?", small="Küçük yalnız arı", smallE="≤ 100 m sıçrar, ~300 m'de beslenir", bumble="Bombus arısı", bumbleE="~1 km'de beslenir",
  month="Ay", before="Bugün", after="+ 25 arı durağı",
  layers="Katmanlar", lHex="Petek", lHexE="boyut ve renk = bağlantı gücü", lTrees="Ağaçlar (3B)", lTreesE="bal rengi = çiçekte ve arılar için iyi",
  lBld="Binalar", lBldE="OSM", lObs="Yabani arı kayıtları", lObsE="iNaturalist, GBIF", lStops="Arı durakları", lStopsE="önerilen 25 çiçekli durak", lGround="Zemin: arılar için çiçek", lGroundE="Berlin biyotop haritası 2024",
  lift="Yükseklik", hexop="Saydamlık", views="Görünümler", vAll="Pilot bölge", vFeld="Tempelhofer Feld", vHasen="Hasenheide", vTop="Üstten",
  stopsT="25 arı durağı", stopsH="30 m × 30 m'lik bir çiçek yatağının küçük arılar için en çok çiçek ağını birleştireceği otobüs ve tramvay durakları (sırayla seçildi, Nisan–Eylül). Tıklayınca oraya gider.",
  legT="Petek nasıl okunur", leg1="Büyük hücre: arılar için güçlü bağlantı (devre modeli)", leg2="Koyu bal rengi: daha çok arı trafiği", leg5="Yabani arı kaydı (iNaturalist, GBIF)", zoomH="Uzaklaşınca ağ petek olarak, yaklaşınca her ağaç, gövde ve bina görünür.", leg3="Mor çerçeve: eksik halka, arı yolları fakir zeminden geçiyor", leg4="Mor hücre (+ 25 arı durağı): en büyük çiçek ağına yeni katılan",
  none="az", many="çok",
  howto="Harita nasıl okunur",
  h_1="<b>Zemin</b> Berlin biyotop haritası: ne kadar yeşilse arılar için o kadar çok çiçek var. Sokaklar ve çatılar soluk.",
  h_2="<b>Ağaçlar</b> sokak ve park ağacı envanterinden tek tek çizildi. Arılar için iyiyseler çiçek açtıkları aylarda <b>bal rengine</b> döner (Haziran–Temmuz'da ıhlamur, Mayıs'ta akasya, Nisan'da akçaağaç …).",
  h_3="Uzaktan bakınca <b>petek</b> zeminde durur: hücreler 30 m genişliğinde, <b>modelin daha çok arı trafiği geçirdiği yerde daha büyük ve koyu</b>. Koyu noktalar insanların gerçekten kaydettiği yabani arılardır. Mor halkalar: eksik halkalar. Yaklaşınca petek ayrıntılı şehre dönüşür.",
  h_4="<b>Arıyı</b>, <b>ayı</b> ve <b>bugün / + 25 arı durağı</b> seçimini değiştirerek ağın nasıl değiştiğini görün.",
  method="Yöntem", m_1="<b>Çiçek ve yuva.</b> 1.675 biyotop tipinin her birine bir besin ve bir yuva puanı (0–1) ile çiçeklenme ayları verildi: ön sınıflandırmadan yola çıkıldı ve kentsel tipler (yeşil iç avlular, hobi bahçeleri, demiryolu alanları, sokaklar) eklendi. Sokak ve park ağaçları cinse ve aya göre çiçek ekler (arı bitkisi listeleri). Kaplı yüzeyler (Berlin 2021) ve binalar (OSM) yuva zeminini azaltır.",
  m_2="<b>Bağlantılar.</b> 10 m'lik grid bir direnç ağına dönüşür: kaplı zemin, yüksek binalar ve çiçeksiz hücreler arıyı yavaşlatır. Çiçekçe zengin 3.600 hücre çifti tek tek bağlanır ve her hücreden geçen akım toplanır (devre teorisi, Circuitscape'teki gibi). Her çift, iki ucu da o ay çiçekteyse ve arının menzili izin veriyorsa o kadar sayılır (küçük yalnız arılar 300 m, bombus 1 km).",
  m_3="<b>Arı durakları.</b> Küçük arılar için aralarında en fazla 100 m olan çiçek alanları tek bir ağ oluşturur. Her aday otobüs ve tramvay durağına 30 m × 30 m'lik bir çiçek yatağı (Nisan–Eylül) konur; en çok ağ alanını birleştiren 25 durak tek tek seçilir (eşdeğer bağlantılı alan). Ardından devre modeli onlarla yeniden çalıştırılır.",
  limits="Sınırlar", l_1="Bu bir <b>potansiyel modeli</b>; ölçülmüş nektar ya da doğrulanmış uçuş rotası değildir. Puanlar uzman tarzı kurallardır ve arazide doğrulanmalıdır. Yabani arılar türe göre farklıdır: kimi tek bir bitkiye, kimi kuma, kimi ölü odun ister.",
  l_2="Kayıt olmaması arı olmadığı anlamına gelmez: kayıtlar insanların yürüdüğü yerlerde (parklar, Tempelhofer Feld) yoğunlaşır. Yalnızca 100 m veya daha iyi konum hassasiyeti kullanıldı; gizlenmiş kayıtlar ve bal arısı çıkarıldı. Açık lisansı olmayan kayıtlar sayılır ama nokta olarak gösterilmez.",
  sources="Kaynaklar",
  r_1="Biotoptypen 2024, Versiegelung 2021, Baumbestand (sokak ve park ağaçları), Grünanlagen: Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin, Geoportal Berlin (dl-de/zero-2-0).",
  r_2="Yabani arı gözlemleri: iNaturalist (Anthophila, Berlin, 17 Kasım 2026 dışa aktarım), kayıt bazında lisans; GBIF.org (17 Kasım 2026) <a href=\"https://doi.org/10.15468/dl.w965pw\">doi:10.15468/dl.w965pw</a>, CC BY-NC 4.0.",
  r_3="Binalar ve duraklar: © OpenStreetMap katkıcıları, ODbL. Altlık © CARTO.",
  r_4="Yöntem: McRae, B. H. vd. (2008) Ecology 89: 2712–2724 (devre teorisi). Saura, S. vd. (2011) Ecol. Indicators 11: 407–416 (eşdeğer bağlantılı alan).",
  foot="Barış Parlatangiller · <a href=\"https://barisparlatangiller.github.io/\">30 haritanın tümü</a> · <a href=\"https://github.com/barisparlatangiller/30DMC26-D20-Hexagons-Berlin-Bee-Highways\">kod ve yöntem</a> · yapay zekâ desteğiyle hazırlandı (Claude, Anthropic)",
  other="index.html", otherL="EN"),
}

for lang, t in S.items():
    tr = lang == "tr"
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title>
<meta name="description" content="{t['desc']}">
<meta property="og:title" content="{t['h1']}">
<meta property="og:description" content="{t['desc']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<link href="style.css?v={V}" rel="stylesheet">
</head>
<body>
<div class="app">
  <main class="mapwrap">
    <div id="map"></div>
    <div class="card mapbar">
      <button class="pill" data-view="all">{t['vAll']}</button><button class="pill" data-view="feld">{t['vFeld']}</button>
      <button class="pill" data-view="hasen">{t['vHasen']}</button><button class="pill" data-view="top">{t['vTop']}</button>
      <a class="pill lang" href="{t['other']}">{t['otherL']}</a>
    </div>
    <div class="card legend">
      <h4>{t['legT']}</h4>
      <div class="lg"><svg width="46" height="18" viewBox="0 0 46 18"><polygon points="4,9 6.5,4.7 11.5,4.7 14,9 11.5,13.3 6.5,13.3" fill="#e8b03c"/><polygon points="18,9 22,2 30,2 34,9 30,16 22,16" fill="#e8b03c"/></svg><span>{t['leg1']}</span></div>
      <div class="lg"><i class="ramp"></i><span>{t['leg2']}</span></div>
      <div class="tk mono"><span>{t['none']}</span><span>{t['many']}</span></div>
      <div class="lg"><i class="dot" style="background:#3c2c18;width:8px;height:8px;margin-left:19px"></i><span>{t['leg5']}</span></div>
      <div class="lg"><svg width="46" height="18" viewBox="0 0 46 18"><polygon points="15,9 19,2 27,2 31,9 27,16 19,16" fill="none" stroke="#8a7ac4" stroke-width="2"/></svg><span>{t['leg3']}</span></div>
      <div class="lg"><svg width="46" height="18" viewBox="0 0 46 18"><polygon points="15,9 19,2 27,2 31,9 27,16 19,16" fill="#8a7ac4"/></svg><span>{t['leg4']}</span></div>
      <div class="lg"><i class="sw" style="background:linear-gradient(90deg,#e8e4dc,#d8e0bb,#93bb72)"></i><span>{t['lGround']}</span></div>
      <div class="lg"><i class="dot" style="background:#ecba46"></i><span>{t['lTreesE']}</span></div>
      <p class="zoomhint">{t['zoomH']}</p>
    </div>
    <div id="load" class="loading">{t['load']}</div>
  </main>
  <aside class="panel card">
    <p class="eyebrow">{t['eyebrow']}</p>
    <h1>{t['h1']}</h1>
    <p class="lede">{t['lede']}</p>
    <div class="stats">
      <div class="st"><b class="mono">{NUM(I7['largest_after'], tr)}</b><span>{t['s1']}</span></div>
      <div class="st"><b class="mono">{NUM(ST['obs_pilot'], tr)}</b><span>{t['s2']}</span></div>
      <div class="st"><b class="mono">{NUM(ST['trees'], tr)}</b><span>{t['s3']}</span></div>
    </div>
    <section class="block" id="detail" hidden></section>
    <section class="block">
      <h2 class="label">{t['bee']}</h2>
      <div class="seg" id="guild"><button data-g="small" class="on">{t['small']}<em>{t['smallE']}</em></button><button data-g="bumble">{t['bumble']}<em>{t['bumbleE']}</em></button></div>
      <div class="sl"><span>{t['month']}</span><input type="range" id="month" min="3" max="9" step="1" value="7"><b id="monthV">July</b></div>
      <div class="seg" id="ba"><button data-a="0" class="on">{t['before']}</button><button data-a="1">{t['after']}</button></div>
      <div id="isl"></div>
    </section>
    <section class="block">
      <h2 class="label">{t['layers']}</h2>
      <div class="toggles">
        <label><input type="checkbox" id="t_hex" checked><span>{t['lHex']}</span><em>{t['lHexE']}</em></label>
        <label><input type="checkbox" id="t_trees" checked><span>{t['lTrees']}</span><em>{t['lTreesE']}</em></label>
        <label><input type="checkbox" id="t_ground" checked><span>{t['lGround']}</span><em>{t['lGroundE']}</em></label>
        <label><input type="checkbox" id="t_bld" checked><span>{t['lBld']}</span><em>{t['lBldE']}</em></label>
        <label><input type="checkbox" id="t_obs" checked><span>{t['lObs']}</span><em>{t['lObsE']}</em></label>
        <label><input type="checkbox" id="t_stops" checked><span>{t['lStops']}</span><em>{t['lStopsE']}</em></label>
      </div>
      <div class="sl"><span>{t['hexop']}</span><input type="range" id="hop" min="0.2" max="1" step="0.02" value="0.85"><b id="hopV">85%</b></div>
    </section>
    <section class="block">
      <h2 class="label">{t['stopsT']}</h2>
      <ol class="stops" id="stops"></ol>
      <p class="hint">{t['stopsH']}</p>
    </section>
    <details class="howto" open><summary>{t['howto']}</summary><ol><li>{t['h_1']}</li><li>{t['h_2']}</li><li>{t['h_3']}</li><li>{t['h_4']}</li></ol></details>
    <details class="howto"><summary>{t['method']}</summary><p>{t['m_1']}</p><p>{t['m_2']}</p><p>{t['m_3']}</p></details>
    <details class="howto"><summary>{t['limits']}</summary><p>{t['l_1']}</p><p>{t['l_2']}</p></details>
    <details class="howto"><summary>{t['sources']}</summary><ol class="refs"><li>{t['r_1']}</li><li>{t['r_2']}</li><li>{t['r_3']}</li><li>{t['r_4']}</li></ol></details>
    <footer class="foot"><p>{t['foot']}</p></footer>
  </aside>
</div>
<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://cdn.jsdelivr.net/npm/deck.gl@9.0.38/dist.min.js"></script>
<script src="app.js?v={V}"></script>
</body>
</html>
"""
    Path("docs/" + ("index.html" if lang == "en" else "tr.html")).write_text(html)
print("ok")
