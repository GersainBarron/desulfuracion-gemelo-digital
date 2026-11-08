import * as M from "./modelo.js";
import { crearGrafica, fmt, miles } from "./graficas.js";

const COLOR = { CaO: "#f2a33a", CaC2: "#3fb8af", Mg: "#9aa8ff", acento: "#ff8a2a", referencia: "#b9a999" };
const COLOR_MEZCLA = ["#3fb8af", "#86c06a", "#cfc04c", "#f5a63c", "#ff6f3c"];
const NOMBRE = { CaO: "Cal (CaO)", CaC2: "Carburo de calcio (CaC₂)", Mg: "Magnesio (Mg)" };
const fS = (v) => `${fmt(v, 3)} %`;
const fSeg = (v) => `${miles(v)} s`;

// ---------- Controles ----------
const DEF = {
  cao:     { etq: "Cal (CaO) en la mezcla", min: 0, max: 100, paso: 1, valor: 100, f: (v) => `${v} %` },
  reparto: { etq: "Resto: CaC₂ / Mg", min: 0, max: 100, paso: 1, valor: 50, f: (v) => `${v} / ${100 - v}` },
  q:       { etq: "Flujo de cal, q", min: 0.25, max: 3, paso: 0.05, valor: M.ARTICULO.q, f: (v) => `${v.toFixed(2)} kg/s` },
  h:       { etq: "Profundidad de lanza, hᵢ", min: 0.5, max: 2.6, paso: 0.05, valor: M.ARTICULO.h, f: (v) => `${v.toFixed(2)} m` },
  tiny:    { etq: "Tiempo de inyección", min: 600, max: 3600, paso: 60, valor: M.ARTICULO.tiny, f: (v) => `${v / 60} min` },
  dp:      { etq: "Diámetro de partícula, dₚ", min: 5, max: 60, paso: 1, valor: M.ARTICULO.dp * 1e6, f: (v) => `${v} µm` },
  db:      { etq: "Diámetro de burbuja, d_b", min: 0.5, max: 3, paso: 0.0025, valor: M.ARTICULO.db * 1e3, f: (v) => `${v.toFixed(3)} mm` },
  w:       { etq: "Masa de arrabio, w_M", min: 50, max: 300, paso: 5, valor: M.ARTICULO.w / 1e3, f: (v) => `${v} t` },
  s0:      { etq: "Azufre inicial, S₀", min: 0.02, max: 0.15, paso: 0.005, valor: M.ARTICULO.S0, f: (v) => `${v.toFixed(3)} %` },
};
const estado = {};
const entradas = {};
for (const caja of document.querySelectorAll(".deslizador")) {
  const id = caja.dataset.id, d = DEF[id];
  caja.innerHTML = `<label for="r-${id}"><span>${d.etq}</span><output id="o-${id}"></output></label>
    <input type="range" id="r-${id}" min="${d.min}" max="${d.max}" step="${d.paso}" value="${d.valor}">`;
  entradas[id] = caja.querySelector("input");
  estado[id] = d.valor;
  entradas[id].addEventListener("input", () => { estado[id] = Number(entradas[id].value); actualizar(); });
}
const fijar = (id, v) => { estado[id] = v; entradas[id].value = v; };
document.querySelectorAll(".presets button").forEach((b) => b.addEventListener("click", () => {
  fijar("cao", Number(b.dataset.cao)); fijar("reparto", 50); actualizar();
}));
document.getElementById("restablecer").addEventListener("click", () => {
  for (const id of Object.keys(DEF)) fijar(id, DEF[id].valor);
  actualizar();
});

const parametros = () => ({ ...M.ARTICULO, q: estado.q, h: estado.h, dp: estado.dp * 1e-6, db: estado.db * 1e-3, w: estado.w * 1e3, S0: estado.s0, tiny: estado.tiny });
const mezcla = () => { const resto = 100 - estado.cao; return { CaO: estado.cao, CaC2: resto * estado.reparto / 100, Mg: resto * (100 - estado.reparto) / 100 }; };

// ---------- Gemelo ----------
const gGemelo = crearGrafica(document.getElementById("g-gemelo"), {
  series: [], x: { min: 0, max: 2400, titulo: "tiempo (s)" }, y: { min: 0, max: 0.1, titulo: "azufre (% en peso)" },
  proporcion: 0.55, tooltipX: (v) => `t = ${fSeg(v)} (${(v / 60).toFixed(1)} min)`, tooltipY: fS,
  descripcion: "Curva de azufre contra tiempo del gemelo",
});
const escalaLog = document.getElementById("escala-log");
escalaLog.addEventListener("change", () => actualizar());
const txt = (id, v) => { document.getElementById(id).textContent = v; };

function actualizar() {
  for (const id of Object.keys(DEF)) document.getElementById(`o-${id}`).textContent = DEF[id].f(estado[id]);
  const p = parametros(), wt = mezcla();
  const km = M.kMezcla(wt, p), kmRef = M.kMezcla(wt, M.ARTICULO);
  const sFin = M.azufre(p.tiny, km, p.S0);
  const t005 = M.tiempoHasta(0.005, km, p.S0);

  txt("l-km", fmt(km, 4));
  txt("l-th", miles(M.vidaMedia(km)));
  txt("l-sf", fmt(sFin, 3));
  txt("l-t005", t005 === 0 ? "ya" : fmt(t005 / 60, 3));
  txt("l-t005-u", t005 === 0 ? "S₀ ≤ 0.005 %" : t005 > p.tiny ? "min, más que la inyección" : "min");
  txt("c-vb", fmt(M.velocidadBurbuja(p), 4));
  txt("c-tr", fmt(M.tiempoResidencia(p), 4));
  txt("c-kcao", fmt(M.kCal(p), 4));
  txt("c-km", fmt(km, 4));

  const barra = document.getElementById("barra-mezcla").children;
  barra[0].style.width = `${wt.CaO}%`; barra[1].style.width = `${wt.CaC2}%`; barra[2].style.width = `${wt.Mg}%`;
  document.querySelectorAll(".presets button").forEach((b) =>
    b.classList.toggle("activo", Number(b.dataset.cao) === estado.cao && estado.reparto === 50));

  const tFin = Math.max(p.tiny, M.ARTICULO.tiny);
  const log = escalaLog.checked;
  const serieRef = M.curva(kmRef, M.ARTICULO.S0, tFin);
  const serie = M.curva(km, p.S0, p.tiny);
  const minimo = Math.min(serie.at(-1)[1], serieRef.at(-1)[1]);
  gGemelo.actualizar({
    x: { min: 0, max: tFin, titulo: "tiempo (s)" },
    y: log
      ? { log: true, min: 10 ** Math.floor(Math.log10(Math.max(minimo, 1e-9))), max: 10 ** Math.ceil(Math.log10(Math.max(p.S0, 0.1)) - 1e-9), titulo: "azufre (% en peso)" }
      : { min: 0, max: Math.max(p.S0, M.ARTICULO.S0), titulo: "azufre (% en peso)" },
    series: [
      { nombre: "Valores del artículo, misma mezcla", color: COLOR.referencia, puntos: serieRef, guion: true, ancho: 1.6 },
      { nombre: "Tu condición", color: COLOR.acento, puntos: serie, ancho: 3 },
    ],
  });
}
// Estado inicial desde la liga, p. ej. ?cao=50&q=2&log=1
const liga = new URLSearchParams(location.search);
for (const id of Object.keys(DEF)) {
  const v = Number(liga.get(id));
  if (liga.has(id) && isFinite(v)) fijar(id, Math.min(DEF[id].max, Math.max(DEF[id].min, v)));
}
escalaLog.checked = liga.get("log") === "1";
actualizar();
txt("cifra-sfinal", fmt(M.azufre(M.ARTICULO.tiny, M.kCal(M.ARTICULO), M.ARTICULO.S0), 2));

// ---------- Figuras 5, 6 y 7 ----------
const P = M.ARTICULO;
const kPolvo = { CaO: M.kCal(P), ...M.K_FIJAS };
const ejeT = { min: 0, max: 2400, titulo: "tiempo (s)", ticks: [0, 600, 1200, 1800, 2400] };
const ejeS = { min: 0, max: 0.1, titulo: "azufre (% en peso)" };
const comunes = { proporcion: 0.78, altoMax: 340, tooltipX: (v) => `t = ${fSeg(v)}`, tooltipY: fS };
crearGrafica(document.getElementById("g-fig5"), {
  ...comunes, x: ejeT, y: ejeS, descripcion: "Figura 5: azufre contra tiempo por polvo",
  series: Object.keys(kPolvo).map((s) => ({ nombre: NOMBRE[s], color: COLOR[s], puntos: M.curva(kPolvo[s], P.S0, 2400) })),
});
crearGrafica(document.getElementById("g-fig6"), {
  ...comunes, x: ejeT, y: ejeS, descripcion: "Figura 6: azufre contra tiempo por mezcla",
  series: M.MEZCLAS.map((m, i) => ({ nombre: `M${i + 1} · ${m.CaO} % CaO`, color: COLOR_MEZCLA[i], puntos: M.curva(M.kMezcla(m, P), P.S0, 2400) })),
});
crearGrafica(document.getElementById("g-fig7"), {
  proporcion: 0.78, altoMax: 340, discreto: true, descripcion: "Figura 7: vida media contra contenido de cal",
  x: { min: 0, max: 100, titulo: "cal en la mezcla (% en peso)", ticks: [0, 25, 50, 75, 100] },
  y: { min: 200, max: 450, titulo: "vida media (s)" },
  tooltipX: (v) => `${v} % de cal`, tooltipY: (v) => fSeg(v),
  series: [{ nombre: "Vida media, tₕ = ln 2 / kₘ", color: COLOR.acento, marcadores: true,
    puntos: M.MEZCLAS.map((m) => [m.CaO, M.vidaMedia(M.kMezcla(m, P))]) }],
});

// ---------- Resultados CFD ----------
const CELDAS = { gruesa: 19456, media: 153344, fina: 515520 };
fetch("datos/barrido.json").then((r) => r.json()).then((filas) => {
  const cuerpo = document.querySelector("#t-malla tbody");
  const base = filas.filter((f) => f.caudal_x === 1 && f.lanza_m === 2);
  cuerpo.innerHTML = base.map((f) => `<tr><td>${f.malla}${f.caso === "c12" ? " + toberas" : ""}</td><td>${miles(CELDAS[f.malla])}</td>
    <td>${f.v_media_m_s.toFixed(3)} m/s</td><td>${f.v_p95_m_s.toFixed(3)} m/s</td></tr>`).join("");

  const medias = filas.filter((f) => f.malla === "media");
  const GAS = [{ x: 0.5, nombre: "Gas ×0.5 · 0.25 L/s", color: "#b5653a" },
               { x: 1, nombre: "Gas ×1 · 0.5 L/s (artículo)", color: "#ff8a2a" },
               { x: 2, nombre: "Gas ×2 · 1 L/s", color: "#ffd27a" }];
  const series = (medida) => GAS.map((g) => ({ nombre: g.nombre, color: g.color, marcadores: true,
    puntos: medias.filter((f) => f.caudal_x === g.x).sort((a, b) => a.lanza_m - b.lanza_m).map((f) => [f.lanza_m, f[medida]]) }));
  const yMax = (medida) => Math.ceil(Math.max(...medias.map((f) => f[medida])) * 1.15 * 100) / 100;
  const opciones = (medida) => ({ series: series(medida), y: { min: 0, max: yMax(medida), titulo: "rapidez del arrabio (m/s)" } });
  const g = crearGrafica(document.getElementById("g-barrido"), {
    proporcion: 0.62, altoMax: 360, discreto: true, descripcion: "Barrido CFD de rapidez contra profundidad de lanza",
    x: { min: 1.4, max: 2.6, titulo: "profundidad de la lanza (m)", ticks: [1.5, 2, 2.5] },
    tooltipX: (v) => `lanza a ${v} m`, tooltipY: (v) => `${v.toFixed(3)} m/s`, ...opciones("v_media_m_s"),
  });
  document.querySelectorAll(".segmentos button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".segmentos button").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
    g.actualizar(opciones(b.dataset.medida));
  }));
});
