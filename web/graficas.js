// Graficas SVG ligeras, sin dependencias: lineas con eje lineal o logaritmico,
// leyenda HTML, reticula y lectura al pasar el cursor.

const NS = "http://www.w3.org/2000/svg";
// Miles con espacio fino (estilo SI): 2 400, 515 520
export const miles = (v) => Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
export const fmt = (v, cifras = 3) => {
  if (!isFinite(v)) return "—";
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a >= 1000) return miles(v);
  if (a < 1e-3) return v.toExponential(cifras - 1).replace("e", "×10^").replace(/\^(-?)(\d+)/, (_, s, d) => superindice(s + d));
  return Number(v.toPrecision(cifras)).toLocaleString("es-MX", { maximumSignificantDigits: cifras });
};
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const superindice = (s) => [...s].map((c) => SUP[c] ?? c).join("");

function ticksLineales(min, max, n = 5) {
  const paso0 = (max - min) / n;
  const mag = 10 ** Math.floor(Math.log10(paso0));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= paso0) ?? 10 * mag;
  const ticks = [];
  for (let v = Math.ceil(min / paso - 1e-9) * paso; v <= max + paso * 1e-6; v += paso) ticks.push(Number(v.toPrecision(12)));
  return ticks;
}
function ticksLog(min, max) {
  const t = [];
  for (let e = Math.ceil(Math.log10(min) - 1e-9); e <= Math.floor(Math.log10(max) + 1e-9); e++) t.push(10 ** e);
  return t;
}
const el = (tag, attrs = {}, padre) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (padre) padre.appendChild(n);
  return n;
};

export function crearGrafica(contenedor, opcionesIniciales) {
  let op = opcionesIniciales;
  const tooltip = document.getElementById("tooltip");
  const leyenda = document.createElement("div");
  leyenda.className = "leyenda-html";
  contenedor.appendChild(leyenda);
  const svg = el("svg", { role: "img" }, contenedor);
  let escalas = null;

  function dibujar() {
    const ancho = Math.max(260, contenedor.clientWidth);
    const alto = Math.round(Math.min(op.altoMax ?? 420, Math.max(220, ancho * (op.proporcion ?? 0.6))));
    const m = { i: 62, d: 14, s: 10, b: 46 };
    const W = ancho - m.i - m.d, H = alto - m.s - m.b;
    svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
    svg.setAttribute("aria-label", op.descripcion ?? "");
    svg.replaceChildren();

    const { x: ox, y: oy } = op;
    const log = !!oy.log;
    const yMin = log ? oy.min : oy.min ?? 0, yMax = oy.max;
    const sx = (v) => m.i + (v - ox.min) / (ox.max - ox.min) * W;
    const sy = log
      ? (v) => m.s + H - (Math.log10(Math.max(v, yMin)) - Math.log10(yMin)) / (Math.log10(yMax) - Math.log10(yMin)) * H
      : (v) => m.s + H - (v - yMin) / (yMax - yMin) * H;
    escalas = { sx, sy, m, W, H, ancho, alto };

    const ret = el("g", { class: "reticula" }, svg);
    const yt = log ? ticksLog(yMin, yMax) : ticksLineales(yMin, yMax, op.nTicksY ?? 5);
    const xt = ox.ticks ?? ticksLineales(ox.min, ox.max, op.nTicksX ?? 6);
    const fy = oy.formato ?? (log ? (v) => (v >= 1e-3 ? fmt(v) : `10${superindice(String(Math.round(Math.log10(v))))}`) : (v) => fmt(v));
    const fx = ox.formato ?? ((v) => fmt(v));
    for (const v of yt) {
      el("line", { x1: m.i, x2: m.i + W, y1: sy(v), y2: sy(v) }, ret);
      el("text", { x: m.i - 8, y: sy(v) + 4, "text-anchor": "end" }, svg).textContent = fy(v);
    }
    for (const v of xt) el("text", { x: sx(v), y: m.s + H + 18, "text-anchor": "middle" }, svg).textContent = fx(v);
    const eje = el("g", { class: "eje" }, svg);
    el("line", { x1: m.i, x2: m.i + W, y1: m.s + H, y2: m.s + H }, eje);
    el("text", { x: m.i + W / 2, y: alto - 6, "text-anchor": "middle", class: "titulo-eje" }, svg).textContent = ox.titulo;
    el("text", { x: 14, y: m.s + H / 2, "text-anchor": "middle", class: "titulo-eje", transform: `rotate(-90 14 ${m.s + H / 2})` }, svg).textContent = oy.titulo;

    const clip = `clip-${Math.random().toString(36).slice(2)}`;
    el("rect", { x: m.i, y: m.s - 4, width: W, height: H + 8 }, el("clipPath", { id: clip }, el("defs", {}, svg)));
    const capa = el("g", { "clip-path": `url(#${clip})` }, svg);
    for (const s of op.series) {
      const d = s.puntos.map(([x, y], i) => `${i ? "L" : "M"}${sx(x).toFixed(1)},${sy(y).toFixed(1)}`).join("");
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": s.ancho ?? 2, "stroke-dasharray": s.guion ? "6 5" : "none",
        "stroke-linejoin": "round", "stroke-linecap": "round", opacity: s.opacidad ?? 1 }, capa);
      if (s.marcadores) for (const [x, y] of s.puntos)
        el("circle", { cx: sx(x), cy: sy(y), r: 4.5, fill: s.color, stroke: "#0d0a08", "stroke-width": 2 }, svg);
    }
    const guia = el("line", { class: "guia", y1: m.s, y2: m.s + H, visibility: "hidden" }, svg);
    const puntosHover = op.series.map((s) => el("circle", { r: 4.5, fill: s.color, stroke: "#0d0a08", "stroke-width": 2, visibility: "hidden" }, svg));
    const zona = el("rect", { x: m.i, y: m.s, width: W, height: H, fill: "transparent" }, svg);

    const ocultar = () => { tooltip.hidden = true; guia.setAttribute("visibility", "hidden"); puntosHover.forEach((p) => p.setAttribute("visibility", "hidden")); };
    const mover = (ev) => {
      const r = svg.getBoundingClientRect();
      const px = (ev.clientX - r.left) * ancho / r.width;
      const xd = ox.min + (px - m.i) / W * (ox.max - ox.min);
      let xRef = null;
      const filas = op.series.map((s, i) => {
        let mejor = s.puntos[0];
        for (const p of s.puntos) if (Math.abs(p[0] - xd) < Math.abs(mejor[0] - xd)) mejor = p;
        if (op.discreto && xRef === null) xRef = mejor[0];
        puntosHover[i].setAttribute("cx", sx(mejor[0])); puntosHover[i].setAttribute("cy", sy(mejor[1]));
        puntosHover[i].setAttribute("visibility", "visible");
        return { s, p: mejor };
      });
      const xg = op.discreto ? xRef : Math.min(ox.max, Math.max(ox.min, xd));
      guia.setAttribute("x1", sx(xg)); guia.setAttribute("x2", sx(xg)); guia.setAttribute("visibility", "visible");
      const fxT = op.tooltipX ?? fx, fyT = op.tooltipY ?? ((v) => fmt(v));
      tooltip.innerHTML = `<b>${fxT(op.discreto ? xg : filas[0].p[0])}</b>` + filas.filter((f) => !f.s.sinTooltip)
        .map((f) => `<div><i style="background:${f.s.color}"></i>${f.s.nombre}: ${fyT(f.p[1])}</div>`).join("");
      tooltip.hidden = false;
      const tx = Math.min(window.innerWidth - tooltip.offsetWidth - 12, ev.clientX + 14);
      tooltip.style.left = `${tx}px`;
      tooltip.style.top = `${ev.clientY - tooltip.offsetHeight - 12}px`;
    };
    zona.addEventListener("pointermove", mover);
    zona.addEventListener("pointerdown", mover);
    zona.addEventListener("pointerleave", ocultar);

    leyenda.innerHTML = op.series.filter((s) => !s.sinLeyenda).map((s) =>
      `<span><i style="background:${s.color};${s.guion ? "background:repeating-linear-gradient(90deg," + s.color + " 0 5px,transparent 5px 9px)" : ""}"></i>${s.nombre}</span>`).join("");
  }

  new ResizeObserver(() => dibujar()).observe(contenedor);
  dibujar();
  return { actualizar(nuevas) { op = { ...op, ...nuevas }; dibujar(); } };
}
