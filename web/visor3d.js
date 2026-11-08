// Explorador 3D de la simulacion CFD: caso base (c12) y los 9 casos del barrido.
// Corte vertical giratorio, rebanada horizontal, pluma de argon, particulas en la velocidad 3D,
// lineas de corriente, recorrido guiado y prueba de mezclado con tinte. Todo sale de la CFD.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const EN = document.documentElement.lang === "en";
const T = (es, en) => (EN ? en : es);
const VMAX = 0.12, ACEL = 10, N_PART = 3500;
const COLORES = [[0.30, 0.02, 0], [0.72, 0.10, 0], [0.98, 0.38, 0.02], [1, 0.72, 0.16], [1, 0.95, 0.62]];
const $ = (id) => document.getElementById(id);
const lienzo = $("visor3d"), lectura = $("visor-lectura"), avisoTinte = $("visor-tinte");
const calmado = matchMedia("(prefers-reduced-motion: reduce)").matches;
const colorDe = (v) => {
  const t = Math.min(1, Math.max(0, v / VMAX)) * (COLORES.length - 1);
  const i = Math.min(COLORES.length - 2, Math.floor(t)), f = t - i;
  return COLORES[i].map((c, q) => c + (COLORES[i + 1][q] - c) * f);
};

const [casos, lineasDatos] = await Promise.all([
  fetch("datos/casos.json").then((r) => r.json()),
  fetch("datos/lineas_c12.json").then((r) => r.json()),
]);

// ---------- Estado del caso ----------
let C = null;                       // caso cargado
const cache = new Map();
async function leerCaso(id) {
  if (cache.has(id)) return cache.get(id);
  const [info, bin] = await Promise.all([fetch(`datos/vol_${id}.json`).then((r) => r.json()), fetch(`datos/vol_${id}.bin`).then((r) => r.arrayBuffer())]);
  const bytes = new Uint8Array(bin), [NX, NY, NZ] = info.dims, N = NX * NY * NZ;
  const rgba = bytes.subarray(0, info.bytes_bloque1), vel = new Float32Array(N * 3), gas = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    for (let c = 0; c < 3; c++) { const e = rgba[i * 4 + c] - 128; vel[i * 3 + c] = Math.sign(e) * (e / 127) ** 2 * info.umax; }
    gas[i] = (rgba[i * 4 + 3] / 255) ** 2;
  }
  const caso = { info, rgba, vel, gas, N, serie: info.serie ? bytes.subarray(info.bytes_bloque1) : null };
  cache.set(id, caso);
  return caso;
}
const B = () => C.info.bounds, D = () => C.info.dims, G = () => C.info.geometria;
let R = 1.6, H = 2.627, LA = 0.1, TIP = 0.627, TOP = 3.027;
const dentro = (x, y, z) => Math.hypot(x, z) < R - 0.02 && y > 0.02 && y < H - 0.02 && !(Math.abs(x) < LA + 0.01 && Math.abs(z) < LA + 0.01 && y > TIP - 0.01);
const salida = [0, 0, 0, 0];
function indices(x, y, z) {
  const [X0, X1, Y0, Y1, Z0, Z1] = B(), [NX, NY, NZ] = D();
  const fx = Math.min(NX - 1.001, Math.max(0, (x - X0) / (X1 - X0) * (NX - 1)));
  const fy = Math.min(NY - 1.001, Math.max(0, (y - Y0) / (Y1 - Y0) * (NY - 1)));
  const fz = Math.min(NZ - 1.001, Math.max(0, (z - Z0) / (Z1 - Z0) * (NZ - 1)));
  return [fx, fy, fz];
}
function muestra(x, y, z) {          // trilineal: [ux, uy, uz, gas]
  const [NX, NY] = D(), [fx, fy, fz] = indices(x, y, z);
  const i = fx | 0, j = fy | 0, k = fz | 0, a = fx - i, b = fy - j, c = fz - k, vel = C.vel, gas = C.gas;
  salida[0] = salida[1] = salida[2] = salida[3] = 0;
  for (let dk = 0; dk < 2; dk++) for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) {
    const w = (di ? a : 1 - a) * (dj ? b : 1 - b) * (dk ? c : 1 - c), n = (k + dk) * NY * NX + (j + dj) * NX + (i + di);
    salida[0] += w * vel[n * 3]; salida[1] += w * vel[n * 3 + 1]; salida[2] += w * vel[n * 3 + 2]; salida[3] += w * gas[n];
  }
  return salida;
}

// ---------- Escena ----------
const render = new THREE.WebGLRenderer({ antialias: true, alpha: true });
render.setPixelRatio(Math.min(devicePixelRatio, 2));
lienzo.prepend(render.domElement);
lienzo.querySelector(".visor-cargando")?.remove();
const escena = new THREE.Scene();
const camara = new THREE.PerspectiveCamera(34, 1, 0.05, 50);
camara.position.set(4.4, 3.0, 4.4);
const controles = new OrbitControls(camara, render.domElement);
controles.target.set(0, 1.25, 0);
controles.enableDamping = true; controles.autoRotate = !calmado; controles.autoRotateSpeed = 0.6;
controles.minDistance = 1.2; controles.maxDistance = 12; controles.update();
const aro = (y, op) => {
  const pts = []; for (let i = 0; i <= 96; i++) { const t = i / 96 * Math.PI * 2; pts.push(new THREE.Vector3(1.6 * Math.cos(t), y, 1.6 * Math.sin(t))); }
  escena.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0xc9a58a, transparent: true, opacity: op })));
};
aro(0, 0.45); aro(2.627, 0.3); aro(3.027, 0.25);
const pared = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 3.027, 72, 1, true),
  new THREE.MeshBasicMaterial({ color: 0xff8a2a, transparent: true, opacity: 0.03, side: THREE.DoubleSide, depthWrite: false }));
pared.position.y = 3.027 / 2; escena.add(pared);
const lanza = new THREE.Group(); escena.add(lanza);
function armarLanza() {
  lanza.clear();
  const caja = new THREE.BoxGeometry(2 * LA, TOP + 0.45 - TIP, 2 * LA), y = (TOP + 0.45 + TIP) / 2;
  lanza.add(new THREE.Mesh(caja, new THREE.MeshBasicMaterial({ color: 0x6d635b })).translateY(y));
  lanza.add(new THREE.LineSegments(new THREE.EdgesGeometry(caja), new THREE.LineBasicMaterial({ color: 0xb8aca2 })).translateY(y));
}

// texturas 3D: velocidad+gas del caso, pluma por instante y tinte
const tex3 = (datos, nx, ny, nz, formato) => {
  const t = new THREE.Data3DTexture(datos, nx, ny, nz);
  t.format = formato; t.type = THREE.UnsignedByteType; t.minFilter = t.magFilter = THREE.LinearFilter; t.unpackAlignment = 1; t.needsUpdate = true;
  return t;
};
let texVel = null, texA = null, texB = null, texTinte = null;
const GEO = new THREE.Vector4(R, H, LA, TIP);
const COMUN = /* glsl */`
precision highp float; precision highp sampler3D;
uniform sampler3D uVel, uTinte; uniform vec3 uMin, uMax, uDims; uniform float uUmax, uVmax, uTinteOn; uniform vec4 uGeo;
vec3 tc(vec3 p, vec3 dims){ vec3 f=clamp((p-uMin)/(uMax-uMin),0.,1.); return (f*(dims-1.)+.5)/dims; }
vec4 campo(vec3 p){ vec4 s=texture(uVel,tc(p,uDims)); vec3 e=s.rgb*255.-128.; return vec4(sign(e)*pow(abs(e)/127.,vec3(2.))*uUmax, s.a*s.a); }
float tinte(vec3 p){ return uTinteOn>.5 ? texture(uTinte,tc(p,uDims)).r : 0.; }
bool dentro(vec3 p){ return length(p.xz)<uGeo.x && p.y>0. && p.y<uGeo.y && !(abs(p.x)<uGeo.z && abs(p.z)<uGeo.z && p.y>uGeo.w); }
vec3 mapa(float t){
  vec3 c0=vec3(.30,.02,0.),c1=vec3(.72,.10,0.),c2=vec3(.98,.38,.02),c3=vec3(1.,.72,.16),c4=vec3(1.,.95,.62);
  t=clamp(t,0.,1.)*4.;
  return t<1.?mix(c0,c1,t):t<2.?mix(c1,c2,t-1.):t<3.?mix(c2,c3,t-2.):mix(c3,c4,t-3.);
}
const vec3 VERDE=vec3(.25,1.,.62);`;
const uniformes = {
  uVel: { value: null }, uTinte: { value: null }, uTinteOn: { value: 0 }, uMin: { value: new THREE.Vector3() }, uMax: { value: new THREE.Vector3() },
  uDims: { value: new THREE.Vector3() }, uUmax: { value: 0.75 }, uVmax: { value: VMAX }, uGeo: { value: GEO },
};
const VERT = `varying vec3 vW; void main(){ vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;
const matCorte = new THREE.ShaderMaterial({
  uniforms: uniformes, side: THREE.DoubleSide, vertexShader: VERT,
  fragmentShader: COMUN + `
varying vec3 vW;
void main(){
  if(!dentro(vW)) discard;
  vec4 c=campo(vW);
  vec3 col=mapa(length(c.xyz)/uVmax);
  col=mix(col,vec3(.80,.90,1.),smoothstep(0.,.45,sqrt(c.w))*.85);
  col=mix(col,VERDE,smoothstep(.02,.5,tinte(vW))*.85);
  gl_FragColor=vec4(col,1.);
}`,
});
const corte = new THREE.Mesh(new THREE.PlaneGeometry(2 * R, H).translate(0, H / 2, 0), matCorte);
corte.add(new THREE.LineSegments(new THREE.EdgesGeometry(corte.geometry), new THREE.LineBasicMaterial({ color: 0xffe2c4, transparent: true, opacity: 0.5 })));
escena.add(corte);
const rebanada = new THREE.Mesh(new THREE.CircleGeometry(R, 96).rotateX(-Math.PI / 2), matCorte);
escena.add(rebanada);

const uPluma = {
  ...uniformes, uSA: { value: null }, uSB: { value: null }, uSDims: { value: new THREE.Vector3(1, 1, 1) }, uMezcla: { value: 0 }, uSerieOn: { value: 1 }, uPlumaOn: { value: 1 },
  uCorte: { value: new THREE.Vector4(0, 0, 1, 0) }, uCorteOn: { value: 1 }, uReb: { value: 1.2 }, uRebOn: { value: 0 },
};
const pluma = new THREE.Mesh(new THREE.BoxGeometry(2 * R, H, 2 * R).translate(0, H / 2, 0), new THREE.ShaderMaterial({
  uniforms: uPluma, vertexShader: VERT, side: THREE.BackSide, transparent: true, depthWrite: false, depthTest: false,
  blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
  fragmentShader: COMUN + `
uniform sampler3D uSA, uSB; uniform vec3 uSDims; uniform float uMezcla, uSerieOn, uPlumaOn, uCorteOn, uReb, uRebOn; uniform vec4 uCorte;
varying vec3 vW;
vec2 caja(vec3 o, vec3 d, vec3 a, vec3 b){ vec3 i=1./d, t0=(a-o)*i, t1=(b-o)*i, n=min(t0,t1), f=max(t0,t1);
  return vec2(max(max(n.x,n.y),n.z), min(min(f.x,f.y),f.z)); }
void main(){
  vec3 o=cameraPosition, d=normalize(vW-o);
  vec2 tt=caja(o,d,vec3(-uGeo.x,0.,-uGeo.x),vec3(uGeo.x,uGeo.y,uGeo.x));
  float ta=max(tt.x,0.), tb=tt.y;
  vec2 tl=caja(o,d,vec3(-uGeo.z,uGeo.w,-uGeo.z),vec3(uGeo.z,9.,uGeo.z)); if(tl.x<tl.y && tl.x>ta) tb=min(tb,tl.x);
  if(uCorteOn>.5){ float dn=dot(d,uCorte.xyz); if(abs(dn)>1e-5){ float tp=-dot(o,uCorte.xyz)/dn; vec3 q=o+d*tp;
    if(tp>ta && tp<tb && q.y>0. && q.y<uGeo.y && length(q.xz)<uGeo.x) tb=tp; } }
  if(uRebOn>.5 && abs(d.y)>1e-5){ float tp=(uReb-o.y)/d.y; vec3 q=o+d*tp; if(tp>ta && tp<tb && length(q.xz)<uGeo.x) tb=tp; }
  if(tb<=ta) discard;
  const int PASOS=72; float dt=(tb-ta)/float(PASOS);
  float j=fract(sin(dot(gl_FragCoord.xy,vec2(12.9898,78.233)))*43758.5453);
  vec4 acc=vec4(0.);
  for(int i=0;i<PASOS;i++){
    vec3 p=o+d*(ta+(float(i)+j)*dt);
    if(!dentro(p)) continue;
    float a=0.;
    if(uPlumaOn>.5){ if(uSerieOn>.5){ vec3 t=tc(p,uSDims); a=mix(texture(uSA,t).r,texture(uSB,t).r,uMezcla); a*=a; } else a=campo(p).w; }
    float rho=smoothstep(.0006,.014,a)*14.;
    vec3 c=mix(vec3(.45,.68,1.),vec3(.95,.98,1.),smoothstep(.01,.08,a));
    float g=tinte(p), rg=smoothstep(.03,.6,g)*7.;
    float r=rho+rg; if(r<1e-4) continue;
    c=mix(c,VERDE,rg/r);
    float al=1.-exp(-r*dt);
    acc.rgb+=(1.-acc.a)*al*c; acc.a+=(1.-acc.a)*al;
    if(acc.a>.96) break;
  }
  gl_FragColor=acc*.9;
}`,
}));
pluma.renderOrder = 10; escena.add(pluma);
let cuadroA = -1, cuadroB = -1;
function plumaEn(tSerie) {
  if (!C.serie) return;
  const [SX, SY, SZ] = C.info.serie.dims, SN = SX * SY * SZ, NT = C.info.serie.t.length;
  const a = Math.floor(tSerie) % NT, b = (a + 1) % NT;
  if (a !== cuadroA) { texA.image.data.set(C.serie.subarray(a * SN, (a + 1) * SN)); texA.needsUpdate = true; cuadroA = a; }
  if (b !== cuadroB) { texB.image.data.set(C.serie.subarray(b * SN, (b + 1) * SN)); texB.needsUpdate = true; cuadroB = b; }
  uPluma.uMezcla.value = tSerie - Math.floor(tSerie);
}

// ---------- Particulas (RK2 en la velocidad promedio 3D) ----------
const pos = new Float32Array(N_PART * 3), col = new Float32Array(N_PART * 3), edad = new Float32Array(N_PART), vida = new Float32Array(N_PART);
const nacer = (i, toberas) => {
  let x, y, z;
  if (toberas) { const lado = Math.random() < 0.5 ? -1 : 1; x = lado * (LA + 0.03 + Math.random() * 0.08); y = TIP + 0.02 + Math.random() * 0.15; z = (Math.random() - 0.5) * 0.12; }
  else do { x = (Math.random() * 2 - 1) * R; z = (Math.random() * 2 - 1) * R; y = Math.random() * H; } while (!dentro(x, y, z));
  pos.set([x, y, z], i * 3); edad[i] = 0; vida[i] = 8 + Math.random() * 10;
};
const geoP = new THREE.BufferGeometry();
geoP.setAttribute("position", new THREE.BufferAttribute(pos, 3));
geoP.setAttribute("color", new THREE.BufferAttribute(col, 3));
const particulas = new THREE.Points(geoP, new THREE.ShaderMaterial({
  uniforms: { uTam: { value: 0.028 }, uEscala: { value: 400 } }, transparent: true, depthWrite: false,
  vertexShader: `attribute vec3 color; varying vec3 vC; uniform float uTam, uEscala;
    void main(){ vC=color; vec4 mv=modelViewMatrix*vec4(position,1.); gl_PointSize=uTam*uEscala/-mv.z; gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `varying vec3 vC; void main(){ vec2 q=gl_PointCoord-.5; float r=length(q); if(r>.5) discard;
    gl_FragColor=vec4(vC*(1.15-r), smoothstep(.5,.3,r)); }`,
}));
escena.add(particulas);
function moverParticulas(dt) {
  const h = dt * ACEL;
  for (let i = 0; i < N_PART; i++) {
    const k = i * 3; let x = pos[k], y = pos[k + 1], z = pos[k + 2];
    edad[i] += dt;
    if (edad[i] > vida[i] || !dentro(x, y, z)) { nacer(i, false); continue; }
    const u = muestra(x, y, z), ux = u[0], uy = u[1], uz = u[2];
    const m = muestra(x + ux * h / 2, y + uy * h / 2, z + uz * h / 2);
    pos[k] = x + m[0] * h; pos[k + 1] = y + m[1] * h; pos[k + 2] = z + m[2] * h;
    const c = colorDe(Math.hypot(m[0], m[1], m[2]));
    const f = Math.min(1, edad[i] / 0.6, (vida[i] - edad[i]) / 0.6);
    col[k] = (c[0] * 1.15 + 0.12) * f; col[k + 1] = (c[1] * 1.15 + 0.08) * f; col[k + 2] = (c[2] * 1.15 + 0.05) * f;
  }
  geoP.attributes.position.needsUpdate = true; geoP.attributes.color.needsUpdate = true;
}

// ---------- Lineas de corriente (caso base) ----------
const LINEAS = lineasDatos.lineas.filter((_, i) => i % 2 === 0);
let nSeg = 0; for (const l of LINEAS) nSeg += l.v.length - 1;
const lp = new Float32Array(nSeg * 6), lc = new Float32Array(nSeg * 6), lt = new Float32Array(nSeg * 2);
let s = 0;
for (const l of LINEAS) {
  let t = Math.random() * 16;
  for (let i = 0; i < l.v.length - 1; i++) {
    const a = i * 3, b = a + 3, p = l.p, v = l.v;
    const t2 = t + Math.hypot(p[b] - p[a], p[b + 1] - p[a + 1], p[b + 2] - p[a + 2]) / Math.max(0.004, (v[i] + v[i + 1]) / 2);
    lp.set([p[a], p[a + 1], p[a + 2], p[b], p[b + 1], p[b + 2]], s * 6);
    lc.set([...colorDe(v[i]), ...colorDe(v[i + 1])], s * 6);
    lt[s * 2] = t; lt[s * 2 + 1] = t2; t = t2; s++;
  }
}
const geoL = new THREE.BufferGeometry();
geoL.setAttribute("position", new THREE.BufferAttribute(lp, 3));
geoL.setAttribute("color", new THREE.BufferAttribute(lc, 3));
geoL.setAttribute("tau", new THREE.BufferAttribute(lt, 1));
const matL = new THREE.ShaderMaterial({
  uniforms: { uTiempo: { value: 0 } }, transparent: true, depthWrite: false,
  vertexShader: `attribute float tau; attribute vec3 color; varying vec3 vC; varying float vT;
    void main(){ vC=color; vT=tau; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float uTiempo; varying vec3 vC; varying float vT;
    void main(){ float f=fract((vT-uTiempo)/16.); gl_FragColor=vec4(vC*(.62+.55*pow(f,22.)),.85); }`,
});
const lineas = new THREE.LineSegments(geoL, matL);
escena.add(lineas);

// ---------- Tinte: escalar pasivo transportado por la velocidad 3D (semi-lagrangiano) ----------
const tinte = { on: false, t: 0, c: null, n: null, liquido: null, masa: 0, buf: null };
function prepararTinte() {
  const [NX, NY, NZ] = D(), [X0, X1, Y0, Y1, Z0, Z1] = B(), N = NX * NY * NZ;
  tinte.c = new Float32Array(N); tinte.n = new Float32Array(N); tinte.liquido = new Uint8Array(N); tinte.buf = new Uint8Array(N);
  for (let k = 0; k < NZ; k++) for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
    const x = X0 + (X1 - X0) * i / (NX - 1), y = Y0 + (Y1 - Y0) * j / (NY - 1), z = Z0 + (Z1 - Z0) * k / (NZ - 1);
    tinte.liquido[(k * NY + j) * NX + i] = dentro(x, y, z) ? 1 : 0;
  }
  texTinte = tex3(tinte.buf, NX, NY, NZ, THREE.RedFormat); uniformes.uTinte.value = texTinte;
  tinte.on = false; uniformes.uTinteOn.value = 0; avisoTinte.textContent = "";
}
function soltarTinte(x, y, z) {
  const [NX, NY, NZ] = D(), [X0, X1, Y0, Y1, Z0, Z1] = B(), r2 = 0.12 ** 2;
  tinte.c.fill(0); let masa = 0;
  for (let k = 0; k < NZ; k++) for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
    const n = (k * NY + j) * NX + i; if (!tinte.liquido[n]) continue;
    const dx = X0 + (X1 - X0) * i / (NX - 1) - x, dy = Y0 + (Y1 - Y0) * j / (NY - 1) - y, dz = Z0 + (Z1 - Z0) * k / (NZ - 1) - z;
    const v = Math.exp(-(dx * dx + dy * dy + dz * dz) / r2); tinte.c[n] = v; masa += v;
  }
  tinte.masa = masa; tinte.t = 0; tinte.on = true; uniformes.uTinteOn.value = 1;
}
function pasoTinte(dt) {            // un paso de dt segundos de flujo real
  const [NX, NY, NZ] = D(), [X0, X1, Y0, Y1, Z0, Z1] = B(), c = tinte.c, n2 = tinte.n, liq = tinte.liquido, vel = C.vel;
  const sx = (NX - 1) / (X1 - X0), sy = (NY - 1) / (Y1 - Y0), sz = (NZ - 1) / (Z1 - Z0);
  let masa = 0;
  for (let k = 0; k < NZ; k++) for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
    const n = (k * NY + j) * NX + i;
    if (!liq[n]) { n2[n] = 0; continue; }
    const fx = Math.min(NX - 1.001, Math.max(0, i - vel[n * 3] * dt * sx));
    const fy = Math.min(NY - 1.001, Math.max(0, j - vel[n * 3 + 1] * dt * sy));
    const fz = Math.min(NZ - 1.001, Math.max(0, k - vel[n * 3 + 2] * dt * sz));
    const a = fx | 0, b = fy | 0, e = fz | 0, u = fx - a, v = fy - b, w = fz - e;
    let suma = 0, peso = 0;
    for (let dk = 0; dk < 2; dk++) for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) {
      const m = ((e + dk) * NY + (b + dj)) * NX + (a + di); if (!liq[m]) continue;
      const p = (di ? u : 1 - u) * (dj ? v : 1 - v) * (dk ? w : 1 - w); suma += p * c[m]; peso += p;
    }
    n2[n] = peso > 1e-6 ? suma / peso : c[n]; masa += n2[n];
  }
  const f = masa > 0 ? tinte.masa / masa : 1;          // conserva la cantidad de tinte
  let s1 = 0, cnt = 0;
  for (let n = 0; n < n2.length; n++) if (liq[n]) { const v = n2[n] * f; c[n] = v; s1 += v; cnt++; }
  tinte.t += dt;
  const media = s1 / cnt;
  let alcanzado = 0;                    // celdas con al menos 10 % de la concentracion media
  for (let n = 0; n < c.length; n++) if (liq[n] && c[n] > 0.1 * media) alcanzado++;
  return { media, alcance: alcanzado / cnt };
}
function mostrarTinte({ media, alcance }) {
  const ref = media * 3;
  for (let n = 0; n < tinte.c.length; n++) tinte.buf[n] = Math.min(255, (tinte.c[n] / ref) * 255);
  texTinte.needsUpdate = true;
  avisoTinte.textContent = T(`Tinte: ${Math.round(tinte.t)} s de flujo · ha alcanzado el ${Math.round(100 * alcance)} % del baño`,
    `Dye: ${Math.round(tinte.t)} s of flow · has reached ${Math.round(100 * alcance)} % of the bath`);
}

// ---------- Carga de un caso ----------
const ctl = { caso: $("ex-caso"), corte: $("ex-corte"), angulo: $("ex-angulo"), reb: $("ex-rebanada"), altura: $("ex-altura"),
  pluma: $("ex-pluma"), part: $("ex-particulas"), lineas: $("ex-lineas") };
const etiqueta = (c) => c.id === "c12"
  ? T("Caso base · malla fina con toberas", "Base case · fine mesh with nozzles")
  : T(`Lanza ${c.lanza_m.toFixed(1)} m · gas ×${c.gas_x}${c.lanza_m === 2 && c.gas_x === 1 ? " (artículo)" : ""} · malla media`,
      `Lance ${c.lanza_m.toFixed(1)} m · gas ×${c.gas_x}${c.lanza_m === 2 && c.gas_x === 1 ? " (paper)" : ""} · medium mesh`);
ctl.caso.innerHTML = casos.map((c) => `<option value="${c.id}">${etiqueta(c)}</option>`).join("");
async function cargarCaso(id) {
  C = await leerCaso(id);
  const g = G(); R = g.radio_olla_m; H = g.altura_bano_m; LA = g.medio_lado_lanza_m; TIP = g.punta_lanza_y_m; TOP = H + g.espacio_libre_m;
  GEO.set(R, H, LA, TIP); armarLanza();
  const [NX, NY, NZ] = D(), [X0, X1, Y0, Y1, Z0, Z1] = B();
  texVel?.dispose(); texVel = tex3(C.rgba, NX, NY, NZ, THREE.RGBAFormat);
  uniformes.uVel.value = texVel; uniformes.uMin.value.set(X0, Y0, Z0); uniformes.uMax.value.set(X1, Y1, Z1); uniformes.uDims.value.set(NX, NY, NZ); uniformes.uUmax.value = C.info.umax;
  if (C.serie) {
    const [SX, SY, SZ] = C.info.serie.dims;
    texA?.dispose(); texB?.dispose();
    texA = tex3(new Uint8Array(SX * SY * SZ), SX, SY, SZ, THREE.RedFormat); texB = tex3(new Uint8Array(SX * SY * SZ), SX, SY, SZ, THREE.RedFormat);
    uPluma.uSA.value = texA; uPluma.uSB.value = texB; uPluma.uSDims.value.set(SX, SY, SZ); uPluma.uSerieOn.value = 1; cuadroA = cuadroB = -1; plumaEn(0);
  } else { uPluma.uSerieOn.value = 0; uPluma.uSA.value = uPluma.uSB.value = texVel; }
  for (let i = 0; i < N_PART; i++) { nacer(i, false); edad[i] = Math.random() * vida[i]; }
  ctl.lineas.disabled = id !== "c12"; if (id !== "c12") ctl.lineas.checked = false;
  $("ex-pluma-nota").textContent = C.serie ? T("40 instantes reales", "40 real time steps") : T("promedio 20–60 s", "20–60 s average");
  prepararTinte(); aplicar();
}

// ---------- Controles ----------
function aplicar() {
  const th = Number(ctl.angulo.value) * Math.PI / 180, h = Number(ctl.altura.value);
  corte.visible = ctl.corte.checked; corte.rotation.y = th;
  rebanada.visible = ctl.reb.checked; rebanada.position.y = h;
  uPluma.uPlumaOn.value = ctl.pluma.checked ? 1 : 0; pluma.visible = ctl.pluma.checked || tinte.on;
  particulas.visible = ctl.part.checked; lineas.visible = ctl.lineas.checked && !ctl.lineas.disabled;
  uPluma.uCorte.value.set(Math.sin(th), 0, Math.cos(th), 0);
  uPluma.uCorteOn.value = corte.visible ? 1 : 0; uPluma.uReb.value = h; uPluma.uRebOn.value = rebanada.visible ? 1 : 0;
  const g = Number(ctl.angulo.value);
  $("ex-angulo-o").textContent = `${g}°${g === 0 || g === 180 ? T(" · toberas", " · nozzles") : g === 90 ? T(" · perpendicular", " · perpendicular") : ""}`;
  $("ex-altura-o").textContent = `${h.toFixed(2)} m`;
  ctl.angulo.disabled = !ctl.corte.checked; ctl.altura.disabled = !ctl.reb.checked;
}
for (const [k, e] of Object.entries(ctl)) if (k !== "caso") e.addEventListener("input", aplicar);
ctl.caso.addEventListener("change", () => cargarCaso(ctl.caso.value));
$("ex-soltar").addEventListener("click", () => { ctl.part.checked = true; aplicar(); for (let i = 0; i < N_PART; i++) nacer(i, true); });
$("ex-tinte").addEventListener("click", () => { soltarTinte(-0.9, H - 0.2, 0.7); aplicar(); });
const botonGiro = $("visor-giro");
const giro = (on) => { controles.autoRotate = on; botonGiro.setAttribute("aria-pressed", String(on)); botonGiro.textContent = on ? T("Pausar giro", "Pause rotation") : T("Girar", "Rotate"); };
botonGiro.addEventListener("click", () => giro(!controles.autoRotate));
const figura = lienzo.closest("figure");
$("ex-completa").addEventListener("click", () => (document.fullscreenElement ? document.exitFullscreen() : figura.requestFullscreen?.()));

// lectura con el cursor y clic para soltar tinte en un corte
const rayo = new THREE.Raycaster(), puntero = new THREE.Vector2();
const tocar = (e) => {
  const r = render.domElement.getBoundingClientRect();
  puntero.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  rayo.setFromCamera(puntero, camara);
  return rayo.intersectObjects([corte, rebanada].filter((o) => o.visible), false).find((h) => dentro(h.point.x, h.point.y, h.point.z));
};
lienzo.addEventListener("pointermove", (e) => {
  const hit = tocar(e);
  if (!hit) { lectura.textContent = ""; return; }
  const p = hit.point, m = muestra(p.x, p.y, p.z);
  lectura.textContent = T(`rapidez ${Math.hypot(m[0], m[1], m[2]).toFixed(3)} m/s · gas ${(100 * m[3]).toFixed(1)} % · altura ${p.y.toFixed(2)} m · a ${Math.hypot(p.x, p.z).toFixed(2)} m del eje · clic: soltar tinte`,
    `speed ${Math.hypot(m[0], m[1], m[2]).toFixed(3)} m/s · gas ${(100 * m[3]).toFixed(1)} % · height ${p.y.toFixed(2)} m · ${Math.hypot(p.x, p.z).toFixed(2)} m from axis · click: release dye`);
});
lienzo.addEventListener("pointerleave", () => { lectura.textContent = ""; });
let abajo = null;
lienzo.addEventListener("pointerdown", (e) => { abajo = [e.clientX, e.clientY]; giro(false); });
lienzo.addEventListener("pointerup", (e) => {
  if (!abajo || Math.hypot(e.clientX - abajo[0], e.clientY - abajo[1]) > 4) return;
  const hit = tocar(e); if (hit) { soltarTinte(hit.point.x, hit.point.y, hit.point.z); aplicar(); }
});

// ---------- Recorrido guiado ----------
const PARADAS = [
  { pos: [4.4, 3.0, 4.4], obj: [0, 1.25, 0], capas: { corte: 1, angulo: 0, pluma: 1, part: 1, reb: 0, lineas: 0 },
    t: T("La olla", "The ladle"), x: T("Olla de 150 t, de 3.2 m de diámetro. La lanza entra 2 m en el arrabio y sopla argón por dos toberas cerca de su punta.",
      "A 150 t ladle, 3.2 m across. The lance reaches 2 m into the hot metal and blows argon through two nozzles near its tip.") },
  { pos: [1.2, 0.95, 1.7], obj: [0, 0.68, 0], capas: { corte: 1, angulo: 0, pluma: 1, part: 0, reb: 0, lineas: 0 },
    t: T("Las toberas", "The nozzles"), x: T("El gas sale por las dos toberas a 45°. Junto a ellas el arrabio alcanza su mayor rapidez, cerca de 0.5 m/s.",
      "Gas leaves the two nozzles at 45°. Next to them the metal reaches its highest speed, about 0.5 m/s.") },
  { pos: [2.3, 1.9, 2.7], obj: [0, 1.6, 0], capas: { corte: 0, angulo: 0, pluma: 1, part: 1, reb: 0, lineas: 0 },
    t: T("La pluma de argón", "The argon plume"), x: T("Con el caudal del artículo, el gas sube pegado a la lanza en una columna delgada: apenas un 3 % del baño tiene gas apreciable.",
      "At the paper's gas flow, the gas rises hugging the lance in a thin column: only about 3 % of the bath holds noticeable gas.") },
  { pos: [0.3, 1.5, 5.4], obj: [0, 1.3, 0], capas: { corte: 1, angulo: 0, pluma: 0, part: 0, reb: 0, lineas: 1 },
    t: T("La recirculación", "Recirculation"), x: T("El arrabio sube con la pluma, se abre bajo la superficie y baja por las paredes: un lazo de recirculación a cada lado de la lanza.",
      "The metal rises with the plume, spreads under the surface and sinks along the walls: one recirculation loop on each side of the lance.") },
  { pos: [3.3, 2.7, 3.3], obj: [0, 0.35, 0], capas: { corte: 0, angulo: 0, pluma: 0, part: 1, reb: 1, altura: 0.3, lineas: 0 },
    t: T("El fondo", "The bottom"), x: T("Cerca del fondo el flujo es lento: la mitad del baño se mueve a menos de 1.4 cm/s. Es la zona que más tarda en mezclarse.",
      "Near the bottom the flow is slow: half of the bath moves slower than 1.4 cm/s. This is the region that takes longest to mix.") },
  { pos: [2.5, 4.4, 2.5], obj: [0, 2.4, 0], capas: { corte: 0, angulo: 0, pluma: 1, part: 0, reb: 1, altura: 2.45, lineas: 0 },
    t: T("Bajo la superficie", "Under the surface"), x: T("Bajo la escoria el flujo es rápido y radial: el metal que sube junto a la lanza se reparte hacia las paredes.",
      "Under the slag the flow is fast and radial: the metal rising by the lance spreads out toward the walls.") },
];
const tour = { i: -1, desde: null, hasta: null, t: 1 };
const panel = $("visor-tour");
function irA(i) {
  tour.i = i; const p = PARADAS[i];
  if (ctl.caso.value !== "c12") { ctl.caso.value = "c12"; cargarCaso("c12"); }
  giro(false);
  tour.desde = { pos: camara.position.clone(), obj: controles.target.clone() };
  tour.hasta = { pos: new THREE.Vector3(...p.pos), obj: new THREE.Vector3(...p.obj) }; tour.t = calmado ? 1 : 0;
  ctl.corte.checked = !!p.capas.corte; ctl.angulo.value = p.capas.angulo; ctl.pluma.checked = !!p.capas.pluma; ctl.part.checked = !!p.capas.part;
  ctl.reb.checked = !!p.capas.reb; if (p.capas.altura) ctl.altura.value = p.capas.altura; ctl.lineas.checked = !!p.capas.lineas;
  aplicar();
  $("tour-titulo").textContent = p.t; $("tour-texto").textContent = p.x; $("tour-n").textContent = `${i + 1} / ${PARADAS.length}`;
  $("tour-ant").disabled = i === 0; $("tour-sig").textContent = i === PARADAS.length - 1 ? T("Terminar", "Finish") : T("Siguiente", "Next");
  panel.hidden = false;
}
$("ex-recorrido").addEventListener("click", () => irA(0));
$("tour-ant").addEventListener("click", () => irA(Math.max(0, tour.i - 1)));
$("tour-sig").addEventListener("click", () => (tour.i < PARADAS.length - 1 ? irA(tour.i + 1) : (panel.hidden = true, tour.i = -1)));
$("tour-cerrar").addEventListener("click", () => { panel.hidden = true; tour.i = -1; });

// ---------- Estado inicial y ciclo ----------
await cargarCaso("c12");
const liga = new URLSearchParams(location.search);
if (liga.has("caso") && casos.some((c) => c.id === liga.get("caso"))) { ctl.caso.value = liga.get("caso"); await cargarCaso(ctl.caso.value); }
if (liga.has("giro")) ctl.angulo.value = liga.get("giro");
if (liga.has("rebanada")) { ctl.reb.checked = true; ctl.altura.value = liga.get("rebanada"); }
for (const [p, e] of [["corte", ctl.corte], ["pluma", ctl.pluma], ["particulas", ctl.part], ["lineas", ctl.lineas]]) if (liga.has(p)) e.checked = liga.get(p) === "1";
aplicar(); giro(controles.autoRotate);
if (liga.has("tinte")) { soltarTinte(-0.9, H - 0.2, 0.7); aplicar(); }
if (liga.has("parada")) irA(Math.min(PARADAS.length - 1, Math.max(0, Number(liga.get("parada")) - 1)));

function ajustar() {
  const w = lienzo.clientWidth, h = lienzo.clientHeight;
  render.setSize(w, h, false); camara.aspect = w / h; camara.fov = w / h < 1 ? 50 : 34; camara.updateProjectionMatrix();
  particulas.material.uniforms.uEscala.value = h * render.getPixelRatio() * 0.9;
}
new ResizeObserver(ajustar).observe(lienzo); ajustar();
let visible = true, tSerie = 0;
new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(lienzo);
const reloj = new THREE.Clock();
render.setAnimationLoop(() => {
  const dt = Math.min(reloj.getDelta(), 1 / 20);
  if (!visible) return;
  if (tour.t < 1) {
    tour.t = Math.min(1, tour.t + dt / 1.6); const e = tour.t * tour.t * (3 - 2 * tour.t);
    camara.position.lerpVectors(tour.desde.pos, tour.hasta.pos, e); controles.target.lerpVectors(tour.desde.obj, tour.hasta.obj, e);
  }
  if (!calmado) {
    if (C.serie) { tSerie = (tSerie + dt) % C.info.serie.t.length; plumaEn(tSerie); }
    if (particulas.visible) moverParticulas(dt);
    matL.uniforms.uTiempo.value += dt * ACEL;
  }
  if (tinte.on && tinte.t < 1800) mostrarTinte(pasoTinte(calmado ? 4 : 2.5));      // ~75 s de flujo por segundo; se detiene a los 30 min
  controles.update();
  render.render(escena, camara);
});
