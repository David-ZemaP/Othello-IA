"""
torneo.py
Enfrentamientos automatizados entre agentes de Othello.

Genera el CSV exigido por la práctica (datos/resultados_othello.csv) con las columnas
agente_a, agente_b, ganador, diferencia_fichas, profundidad_a, profundidad_b, tiempo_a, tiempo_b
y columnas adicionales para el análisis (fichas, nodos, nodos/s, semilla, color, etc.).

Condiciones controladas:
  * Profundidad fija por agente (E3 además profundiza en el final, ver AgenteOthello.programa).
  * Apertura aleatoria documentada: antes de que jueguen los agentes se hacen
    `--apertura` jugadas legales al azar (por defecto 4) con la semilla `semilla_base + par`.
    Sin esto los agentes son deterministas y las 100 partidas serían la misma partida repetida.
  * Diseño pareado: cada apertura se juega dos veces, intercambiando los colores
    (con --sin_pares cada partida usa su propia apertura; se usa en las partidas espejo,
    donde jugar la misma apertura con colores cambiados repetiría la misma partida).
  * Tiempos medidos con time.perf_counter().

Uso:
  python torneo.py --modo_a estatica --modo_b adaptativa --altura_a 4 --altura_b 4 \
                   --partidas 100 --semilla 3000 --csv ../../datos/resultados_othello.csv \
                   --posiciones ../../datos/posiciones_othello.csv
"""

import argparse
import csv
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from AgenteIA.AgenteJugador import ElEstado
from AgentesEspecificos.AgenteOthello import AgenteOthello

NOMBRES = {'estatica': 'E1', 'adaptativa': 'E2', 'adaptativa_dinamica': 'E3',
           'adaptativa_dinamica_fija': 'E3fija'}   # E3fija: pesos de E3 con profundidad fija (ablación)
CORTES_POSICION = (20, 30, 40, 50)   # fichas en el tablero en las que se guarda la posición


def tablero_inicial():
    t = np.zeros((8, 8), dtype=int)
    t[3, 3] = t[4, 4] = 2   # blancas
    t[3, 4] = t[4, 3] = 1   # negras
    return t


def apertura_aleatoria(n_jugadas, semilla, validador):
    """Juega n_jugadas legales al azar desde la posición inicial. Devuelve (tablero, jugador)."""
    rng = random.Random(semilla)
    t, jugador = tablero_inicial(), 1
    for _ in range(n_jugadas):
        movs = validador._get_valid_moves(t, jugador)
        e = ElEstado(jugador=jugador, get_utilidad=0, tablero=t, movidas=movs)
        nuevo = validador.getResultado(e, rng.choice(movs))
        t, jugador = nuevo.tablero, nuevo.jugador
    return t, jugador


def jugar_partida(agente_negro, agente_blanco, tablero, jugador):
    """Juega desde (tablero, jugador) hasta el final. Devuelve métricas y posiciones intermedias."""
    met = {1: {'t': [], 'nodos': [], 'evals': [], 'prof': []},
           2: {'t': [], 'nodos': [], 'evals': [], 'prof': []}}
    posiciones = []
    pendientes = list(CORTES_POSICION)
    validador = agente_negro
    while True:
        fichas = int(np.sum(tablero != 0))
        while pendientes and fichas >= pendientes[0]:
            posiciones.append((pendientes.pop(0), fichas, jugador,
                               ''.join(map(str, tablero.ravel().tolist()))))
        movidas = validador._get_valid_moves(tablero, jugador)
        if not movidas:
            if not validador._get_valid_moves(tablero, 3 - jugador):
                break                                   # fin: nadie puede mover
            jugador = 3 - jugador                       # pase
            continue
        agente = agente_negro if jugador == 1 else agente_blanco
        estado = ElEstado(jugador=jugador, tablero=tablero, movidas=movidas, get_utilidad=0)
        agente.estado = estado
        agente.programa()
        accion = agente.get_acciones()
        if not accion or accion not in movidas:
            raise RuntimeError(f"Jugada ilegal {accion}")
        m = met[jugador]
        m['t'].append(agente.tiempo_decision)
        m['nodos'].append(agente.nodos)
        m['evals'].append(agente.evaluaciones)
        m['prof'].append(agente.altura)
        nuevo = agente.getResultado(estado, accion)
        tablero, jugador = nuevo.tablero, nuevo.jugador
    return int(np.sum(tablero == 1)), int(np.sum(tablero == 2)), met, posiciones


def crear_agente(modo, altura):
    if modo == 'adaptativa_dinamica_fija':
        return AgenteOthello(altura=altura, modo_evaluacion='adaptativa_dinamica', profundidad_dinamica=False)
    return AgenteOthello(altura=altura, modo_evaluacion=modo)


def _una_partida(args):
    (k, modo_a, alt_a, modo_b, alt_b, n_apertura, semilla_base, pareado) = args
    par = k // 2 if pareado else k
    semilla = semilla_base + par
    a_es_negro = (k % 2 == 0)
    ag_a, ag_b = crear_agente(modo_a, alt_a), crear_agente(modo_b, alt_b)
    negro, blanco = (ag_a, ag_b) if a_es_negro else (ag_b, ag_a)
    t, j = apertura_aleatoria(n_apertura, semilla, ag_a)
    t0 = time.perf_counter()
    fn, fb, met, pos = jugar_partida(negro, blanco, t, j)
    duracion = time.perf_counter() - t0
    fa, fb_ = (fn, fb) if a_es_negro else (fb, fn)
    ma, mb = (met[1], met[2]) if a_es_negro else (met[2], met[1])
    return k, semilla, a_es_negro, fa, fb_, ma, mb, pos, duracion


def ejecutar_torneo(modo_a, altura_a, modo_b, altura_b, partidas, semilla_base, n_apertura,
                    salida_csv, salida_pos=None, workers=None, etiqueta=None, pareado=True):
    nombre_a = f"{NOMBRES[modo_a]}_d{altura_a}"
    nombre_b = f"{NOMBRES[modo_b]}_d{altura_b}"
    if nombre_a == nombre_b:
        nombre_a, nombre_b = nombre_a + "_A", nombre_b + "_B"
    etiqueta = etiqueta or f"{nombre_a}_vs_{nombre_b}"
    tareas = [(k, modo_a, altura_a, modo_b, altura_b, n_apertura, semilla_base, pareado) for k in range(partidas)]
    workers = workers or max(1, (os.cpu_count() or 2))
    filas, filas_pos = [], []
    ultima = semilla_base + (partidas // 2 if pareado else partidas) - 1
    print(f"Torneo {etiqueta}: {partidas} partidas, semillas {semilla_base}..{ultima}",
          flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for hechos, (k, semilla, a_negro, fa, fb, ma, mb, pos, dur) in enumerate(ex.map(_una_partida, tareas), 1):
            ganador = nombre_a if fa > fb else nombre_b if fb > fa else "Empate"

            def resumen(m):
                t = sum(m['t'])
                return (np.mean(m['t']) if m['t'] else 0.0, np.mean(m['nodos']) if m['nodos'] else 0.0,
                        (sum(m['nodos']) / t) if t > 0 else 0.0, np.mean(m['evals']) if m['evals'] else 0.0,
                        max(m['prof']) if m['prof'] else 0, len(m['t']))
            ta, na, nsa, ea, pa, ja = resumen(ma)
            tb, nb, nsb, eb, pb, jb = resumen(mb)
            filas.append({
                'agente_a': nombre_a, 'agente_b': nombre_b, 'ganador': ganador,
                'diferencia_fichas': fa - fb,
                'profundidad_a': altura_a, 'profundidad_b': altura_b,
                'tiempo_a': round(ta, 5), 'tiempo_b': round(tb, 5),
                'fichas_a': fa, 'fichas_b': fb, 'color_a': 'negro' if a_negro else 'blanco',
                'nodos_a': round(na, 1), 'nodos_b': round(nb, 1),
                'nodos_seg_a': round(nsa, 1), 'nodos_seg_b': round(nsb, 1),
                'evals_a': round(ea, 1), 'evals_b': round(eb, 1),
                'prof_max_a': pa, 'prof_max_b': pb, 'jugadas_a': ja, 'jugadas_b': jb,
                'semilla_apertura': semilla, 'jugadas_apertura': n_apertura, 'partida': k,
                'experimento': etiqueta,
            })
            dif_negro = (fa - fb) if a_negro else (fb - fa)
            for corte, fichas, turno, tab in pos:
                filas_pos.append({'experimento': etiqueta, 'partida': k, 'corte': corte, 'fichas': fichas,
                                  'turno': turno, 'tablero': tab, 'dif_final_negro': dif_negro})
            if hechos % 10 == 0:
                ga = sum(f['ganador'] == nombre_a for f in filas)
                gb = sum(f['ganador'] == nombre_b for f in filas)
                print(f"  {hechos}/{partidas}  {nombre_a} {ga} - {gb} {nombre_b}", flush=True)

    for ruta, datos in ((salida_csv, filas), (salida_pos, filas_pos)):
        if not ruta or not datos:
            continue
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        nuevo = not os.path.exists(ruta)
        with open(ruta, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(datos[0].keys()))
            if nuevo:
                w.writeheader()
            w.writerows(datos)
    return filas


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Torneo de IAs para Othello")
    p.add_argument("--partidas", type=int, default=100)
    p.add_argument("--altura_a", type=int, default=4)
    p.add_argument("--modo_a", choices=list(NOMBRES), default="adaptativa_dinamica")
    p.add_argument("--altura_b", type=int, default=4)
    p.add_argument("--modo_b", choices=list(NOMBRES), default="estatica")
    p.add_argument("--semilla", type=int, default=3000, help="semilla de la primera apertura")
    p.add_argument("--apertura", type=int, default=4, help="jugadas aleatorias iniciales")
    p.add_argument("--csv", default="../../datos/resultados_othello.csv")
    p.add_argument("--posiciones", default=None, help="CSV de posiciones intermedias (opcional)")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--etiqueta", default=None)
    p.add_argument("--sin_pares", action="store_true",
                   help="una apertura distinta por partida (para partidas espejo entre agentes idénticos)")
    a = p.parse_args()
    ejecutar_torneo(a.modo_a, a.altura_a, a.modo_b, a.altura_b, a.partidas, a.semilla, a.apertura,
                    a.csv, a.posiciones, a.workers, a.etiqueta, pareado=not a.sin_pares)
