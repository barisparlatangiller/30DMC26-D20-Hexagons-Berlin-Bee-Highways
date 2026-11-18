/* Day 20 · Hexagons · Berlin — Bee highways: a floating honeycomb over a detailed city.
   Hex size = connection strength (circuit current), hex colour = wild-bee observations nearby. */
const TR = document.documentElement.lang === "tr";
const L = (en, tr) => (TR ? tr : en);
const $ = s => document.querySelector(s);
const fmt = (n, d = 0) => n.toLocaleString(TR ? "tr-TR" : "en-GB", { maximumFractionDigits: d, minimumFractionDigits: d });
const Q = new URLSearchParams(location.search);
const FILM = Q.has("film");
const MONTHS = TR ? ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"] : ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_L = TR ? ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"] : ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const S = { guild: "small", month: 7, after: false, hexOp: 0.85, show: { hex: true, trees: true, bld: true, obs: true, stops: true, ground: true }, sel: null };
window.S = S;

// palette: warm paper, greens for forage, honey for bees, violet for gaps
const HONEY = [[0, [252, 246, 228]], [1, [244, 214, 128]], [3, [232, 176, 60]], [8, [196, 128, 22]], [20, [140, 84, 10]]];
const GAP = [138, 122, 196];
function honey(n) {
  for (let i = 0; i < HONEY.length - 1; i++) { const [a, ca] = HONEY[i], [b, cb] = HONEY[i + 1];
    if (n <= b) { const t = (n - a) / (b - a); return ca.map((c, k) => Math.round(c + (cb[k] - c) * t)); } }
  return HONEY[HONEY.length - 1][1];
}
const FORAGE = ["interpolate", ["linear"], ["get", "forage"], 0, "#e8e4dc", 0.15, "#e4e2d2", 0.35, "#d8e0bb", 0.6, "#bcd39a", 0.85, "#93bb72", 1, "#7aa65d"];

let map, overlay, H, HV, TREES, TMETA, STOPS, OBS, ST;
const SCEN = () => (S.guild === "small" ? 0 : 7) + (S.month - 3) + (S.after ? 14 : 0);

async function load() {
  const j = u => fetch(u).then(r => r.json());
  [H, ST, TMETA, STOPS, OBS] = await Promise.all([j("data/hex.json"), j("data/stats.json"), j("data/trees_meta.json"), j("data/stops.json"), j("data/obs.json")]);
  HV = new Uint8Array(await fetch("data/hexv.bin").then(r => r.arrayBuffer()));
  const tb = new Float32Array(await fetch("data/trees.bin").then(r => r.arrayBuffer())); const n = tb.length / 7;
  TREES = { n, pos: new Float32Array(n * 3), sc: new Float32Array(n * 3), val: new Float32Array(n), mask: new Uint16Array(n), gen: new Uint16Array(n), lon: new Float32Array(n), lat: new Float32Array(n), crown: new Float32Array(n), h: new Float32Array(n), tpos: new Float32Array(n * 3), tsc: new Float32Array(n * 3) };
  for (let i = 0; i < n; i++) {
    const lon = tb[i * 7], lat = tb[i * 7 + 1], cr = tb[i * 7 + 2], h = tb[i * 7 + 3];
    TREES.lon[i] = lon; TREES.lat[i] = lat; TREES.crown[i] = cr; TREES.h[i] = h; TREES.val[i] = tb[i * 7 + 4]; TREES.mask[i] = tb[i * 7 + 5]; TREES.gen[i] = tb[i * 7 + 6];
    const r = cr / 2, ch = Math.max(2.5, Math.min(h * 0.6, h - 1.5));
    TREES.pos[i * 3] = lon; TREES.pos[i * 3 + 1] = lat; TREES.pos[i * 3 + 2] = h - ch / 2;
    TREES.sc[i * 3] = r; TREES.sc[i * 3 + 1] = r; TREES.sc[i * 3 + 2] = ch / 2;
    const th = h - ch + 0.8;                                                    // trunk up into the crown
    TREES.tpos[i * 3] = lon; TREES.tpos[i * 3 + 1] = lat; TREES.tpos[i * 3 + 2] = th / 2;
    TREES.tsc[i * 3] = Math.max(0.15, Math.min(0.5, 0.05 * cr + 0.08)); TREES.tsc[i * 3 + 2] = th / 2;
  }
  TREES.col = new Uint8Array(n * 4);
  // hex geometry helpers (flat-top hex, edge in metres → degrees)
  const lat0 = H.lat[0], KX = 111320 * Math.cos(lat0 * Math.PI / 180), KY = 110540;
  H.vx = [0, 1, 2, 3, 4, 5].map(k => Math.cos(k * Math.PI / 3) * H.edge / KX);
  H.vy = [0, 1, 2, 3, 4, 5].map(k => Math.sin(k * Math.PI / 3) * H.edge / KY);
  H.idx = Array.from({ length: H.n }, (_, i) => i);
  H.gapThr = [...H.gap].sort((a, b) => a - b)[Math.floor(H.n * 0.975)];                       // top 2.5% = missing links
}

function treeColours() {
  const bit = 1 << (S.month - 1), c = TREES.col;
  for (let i = 0; i < TREES.n; i++) {
    const on = TREES.mask[i] & bit, v = TREES.val[i];
    if (on && v >= 0.5) { c[i * 4] = 236; c[i * 4 + 1] = 186; c[i * 4 + 2] = 70; }                 // in bloom, good for bees: honey
    else if (on && v >= 0.25) { c[i * 4] = 200; c[i * 4 + 1] = 196; c[i * 4 + 2] = 104; }
    else { c[i * 4] = 104 + v * 30; c[i * 4 + 1] = 142 + v * 20; c[i * 4 + 2] = 92; }               // green
    c[i * 4 + 3] = 255;
  }
}

const SPHERE = (() => { const P = [], Nn = [], I = [], LA = 6, LO = 10;
  for (let a = 0; a <= LA; a++) { const t = Math.PI * a / LA; for (let o = 0; o <= LO; o++) { const f = 2 * Math.PI * o / LO, x = Math.sin(t) * Math.cos(f), y = Math.sin(t) * Math.sin(f), z = Math.cos(t); P.push(x, y, z); Nn.push(x, y, z); } }
  for (let a = 0; a < LA; a++) for (let o = 0; o < LO; o++) { const p = a * (LO + 1) + o, q = p + LO + 1; I.push(p, q, p + 1, q, q + 1, p + 1); }
  return { attributes: { positions: { value: new Float32Array(P), size: 3 }, normals: { value: new Float32Array(Nn), size: 3 } }, indices: { value: new Uint16Array(I), size: 1 } }; })();

// two scales: zoomed out the honeycomb lies flat on the ground as a heat map of bee links; zoomed in it fades away and
// the detailed city (every tree with its trunk, every building, every biotope) takes over
const Z_HEX = [14.4, 15.3];                       // hex opacity 1 → 0 between these zooms
const HEAT = [[0.3, [247, 236, 210]], [0.55, [241, 204, 110]], [0.8, [222, 156, 46]], [1, [166, 98, 14]]];
function heat(v) { for (let i = 0; i < HEAT.length - 1; i++) { const [a, ca] = HEAT[i], [b, cb] = HEAT[i + 1];
  if (v <= b) { const t = Math.max(0, (v - a) / (b - a)); return ca.map((c, k) => Math.round(c + (cb[k] - c) * t)); } } return HEAT[HEAT.length - 1][1]; }
function hexFade(z) { return Math.max(0, Math.min(1, (Z_HEX[1] - z) / (Z_HEX[1] - Z_HEX[0]))); }
function cityFade(z) { return Math.max(0, Math.min(1, (z - Z_HEX[0]) / (Z_HEX[1] - Z_HEX[0]))); }
function hexPoly(i, s) {
  const lon = H.lon[i], lat = H.lat[i], P = [];
  for (let k = 0; k < 6; k++) P.push([lon + H.vx[k] * s, lat + H.vy[k] * s]);
  return P;
}
function hexScale(v) { return v < 0.3 ? 0 : 0.35 + 0.6 * Math.pow((v - 0.3) / 0.7, 1.2); }
// newly joined to the largest flower network for small bees by the 25 bee stops (AFTER, April–September)
function joined(i) { if (!S.after || S.guild !== "small" || S.month < 4) return false; const m = String(S.month).padStart(2, "0"); return H.big1[m][i] && !H.big0[m][i]; }
function hexSize(i, k) { const v = HV[i * 28 + k] / 255; return joined(i) ? Math.max(hexScale(v), 0.8) : hexScale(v); }
const CYL = (() => { const P = [], Nn = [], I = [], n = 8;
  for (let k = 0; k <= n; k++) { const f = 2 * Math.PI * k / n, x = Math.cos(f), y = Math.sin(f); P.push(x, y, -1, x, y, 1); Nn.push(x, y, 0, x, y, 0); }
  for (let k = 0; k < n; k++) { const a = 2 * k; I.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  return { attributes: { positions: { value: new Float32Array(P), size: 3 }, normals: { value: new Float32Array(Nn), size: 3 } }, indices: { value: new Uint16Array(I), size: 1 } }; })();

function layers() {
  const L_ = [], k = SCEN(), z = map ? map.getZoom() : 14, hf = hexFade(z), cf = cityFade(z);
  if (S.show.trees && cf > 0.01) {
    L_.push(new deck.SimpleMeshLayer({ id: "trunks", data: { length: TREES.n, attributes: { getPosition: { value: TREES.tpos, size: 3 } } },
      getScale: (_, { index }) => [TREES.tsc[3 * index], TREES.tsc[3 * index], TREES.tsc[3 * index + 2]], mesh: CYL, getColor: [118, 92, 70, 255], opacity: cf,
      material: { ambient: 0.6, diffuse: 0.5, shininess: 0 } }));
    L_.push(new deck.SimpleMeshLayer({ id: "trees", data: { length: TREES.n, attributes: { getPosition: { value: TREES.pos, size: 3 }, getColor: { value: TREES.col, size: 4 } } },
      getScale: (_, { index }) => [TREES.sc[3 * index], TREES.sc[3 * index + 1], TREES.sc[3 * index + 2]], mesh: SPHERE, getOrientation: [0, 0, 0], opacity: cf,
      material: { ambient: 0.55, diffuse: 0.6, shininess: 8, specularColor: [30, 30, 30] }, pickable: true, autoHighlight: true, highlightColor: [138, 122, 196, 255],
      updateTriggers: { getColor: S.month } }));
  }
  if (S.show.hex && hf > 0.01) {
    L_.push(new deck.PolygonLayer({ id: "hex", data: H.idx, getPolygon: i => hexPoly(i, hexSize(i, k)), filled: true, stroked: false, opacity: hf,
      getFillColor: i => { const v = HV[i * 28 + k] / 255, j = joined(i); if (v < 0.3 && !j) return [0, 0, 0, 0];
        if (j) return [...GAP, Math.round(255 * S.hexOp)];
        return [...heat(v), Math.round(255 * S.hexOp * (0.6 + 0.4 * v))]; },
      pickable: true, autoHighlight: true, highlightColor: [138, 122, 196, 200],
      updateTriggers: { getPolygon: [k, S.after, S.month], getFillColor: [k, S.hexOp, S.after, S.month] } }));
    // missing links: violet rings where many bee paths cross poor ground
    L_.push(new deck.PolygonLayer({ id: "gaps", data: H.idx.filter(i => H.gap[i] >= H.gapThr), getPolygon: i => hexPoly(i, 0.95), filled: false, stroked: true, opacity: hf,
      getLineColor: [...GAP, 230], getLineWidth: 1.6, lineWidthUnits: "pixels" }));
  }
  if (S.show.obs) L_.push(new deck.ScatterplotLayer({ id: "obs", data: OBS, getPosition: d => [d.lon, d.lat, 1.5], getRadius: 6, radiusUnits: "meters", radiusMinPixels: 1.8, radiusMaxPixels: 6,
    getFillColor: [60, 44, 24, 220], stroked: true, getLineColor: [255, 255, 255, 200], lineWidthMinPixels: 0.8, pickable: true }));
  if (S.show.stops) {
    const ch = STOPS.filter(s => s.rank > 0);
    L_.push(new deck.ScatterplotLayer({ id: "stops", data: ch, getPosition: d => [d.lon, d.lat, 3], getRadius: 18, radiusUnits: "meters", radiusMinPixels: 9,
      filled: true, getFillColor: S.after ? [138, 122, 196, 240] : [255, 255, 255, 240], stroked: true, getLineColor: [138, 122, 196, 255], lineWidthMinPixels: 2.5, pickable: true,
      updateTriggers: { getFillColor: S.after } }));
    L_.push(new deck.TextLayer({ id: "stoplbl", data: ch, getPosition: d => [d.lon, d.lat, 3], getText: d => String(d.rank), getSize: 11, getColor: S.after ? [255, 255, 255, 255] : [90, 76, 160, 255],
      fontWeight: 700, fontFamily: "Inter, sans-serif", fontSettings: { sdf: true }, updateTriggers: { getColor: S.after } }));
  }
  return L_;
}
function redraw() { if (overlay) overlay.setProps({ layers: layers() }); }

function tip({ layer, object, index }) {
  if (!layer) return null;
  const st = { fontFamily: "Inter, sans-serif", fontSize: "12.5px", background: "rgba(255,253,248,.96)", color: "#2b2925", borderRadius: "10px", padding: "8px 10px", boxShadow: "0 4px 16px rgba(60,45,30,.18)", maxWidth: "260px" };
  if (layer.id === "trees") { const g = TMETA.genus[TREES.gen[index]], de = TMETA.de[TREES.gen[index]], v = TREES.val[index];
    const mon = []; for (let m = 1; m <= 12; m++) if (TREES.mask[index] & (1 << (m - 1))) mon.push(MONTHS[m]);
    return { text: `${de || g} (${g})\n${L("for bees", "arılar için")}: ${v >= 0.7 ? L("very good", "çok iyi") : v >= 0.4 ? L("good", "iyi") : v >= 0.2 ? L("some", "biraz") : L("little", "az")}${mon.length ? ` · ${L("flowers", "çiçek")} ${mon[0]}${mon.length > 1 ? "–" + mon[mon.length - 1] : ""}` : ""}\n${L("crown", "taç")} Ø ${TREES.crown[index].toFixed(0)} m · ${TREES.h[index].toFixed(0)} m`, style: st }; }
  if (layer.id === "obs" && object) return { text: `${object.t}\n${object.d} · ${object.s}`, style: st };
  if (layer.id === "stops" && object) return { text: `${L("Bee stop", "Arı durağı")} ${object.rank}\n${object.n || L("bus / tram stop", "otobüs / tramvay durağı")}`, style: st };
  if (layer.id === "hex" && object !== undefined && object !== null) { const i = object, v = HV[i * 28 + SCEN()] / 255;
    if (joined(i)) return { text: L("Joins the largest flower network for small bees, thanks to the bee stops", "Arı durakları sayesinde küçük arılar için en büyük çiçek ağına katılıyor"), style: st };
    return { text: `${L("Connection strength", "Bağlantı gücü")}: ${v >= 0.8 ? L("highway", "otoyol") : v >= 0.5 ? L("busy", "yoğun") : v >= 0.2 ? L("some", "biraz") : L("weak", "zayıf")} (${L("top", "ilk")} ${Math.max(1, Math.round((1 - v) * 100))}%)\n${L("Wild-bee records within 120 m", "120 m içinde yabani arı kaydı")}: ${H.obs[i]}${H.taxa[i] ? ` · ${H.taxa[i]} ${L("taxa", "takson")}` : ""}${H.gap[i] >= H.gapThr ? "\n" + L("Missing link: bee paths cross poor ground here", "Eksik halka: arı yolları burada fakir zeminden geçiyor") : ""}`, style: st }; }
  return null;
}

function ground() {
  const bb = ST.bbox;
  map.addSource("pilot", { type: "geojson", data: { type: "Feature", geometry: { type: "Polygon", coordinates: [[[bb[0][0], bb[0][1]], [bb[1][0], bb[0][1]], [bb[1][0], bb[1][1]], [bb[0][0], bb[1][1]], [bb[0][0], bb[0][1]]]] } } });
  map.addSource("bio", { type: "geojson", data: "data/biotopes.json" });
  map.addLayer({ id: "bio", type: "fill", source: "bio", paint: { "fill-color": FORAGE, "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.35, 14.4, 0.4, 15.3, 0.92] } });
  map.addLayer({ id: "bio-line", type: "line", source: "bio", minzoom: 14.5, paint: { "line-color": "#ffffff", "line-width": 0.5, "line-opacity": 0.6 } });
  map.addLayer({ id: "pilot-line", type: "line", source: "pilot", paint: { "line-color": "#8a7ac4", "line-width": 1.5, "line-dasharray": [3, 2] } });
  map.addSource("bld", { type: "geojson", data: "data/buildings.json" });
  map.addLayer({ id: "bld-flat", type: "fill", source: "bld", maxzoom: 15.3, paint: { "fill-color": "#e9e4da", "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.55, 15.3, 0] } });
  map.addLayer({ id: "bld", type: "fill-extrusion", source: "bld", minzoom: 14.4, paint: { "fill-extrusion-color": "#ece7de", "fill-extrusion-height": ["interpolate", ["linear"], ["zoom"], 14.4, 0, 15.3, ["get", "h"]], "fill-extrusion-opacity": 0.85, "fill-extrusion-vertical-gradient": true } });
}

function panel() {
  const I = ST.islands, m = String(S.month).padStart(2, "0"), d = I[m];
  $("#isl").innerHTML = d ? `<div class="isl"><span>${L("Largest connected flower network for small bees", "Küçük arılar için en büyük bağlantılı çiçek ağı")} · ${MONTHS_L[S.month]}</span>
    <b class="mono">${fmt(d.largest_before)} ha</b><i>→</i><b class="mono acc">${fmt(d.largest_after)} ha</b><em>${L("with 25 bee stops", "25 arı durağıyla")}</em></div>` : `<p class="hint">${L("In March almost nothing flowers yet; the bee stops start in April.", "Mart'ta henüz neredeyse hiçbir şey çiçek açmıyor; arı durakları Nisan'da başlıyor.")}</p>`;
  $("#monthV").textContent = MONTHS_L[S.month];
}

function init() {
  map = new maplibregl.Map({ container: "map", style: "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json", center: [13.425, 52.4655], zoom: 12.95, pitch: 48, bearing: -12, maxPitch: 75,
    attributionControl: false, preserveDrawingBuffer: FILM });
  if (!FILM && innerWidth > 760) map.setPadding({ left: 390, top: 40, right: 20, bottom: 0 });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "Biotoptypen, Versiegelung, Baumbestand © Berlin SenMVKU (dl-de/zero-2-0) · bees © iNaturalist / GBIF · © OSM · © CARTO" }), "bottom-right");
  overlay = new deck.MapboxOverlay({ interleaved: false, layers: [], getTooltip: tip });
  map.addControl(overlay);
  map.on("load", () => { ground(); treeColours(); redraw(); panel(); $("#load").classList.add("gone"); });
  let raf = 0;
  map.on("zoom", () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; redraw(); }); });
  map.on("click", e => { const f = map.queryRenderedFeatures(e.point, { layers: ["bio"] })[0]; if (!f) return;
    const p = f.properties; $("#detail").hidden = false;
    $("#detail").innerHTML = `<h3>${p.bt_name}</h3><div class="row"><span>${L("Flowers for bees (score)", "Arılar için çiçek (puan)")}</span><b class="mono">${(+p.forage).toFixed(2)}</b></div>
      <div class="row"><span>${L("Nesting ground (score)", "Yuva zemini (puan)")}</span><b class="mono">${(+p.nest).toFixed(2)}</b></div><div class="row"><span>${L("Rule", "Kural")}</span><b>${p.rule}</b></div>`; });
}

function ui() {
  document.querySelectorAll("#guild button").forEach(b => b.onclick = () => { document.querySelectorAll("#guild button").forEach(x => x.classList.toggle("on", x === b)); S.guild = b.dataset.g; redraw(); });
  document.querySelectorAll("#ba button").forEach(b => b.onclick = () => { document.querySelectorAll("#ba button").forEach(x => x.classList.toggle("on", x === b)); S.after = b.dataset.a === "1"; redraw(); });
  $("#month").oninput = e => { S.month = +e.target.value; treeColours(); redraw(); panel(); };
  for (const k of Object.keys(S.show)) { const el = $("#t_" + k); if (el) el.onchange = e => { S.show[k] = e.target.checked;
    if (k === "bld") ["bld", "bld-flat"].forEach(l => map.setLayoutProperty(l, "visibility", e.target.checked ? "visible" : "none"));
    else if (k === "ground") map.setLayoutProperty("bio", "visibility", e.target.checked ? "visible" : "none");
    else redraw(); }; }
  $("#hop").oninput = e => { S.hexOp = +e.target.value; $("#hopV").textContent = Math.round(S.hexOp * 100) + "%"; redraw(); };
  $("#stops").innerHTML = STOPS.filter(s => s.rank > 0).sort((a, b) => a.rank - b.rank).map(s => `<li data-r="${s.rank}"><b class="mono">${s.rank}</b><span>${s.n || L("stop", "durak")}</span></li>`).join("");
  $("#stops").querySelectorAll("li").forEach(li => li.onclick = () => { const s = STOPS.find(x => x.rank === +li.dataset.r); map.flyTo({ center: [s.lon, s.lat], zoom: 16.3, pitch: 58, duration: 1600 }); });
  document.querySelectorAll("[data-view]").forEach(b => b.onclick = () => {
    const v = { all: { center: [13.425, 52.4655], zoom: 12.95, pitch: 48, bearing: -12 }, feld: { center: [13.402, 52.474], zoom: 14.6, pitch: 60, bearing: 20 }, hasen: { center: [13.418, 52.484], zoom: 15.6, pitch: 60, bearing: -25 },
      top: { center: [13.425, 52.4655], zoom: 13.1, pitch: 0, bearing: 0 } }[b.dataset.view]; map.flyTo({ ...v, duration: 1800 }); });
}

(async () => {
  await load();
  init(); ui();
  window.Film = { map, S, redraw, treeColours, panel, ready: () => map.loaded() };
})();
