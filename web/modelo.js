// Modelo de Barrón, Hilerio y Medina (2015), ecuaciones 6-9, 15 y 16.
// Port directo de modelo/modelo.py; se valida con web/probar_modelo.mjs.

export const ARTICULO = {
  beta: 6.3e-5,        // m/s
  q: 1.25,             // kg/s de cal
  rhoM: 7100,          // kg/m3
  dp: 1.0e-5,          // m
  w: 150000,           // kg
  rhoCaO: 3345,        // kg/m3
  h: 2.0,              // m
  g: 9.81,             // m/s2
  rhoG: 1.165,         // kg/m3
  db: 0.0011725,       // m
  mu: 0.0067,          // kg/(m s)
  Se: 0,               // % en peso
  S0: 0.1,             // % en peso
  tiny: 2400,          // s
};
export const K_FIJAS = { CaC2: 0.004, Mg: 0.00244 };           // tabla 2, 1/s
export const MASA_MOLAR = { CaO: 56.077, CaC2: 64.099, Mg: 24.305 };
export const MEZCLAS = [0, 25, 50, 75, 100].map((cao, i) => ({
  nombre: `Mezcla ${i + 1}`, CaO: cao, CaC2: (100 - cao) / 2, Mg: (100 - cao) / 2,
}));

export const velocidadBurbuja = (p) => p.g * (p.rhoM - p.rhoG) * p.db ** 2 / (18 * p.mu);   // ec. 9
export const tiempoResidencia = (p) => p.h / velocidadBurbuja(p);                            // ec. 8
export const kCal = (p) => 6 * p.beta * tiempoResidencia(p) * p.q * p.rhoM / (p.dp * p.w * p.rhoCaO); // ec. 7
export const azufre = (t, k, S0, Se = 0) => Se + (S0 - Se) * Math.exp(-k * t);              // ec. 6
export const vidaMedia = (k) => Math.LN2 / k;                                                // ec. 16

export function fraccionesMolares(wt) {
  const n = {};
  let total = 0;
  for (const s of Object.keys(MASA_MOLAR)) { n[s] = (wt[s] || 0) / MASA_MOLAR[s]; total += n[s]; }
  for (const s of Object.keys(n)) n[s] = total > 0 ? n[s] / total : 0;
  return n;
}
export function kMezcla(wt, p) {                                                             // ec. 15
  const x = fraccionesMolares(wt);
  const k = { CaO: kCal(p), ...K_FIJAS };
  return Object.keys(x).reduce((s, sp) => s + x[sp] * k[sp], 0);
}
export function tiempoHasta(Sobj, k, S0, Se = 0) {
  if (Sobj <= Se || Sobj >= S0) return Sobj >= S0 ? 0 : Infinity;
  return Math.log((S0 - Se) / (Sobj - Se)) / k;
}
export function curva(k, S0, tFin, Se = 0, n = 241) {
  const pts = [];
  for (let i = 0; i < n; i++) { const t = tFin * i / (n - 1); pts.push([t, azufre(t, k, S0, Se)]); }
  return pts;
}
