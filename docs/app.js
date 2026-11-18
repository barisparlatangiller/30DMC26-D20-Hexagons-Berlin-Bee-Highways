/* Day 20 · Hexagons · Berlin — Bee highways: the missing links.
   One map: flower islands (hexagons, one colour = one network a small wild bee can use), bee highways (strongest current
   corridors, with bees flowing along them), the missing links and four kinds of additions that join islands live
   (union-find in the browser). A story mode walks through it, partly from a bee's height. */
const TR = document.documentElement.lang === "tr";
const L = (en, tr) => (TR ? tr : en);
const $ = s => document.querySelector(s);
const fmt = (n, d = 0) => n.toLocaleString(TR ? "tr-TR" : "en-GB", { maximumFractionDigits: d, minimumFractionDigits: d });
const Q = new URLSearchParams(location.search);
const FILM = Q.has("film");
const MON = TR ? ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"] : ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const MS = TR ? ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"] : ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const KINDS = {
  stops: { c: [138, 122, 196], en: "Bus & tram stops", tr: "Otobüs ve tramvay durakları", ic: "stop" },
  treepits: { c: [79, 143, 90], en: "Tree pits", tr: "Ağaç dipleri", ic: "tree" },
  schools: { c: [91, 134, 196], en: "School & nursery yards", tr: "Okul ve kreş bahçeleri", ic: "school" },
  parking: { c: [150, 132, 110], en: "Car-park edges", tr: "Otopark kenarları", ic: "park" } };
const FLOWERS = {
  meadow: { c: "#9cc46a", en: "Meadows & dry grassland", tr: "Çayırlar ve kuru çimenler" },
  garden: { c: "#bcd07e", en: "Gardens & allotments", tr: "Bahçeler ve hobi bahçeleri" },
  park: { c: "#a8c59a", en: "Parks, cemeteries, woods", tr: "Parklar, mezarlıklar, korular" },
  yard: { c: "#d4dcb6", en: "Green courtyards", tr: "Yeşil iç avlular" },
  lawn: { c: "#dfe3cc", en: "Mown lawns", tr: "Biçilmiş çimler" } };
const HONEY = [220, 154, 44];
const PAL = [[127, 167, 184], [165, 140, 191], [143, 176, 138], [201, 154, 138], [159, 165, 201], [184, 176, 122], [134, 181, 168], [190, 150, 175]];

const S = { month: 7, guild: "small", add: { stops: false, treepits: false, schools: false, parking: false },
  show: { islands: true, highways: true, flow: true, bridges: true, records: false, hidden: false, trees: true, bld: true, adds: true },
  flowers: { meadow: true, garden: true, park: true, yard: true, lawn: true }, focus: -1, t: 0, story: !FILM && !Q.has("explore") };
window.S = S;

let map, overlay, H, HISL, IV, HW, TREES, TMETA, OBS, ST;
const MI = () => S.month - 4;                                  // month index in hexisl / interventions (April–September)

async function load() {
  const j = u => fetch(u).then(r => r.json());
  [H, ST, TMETA, OBS, IV, HW] = await Promise.all([j("data/hex.json"), j("data/stats.json"), j("data/trees_meta.json"), j("data/obs.json"), j("data/interventions.json"), j("data/highways.json")]);
  HISL = new Uint16Array(await fetch("data/hexisl.bin").then(r => r.arrayBuffer()));
  const tb = new Float32Array(await fetch("data/trees.bin").then(r => r.arrayBuffer())), n = tb.length / 7;
  TREES = { n, pos: new Float32Array(n * 3), sc: new Float32Array(n * 3), tpos: new Float32Array(n * 3), tsc: new Float32Array(n * 3), val: new Float32Array(n), mask: new Uint16Array(n), gen: new Uint16Array(n), crown: new Float32Array(n), h: new Float32Array(n), col: new Uint8Array(n * 4) };
  for (let i = 0; i < n; i++) {
    const lon = tb[i * 7], lat = tb[i * 7 + 1], cr = tb[i * 7 + 2], h = tb[i * 7 + 3], r = cr / 2, ch = Math.max(2.5, Math.min(h * 0.6, h - 1.5)), th = h - ch + 0.8;
    TREES.crown[i] = cr; TREES.h[i] = h; TREES.val[i] = tb[i * 7 + 4]; TREES.mask[i] = tb[i * 7 + 5]; TREES.gen[i] = tb[i * 7 + 6];
    TREES.pos.set([lon, lat, h - ch / 2], i * 3); TREES.sc.set([r, r, ch / 2], i * 3);
    TREES.tpos.set([lon, lat, th / 2], i * 3); TREES.tsc.set([Math.max(0.15, Math.min(0.5, 0.05 * cr + 0.08)), 0, th / 2], i * 3);
  }
  const KX = 111320 * Math.cos(H.lat[0] * Math.PI / 180), KY = 110540;
  H.vx = [0, 1, 2, 3, 4, 5].map(k => Math.cos(k * Math.PI / 3) * H.edge * 0.93 / KX);
  H.vy = [0, 1, 2, 3, 4, 5].map(k => Math.sin(k * Math.PI / 3) * H.edge * 0.93 / KY);
  // bee trips along the highways (one set per guild × month)
  HW.trips = {};
}

// ---------- islands: union-find over the chosen additions ----------
let NET = null;
function network() {
  const m = IV.months[MI()], A = IV.area[m], par = new Int32Array(A.length).map((_, i) => i);
  const find = i => { while (par[i] !== i) { par[i] = par[par[i]]; i = par[i]; } return i; };
  for (const k in S.add) if (S.add[k]) for (const p of IV.picks[k]) { const r = p.reach[m].map(find); for (let q = 1; q < r.length; q++) par[find(r[q])] = find(r[0]); }
  const tot = new Float64Array(A.length);
  for (let i = 1; i < A.length; i++) tot[find(i)] += A[i];
  let big = 0; for (let i = 1; i < A.length; i++) if (tot[i] > tot[big]) big = i;
  const root = new Int32Array(A.length); for (let i = 0; i < A.length; i++) root[i] = find(i);
  const base = IV.combos.none[m];
  const n = new Set(Array.from(root.slice(1)).filter((r, i) => A[i + 1] > 0)).size;
  NET = { m, root, tot, big, largest: tot[big], base, n };
  return NET;
}
function islandColour(isl) {
  const r = NET.root[isl], a = NET.tot[r];
  if (r === NET.big) return HONEY;
  if (a < 3) return [214, 208, 194];
  return PAL[r % PAL.length];
}

// ---------- trees ----------
function treeColours() {
  const bit = 1 << (S.month - 1), c = TREES.col;
  for (let i = 0; i < TREES.n; i++) {
    const on = TREES.mask[i] & bit, v = TREES.val[i];
    if (on && v >= 0.5) c.set([236, 186, 70, 255], i * 4);
    else if (on && v >= 0.25) c.set([200, 196, 104, 255], i * 4);
    else c.set([104 + v * 30, 142 + v * 20, 92, 255], i * 4);
  }
}
const SPHERE = (() => { const P = [], I = [], LA = 6, LO = 10;
  for (let a = 0; a <= LA; a++) { const t = Math.PI * a / LA; for (let o = 0; o <= LO; o++) { const f = 2 * Math.PI * o / LO; P.push(Math.sin(t) * Math.cos(f), Math.sin(t) * Math.sin(f), Math.cos(t)); } }
  for (let a = 0; a < LA; a++) for (let o = 0; o < LO; o++) { const p = a * (LO + 1) + o, q = p + LO + 1; I.push(p, q, p + 1, q, q + 1, p + 1); }
  return { attributes: { positions: { value: new Float32Array(P), size: 3 }, normals: { value: new Float32Array(P), size: 3 } }, indices: { value: new Uint16Array(I), size: 1 } }; })();
const CYL = (() => { const P = [], N = [], I = [], n = 8;
  for (let k = 0; k <= n; k++) { const f = 2 * Math.PI * k / n, x = Math.cos(f), y = Math.sin(f); P.push(x, y, -1, x, y, 1); N.push(x, y, 0, x, y, 0); }
  for (let k = 0; k < n; k++) { const a = 2 * k; I.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  return { attributes: { positions: { value: new Float32Array(P), size: 3 }, normals: { value: new Float32Array(N), size: 3 } }, indices: { value: new Uint16Array(I), size: 1 } }; })();

// ---------- icons for the additions ----------
const svg = (body, col) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="rgb(${col})" stroke="white" stroke-width="5"/>${body}</svg>`);
const ICONS = {
  stop: c => svg(`<rect x="22" y="15" width="20" height="24" rx="4" fill="white"/><rect x="30" y="39" width="4" height="12" fill="white"/><rect x="26" y="20" width="12" height="7" rx="1.5" fill="rgb(${c})"/>`, c),
  tree: c => svg(`<circle cx="32" cy="27" r="13" fill="white"/><rect x="29.5" y="36" width="5" height="14" fill="white"/>`, c),
  school: c => svg(`<path d="M16 30 L32 17 L48 30 Z" fill="white"/><rect x="20" y="30" width="24" height="17" fill="white"/><rect x="29" y="37" width="6" height="10" fill="rgb(${c})"/>`, c),
  park: c => svg(`<text x="32" y="44" text-anchor="middle" font-family="Arial,sans-serif" font-weight="700" font-size="30" fill="white">P</text>`, c) };

// ---------- trips: bees flowing along the highways ----------
function trips(key) {
  if (HW.trips[key]) return HW.trips[key];
  const out = [], KX = 111320 * Math.cos(52.47 * Math.PI / 180), KY = 110540;
  for (const h of HW[key] || []) {
    const p = h.p, d = [0];
    for (let i = 1; i < p.length; i++) d.push(d[i - 1] + Math.hypot((p[i][0] - p[i - 1][0]) * KX, (p[i][1] - p[i - 1][1]) * KY));
    const n = 2 + Math.round(8 * h.s);
    for (let k = 0; k < n; k++) {
      const off = Math.random() * 3000, rev = k % 2 === 1;
      const path = rev ? [...p].reverse() : p, dd = rev ? d.map(x => d[d.length - 1] - x).reverse() : d;
      out.push({ path: path.map(q => [q[0], q[1], 7 + 5 * Math.random()]), ts: dd.map(x => off + x), s: h.s });
    }
  }
  return (HW.trips[key] = out);
}

// ---------- layers ----------
const MEMO = {};
const memo = (k, f) => { const t = k.slice(0, 3); if (MEMO[t] && MEMO[t].k === k) return MEMO[t].v; MEMO[t] = { k, v: f() }; return MEMO[t].v; };
const Z = [14.4, 15.4];
const cityF = z => Math.max(0, Math.min(1, (z - Z[0]) / (Z[1] - Z[0])));
function hexPoly(i) { const lon = H.lon[i], lat = H.lat[i], P = []; for (let k = 0; k < 6; k++) P.push([lon + H.vx[k], lat + H.vy[k]]); return P; }

function layers() {
  const L_ = [], z = map.getZoom(), cf = cityF(z), mi = MI(), key = `${S.guild}_${String(S.month).padStart(2, "0")}`;
  network();
  if (S.show.islands && S.month >= 4) {
    const data = memo("isl" + mi, () => { const d = []; for (let i = 0; i < H.n; i++) if (HISL[i * 6 + mi] > 0) d.push(i); return d; });
    L_.push(new deck.PolygonLayer({ id: "islands", data, getPolygon: hexPoly, stroked: false, opacity: 0.88 - 0.38 * cf,
      getFillColor: i => { const isl = HISL[i * 6 + mi], c = islandColour(isl), f = S.focus;
        const dim = f >= 0 && NET.root[isl] !== NET.root[f]; return [...c, dim ? 60 : 235]; },
      pickable: true, updateTriggers: { getFillColor: [mi, JSON.stringify(S.add), S.focus] } }));
  }
  if (S.show.highways) {
    L_.push(new deck.PathLayer({ id: "highways", data: HW[key] || [], getPath: d => d.p, getWidth: d => 5 + 16 * d.s, widthUnits: "meters", widthMinPixels: 1.5, widthMaxPixels: 14, capRounded: true, jointRounded: true,
      getColor: d => [150, 88, 14, Math.round(120 + 110 * d.s)], opacity: 0.85, updateTriggers: {} }));
    if (S.show.flow) L_.push(new deck.TripsLayer({ id: "flow", data: trips(key), getPath: d => d.path, getTimestamps: d => d.ts, getColor: [255, 238, 176], widthMinPixels: 3, widthUnits: "meters",
      getWidth: 4, trailLength: 140, currentTime: S.t % 3600, fadeTrail: true, capRounded: true, jointRounded: true, shadowEnabled: false }));
  }
  // possible bridges (thin) and built ones (strong), from every chosen place to the islands it joins
  if (S.show.bridges && S.month >= 4) {
    const m = IV.months[mi], seg = memo(`br${mi}${JSON.stringify(S.add)}${S.show.adds}`, () => { const o = [];
      for (const k in IV.picks) for (const p of IV.picks[k]) { const on = S.add[k]; if (!on && !S.show.adds) continue;
        for (const q of p.bridges[m] || []) o.push({ a: [p.lon, p.lat], b: q, on, k }); } return o; });
    L_.push(new deck.LineLayer({ id: "bridges", data: seg, getSourcePosition: d => d.a, getTargetPosition: d => d.b, getWidth: d => d.on ? 3.5 : 1.2, widthUnits: "pixels",
      getColor: d => d.on ? [...KINDS[d.k].c, 255] : [...KINDS[d.k].c, 120], updateTriggers: { getWidth: JSON.stringify(S.add), getColor: JSON.stringify(S.add) } }));
  }
  if (S.show.trees && cf > 0.01) {
    L_.push(new deck.SimpleMeshLayer({ id: "trunks", data: { length: TREES.n, attributes: { getPosition: { value: TREES.tpos, size: 3 } } },
      getScale: (_, { index: i }) => [TREES.tsc[3 * i], TREES.tsc[3 * i], TREES.tsc[3 * i + 2]], mesh: CYL, getColor: [118, 92, 70, 255], opacity: cf, material: { ambient: 0.6, diffuse: 0.5, shininess: 0 } }));
    L_.push(new deck.SimpleMeshLayer({ id: "trees", data: { length: TREES.n, attributes: { getPosition: { value: TREES.pos, size: 3 }, getColor: { value: TREES.col, size: 4 } } },
      getScale: (_, { index: i }) => [TREES.sc[3 * i], TREES.sc[3 * i + 1], TREES.sc[3 * i + 2]], mesh: SPHERE, opacity: cf,
      material: { ambient: 0.55, diffuse: 0.6, shininess: 8, specularColor: [30, 30, 30] }, pickable: true, updateTriggers: { getColor: S.month } }));
  }
  if (S.show.records || S.show.hidden) {
    const d = memo(`obs${S.show.records}${S.show.hidden}`, () => OBS.filter(o => (S.show.records && !o.h) || (S.show.hidden && o.h) || (S.show.records && !S.show.hidden && o.h)));
    L_.push(new deck.ScatterplotLayer({ id: "obs", data: d, getPosition: o => [o.lon, o.lat, 2], getRadius: 7, radiusUnits: "meters", radiusMinPixels: 3, radiusMaxPixels: 8,
      getFillColor: o => o.h && S.show.hidden ? [255, 255, 255, 240] : [60, 44, 24, 230], stroked: true, getLineColor: o => o.h && S.show.hidden ? [196, 92, 60, 255] : [255, 255, 255, 220],
      lineWidthMinPixels: o => 1.5, getLineWidth: 2, lineWidthUnits: "pixels", pickable: true, updateTriggers: { getFillColor: S.show.hidden, getLineColor: S.show.hidden } }));
  }
  if (S.month >= 4) {
    const icons = memo(`ic${JSON.stringify(S.add)}${S.show.adds}`, () => { const o = []; for (const k in IV.picks) if (S.add[k] || S.show.adds) for (const p of IV.picks[k]) o.push({ ...p, k, on: S.add[k] }); return o; });
    L_.push(new deck.IconLayer({ id: "adds", data: icons, getPosition: d => [d.lon, d.lat, 4], getIcon: d => ({ url: ICONS[KINDS[d.k].ic](KINDS[d.k].c.join(",")), width: 64, height: 64, id: d.k }),
      getSize: d => d.on ? 30 : 17, sizeUnits: "pixels", getColor: d => [255, 255, 255, d.on ? 255 : 150], pickable: true, updateTriggers: { getSize: JSON.stringify(S.add), getColor: JSON.stringify(S.add) } }));
  }
  return L_;
}
function redraw() { if (overlay) overlay.setProps({ layers: layers() }); kpi(); }

// ---------- tooltips ----------
function tip({ layer, object, index }) {
  if (!layer) return null;
  const st = { fontFamily: "Inter, sans-serif", fontSize: "12.5px", background: "rgba(255,253,248,.97)", color: "#2b2925", borderRadius: "10px", padding: "8px 10px", boxShadow: "0 4px 16px rgba(60,45,30,.18)", maxWidth: "270px", whiteSpace: "pre-line" };
  if (layer.id === "islands" && object != null) { const isl = HISL[object * 6 + MI()], r = NET.root[isl];
    return { text: `${r === NET.big ? L("Largest flower network", "En büyük çiçek ağı") : L("Flower island", "Çiçek adası")}: ${fmt(NET.tot[r])} ha\n${L("A small wild bee can travel anywhere in this colour without a gap over 100 m.", "Küçük bir yabani arı bu renkteki her yere 100 m'den büyük boşluk olmadan gidebilir.")}\n${L("Click to see only this network.", "Yalnızca bu ağı görmek için tıklayın.")}`, style: st }; }
  if (layer.id === "trees") { const g = TMETA.genus[TREES.gen[index]], de = TMETA.de[TREES.gen[index]], v = TREES.val[index]; const mon = []; for (let m = 1; m <= 12; m++) if (TREES.mask[index] & (1 << (m - 1))) mon.push(MS[m]);
    return { text: `${de || g} (${g})\n${L("for bees", "arılar için")}: ${v >= 0.7 ? L("very good", "çok iyi") : v >= 0.4 ? L("good", "iyi") : v >= 0.2 ? L("some", "biraz") : L("little", "az")}${mon.length ? ` · ${L("flowers", "çiçek")} ${mon[0]}${mon.length > 1 ? "–" + mon[mon.length - 1] : ""}` : ""}`, style: st }; }
  if (layer.id === "obs" && object) return { text: `${object.t}\n${object.d} · ${object.s}${object.h ? "\n" + L("Seen where the biotope map shows few flowers", "Biyotop haritasının az çiçek gösterdiği yerde görüldü") : ""}`, style: st };
  if (layer.id === "adds" && object) return { text: `${L(KINDS[object.k].en, KINDS[object.k].tr)} · ${object.rank}\n${object.name || ""}\n${L("A 30 m × 30 m flower bed here joins", "Buraya 30 m × 30 m'lik bir çiçek yatağı")} ${object.reach[IV.months[MI()]].length} ${L("flower islands", "çiçek adasını birleştirir")}`, style: st };
  if (layer.id === "highways" && object) return { text: `${L("Bee highway", "Arı otoyolu")}: ${object.s >= 0.6 ? L("very busy", "çok yoğun") : object.s >= 0.35 ? L("busy", "yoğun") : L("used", "kullanılıyor")}\n${L("Where the model sends the most flower-to-flower trips", "Modelin en çok çiçekten çiçeğe yolculuğu geçirdiği yer")}`, style: st };
  return null;
}

// ---------- ground ----------
function ground() {
  map.addSource("bio", { type: "geojson", data: "data/biotopes.json" });
  const colour = ["match", ["get", "cat"], ...Object.entries(FLOWERS).flatMap(([k, v]) => [k, v.c]), "water", "#cfe0e6", "#ece8e0"];
  map.addLayer({ id: "bio", type: "fill", source: "bio", paint: { "fill-color": colour, "fill-opacity": ["interpolate", ["linear"], ["zoom"], 12, 0.55, 15, 0.95] } });
  map.addLayer({ id: "bio-line", type: "line", source: "bio", minzoom: 15, paint: { "line-color": "#ffffff", "line-width": 0.6, "line-opacity": 0.7 } });
  const bb = ST.bbox;
  map.addSource("pilot", { type: "geojson", data: { type: "Feature", geometry: { type: "Polygon", coordinates: [[[bb[0][0], bb[0][1]], [bb[1][0], bb[0][1]], [bb[1][0], bb[1][1]], [bb[0][0], bb[1][1]], [bb[0][0], bb[0][1]]]] } } });
  map.addLayer({ id: "pilot-line", type: "line", source: "pilot", paint: { "line-color": "#8a7ac4", "line-width": 1.2, "line-dasharray": [3, 2] } });
  map.addSource("bld", { type: "geojson", data: "data/buildings.json" });
  map.addLayer({ id: "bld-flat", type: "fill", source: "bld", maxzoom: Z[1], paint: { "fill-color": "#e4dfd5", "fill-opacity": 0.7 } });
  map.addLayer({ id: "bld", type: "fill-extrusion", source: "bld", minzoom: Z[0], paint: { "fill-extrusion-color": "#efeae1", "fill-extrusion-height": ["interpolate", ["linear"], ["zoom"], Z[0], 0, Z[1], ["get", "h"]], "fill-extrusion-opacity": 0.86, "fill-extrusion-vertical-gradient": true } });
  applyFlowers();
}
function applyFlowers() {
  const on = Object.keys(S.flowers).filter(k => S.flowers[k]);
  map.setFilter("bio", ["any", ["!", ["in", ["get", "cat"], ["literal", Object.keys(FLOWERS)]]], ["in", ["get", "cat"], ["literal", on]]]);
}

// ---------- panel ----------
function kpi() {
  if (!NET || !$("#kpi")) return;
  const gain = NET.largest - NET.base, mo = S.month;
  $("#kpi").innerHTML = S.month < 4 ? `<p class="hint">${L("In March almost nothing flowers yet.", "Mart'ta henüz neredeyse hiçbir şey çiçek açmıyor.")}</p>` :
    `<div class="k"><span>${L("Largest flower network for small wild bees", "Küçük yabani arılar için en büyük çiçek ağı")} · ${MON[mo]}</span><b class="mono">${fmt(NET.largest)} ha</b>
     <em>${gain > 0.5 ? `<i class="up">+${fmt(gain)} ha</i> ${L("with the additions", "eklemelerle")}` : L("today", "bugün")} · ${fmt(NET.n)} ${L("separate islands", "ayrı ada")}</em></div>`;
  for (const k in KINDS) { const el = $(`#g_${k}`); if (el) el.textContent = `+${fmt(Math.max(0, IV.combos[k][IV.months[MI()]] - NET.base))} ha`; }
  $("#monthV").textContent = MON[mo];
}
function panelUI() {
  $("#flowers").innerHTML = Object.entries(FLOWERS).map(([k, v]) => `<label><input type="checkbox" data-f="${k}" checked><i class="sw" style="background:${v.c}"></i><span>${L(v.en, v.tr)}</span></label>`).join("");
  $("#adds").innerHTML = Object.entries(KINDS).map(([k, v]) => `<label class="add"><input type="checkbox" data-a="${k}"><img src="${ICONS[v.ic](v.c.join(","))}" alt=""><span>${L(v.en, v.tr)}<em>${L("25 best places", "en iyi 25 yer")}</em></span><b class="mono" id="g_${k}"></b></label>`).join("");
  document.querySelectorAll("[data-f]").forEach(el => el.onchange = () => { S.flowers[el.dataset.f] = el.checked; applyFlowers(); });
  document.querySelectorAll("[data-a]").forEach(el => el.onchange = () => { S.add[el.dataset.a] = el.checked; redraw(); });
  document.querySelectorAll("[data-s]").forEach(el => el.onchange = () => { S.show[el.dataset.s] = el.checked;
    if (el.dataset.s === "bld") ["bld", "bld-flat"].forEach(l => map.setLayoutProperty(l, "visibility", el.checked ? "visible" : "none")); redraw(); });
  $("#month").oninput = e => { S.month = +e.target.value; treeColours(); redraw(); };
  document.querySelectorAll("#guild button").forEach(b => b.onclick = () => { document.querySelectorAll("#guild button").forEach(x => x.classList.toggle("on", x === b)); S.guild = b.dataset.g; redraw(); });
}
function syncPanel() {
  document.querySelectorAll("[data-a]").forEach(el => el.checked = S.add[el.dataset.a]);
  document.querySelectorAll("[data-s]").forEach(el => el.checked = S.show[el.dataset.s]);
  $("#month").value = S.month;
}

// ---------- camera along a highway: a bee's-eye flight ----------
let flight = null;
function beeFlight(path, sec = 22) {
  const KX = 111320 * Math.cos(52.47 * Math.PI / 180), KY = 110540, d = [0];
  for (let i = 1; i < path.length; i++) d.push(d[i - 1] + Math.hypot((path[i][0] - path[i - 1][0]) * KX, (path[i][1] - path[i - 1][1]) * KY));
  const T = d[d.length - 1], t0 = performance.now(), id = {};
  flight = id;
  const at = s => { let i = 1; while (i < d.length - 1 && d[i] < s) i++; const f = (s - d[i - 1]) / Math.max(1e-6, d[i] - d[i - 1]);
    return [path[i - 1][0] + (path[i][0] - path[i - 1][0]) * f, path[i - 1][1] + (path[i][1] - path[i - 1][1]) * f]; };
  const step = () => { if (flight !== id) return; const u = Math.min(1, (performance.now() - t0) / (sec * 1000)), s = u * T;
    const a = at(s), b = at(Math.min(T, s + 90)), br = Math.atan2((b[0] - a[0]) * KX, (b[1] - a[1]) * KY) * 180 / Math.PI;
    const cur = map.getBearing(), nb = cur + ((((br - cur) % 360) + 540) % 360 - 180) * 0.06;
    map.jumpTo({ center: a, bearing: nb, pitch: 72, zoom: 17.6 });
    if (u < 1) requestAnimationFrame(step); };
  map.jumpTo({ center: path[0], zoom: 17.4, pitch: 74 }); requestAnimationFrame(step);
}
const stopFlight = () => { flight = null; };

// ---------- story ----------
function bestPath(key, near) {
  let best = null, bs = -1;
  for (const h of HW[key] || []) { const m = h.p[Math.floor(h.p.length / 2)]; const d = Math.hypot(m[0] - near[0], (m[1] - near[1]) * 1.6);
    const sc = h.len * (0.4 + h.s) / (1 + d * 3000); if (sc > bs) { bs = sc; best = h; } }
  return best ? best.p : null;
}
const VIEW = { city: { center: [13.425, 52.4655], zoom: 12.75, pitch: 35, bearing: -10 }, flat: { center: [13.425, 52.4655], zoom: 12.85, pitch: 0, bearing: 0 },
  hasen: { center: [13.418, 52.4845], zoom: 15.0, pitch: 55, bearing: -20 }, south: { center: [13.437, 52.457], zoom: 13.9, pitch: 45, bearing: -15 } };
function steps() {
  const c = IV.combos, b7 = c.none["07"], obsH = OBS.filter(o => o.h).length;
  return [
    { kick: L("#30DayMapChallenge · Day 20 · Hexagons", "#30DayMapChallenge · Gün 20 · Altıgenler"), title: L("Can a wild bee cross Neukölln?", "Bir yabani arı Neukölln'ü geçebilir mi?"),
      text: L(`Between Tempelhofer Feld, Hasenheide and Neukölln, every flower patch, all ${fmt(ST.trees)} street and park trees and every building are on this map. Most wild bees fly only a few hundred metres. Can they get from flower to flower?`,
        `Tempelhofer Feld, Hasenheide ve Neukölln arasında her çiçek alanı, ${fmt(ST.trees)} sokak ve park ağacının hepsi ve her bina bu haritada. Çoğu yabani arı yalnızca birkaç yüz metre uçar. Çiçekten çiçeğe gidebiliyorlar mı?`),
      btn: L("Start", "Başla"), cam: VIEW.city, set: { islands: false, highways: false, bridges: false, adds: false, records: false, hidden: false }, add: {} },
    { kick: L("1 · The flowers", "1 · Çiçekler"), title: L("Where bees find food.", "Arılar besini nerede buluyor?"), key: "flowers",
      text: L("Meadows and dry grassland (Tempelhofer Feld), gardens and allotments, parks and cemeteries, green courtyards. Lime, maple and black locust add flowers along the streets, each in its own month.",
        "Çayırlar ve kuru çimenler (Tempelhofer Feld), bahçeler ve hobi bahçeleri, parklar ve mezarlıklar, yeşil iç avlular. Ihlamur, akçaağaç ve akasya sokaklara kendi aylarında çiçek ekler."),
      cam: VIEW.city, set: { islands: false, highways: false, bridges: false, adds: false } },
    { kick: L("2 · Through a bee's eyes", "2 · Bir arının gözünden"), title: L("July, along a bee highway.", "Temmuz, bir arı otoyolu boyunca."), key: "flow",
      text: L("Flying low along one of the busiest bee highways, between allotments and street trees in Tempelhof. Lime trees are in flower (honey); the light streaks are bees moving along the model's flower-to-flower routes.",
        "Tempelhof'ta hobi bahçeleri ve sokak ağaçları arasında, en yoğun arı otoyollarından birinin üzerinde alçaktan uçuyoruz. Ihlamurlar çiçekte (bal rengi); açık renkli izler modelin çiçekten çiçeğe rotalarında ilerleyen arılar."),
      fly: [13.4079, 52.4531], set: { islands: false, highways: true, flow: true, bridges: false, adds: false } },
    { kick: L("3 · Flower islands", "3 · Çiçek adaları"), title: L(`${fmt(ST.islands_n["07"])} islands in July.`, `Temmuz'da ${fmt(ST.islands_n["07"])} ada.`), key: "islands",
      text: L(`One colour is one network a small solitary bee can use without a gap of more than 100 m. The largest (honey) is <b>${fmt(b7)} ha</b>. Everything else is cut off for small bees.`,
        `Bir renk, küçük bir yalnız arının 100 m'den büyük boşluk olmadan kullanabildiği bir ağdır. En büyüğü (bal rengi) <b>${fmt(b7)} ha</b>. Geri kalan her şey küçük arılar için kopuk.`),
      cam: VIEW.flat, set: { islands: true, highways: false, bridges: false, adds: false } },
    { kick: L("4 · Bee highways", "4 · Arı otoyolları"), title: L("Where the traffic flows.", "Trafiğin aktığı yerler."), key: "flow",
      text: L("The model links thousands of flower pairs through a grid of resistors: sealed ground and tall buildings slow a bee down. The thick lines carry the most trips.",
        "Model binlerce çiçek çiftini bir direnç ağı üzerinden bağlar: kaplı zemin ve yüksek binalar arıyı yavaşlatır. Kalın çizgiler en çok yolculuğu taşıyor."),
      cam: VIEW.city, set: { islands: true, highways: true, flow: true, bridges: false, adds: false } },
    { kick: L("5 · The missing links", "5 · Eksik halkalar"), title: L("Small gaps, big effect.", "Küçük boşluklar, büyük etki."), key: "bridges",
      text: L("Thin lines show places where one small flower bed would bridge two or more islands: bus stops, tree pits, school yards and car parks, the 25 best of each.",
        "İnce çizgiler, tek bir küçük çiçek yatağının iki ya da daha fazla adayı birleştireceği yerleri gösteriyor: otobüs durakları, ağaç dipleri, okul bahçeleri ve otoparklar, her birinin en iyi 25'i."),
      cam: VIEW.south, set: { islands: true, highways: false, bridges: true, adds: true } },
    { kick: L("6 · What if: bus stops", "6 · Ya olursa: otobüs durakları"), title: L(`25 flowering stops: ${fmt(b7)} → ${fmt(c.stops["07"])} ha.`, `25 çiçekli durak: ${fmt(b7)} → ${fmt(c.stops["07"])} ha.`), key: "adds",
      text: L("A nice idea, but stops are often on wide, sealed streets: they join only a few islands.", "Güzel bir fikir, ama duraklar çoğu zaman geniş ve kaplı caddelerde: yalnızca birkaç adayı birleştiriyorlar."),
      cam: VIEW.city, set: { islands: true, highways: false, bridges: true, adds: false }, add: { stops: true } },
    { kick: L("7 · What if: tree pits", "7 · Ya olursa: ağaç dipleri"), title: L(`25 tree pits in flower: ${fmt(b7)} → ${fmt(c.treepits["07"])} ha.`, `Çiçekli 25 ağaç dibi: ${fmt(b7)} → ${fmt(c.treepits["07"])} ha.`), key: "adds",
      text: L("Street trees stand right in the gaps between courtyards and parks. Planting the soil around 25 of them joins the honey network across Neukölln.",
        "Sokak ağaçları tam avlular ve parklar arasındaki boşluklarda duruyor. 25 tanesinin dibindeki toprağı çiçeklendirmek bal rengi ağı Neukölln boyunca birleştiriyor."),
      cam: VIEW.city, set: { islands: true, highways: false, bridges: true, adds: false }, add: { treepits: true } },
    { kick: L("8 · Real bees", "8 · Gerçek arılar"), title: L(`${fmt(ST.obs_pilot)} wild-bee records.`, `${fmt(ST.obs_pilot)} yabani arı kaydı.`), key: "records",
      text: L(`${fmt(Math.round(obsH / ST.obs_pilot * 100))}% of them (white) are where the biotope map shows few flowers: balconies, front gardens, tree pits. The map misses the small flowers; the bees don't.`,
        `Bunların %${fmt(Math.round(obsH / ST.obs_pilot * 100))}'si (beyaz) biyotop haritasının az çiçek gösterdiği yerlerde: balkonlar, ön bahçeler, ağaç dipleri. Harita küçük çiçekleri kaçırıyor; arılar kaçırmıyor.`),
      cam: VIEW.city, set: { islands: true, highways: false, bridges: false, adds: false, records: true, hidden: true }, add: {} },
    { kick: L("Your turn", "Sıra sizde"), title: L("Add flowers. See islands join.", "Çiçek ekleyin. Adaların birleştiğini görün."), key: "adds",
      text: L("Switch the additions on and off, slide through the months, click an island to see only its network. Zoom in for every tree and building.",
        "Eklemeleri açıp kapatın, ayları değiştirin, yalnızca ağını görmek için bir adaya tıklayın. Her ağaç ve bina için yakınlaşın."),
      btn: L("Explore the map", "Haritayı keşfet"), cam: VIEW.city, set: { islands: true, highways: true, flow: true, bridges: true, adds: true, records: false, hidden: false }, add: {} },
  ];
}
const KEYS = {
  flowers: () => Object.values(FLOWERS).slice(0, 4).map(v => `<span><i style="background:${v.c}"></i>${L(v.en, v.tr)}</span>`).join("") + `<span><i style="background:#ecba46;border-radius:50%"></i>${L("tree in flower", "çiçekteki ağaç")}</span>`,
  flow: () => `<span><i style="background:#96580e;height:5px;width:18px;border-radius:3px"></i>${L("bee highway", "arı otoyolu")}</span><span><i style="background:#ffeca8;height:4px;width:18px;border-radius:3px;box-shadow:0 0 0 1px #d9a640"></i>${L("bees moving", "hareket eden arılar")}</span>`,
  islands: () => `<span><i style="background:rgb(${HONEY})"></i>${L("largest network", "en büyük ağ")}</span><span><i style="background:rgb(${PAL[0]})"></i><i style="background:rgb(${PAL[1]});margin-left:-4px"></i>${L("separate islands", "ayrı adalar")}</span>`,
  bridges: () => Object.values(KINDS).map(v => `<span><img src="${ICONS[v.ic](v.c.join(","))}" alt="">${L(v.en, v.tr)}</span>`).join(""),
  adds: () => `<span><i style="background:rgb(${HONEY})"></i>${L("largest network", "en büyük ağ")}</span><span><i style="background:#8a7ac4;height:4px;width:18px;border-radius:2px"></i>${L("new bridge", "yeni köprü")}</span>`,
  records: () => `<span><i style="background:#3c2c18;border-radius:50%"></i>${L("record where the map shows flowers", "haritanın çiçek gösterdiği yerde kayıt")}</span><span><i style="background:#fff;border-radius:50%;box-shadow:0 0 0 2px #c45c3c"></i>${L("record where the map shows few flowers", "haritanın az çiçek gösterdiği yerde kayıt")}</span>`,
};
let STEPS, cur = -1;
function go(i) {
  STEPS = STEPS || steps();
  cur = Math.max(0, Math.min(STEPS.length - 1, i)); const s = STEPS[cur];
  stopFlight(); S.focus = -1; S.month = 7; S.guild = "small"; treeColours();
  Object.assign(S.show, { islands: true, highways: true, flow: true, bridges: true, adds: true, records: false, hidden: false }, s.set || {});
  S.add = { stops: false, treepits: false, schools: false, parking: false, ...(s.add || {}) };
  $("#s-kick").textContent = s.kick; $("#s-title").innerHTML = s.title; $("#s-text").innerHTML = s.text;
  $("#s-key").innerHTML = s.key ? KEYS[s.key]() : "";
  $("#s-next").textContent = s.btn || L("Next", "İleri"); $("#s-prev").disabled = cur === 0;
  document.querySelectorAll("#s-dots i").forEach((d, k) => d.classList.toggle("on", k === cur));
  if (s.fly) { const p = bestPath("small_07", s.fly); if (p) beeFlight(p); }
  else if (s.cam) map.flyTo({ ...s.cam, duration: 2600, essential: true });
  syncPanel(); redraw();
}
function setMode(story) {
  S.story = story; document.body.classList.toggle("story-on", story);
  $("#m-story").classList.toggle("on", story); $("#m-explore").classList.toggle("on", !story);
  if (story) go(cur < 0 ? 0 : cur); else { stopFlight(); S.add = { stops: false, treepits: false, schools: false, parking: false }; Object.assign(S.show, { islands: true, highways: true, flow: true, bridges: true, adds: true }); syncPanel(); redraw(); }
}

// ---------- init ----------
function init() {
  map = new maplibregl.Map({ container: "map", style: "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json", center: VIEW.city.center, zoom: VIEW.city.zoom, pitch: VIEW.city.pitch, bearing: VIEW.city.bearing,
    maxPitch: 78, attributionControl: false, preserveDrawingBuffer: FILM });
  if (!FILM && innerWidth > 760) map.setPadding({ left: 420, top: 30, right: 10, bottom: 0 });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "Biotoptypen, Versiegelung, Baumbestand © Berlin SenMVKU (dl-de/zero-2-0) · bees © iNaturalist / GBIF · © OSM · © CARTO" }), "bottom-right");
  overlay = new deck.MapboxOverlay({ interleaved: true, layers: [], getTooltip: tip,
    onClick: ({ layer, object }) => { if (layer && layer.id === "islands" && object != null) { const isl = HISL[object * 6 + MI()]; S.focus = S.focus >= 0 && NET.root[S.focus] === NET.root[isl] ? -1 : isl; redraw(); } else if (!layer && S.focus >= 0) { S.focus = -1; redraw(); } } });
  map.addControl(overlay);
  map.on("load", () => { ground(); treeColours(); panelUI(); redraw(); $("#load").classList.add("gone"); if (S.story) setMode(true); else setMode(false); animate(); });
  let raf = 0; map.on("zoom", () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; redraw(); }); });
  $("#m-story").onclick = () => setMode(true); $("#m-explore").onclick = () => setMode(false);
  $("#s-next").onclick = () => { if (cur === STEPS.length - 1) setMode(false); else go(cur + 1); };
  $("#s-prev").onclick = () => go(cur - 1); $("#s-skip").onclick = () => setMode(false);
  STEPS = steps();
  $("#s-dots").innerHTML = STEPS.map((_, i) => `<i data-i="${i}"></i>`).join("");
  document.querySelectorAll("#s-dots i").forEach(d => d.onclick = () => go(+d.dataset.i));
}
let last = performance.now();
function animate(now = performance.now()) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (!FILM) { S.t += dt * 260; if (S.show.flow && S.show.highways) overlay.setProps({ layers: layers() }); }
  requestAnimationFrame(animate);
}

(async () => {
  await load();
  STEPS = null; init();
  window.Film = { map, S, redraw, treeColours, go, beeFlight, bestPath, network: () => NET, tick: dt => { S.t += dt * 260; redraw(); } };
})();
