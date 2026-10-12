"""
bench_jugadas.py
Compara la generación de jugadas anterior (casilla por casilla, 8 direcciones) con la actual
(bitboards). Verifica que ambas devuelvan la misma lista y mide el tiempo medio por llamada.
Uso: python bench_jugadas.py  -> datos/bench_jugadas_othello.csv
"""
import csv
import os
import time

from AgentesEspecificos.AgenteOthello import AgenteOthello
from test_othello import posiciones

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _is_valid_move_anterior(board, player, row, col):
    """Copia literal del método usado antes de la mejora."""
    if board[row, col] != 0:
        return False
    opponent = 3 - player
    for dr, dc in DIRS:
        r, c = row + dr, col + dc
        found_opponent = False
        while 0 <= r < 8 and 0 <= c < 8 and board[r, c] == opponent:
            found_opponent = True
            r += dr
            c += dc
        if found_opponent and 0 <= r < 8 and 0 <= c < 8 and board[r, c] == player:
            return True
    return False


def get_valid_moves_anterior(board, player):
    return [(r, c) for r in range(8) for c in range(8) if _is_valid_move_anterior(board, player, r, c)]


if __name__ == '__main__':
    ag = AgenteOthello()
    pos = posiciones(500, semilla=11)
    for t, j in pos:
        assert get_valid_moves_anterior(t, j) == ag._get_valid_moves(t, j)
    filas = []
    for nombre, f in (('anterior (casilla por casilla)', get_valid_moves_anterior),
                      ('bitboards', ag._get_valid_moves)):
        t0 = time.perf_counter()
        for _ in range(5):
            for t, j in pos:
                f(t, j)
        us = (time.perf_counter() - t0) / (5 * len(pos)) * 1e6
        filas.append({'implementacion': nombre, 'microsegundos_por_llamada': round(us, 2), 'posiciones': len(pos)})
        print(f"{nombre:32s} {us:8.2f} us")
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'datos', 'bench_jugadas_othello.csv')
    with open(ruta, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
