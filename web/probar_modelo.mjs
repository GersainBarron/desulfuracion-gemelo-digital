// Compara el modelo JS contra modelo/figuras.json y modelo/validacion.json (Python).
// Uso: node web/probar_modelo.mjs
import { readFileSync } from "node:fs";
import * as M from "./modelo.js";

const raiz = new URL("../modelo/", import.meta.url);
const fig = JSON.parse(readFileSync(new URL("figuras.json", raiz)));
const val = JSON.parse(readFileSync(new URL("validacion.json", raiz)));
const p = M.ARTICULO;
let fallas = 0;
const comparar = (nombre, js, py) => {
  const err = Math.abs(js - py) / Math.max(Math.abs(py), 1e-30);
  const ok = err < 1e-9;
  if (!ok) fallas++;
  console.log(`${ok ? "ok " : "MAL"} ${nombre.padEnd(28)} js=${js.toPrecision(10)} py=${py.toPrecision(10)}`);
};
comparar("v_b", M.velocidadBurbuja(p), val.cadena.v_b);
comparar("t_R", M.tiempoResidencia(p), val.cadena.t_R);
comparar("k_CaO", M.kCal(p), val.cadena.k);
const kPolvo = { CaO: M.kCal(p), ...M.K_FIJAS };
for (const s of Object.keys(fig.figura5)) {
  fig.figura5[s].forEach((S, i) => { if (i % 30 === 0) comparar(`fig5 ${s} t=${fig.t_s[i]}`, M.azufre(fig.t_s[i], kPolvo[s], p.S0), S); });
}
M.MEZCLAS.forEach((m, i) => {
  const k = M.kMezcla(m, p);
  const serie = fig.figura6[`mezcla_${i + 1}`];
  comparar(`fig6 mezcla ${i + 1} final`, M.azufre(fig.t_s.at(-1), k, p.S0), serie.at(-1));
  comparar(`fig7 vida media ${m.CaO}% CaO`, M.vidaMedia(k), fig.figura7[i].vida_media_s);
});
console.log(fallas ? `\n${fallas} diferencias` : "\nJS = Python en todas las pruebas");
process.exit(fallas ? 1 : 0);
