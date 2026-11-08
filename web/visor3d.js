// Visor 3D de las lineas de corriente del caso c12 (flujo promedio 20-60 s).
// Los pulsos avanzan con el tiempo de viaje real del arrabio a lo largo de cada linea (acelerado 10x).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const V_MAX = 0.12;                 // m/s para la escala de color del visor
const ACELERACION = 10;             // tiempo de animacion = 10x el tiempo real
const PERIODO = 16;                 // s de flujo real entre pulsos
const COLORES = [[0.30, 0.02, 0], [0.72, 0.10, 0], [0.98, 0.38, 0.02], [1, 0.72, 0.16], [1, 0.95, 0.62]];
const lienzo = document.getElementById("visor3d");
const botonGiro = document.getElementById("visor-giro");
const calmado = matchMedia("(prefers-reduced-motion: reduce)").matches;
document.querySelector(".escala-color span:last-child").textContent = `${V_MAX} m/s`;

function colorDe(v) {
  const t = Math.min(1, Math.max(0, v / V_MAX)) * (COLORES.length - 1);
  const i = Math.min(COLORES.length - 2, Math.floor(t)), f = t - i;
  return COLORES[i].map((c, k) => c + (COLORES[i + 1][k] - c) * f);
}

const datos = await fetch("datos/lineas_c12.json").then((r) => r.json());
const G = datos.geometria;
lienzo.replaceChildren();

const render = new THREE.WebGLRenderer({ antialias: true, alpha: true });
render.setPixelRatio(Math.min(devicePixelRatio, 2));
lienzo.appendChild(render.domElement);
const escena = new THREE.Scene();
const camara = new THREE.PerspectiveCamera(34, 1, 0.05, 50);
camara.position.set(4.6, 2.9, 4.6);
const controles = new OrbitControls(camara, render.domElement);
controles.target.set(0, 1.25, 0);
controles.enableDamping = true;
controles.autoRotate = !calmado;
controles.autoRotateSpeed = 0.7;
controles.minDistance = 2.5;
controles.maxDistance = 12;
controles.update();
botonGiro.setAttribute("aria-pressed", String(controles.autoRotate));
botonGiro.textContent = controles.autoRotate ? "Pausar giro" : "Girar";
botonGiro.addEventListener("click", () => {
  controles.autoRotate = !controles.autoRotate;
  botonGiro.setAttribute("aria-pressed", String(controles.autoRotate));
  botonGiro.textContent = controles.autoRotate ? "Pausar giro" : "Girar";
});

// Olla: pared translucida, aros y superficie del bano
const R = G.radio_olla_m, Hb = G.altura_bano_m, Htop = Hb + G.espacio_libre_m;
const pared = new THREE.Mesh(new THREE.CylinderGeometry(R, R, Htop, 72, 1, true),
  new THREE.MeshBasicMaterial({ color: 0xff8a2a, transparent: true, opacity: 0.035, side: THREE.DoubleSide, depthWrite: false }));
pared.position.y = Htop / 2;
escena.add(pared);
const aro = (y, opacidad) => {
  const pts = [];
  for (let i = 0; i <= 96; i++) { const a = i / 96 * Math.PI * 2; pts.push(new THREE.Vector3(R * Math.cos(a), y, R * Math.sin(a))); }
  escena.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: 0xc9a58a, transparent: true, opacity: opacidad })));
};
aro(0, 0.45); aro(Hb, 0.3); aro(Htop, 0.25);
const bano = new THREE.Mesh(new THREE.CircleGeometry(R, 72),
  new THREE.MeshBasicMaterial({ color: 0xff7a1a, transparent: true, opacity: 0.05, side: THREE.DoubleSide, depthWrite: false }));
bano.rotation.x = -Math.PI / 2; bano.position.y = Hb;
escena.add(bano);
const lado = 2 * G.medio_lado_lanza_m, yPunta = G.punta_lanza_y_m, yLanzaTop = Htop + 0.45;
const lanza = new THREE.Mesh(new THREE.BoxGeometry(lado, yLanzaTop - yPunta, lado),
  new THREE.MeshBasicMaterial({ color: 0x6d635b }));
lanza.position.y = (yLanzaTop + yPunta) / 2;
escena.add(lanza);
escena.add(new THREE.LineSegments(new THREE.EdgesGeometry(lanza.geometry),
  new THREE.LineBasicMaterial({ color: 0xb8aca2 })).translateY(lanza.position.y));

// Lineas de corriente como segmentos, con color por rapidez y tiempo de viaje acumulado
let n = 0;
const LINEAS = datos.lineas.filter((_, i) => i % 2 === 0);   // la mitad: se lee mejor
for (const l of LINEAS) n += l.v.length - 1;
const pos = new Float32Array(n * 6), col = new Float32Array(n * 6), tau = new Float32Array(n * 2);
let j = 0;
for (const l of LINEAS) {
  const p = l.p, v = l.v;
  let t = Math.random() * PERIODO;
  for (let i = 0; i < v.length - 1; i++) {
    const a = i * 3, b = a + 3;
    const ds = Math.hypot(p[b] - p[a], p[b + 1] - p[a + 1], p[b + 2] - p[a + 2]);
    const vm = Math.max(0.004, (v[i] + v[i + 1]) / 2);
    const t2 = t + ds / vm;
    pos.set([p[a], p[a + 1], p[a + 2], p[b], p[b + 1], p[b + 2]], j * 6);
    col.set([...colorDe(v[i]), ...colorDe(v[i + 1])], j * 6);
    tau[j * 2] = t; tau[j * 2 + 1] = t2;
    t = t2; j++;
  }
}
const geo = new THREE.BufferGeometry();
geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
geo.setAttribute("tau", new THREE.BufferAttribute(tau, 1));
const material = new THREE.ShaderMaterial({
  uniforms: { uTiempo: { value: 0 }, uPeriodo: { value: PERIODO }, uAnimar: { value: calmado ? 0 : 1 } },
  vertexShader: `attribute float tau; attribute vec3 color; varying vec3 vColor; varying float vTau;
    void main() { vColor = color; vTau = tau; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `uniform float uTiempo, uPeriodo, uAnimar; varying vec3 vColor; varying float vTau;
    void main() {
      float f = fract((vTau - uTiempo) / uPeriodo);
      float brillo = mix(0.8, 0.62 + 0.55 * pow(f, 22.0), uAnimar);
      gl_FragColor = vec4(vColor * brillo, 0.85);
    }`,
  transparent: true, depthWrite: false,
});
escena.add(new THREE.LineSegments(geo, material));

function ajustar() {
  const w = lienzo.clientWidth, h = lienzo.clientHeight;
  render.setSize(w, h, false);
  camara.aspect = w / h;
  camara.fov = w / h < 1 ? 50 : 34;
  camara.updateProjectionMatrix();
}
new ResizeObserver(ajustar).observe(lienzo);
ajustar();

let visible = true;
new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(lienzo);
const reloj = new THREE.Clock();
render.setAnimationLoop(() => {
  if (!visible) { reloj.getDelta(); return; }
  material.uniforms.uTiempo.value += reloj.getDelta() * ACELERACION;
  controles.update();
  render.render(escena, camara);
});

const botonFlujo = document.getElementById("visor-flujo");
botonFlujo.setAttribute("aria-pressed", String(!calmado));
botonFlujo.textContent = calmado ? "Flujo quieto" : "Flujo animado";
botonFlujo.addEventListener("click", () => {
  const on = material.uniforms.uAnimar.value < 0.5;
  material.uniforms.uAnimar.value = on ? 1 : 0;
  botonFlujo.setAttribute("aria-pressed", String(on));
  botonFlujo.textContent = on ? "Flujo animado" : "Flujo quieto";
});
