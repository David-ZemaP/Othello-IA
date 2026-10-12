"""
eficiencia_othello.py
Costo de cada componente de la función de evaluación y de cada E_k por llamada.

Se toman posiciones reales (datos/posiciones_othello.csv) y se mide el tiempo medio
de f_P, f_M (incluye generar las jugadas de ambos jugadores), f_C y f_T, y de
E1, E2 y E3 completas. Salida: datos/costo_componentes_othello.csv

Uso: python eficiencia_othello.py --repeticiones 20
"""

import argparse
import csv
import os
import time

import numpy as np

from AgentesEspecificos.AgenteOthello import AgenteOthello
from evaluador import EvaluadorOthello as EV

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, '..', '..', 'datos')


def cargar_posiciones(maximo=400):
    filas = list(csv.DictReader(open(os.path.join(DATOS, 'posiciones_othello.csv'))))
    tabs = []
    for f in filas[:maximo]:
        t = np.array([int(c) for c in f['tablero']], dtype=int).reshape(8, 8)
        tabs.append((t, int(f['turno'])))
    return tabs


def medir(func, posiciones, rep):
    t0 = time.perf_counter()
    for _ in range(rep):
        for t, j in posiciones:
            func(t, j)
    return (time.perf_counter() - t0) / (rep * len(posiciones)) * 1e6   # microsegundos


def main(rep):
    pos = cargar_posiciones()
    ag = AgenteOthello()
    mov = lambda t, j: (len(ag._get_valid_moves(t, j)), len(ag._get_valid_moves(t, 3 - j)))
    componentes = {
        'f_P paridad': lambda t, j: EV.paridad_fichas(t, j, 3 - j),
        'f_M movilidad (incluye generar jugadas)': lambda t, j: EV.movilidad_relativa(*mov(t, j)),
        'f_C esquinas': lambda t, j: EV.control_esquinas(t, j, 3 - j),
        'f_T posicional': lambda t, j: EV.valor_posicional(t, j, 3 - j),
        'E1 completa': lambda t, j: EV.evaluar_estatica(t, j, 3 - j, *mov(t, j)),
        'E2 completa': lambda t, j: EV.evaluar_adaptativa(t, j, 3 - j, *mov(t, j)),
        'E3 completa': lambda t, j: EV.evaluar_adaptativa_dinamica(t, j, 3 - j, *mov(t, j)),
    }
    filas = []
    for nombre, f in componentes.items():
        us = medir(f, pos, rep)
        filas.append({'componente': nombre, 'microsegundos_por_llamada': round(us, 2),
                      'posiciones': len(pos), 'repeticiones': rep})
        print(f"{nombre:45s} {us:8.2f} us")
    with open(os.path.join(DATOS, 'costo_componentes_othello.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--repeticiones', type=int, default=20)
    main(ap.parse_args().repeticiones)
