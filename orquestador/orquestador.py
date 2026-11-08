#!/usr/bin/env python3
"""Orquestador de la cola CFD. Corre dentro de WSL (Ubuntu) con la biblioteca estandar.

- Lanza los casos de cola.json uno por uno y reanuda el que quedo a medias.
- Pausa limpia si existe el archivo orquestador/PAUSA (OpenFOAM: stopAt writeNow).
- Respalda cada instante guardado en cfd/respaldos/<caso> (D:) y conserva los ultimos N.
- Al arrancar recupera: usa el caso en WSL o, si se perdio, lo restaura desde D:.
- Descarta instantes a medio escribir. Relanza un caso que diverge con maxCo menor.
"""
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ORQ = Path(__file__).resolve().parent
CFG = json.loads(Path(os.environ.get("ORQ_CONFIG", ORQ / "config.json")).read_text(encoding="utf-8"))
# Las pruebas usan otra raiz para no tocar el estado real del proyecto.
PROY = Path(CFG["raiz"]) if CFG.get("raiz") else ORQ.parent
ORQ = PROY / "orquestador"
COLA, PAUSA = ORQ / "cola.json", ORQ / "PAUSA"
ESTADO, AVISOS = PROY / "ESTADO.txt", PROY / "AVISOS.txt"
BITACORA, RESPALDOS = PROY / "cfd" / "bitacora", PROY / "cfd" / "respaldos"
TERMINADOS, PLANTILLA = PROY / "cfd" / "casos", PROY / "cfd" / "plantilla"
ACTIVOS = Path(os.path.expanduser(CFG["activos"]))
LOCK = ACTIVOS.parent / "orquestador.pid"
NUM = re.compile(r"^\d+(\.\d+)?(e[+-]?\d+)?$")
PIE = b"// ****"
DETENER = False
SOLVER = None          # proceso del solver en marcha (para detenerlo si el orquestador falla)


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    """Primero al archivo; la pantalla es opcional (sin consola, print fallaria)."""
    BITACORA.mkdir(parents=True, exist_ok=True)
    linea = f"[{ahora()}] {msg}"
    with open(BITACORA / "orquestador.log", "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    try:
        print(linea, flush=True)
    except OSError:
        pass


def aviso(msg):
    with open(AVISOS, "a", encoding="utf-8") as f:
        f.write(f"[{ahora()}] {msg}\n")
    log("AVISO: " + msg)


def escribir_atomico(ruta, texto):
    tmp = ruta.with_name(ruta.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texto)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, ruta)


def leer_cola():
    return json.loads(COLA.read_text(encoding="utf-8"))


def guardar_cola(cola):
    cola["actualizado"] = ahora()
    escribir_atomico(COLA, json.dumps(cola, indent=2, ensure_ascii=False))


# ---------- instantes de tiempo e integridad ----------

def raices(caso):
    """Carpetas que contienen instantes: processor* en paralelo, o el caso."""
    procs = sorted(p for p in caso.glob("processor*") if p.is_dir())
    return procs or [caso]


def instantes(d):
    if not d.is_dir():
        return []
    return sorted((float(p.name), p.name) for p in d.iterdir()
                  if p.is_dir() and NUM.match(p.name))


def con_pie(f):
    if not f.is_file() or f.stat().st_size == 0:
        return False
    with open(f, "rb") as fh:
        fh.seek(max(0, f.stat().st_size - 400))
        return PIE in fh.read()


def completo(dir_t, campos):
    """Valido si estan los campos clave y todos los archivos escritos terminan con el pie."""
    if not all((dir_t / c).is_file() for c in campos):
        return False
    return all(con_pie(f) for f in dir_t.iterdir() if f.is_file())


def campos_de(raiz):
    """Campos clave: los de config, o los de 0/ que el solver reescribe siempre."""
    if CFG.get("campos_clave"):
        return CFG["campos_clave"]
    cero = raiz / "0"
    return [p.name for p in cero.iterdir() if p.is_file() and p.name.startswith(("p", "U", "alpha"))] \
        if cero.is_dir() else []


def ultimo_valido(caso, limpiar=False):
    """(valor, nombre) del ultimo instante completo en todas las raices."""
    rs = raices(caso)
    campos = campos_de(rs[0])
    comunes = None
    for r in rs:
        ok = {(t, n) for t, n in instantes(r) if t == 0 or completo(r / n, campos)}
        comunes = ok if comunes is None else comunes & ok
    if not comunes:
        return None
    mejor = max(comunes)
    if limpiar:
        for r in rs:
            for t, n in instantes(r):
                if t > mejor[0]:
                    shutil.rmtree(r / n, ignore_errors=True)
                    log(f"{caso.name}: descartado instante incompleto {n}")
    return mejor


# ---------- controlDict ----------

def leer_control(caso, clave):
    txt = (caso / "system" / "controlDict").read_text(encoding="utf-8")
    return float(re.search(rf"^\s*{clave}\s+([^;]*);", txt, re.M).group(1))


def fijar(caso, clave, valor):
    """Cambia una entrada de system/controlDict (OpenFOAM la relee al vuelo)."""
    cd = caso / "system" / "controlDict"
    txt = cd.read_text(encoding="utf-8")
    patron = re.compile(rf"^(\s*{clave}\s+)[^;]*;", re.M)
    if patron.search(txt):
        txt = patron.sub(lambda m: f"{m.group(1)}{valor};", txt, count=1)
    else:
        txt += f"\n{clave} {valor};\n"
    escribir_atomico(cd, txt)


# ---------- respaldos en D: ----------

def respaldar_base(caso, cid):
    """Copia unica de todo menos los instantes > 0 (malla, sistema, condiciones)."""
    base = RESPALDOS / cid / "base"
    if (base / "COMPLETO").exists():
        return
    shutil.rmtree(base, ignore_errors=True)
    def ignorar(d, nombres):
        return [n for n in nombres if NUM.match(n) and float(n) > 0] + ["log.solver"]
    shutil.copytree(caso, base, ignore=ignorar)
    (base / "COMPLETO").write_text(ahora())


def respaldar(caso, instante, cid):
    """Copia un instante (de cada raiz) a D: y conserva solo los ultimos N."""
    valor, nombre = instante
    dest = RESPALDOS / cid / "t" / nombre
    if (dest / "COMPLETO").exists():
        return
    shutil.rmtree(dest, ignore_errors=True)
    for r in raices(caso):
        shutil.copytree(r / nombre, dest / r.relative_to(caso) / nombre)
    (dest / "COMPLETO").write_text(ahora())
    guardados = sorted((float(p.name), p) for p in (RESPALDOS / cid / "t").iterdir()
                       if (p / "COMPLETO").exists())
    for _, viejo in guardados[:-CFG["respaldos_a_conservar"]]:
        shutil.rmtree(viejo, ignore_errors=True)
    log(f"{cid}: respaldado instante {nombre}")


def restaurar(cid, caso):
    """Reconstruye el caso en WSL desde D: (base + ultimo instante completo)."""
    base = RESPALDOS / cid / "base"
    if not (base / "COMPLETO").exists():
        return False
    shutil.rmtree(caso, ignore_errors=True)
    shutil.copytree(base, caso, ignore=shutil.ignore_patterns("COMPLETO"))
    tdir = RESPALDOS / cid / "t"
    guardados = sorted((float(p.name), p) for p in tdir.iterdir()
                       if (p / "COMPLETO").exists()) if tdir.is_dir() else []
    if guardados:
        shutil.copytree(guardados[-1][1], caso, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("COMPLETO"))
    log(f"{cid}: restaurado desde respaldo en D: "
        f"(instante {guardados[-1][1].name if guardados else '0'})")
    return True


# ---------- ejecucion ----------

def bash(cmd, cwd=None, log_archivo=None):
    """Lanza un comando con el entorno de OpenFOAM, en su propio grupo de procesos."""
    entorno = CFG.get("entorno") or ""
    pre = f"source '{entorno}' >/dev/null 2>&1; " if entorno else ""
    # En WSL, hwloc se cuelga consultando la GPU al arrancar mpirun; se desactiva esa consulta.
    pre += "".join(f"export {k}='{v}'; " for k, v in CFG.get("variables", {}).items())
    salida = open(log_archivo, "a") if log_archivo else subprocess.DEVNULL
    return subprocess.Popen(["bash", "-c", pre + cmd], cwd=cwd, stdout=salida,
                            stderr=subprocess.STDOUT, start_new_session=True)


def preparar(caso_d, caso):
    """Crea el caso desde la plantilla: malla, campos iniciales y descomposicion."""
    caso.parent.mkdir(parents=True, exist_ok=True)
    params = caso.parent / f"{caso.name}.params.json"
    params.write_text(json.dumps(caso_d["parametros"], indent=2))
    # Preparacion atomica: se arma en <caso>.preparando y solo se renombra al terminar bien.
    # Si WSL se reinicia a la mitad, queda la carpeta temporal y el caso se prepara de nuevo.
    tmp = caso.with_name(caso.name + ".preparando")
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"{caso.name}: preparando desde la plantilla")
    p = bash(f"bash '{PLANTILLA / CFG['preparar']}' '{tmp}' '{params}' '{CFG['nucleos']}'",
             log_archivo=caso.parent / f"{caso.name}.preparar.log")
    if p.wait() != 0 or not (tmp / "resumen_caso.json").exists():
        raise RuntimeError("fallo la preparacion; ver activos/<caso>.preparar.log")
    shutil.rmtree(caso, ignore_errors=True)
    os.replace(tmp, caso)
    respaldar_base(caso, caso.name)


def comando_solver():
    n = CFG["nucleos"]
    # WSL expone hilos, no nucleos completos: se cuentan los hilos como lugares para MPI.
    return f"mpirun --use-hwthread-cpus -np {n} {CFG['solver']} -parallel" if n > 1 else CFG["solver"]


def divergio(caso):
    log_s = caso / "log.solver"
    if not log_s.exists():
        return False
    with open(log_s, "rb") as f:
        f.seek(max(0, log_s.stat().st_size - 20000))
        cola = f.read().decode(errors="ignore")
    if "cannot find file" in cola:
        # Falta un archivo: problema de configuracion, no numerico. Se avisa con el detalle.
        aviso(f"{caso.name}: OpenFOAM no encontro un archivo al arrancar; revisar log.solver")
    return "FOAM FATAL" in cola or re.search(r"\bnan\b", cola, re.I) is not None


def detener(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=60)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass


# ---------- estado legible ----------

# Costo relativo de cada malla frente a la media (celdas x paso de tiempo), para estimar
# las mallas que aun no tienen un caso terminado.
COSTO_MALLA = {"gruesa": 0.15, "media": 1.0, "fina": 5.0}


def estimar_horas_restantes(cola, caso_d, sim, ritmo):
    """Horas que faltan: lo que resta del caso actual + cada pendiente segun su malla."""
    horas_malla = {}
    for c in cola["casos"]:
        if c.get("duracion_h"):
            horas_malla.setdefault(c["parametros"].get("malla", "media"), []).append(c["duracion_h"])
    # Mediana, no promedio: un caso que espero en la cola (c02 cedio su turno a c03) infla su duracion.
    horas_malla = {m: sorted(v)[len(v) // 2] for m, v in horas_malla.items()}
    resta = 0.0
    if caso_d is not None and ritmo:
        fin = caso_d.get("endTime", CFG["endTime"])
        m = caso_d["parametros"].get("malla", "media")
        horas_malla.setdefault(m, fin / ritmo / 3600)
        resta = (fin - (sim or 0)) / ritmo / 3600
    if not horas_malla:
        return None
    ref_m = max(horas_malla, key=lambda m: COSTO_MALLA.get(m, 1.0))   # la mas parecida a las grandes
    ref_h = horas_malla[ref_m]
    def horas(m):
        if m in horas_malla:
            return horas_malla[m]
        return ref_h * COSTO_MALLA.get(m, 1.0) / COSTO_MALLA.get(ref_m, 1.0)
    pendientes = [c for c in cola["casos"] if c["estado"] in ("pendiente", "pausado") and c is not caso_d]
    return resta + sum(horas(c["parametros"].get("malla", "media")) for c in pendientes)

def escribir_estado(cola, general, caso_d=None, sim=None, ritmo=None):
    casos = cola["casos"]
    cuenta = {e: sum(c["estado"] == e for c in casos)
              for e in ("terminado", "corriendo", "pausado", "pendiente", "fallido")}
    lineas = ["Cola CFD - Modeling and Simulation of Hot Metal Desulfurization",
              f"Actualizado: {ahora()}", f"Estado general: {general}", ""]
    if caso_d is not None:
        fin = caso_d.get("endTime", CFG["endTime"])
        avance = f"{sim:.3g} s de {fin:g} s simulados ({100 * sim / fin:.0f} %)" if sim else "iniciando"
        lineas += [f"Caso actual: {caso_d['id']}  {json.dumps(caso_d['parametros'], ensure_ascii=False)}",
                   f"Avance: {avance}"]
        if ritmo:
            resta = (fin - (sim or 0)) / ritmo
            lineas.append(f"Ritmo: {ritmo * 3600:.3g} s simulados por hora; termina el caso "
                          f"hacia {(datetime.now() + timedelta(seconds=resta)):%Y-%m-%d %H:%M}")
        lineas.append("")
    lineas.append("Casos: " + ", ".join(f"{v} {k}" for k, v in cuenta.items()))
    h = estimar_horas_restantes(cola, caso_d, sim, ritmo)
    if h is not None:
        lineas.append(f"Termino estimado de la cola: {(datetime.now() + timedelta(hours=h)):%Y-%m-%d %H:%M}"
                      f" (faltan ~{h:.0f} h)")
    lineas += ["", "Pausar: doble clic en Pausar.bat   Reanudar: doble clic en Reanudar.bat",
               "Avisos: AVISOS.txt   Detalle: cfd/bitacora/orquestador.log"]
    escribir_atomico(ESTADO, "\n".join(lineas) + "\n")


# ---------- un caso ----------

def correr_caso(cola, caso_d):
    cid = caso_d["id"]
    caso = ACTIVOS / cid
    fin = caso_d.get("endTime", CFG["endTime"])
    if not (caso / "resumen_caso.json").exists():      # solo un caso preparado completo lo tiene
        if not restaurar(cid, caso):
            preparar(caso_d, caso)
    ult = ultimo_valido(caso, limpiar=True)
    if ult and ult[0] >= fin - 1e-6:
        finalizar(caso_d, caso)
        guardar_cola(cola)
        return
    fijar(caso, "startFrom", "latestTime")
    fijar(caso, "stopAt", "endTime")
    # Con 6 digitos, un instante de pausa como 49.230123 se busca como "49.2301" y no existe.
    fijar(caso, "timePrecision", 12)
    # OpenFOAM cuenta los instantes de escritura desde donde reanuda; se alinea el final
    # con uno de ellos para que el ultimo estado siempre quede guardado.
    inicio_t = ult[0] if ult else 0.0
    cada = leer_control(caso, "writeInterval")
    pasos = max(1, math.ceil((fin - inicio_t) / cada - 1e-9))
    fijar(caso, "endTime", f"{inicio_t + pasos * cada:.10g}")
    fijar(caso, "maxCo", round(CFG["maxCo"] * caso_d.get("factor_maxCo", 1.0), 4))
    caso_d.update(estado="corriendo", ultimo_instante=ult[1] if ult else None)
    caso_d.setdefault("inicio", ahora())
    guardar_cola(cola)
    log(f"{cid}: arranca desde el instante {ult[1] if ult else 'inicial'}")
    global SOLVER
    proc = SOLVER = bash(f"{comando_solver()}", cwd=caso, log_archivo=caso / "log.solver")
    visto, pausando, fallo = ult, False, False
    t0, s0 = time.time(), (ult[0] if ult else 0.0)
    ultimo_avance = time.time()
    while proc.poll() is None:
        time.sleep(CFG["intervalo_s"])
        nuevo = ultimo_valido(caso)
        if nuevo and nuevo != visto and nuevo[0] > 0:
            respaldar(caso, nuevo, cid)
            visto = nuevo
            ultimo_avance = time.time()
            caso_d["ultimo_instante"] = nuevo[1]
            guardar_cola(cola)
        if (PAUSA.exists() or DETENER) and not pausando:
            log(f"{cid}: pausa solicitada, guardando el instante actual")
            fijar(caso, "stopAt", "writeNow")
            pausando = True
        if divergio(caso):
            log(f"{cid}: divergencia detectada en log.solver")
            detener(proc)
            fallo = True
            break
        if not pausando and time.time() - ultimo_avance > 60 * CFG.get("sin_avance_min", 180):
            log(f"{cid}: sin instantes nuevos en {CFG.get('sin_avance_min', 180)} min; se considera colgado")
            detener(proc)
            fallo = True
            break
        sim = visto[0] if visto else 0.0
        ritmo = (sim - s0) / (time.time() - t0) if sim > s0 else None
        escribir_estado(cola, "EN PAUSA (guardando)" if pausando else "CORRIENDO", caso_d, sim, ritmo)
    rc = proc.wait()
    ult = ultimo_valido(caso, limpiar=True)
    if ult and ult != visto and ult[0] > 0:
        respaldar(caso, ult, cid)
    caso_d["ultimo_instante"] = ult[1] if ult else None
    if not fallo and pausando:
        fijar(caso, "stopAt", "endTime")
        caso_d["estado"] = "pausado"
        log(f"{cid}: en pausa en el instante {caso_d['ultimo_instante']}")
    elif not fallo and rc == 0 and ult and ult[0] >= fin - 1e-6:
        finalizar(caso_d, caso)
    else:
        # Solo cuentan los fallos seguidos sin avanzar: un caso que progreso entre fallos no se descarta.
        avance = ult[0] if ult else 0.0
        if avance > caso_d.get("instante_ultimo_fallo", -1.0) + 1e-6:
            caso_d["intentos"] = 1
        else:
            caso_d["intentos"] = caso_d.get("intentos", 0) + 1
        caso_d["instante_ultimo_fallo"] = avance
        caso_d["factor_maxCo"] = max(0.125, caso_d.get("factor_maxCo", 1.0) * 0.5)
        aviso(f"{cid}: el solver fallo en {avance:g} s (codigo {rc}); se relanza con maxCo "
              f"{CFG['maxCo'] * caso_d['factor_maxCo']:g}")
        if caso_d["intentos"] >= CFG["max_intentos"]:
            caso_d["estado"] = "fallido"
            aviso(f"{cid} fallo {caso_d['intentos']} veces; se salta. Revisar {caso / 'log.solver'}")
        else:
            caso_d["estado"] = "pendiente"
            log(f"{cid}: fallo (codigo {rc}); se relanza con maxCo menor")
    guardar_cola(cola)


def finalizar(caso_d, caso):
    cid = caso_d["id"]
    if CFG.get("finalizar"):
        p = bash(CFG["finalizar"], cwd=caso, log_archivo=caso / "log.finalizar")
        p.wait()
    destino = TERMINADOS / cid
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(caso, destino, ignore=shutil.ignore_patterns("processor*"))
    inicio = datetime.strptime(caso_d["inicio"], "%Y-%m-%d %H:%M:%S")
    caso_d.update(estado="terminado", termino=ahora(), extraccion="pendiente",
                  duracion_h=round((datetime.now() - inicio).total_seconds() / 3600, 2))
    log(f"{cid}: terminado en {caso_d['duracion_h']} h; copiado a cfd/casos")


# ---------- ciclo principal ----------

def tomar_candado():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            os.kill(int(LOCK.read_text()), 0)
            print("El orquestador ya esta corriendo.")
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            pass
    LOCK.write_text(str(os.getpid()))


def al_detener(signum, frame):
    """Windows se apaga o cierran WSL: guardar el instante y salir sin marcar pausa."""
    global DETENER
    DETENER = True


def main():
    tomar_candado()
    signal.signal(signal.SIGTERM, al_detener)
    signal.signal(signal.SIGHUP, al_detener)
    log("orquestador iniciado")
    avisado_fin = False
    while not DETENER:
        cola = leer_cola()
        if PAUSA.exists():
            escribir_estado(cola, "EN PAUSA")
            time.sleep(CFG["intervalo_s"])
            continue
        casos = cola["casos"]
        caso_d = (next((c for c in casos if c["estado"] in ("corriendo", "pausado")), None)
                  or next((c for c in casos if c["estado"] == "pendiente"), None))
        if caso_d is None:
            escribir_estado(cola, "COLA TERMINADA")
            if not avisado_fin:
                aviso("la cola termino: todos los casos estan terminados o fallidos")
                avisado_fin = True
            if CFG.get("salir_al_terminar"):
                break
            time.sleep(60)
            continue
        avisado_fin = False
        try:
            correr_caso(cola, caso_d)
        except Exception:
            # Un error del orquestador no es un fallo del caso: se deja pendiente y se reintenta.
            # Solo tras 3 errores seguidos del orquestador en el mismo caso se marca y se salta.
            import traceback
            if SOLVER is not None and SOLVER.poll() is None:
                detener(SOLVER)        # nunca dejar un solver huerfano que choque con el relanzamiento
            caso_d["errores_orquestador"] = caso_d.get("errores_orquestador", 0) + 1
            caso_d["estado"] = "fallido" if caso_d["errores_orquestador"] >= 3 else "pendiente"
            guardar_cola(cola)
            aviso(f"{caso_d['id']}: error del orquestador ({caso_d['errores_orquestador']}):\n"
                  + traceback.format_exc())
            time.sleep(CFG["intervalo_s"])
    log("orquestador detenido")
    LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
