// Fig. 1 del gemelo: estacion de desulfuracion seccionada (kit anatomy).
// Unidades: 1 = 2 cm (50 por metro). Todo numero mostrado sale del modelo del articulo.
// Uso: node figura/build.mjs  ->  web/figura/olla.html
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// kit anatomy (MIT, https://github.com/wheresryan22/anatomy): ANATOMY_KIT o un clon junto al proyecto
const KIT = process.env.ANATOMY_KIT ?? fileURLToPath(new URL("../../anatomy", import.meta.url));
const k = await import(pathToFileURL(`${KIT}/kit/iso-kit.mjs`).href);
const { kitScript, glScript } = await import(pathToFileURL(`${KIT}/scripts/inline-kit.mjs`).href);
const { glCamera } = await import(pathToFileURL(`${KIT}/kit/gl.mjs`).href);
const HERE = dirname(fileURLToPath(import.meta.url));
const M = await import(pathToFileURL(join(HERE, "../web/modelo.js")).href);

const OUT = join(HERE, "..", "web", "figura");
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 470;

const FRAG = `
// Brillo del arrabio: cara del corte (plano y = 0) y ojo abierto por las burbujas en la escoria.
// Todo en coordenadas del mundo, con la misma camara que el SVG.
uniform float uHeat;
uniform vec4 uBath;   // radio interior, z del fondo, z de la superficie, 0
uniform vec3 uEye;    // z de la escoria, radio del ojo, medio lado de la lanza
vec2 deriva(float x){
  // sube junto a la lanza y baja por las paredes, como la recirculacion de la CFD
  float a=abs(x)/uBath.x;
  return vec2(sign(x)*.35*sin(a*3.1416), mix(1.2,-.75,smoothstep(.18,.7,a)));
}
float conveccion(vec3 p){
  vec2 q=vec2(p.x,p.z)*vec2(.05,.04);
  vec2 d=deriva(p.x)*.9;
  float f=fract(uTime*.07), g=fract(uTime*.07+.5);
  float a=fbm2(q-d*f+vec2(1.7,3.1)), b=fbm2(q-d*g+vec2(5.3,.4));
  return mix(a,b,abs(1.-2.*f));
}
void main(){
  vec2 vb=viewOf(gl_FragCoord.xy);
  float px=pixelOf();
  vec3 col=vec3(0.);
  // cara del bano
  vec3 p=onWallY(vb,0.);
  float cara=window(p.x,-uBath.x,uBath.x,.7*px/uCam.x)*window(p.z,uBath.y,uBath.z,.7*px/uCam.w);
  if(cara>0.){
    float frio=smoothstep(0.,14.,uBath.x-abs(p.x))*smoothstep(0.,10.,p.z-uBath.y);
    float n=conveccion(p);
    float t=mix(.62,1.,frio)*(.72+.5*n);
    vec3 c=mix(vec3(.62,.08,.01),vec3(1.,.47,.1),t*t)*t;
    col+=c*cara*.8;
  }
  // ojo de la escoria junto a la lanza
  vec3 e=onFloor(vb,uEye.x);
  float r=length(e.xy);
  float dentro=window(e.y,-1e4,0.,.7*px/uCam.z)*window(r,-1.,uBath.x-2.,.7*px/uCam.z);
  float ojo=exp(-pow(max(r-uEye.z,0.)/uEye.y,2.))*dentro;
  ojo*=.75+.25*noise2(vec2(atan(e.y,e.x)*3.,uTime*1.4))+.15*noise2(vec2(r*.3-uTime*2.,1.));
  col+=vec3(1.,.55,.14)*ojo*.75;
  col=tonemap(col*uHeat,1.25);
  float m=max(col.r,max(col.g,col.b));
  float nz=(hash12(gl_FragCoord.xy+fract(uTime*.61)*91.)+hash12(gl_FragCoord.yx*1.37+fract(uTime*.37)*57.)-1.)/255.;
  col=max(col+nz*smoothstep(0.,1.5/255.,m),0.);
  m=max(col.r,max(col.g,col.b));
  gl_FragColor=vec4(col,m);
}
`;

// ---------- Modelo (articulo) ----------
const A = M.ARTICULO;
const K_CAL = M.kCal(A), T_R = M.tiempoResidencia(A), V_B = M.velocidadBurbuja(A);

// ---------- Mundo ----------
const U = 50;
const Z0 = 14;
const R_OUT = 92, WALL = 12, R_IN = R_OUT - WALL, FLOOR = 12;
const BATH = Z0 + FLOOR + Math.round(2.627 * U);
const SLAG = BATH + 5;
const RIM = Z0 + FLOOR + Math.round((2.627 + 0.4) * U);
const TIP = BATH - A.h * U;
const LANCE = 5, LANCE_TOP = 240;
const MAST = [0, -134], ARM_Z = 212;
const HOP = [170, -46], BOT = [50, -184], CON = { x: 132, y: 30, w: 64, d: 38, r: 3 }, CON_Z = 42;
const PLATE = { x: -180, y: -206, w: 420, d: 284, r: 10 };

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -14, 0), [MAST[0], MAST[1], 262], [0, 0, LANCE_TOP + 8], [HOP[0], HOP[1], 160], [R_OUT, 0, RIM], [-R_OUT, 0, RIM]],
  WIDTH, HEIGHT, { pad: 22, azimuth: 62 },
);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const seg = (a, b) => k.segment(a, b, P);

const arc = (r, from, to, n) => Array.from({ length: n + 1 }, (_, i) => {
  const t = from + (to - from) * i / n; return [r * Math.cos(t), r * Math.sin(t)];
});
const HALF_OUT = arc(R_OUT, Math.PI, 2 * Math.PI, 40);
const HALF_IN = arc(R_IN, Math.PI, 2 * Math.PI, 40);
// el casco se parte en la silueta (normal perpendicular a la vista): la parte de enfrente
// tapa al bano y se pinta despues de el
const SIL = (62 - 90 + 360) * Math.PI / 180;
const corona = (a, b) => [...arc(R_OUT, a, b, 30), ...arc(R_IN, a, b, 30).reverse()];
const ANN_BACK = corona(Math.PI, SIL), ANN_FRONT = corona(SIL, 2 * Math.PI);
const brida = (a, b) => [...arc(R_OUT + 3, a, b, 30), ...arc(R_IN + 4, a, b, 30).reverse()];
const BRIDA_BACK = brida(Math.PI, SIL), BRIDA_FRONT = brida(SIL, 2 * Math.PI);

// Lineas de corriente del corte por la lanza (CFD c12, flujo promedio 20-60 s), en metros
const corte = JSON.parse(readFileSync(join(HERE, "../extraccion/c12/lineas_corte.json"), "utf-8")).lineas;
const FLUJO = [];
corte.forEach((ln, i) => {
  if (i % 6) return;
  const q = ln.p.filter((_, j) => j % 6 === 0).map(([x, y], j) => [x * U, y * U + Z0 + FLOOR, ln.v[j * 6] ?? 0])
    .filter(([x, z]) => Math.abs(x) < R_IN - 1.5 && z > Z0 + FLOOR + 1 && z < BATH - 2 && Math.abs(x) > LANCE + 1.5);
  // cortar en tramos donde la linea salta (sale y entra de la region)
  let tramo = [];
  for (const pt of q) {
    if (tramo.length && Math.hypot(pt[0] - tramo.at(-1)[0], pt[1] - tramo.at(-1)[1]) > 8) { if (tramo.length > 6) FLUJO.push(tramo); tramo = []; }
    tramo.push(pt);
  }
  if (tramo.length > 6) FLUJO.push(tramo);
});
function flujo() {
  const rapido = [], lento = [];
  for (const t of FLUJO) {
    const vm = t.reduce((a, p) => a + p[2], 0) / t.length;
    (vm > 0.035 ? rapido : lento).push(k.pathOf(t.map(([x, z]) => at([x, 0.3, z]))));
  }
  return `<g data-part="flujo">${L(lento.join(""), { tone: "lo", flow: true })}${L(rapido.join(""), { tone: "mid", flow: true })}</g>`;
}

function plate() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -14, 14, P)}"/>`];
  for (const [x, y] of k.corners(PLATE, 24)) {
    out.push(S(k.cylinder(x, y, 8, -14, 2, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 6, -12, 4, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -8, 8, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 6), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 12);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.4, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  const strip = { x: -150, y: PLATE.y + PLATE.d - 17, w: 250, d: 8, r: 1 };
  out.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const ticks = k.topTicks(strip.x + 5, strip.x + 5 + 240, 5, 10, strip.y + 0.8, 0.6, [2.2, 4], P);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  out.push(D([at([strip.x + 2.5, strip.y + 4, 0.6]), at([strip.x + strip.w - 2.5, strip.y + 4, 0.6])], { size: 0.45 }));
  return out.join("");
}

function argon() {
  const [x, y] = BOT, out = [];
  out.push(`<path class="iso-halo" d="${k.haloOf({ x: x - 14, y: y - 14, w: 28, d: 28, r: 14 }, 0, 0.1, P)}" style="filter:blur(3px)"/>`);
  out.push(S(k.cylinder(x, y, 13, 0, 3, P, 36), { tone: "lo" }));
  out.push(S(k.cylinder(x, y, 11, 3, 104, P, 40, 0.8), { tone: "mid", crease: "none" }));
  out.push(L([30, 80].map((z) => k.sideArc(x, y, 11, z, P, 28)).join(""), { tone: "faint" }));
  out.push(S(k.cylinder(x, y, 9, 107, 5, P, 32), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, 5, 112, 5, P, 24), { tone: "mid" }));
  out.push(S(k.slabOf({ x: x - 3, y: y - 3, w: 6, d: 6, r: 1 }, 117, 7, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, 4.5, 124, 2.5, P, 24), { tone: "mid" }));
  out.push(L(k.knurl(x, y, 4.5, 124, 126.5, 20, P), { tone: "lo" }));
  const reg = { x: x + 3, y: y - 4, w: 9, d: 8, r: 1.5 };
  out.push(S(k.slabOf(reg, 115, 9, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.cylinder(reg.x + 4.5, reg.y + 4, 3.4, 124, 1.6, P, 24), { tone: "hi" }));
  out.push(L(k.radialTicks(reg.x + 4.5, reg.y + 4, 2.6, 12, 3, 125.6, [0.6, 1], P, -2.4, 4.8).major, { tone: "lo" }));
  out.push(D([at([reg.x + 4.5, reg.y + 4, 125.6])], { size: 0.4, tone: "hi" }));
  return out.join("");
}

function mast() {
  const [x, y] = MAST, out = [];
  out.push(S(k.cylinder(x, y, 16, 0, 4, P, 40, 0.6), { tone: "mid" }));
  out.push(D(arc(12, 0, 2 * Math.PI, 6).slice(0, 6).map(([a, b]) => at([x + a, y + b, 4])), { size: 0.45 }));
  const col = { x: x - 6, y: y - 6, w: 12, d: 12, r: 1.5 };
  out.push(S(k.slabOf(col, 4, 252, P, 4, 0.5), { tone: "mid" }));
  const face = y + 6.01, zs = [];
  for (let z = BATH; z <= 250; z += 5) zs.push(z);
  out.push(L(zs.map((z, i) => seg([x - 6, face, z], [x - (i % 10 ? 3.5 : 1.2), face, z])).join(""), { tone: "lo" }));
  out.push(S(k.slabOf({ x: x - 7.5, y: y - 7.5, w: 15, d: 15, r: 2 }, 256, 3, P, 4, 0.5), { tone: "mid" }));
  const car = { x: x - 10, y: y - 10, w: 20, d: 20, r: 2.5 };
  out.push(S(k.slabOf(car, ARM_Z - 8, 22, P, 4, 0.6), { tone: "mid" }));
  out.push(D([[car.x + 3, car.y + car.d], [car.x + car.w - 3, car.y + car.d]].map(([a, b]) => at([a, b, ARM_Z + 10])), { size: 0.45 }));
  out.push(S(k.cylinder(car.x + car.w + 3, y, 3.4, ARM_Z, 7, P, 20), { tone: "mid" }));
  out.push(L(k.knurl(car.x + car.w + 3, y, 3.4, ARM_Z, ARM_Z + 7, 18, P), { tone: "lo" }));
  out.push(S(k.slabOf({ x: -4, y: car.y + car.d, w: 8, d: -car.y - car.d - 8, r: 1.5 }, ARM_Z, 8, P, 3, 0.5), { tone: "mid" }));
  return out.join("");
}

function hopper() {
  const [x, y] = HOP, out = [];
  out.push(`<path class="iso-halo" d="${k.haloOf({ x: x - 26, y: y - 26, w: 52, d: 52, r: 8 }, 0, 0.1, P)}" style="filter:blur(3px)"/>`);
  const legs = k.corners({ x: x - 18, y: y - 18, w: 36, d: 36 }).sort((a, b) => k.depthOf([...a, 0], P) - k.depthOf([...b, 0], P));
  const back = legs.slice(0, 3), front = legs.slice(3);
  const leg = ([a, b]) => S(k.slabOf({ x: a - 2.5, y: b - 2.5, w: 5, d: 5, r: 0.8 }, 0, 76, P, 3, 0.3), { tone: "mid" })
    + S(k.slabOf({ x: a - 4, y: b - 4, w: 8, d: 8, r: 1 }, 0, 1.6, P, 3), { tone: "lo" });
  out.push(back.map(leg).join(""));
  const box = { x: x - 10, y: y - 10, w: 20, d: 20, r: 2 };
  out.push(S(k.cylinder(x, y, 3.2, 40, 14, P, 20), { tone: "mid" }));
  out.push(S(k.slabOf(box, 54, 14, P, 4, 0.6), { tone: "mid" }));
  out.push(S(k.cylinder(box.x + box.w + 4, y, 5, 56, 10, P, 24), { tone: "mid" }));
  out.push(L(k.sideArc(box.x + box.w + 4, y, 5, 61, P, 20), { tone: "faint" }));
  out.push(front.map(leg).join(""));
  out.push(S(k.slabOf({ x: x - 21, y: y - 21, w: 42, d: 42, r: 3 }, 72, 4, P, 4, 0.5), { tone: "mid" }));
  out.push(D(k.corners({ x: x - 21, y: y - 21, w: 42, d: 42 }, 3).map(([a, b]) => at([a, b, 76])), { size: 0.45 }));
  [[7, 76, 8], [12, 84, 8], [17, 92, 8]].forEach(([r, z, h]) => out.push(S(k.cylinder(x, y, r, z, h, P, 36), { tone: "mid" })));
  out.push(S(k.cylinder(x, y, 22, 100, 52, P, 48, 0.8), { tone: "mid", crease: "none" }));
  out.push(L([116, 136].map((z) => k.sideArc(x, y, 22, z, P, 32)).join(""), { tone: "faint" }));
  out.push(S(k.cylinder(x, y, 23, 152, 4, P, 48, 0.5), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, 7, 156, 4, P, 28), { tone: "mid" }));
  out.push(L(k.knurl(x, y, 7, 156, 160, 28, P), { tone: "lo" }));
  return out.join("");
}

function stand() {
  const out = [];
  const base = { x: -76, y: -86, w: 152, d: 82, r: 4 };
  out.push(`<path class="iso-halo" d="${k.haloOf(base, 0, 0.1, P)}" style="filter:blur(4px)"/>`);
  out.push(S(k.slabOf(base, 0, Z0, P, 6, 0.8), { tone: "lo" }));
  out.push(D(k.corners(base, 6).map(([a, b]) => at([a, b, Z0])), { size: 0.45 }));
  return out.join("");
}

function ladle() {
  const out = [];
  out.push(S(k.extrude(ANN_BACK, Z0, RIM - Z0, P, { convex: false }), { tone: "mid" }));
  out.push(S(k.extrude(BRIDA_BACK, RIM, 3, P, { convex: false }), { tone: "mid" }));
  out.push(S(k.extrude(HALF_IN, Z0, FLOOR, P), { tone: "mid", crease: "none" }));
  const courses = [];
  // hiladas del refractario: del muro interior al forro de acero (a 2.5 del borde exterior)
  for (const [x0, x1] of [[-R_OUT + 2.5, -R_IN], [R_IN, R_OUT - 2.5]]) {
    for (let z = Z0 + 8; z < RIM - 2; z += 8) courses.push(seg([x0, 0, z], [x1, 0, z]));
    for (let z = Z0, i = 0; z < RIM - 8; z += 8, i++) { const xm = Math.min(x0, x1) + (i % 2 ? 5 : 9); courses.push(seg([xm, 0, z], [xm, 0, Math.min(z + 8, RIM)])); }
  }
  courses.push(seg([-R_IN, 0, Z0 + 6], [R_IN, 0, Z0 + 6]));
  for (let x = -R_IN + 10, i = 0; x < R_IN; x += 14, i++) courses.push(seg([x, 0, Z0 + (i % 2 ? 0 : 6)], [x, 0, Z0 + (i % 2 ? 6 : FLOOR)]));
  out.push(L(courses.join(""), { tone: "lo" }));
  out.push(L(seg([-R_OUT + 2.5, 0, Z0], [-R_OUT + 2.5, 0, RIM]) + seg([R_OUT - 2.5, 0, Z0], [R_OUT - 2.5, 0, RIM]), { tone: "mid" }));
  out.push(S(k.extrude(HALF_IN, Z0 + FLOOR, BATH - Z0 - FLOOR, P), { tone: "hi", crease: "none" }));
  out.push(S(k.extrude(HALF_IN, BATH, SLAG - BATH, P), { tone: "mid", crease: "none" }));
  out.push(S(k.extrude(ANN_FRONT, Z0, RIM - Z0, P, { convex: false }), { tone: "mid" }));
  out.push(S(k.extrude(BRIDA_FRONT, RIM, 3, P, { convex: false }), { tone: "mid" }));
  // bandas de refuerzo del casco en la parte visible
  out.push(L([Z0 + 40, Z0 + 100].map((z) => k.onTop(arc(R_OUT + 0.2, SIL, 2 * Math.PI, 12), z, P)).join(""), { tone: "faint" }));
  out.push(L(courses.join(""), { tone: "lo" }));
  out.push(L(seg([-R_OUT + 2.5, 0, Z0], [-R_OUT + 2.5, 0, RIM]) + seg([R_OUT - 2.5, 0, Z0], [R_OUT - 2.5, 0, RIM]), { tone: "mid" }));
  return out.join("");
}

let semilla = 7;
const azar = () => ((semilla = (semilla * 16807) % 2147483647) / 2147483647);
const SULFURO = [];
while (SULFURO.length < 90) {
  const x = (azar() * 2 - 1) * (R_IN - 4), y = -azar() * (R_IN - 4);
  if (Math.hypot(x, y) < R_IN - 4 && Math.abs(x) > 9) SULFURO.push([x, y]);
}
SULFURO.sort((a, b) => Math.abs(a[0]) - Math.abs(b[0]));
const sulfuro = () => `<g data-part="sulfuro">${SULFURO.map(([x, y]) =>
  `<g style="display:none">${D([at([x, y, SLAG])], { size: 0.55, tone: "hi" })}</g>`).join("")}</g>`;

function lance() {
  const out = [];
  const sec = { x: -LANCE, y: -LANCE, w: 2 * LANCE, d: 2 * LANCE, r: 1 };
  out.push(S(k.slabOf(sec, TIP, LANCE_TOP - TIP, P, 3, 0.4), { tone: "mid" }));
  out.push(L([BATH + 8, RIM + 22, ARM_Z + 24].map((z) => k.sideSeam(sec, z, P, 3)).join(""), { tone: "faint" }));
  out.push(S(k.slabOf({ x: -9, y: -9, w: 18, d: 18, r: 2 }, ARM_Z - 6, 20, P, 4, 0.5), { tone: "mid" }));
  out.push(S(k.cylinder(0, 0, 4, LANCE_TOP, 6, P, 24), { tone: "mid" }));
  out.push(D([at([-LANCE, 0.5, TIP + 4]), at([LANCE, 0.5, TIP + 4])], { size: 0.7, tone: "lo" }));
  return out.join("");
}

const pts = (list) => list.map(at);
const wire = (list, ends) => { const q = pts(list); return k.wireSvg(q[0], q.at(-1), { via: q.slice(1, -1), tone: "mid", size: 1, ends }); };
// gas: regulador del cilindro -> cara trasera del alimentador
const hoseGas = () => wire([[BOT[0] + 7.5, BOT[1], 120], [BOT[0] + 15, BOT[1], 120], [BOT[0] + 15, BOT[1], 3], [HOP[0] - 4, BOT[1], 3], [HOP[0] - 4, HOP[1] - 30, 3], [HOP[0] - 4, HOP[1] - 30, 61], [HOP[0] - 4, HOP[1] - 10, 61]]);
// polvo, tramo trasero: salida del alimentador -> por el mastil -> bajo el brazo
const hosePolvoAtras = () => wire([[HOP[0], HOP[1], 40], [HOP[0], MAST[1] + 4, 40], [9, MAST[1] + 4, 40], [9, MAST[1] + 4, ARM_Z - 9], [9, -14, ARM_Z - 9]], "from");
// polvo, tramo final: bajo el brazo -> conexion en la cabeza de la lanza
const hosePolvoFinal = () => wire([[9, -14, ARM_Z - 9], [9, -4, ARM_Z - 9], [9, 0, LANCE_TOP + 3], [4, 0, LANCE_TOP + 3]], "to");

const S_DIAL = [CON.x + 18, CON.y + 19], T_DIAL = [CON.x + 46, CON.y + 19], DR = 12;
function consola() {
  const out = [`<path class="iso-halo" d="${k.haloOf(CON, 0, 0.1, P)}" style="filter:blur(3px)"/>`];
  out.push(S(k.slabOf(CON, 0, CON_Z, P, 6, 0.8), { tone: "mid" }));
  out.push(L(k.sideSeam(CON, 8, P, 6), { tone: "faint" }));
  out.push(D(k.corners(CON, 2.4).map(([a, b]) => at([a, b, CON_Z])), { size: 0.45 }));
  for (const [x, y, label] of [[...S_DIAL, "S %"], [...T_DIAL, "t s"]]) {
    out.push(S(k.cylinder(x, y, DR, CON_Z, 4, P, 56, 0.6), { tone: "hi", crease: "lo" }));
    out.push(L(k.knurl(x, y, DR, CON_Z + 1.4, CON_Z + 4, 64, P, 0.3), { tone: "lo" }));
    out.push(L(k.ring(x, y, DR - 1.8, CON_Z + 4, P, 56), { tone: "lo" }));
    const t = k.radialTicks(x, y, DR - 2.4, 50, 5, CON_Z + 4, [1, 2.2], P, -Math.PI * 1.3, Math.PI * 1.6);
    out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
    out.push(L(k.ring(x, y, 1.2, CON_Z + 4, P, 16), { tone: "mid" }));
    out.push(k.faceTextSvg(k.topMatrix([x, y + 6.5], CON_Z + 4, P, "x"), label, { size: 2.6, tone: "lo", anchor: "middle" }));
  }
  return out.join("");
}
const needleAt = (c, f, z) => {
  const a = -Math.PI * 1.3 + Math.PI * 1.6 * f;
  return k.lineOnTop([c[0] - Math.cos(a) * 2.4, c[1] - Math.sin(a) * 2.4], [c[0] + Math.cos(a) * (DR - 3.4), c[1] + Math.sin(a) * (DR - 3.4)], z, P);
};

const NB = 16;
const burbujas = () => `<g data-part="burbujas">${Array.from({ length: NB }, (_, i) =>
  `<g data-b="${i}">${D([[0, 0]], { size: 2.1, tone: "hi" })}<g transform="translate(2.3 0.9)">${D([[0, 0]], { size: 0.7, tone: "mid" })}</g></g>`).join("")}</g>`;

const ATRAS = [plate(), argon(), hoseGas(), mast(), hosePolvoAtras(), stand(), ladle()];
const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "Estación de desulfuración seccionada. Una lanza colgada de un mástil entra 2 m en una olla de arrabio; un dosificador de cal y un cilindro de argón la alimentan. En el corte, las burbujas suben desde las toberas hasta la escoria en el tiempo de residencia del artículo, la escoria acumula sulfuro y la carátula de la consola marca el azufre del modelo.",
  body: ATRAS,
});
const FRENTE = [flujo(), sulfuro(), burbujas(), lance(), hosePolvoFinal(), hopper(), consola(),
  `<path data-part="aguja-s" class="iso-line" data-tone="lit" d="${needleAt(S_DIAL, 1, CON_Z + 4.2)}" style="stroke-width:1.1"/>`,
  `<path data-part="aguja-t" class="iso-line" data-tone="hi" d="${needleAt(T_DIAL, 0, CON_Z + 4.2)}" style="stroke-width:0.9"/>`];
const svgFrente = `<svg xmlns="http://www.w3.org/2000/svg" class="iso-svg fx-layer" viewBox="0 0 ${WIDTH} ${HEIGHT}" aria-hidden="true">${FRENTE.join("")}</svg>`;
const GL = { view: [WIDTH, HEIGHT], camera: glCamera(P), bath: [R_IN, Z0 + FLOOR, BATH, 0], eye: [SLAG + 0.05, 16, LANCE] };
const CSS = `.fx-stage{position:relative}.fx-stage>svg,.fx-stage>canvas{display:block;width:100%;height:auto}
.fx-stage>.fx-layer{position:absolute;inset:0;height:100%!important;pointer-events:none}
.iso:not([data-theme="light"]) .fx-gl{mix-blend-mode:screen}`;

const live = `
const P = ${JSON.stringify(P)};
const K = ${K_CAL}, S0 = ${A.S0}, TR = ${T_R}, TFIN = ${A.tiny};
const TIP = ${TIP}, BATH = ${BATH}, LANCE = ${LANCE}, NB = ${NB}, NS = ${SULFURO.length};
const S_DIAL = ${JSON.stringify(S_DIAL)}, T_DIAL = ${JSON.stringify(T_DIAL)}, DR = ${DR}, CZ = ${CON_Z + 4.2};
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const agujaS = stage.querySelector('[data-part="aguja-s"]'), agujaT = stage.querySelector('[data-part="aguja-t"]');
const bs = [...stage.querySelectorAll("[data-b]")], sulf = [...stage.querySelectorAll('[data-part="sulfuro"] > g')];
const GL = ${JSON.stringify(GL)};
const FRAG = ${JSON.stringify(FRAG)};
const capa = typeof glLayer === "function" ? glLayer({ canvas: stage.querySelector(".fx-gl"), fragment: FRAG, view: GL.view, camera: GL.camera, uniforms: ["uHeat"], fixed: { uBath: GL.bath, uEye: GL.eye } }) : null;
if (capa) stage.setAttribute("data-gl", "");
const calor = { x: 0, v: 0 };
let relojGL = 0;
const readout = document.querySelector("[data-readout]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const needleAt = ${needleAt.toString().replace("k.lineOnTop", "lineOnTop")};
const S = (t) => S0 * Math.exp(-K * t);
const fase = bs.map((_, i) => (i * 0.618) % 1), lado = bs.map((_, i) => (i % 2 ? 1 : -1));
let t = 0, tObj = 0, reloj = 0, tour = true, visible = false, frame = 0, last = 0, ocio = 0, mostrados = -1;
function burbuja(i, s) {
  const sd = lado[i], z = TIP + 4 + (BATH - TIP - 6) * s;
  const x = sd * (LANCE + 1.5 + 12 * (1 - Math.exp(-s * 9)) + 4 * Math.sin(s * 9 + i) * s + 46 * Math.pow(Math.max(0, s - 0.78) / 0.22, 2));
  const [px, py] = iso([x, 0.6, z], P);
  bs[i].setAttribute("transform", "translate(" + px.toFixed(1) + " " + py.toFixed(1) + ")");
  bs[i].style.opacity = s > 0.96 ? String(Math.max(0, (1 - s) / 0.04)) : s < 0.03 ? String(s / 0.03) : "1";
}
function draw(dt) {
  const s = S(t);
  agujaS.setAttribute("d", needleAt(S_DIAL, s / S0, CZ));
  agujaT.setAttribute("d", needleAt(T_DIAL, t / TFIN, CZ));
  const n = Math.round(NS * (1 - s / S0));
  if (n !== mostrados) { sulf.forEach((g, i) => { g.style.display = i < n ? "" : "none"; }); mostrados = n; }
  for (let i = 0; i < NB; i++) { if (!still.matches) fase[i] = (fase[i] + dt / TR) % 1; burbuja(i, fase[i]); }
  const txt = "t = " + Math.round(t) + " s · S = " + (s >= 0.01 ? s.toFixed(3) : s.toFixed(4)) + " % · burbuja " + TR.toFixed(2) + " s";
  if (readout.textContent !== txt) readout.textContent = txt;
  stage.setAttribute("aria-valuenow", String(Math.round(t)));
  stage.setAttribute("aria-valuetext", txt);
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now;
  if (tour) { reloj += dt; const c = reloj % 30; tObj = c < 24 ? TFIN * c / 24 : TFIN; }
  t = still.matches ? tObj : t + (tObj - t) * (1 - Math.exp(-dt / 0.25));
  draw(dt);
  settle(calor, 1, dt, 0.9, still.matches);
  if (!still.matches) relojGL += dt;
  if (capa) calor.x > 1e-3 ? capa.draw({ uHeat: calor.x }, still.matches ? 4 : relojGL) : capa.clear();
  frame = visible ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const mover = (v) => { tour = false; tObj = Math.min(TFIN, Math.max(0, v)); clearTimeout(ocio); ocio = setTimeout(() => { tour = !still.matches; reloj = tObj / TFIN * 24; }, 4000); run(); };
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches) { tour = false; t = tObj = TFIN / 2; }
stage.addEventListener("pointermove", (e) => { const b = svg.getBoundingClientRect(); mover(TFIN * Math.min(1, Math.max(0, ((e.clientX - b.left) / b.width - 0.15) / 0.7))); });
stage.addEventListener("keydown", (e) => {
  const paso = { ArrowRight: 240, ArrowUp: 240, ArrowLeft: -240, ArrowDown: -240 }[e.key];
  if (e.key === "Home") { e.preventDefault(); return mover(0); }
  if (e.key === "End") { e.preventDefault(); return mover(TFIN); }
  if (paso) { e.preventDefault(); mover(tObj + paso); }
});
draw(0);
// incrustada en la pagina del gemelo: fondo transparente y aviso de altura al marco
if (window.parent !== window) {
  document.documentElement.style.background = "transparent"; document.body.style.background = "transparent";
  const avisar = () => parent.postMessage({ figura: "olla", alto: Math.ceil(Math.max(...[...document.body.children].map((e) => e.getBoundingClientRect().bottom + scrollY))) + 24 }, "*");
  addEventListener("load", avisar); addEventListener("resize", avisar); setTimeout(avisar, 250);
}
`;

const body = k.plateHtml({
  fig: "Fig 1",
  title: "Estación de desulfuración",
  hint: "Mueve el cursor para recorrer la inyección",
  readout: `t = 0 s · S = 0.100 % · burbuja ${T_R.toFixed(2)} s`,
  keys: [
    { mark: "lit", label: `Burbujas de argón con partículas de cal: suben ${A.h} m en ${T_R.toFixed(2)} s` },
    { mark: "raised", label: "Escoria: se carga de sulfuro conforme baja el azufre del arrabio" },
    { mark: "line", label: "Líneas de corriente del arrabio en el corte: CFD propia en OpenFOAM, flujo promedio" },
  ],
  caption: `Olla de 150 t seccionada por la lanza. El dosificador entrega 1.25 kg/s de cal arrastrada por argón; cada partícula viaja con su burbuja desde las toberas hasta la escoria en t_R = ${T_R.toFixed(2)} s (v_b = ${V_B.toFixed(2)} m/s), el tiempo real que se ve en la animación. La carátula S sigue la ec. 6 con k = ${K_CAL.toFixed(6)} 1/s: de 0.1 % a ${M.azufre(A.tiny, K_CAL, A.S0).toFixed(5)} % en 2400 s. Escala: 1 m = 50 unidades; el equipo auxiliar es supuesto. El brillo del metal es ilustrativo: el proceso es isotérmico y no se calculó un campo de temperatura.`,
  body: `<style>${CSS}</style><div class="iso-stage fx-stage" tabindex="0" role="slider" aria-label="Estación de desulfuración: las flechas avanzan el tiempo de inyección" aria-valuemin="0" aria-valuemax="${A.tiny}" aria-valuenow="0">${svg}<canvas class="fx-layer fx-gl" aria-hidden="true"></canvas>${svgFrente}</div>`,
});

mkdirSync(OUT, { recursive: true });
const nombre = theme === "light" ? "olla-light.html" : "olla.html";
writeFileSync(join(OUT, nombre), k.pageHtml({ title: "Estación de desulfuración", theme, body, script: kitScript() + glScript() + live, width: 760 }));
console.log("escrito", nombre, "TIP", TIP, "BATH", BATH, "RIM", RIM);
