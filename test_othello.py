"""
Pruebas del agente de Othello: python -m unittest -v test_othello
  1. La generación de jugadas con bitboards coincide con la verificación casilla por casilla.
  2. Alpha-Beta devuelve el mismo valor que Minimax sin poda (incluye posiciones con pase).
  3. Las funciones E1, E2 y E3 usan los pesos de la Tabla 1 del artículo.
"""
import random
import unittest

import numpy as np

from AgenteIA.AgenteJugador import ElEstado
from AgentesEspecificos.AgenteOthello import AgenteOthello
from evaluador import EvaluadorOthello as EV

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def valida_lenta(b, p, r, c):
    if b[r, c] != 0:
        return False
    for dr, dc in DIRS:
        rr, cc, vio = r + dr, c + dc, False
        while 0 <= rr < 8 and 0 <= cc < 8 and b[rr, cc] == 3 - p:
            rr, cc, vio = rr + dr, cc + dc, True
        if vio and 0 <= rr < 8 and 0 <= cc < 8 and b[rr, cc] == p:
            return True
    return False


def posiciones(n, semilla=0):
    ag, rng, out = AgenteOthello(), random.Random(semilla), []
    for _ in range(n):
        t = np.zeros((8, 8), int)
        t[3, 3] = t[4, 4] = 2
        t[3, 4] = t[4, 3] = 1
        j = 1
        for _ in range(rng.randint(4, 56)):
            m = ag._get_valid_moves(t, j)
            if not m:
                break
            e = ag.getResultado(ElEstado(j, 0, t, m), rng.choice(m))
            t, j = e.tablero, e.jugador
        out.append((t, j))
    return out


def minimax(ag, e, prof, raiz):
    if ag.testTerminal(e) or prof >= ag.altura:
        return ag.funcion_evaluacion(e)
    vals = [minimax(ag, ag.getResultado(e, a), prof + 1, raiz) for a in ag.jugadas(e)]
    return max(vals) if e.jugador == raiz else min(vals)


class Pruebas(unittest.TestCase):
    def test_jugadas(self):
        ag = AgenteOthello()
        for t, _ in posiciones(200):
            for p in (1, 2):
                lenta = [(r, c) for r in range(8) for c in range(8) if valida_lenta(t, p, r, c)]
                self.assertEqual(ag._get_valid_moves(t, p), lenta)

    def test_alphabeta_igual_minimax(self):
        for modo in ('estatica', 'adaptativa', 'adaptativa_dinamica'):
            ag = AgenteOthello(altura=3, modo_evaluacion=modo, profundidad_dinamica=False)
            for t, j in posiciones(25, semilla=1):
                m = ag._get_valid_moves(t, j)
                if not m:
                    continue
                ag.estado = ElEstado(j, 0, t, m)
                ag.podaAlphaBeta_eval(ag.estado)
                esperado = max(minimax(ag, ag.getResultado(ag.estado, a), 1, j) for a in ag.jugadas(ag.estado))
                self.assertAlmostEqual(ag.valor_decision, esperado, places=9)

    def test_pesos_articulo(self):
        self.assertEqual(EV.PESOS_E1, (0.10, 0.35, 0.35, 0.20))
        f = EV._pesos_por_fase
        self.assertEqual(f(EV.PESOS_E2, 20), (0.00, 0.45, 0.30, 0.25))
        self.assertEqual(f(EV.PESOS_E2, 50), (0.15, 0.30, 0.40, 0.15))
        self.assertEqual(f(EV.PESOS_E2, 51), (0.75, 0.05, 0.20, 0.00))
        self.assertEqual(f(EV.PESOS_E3, 43), (0.15, 0.30, 0.40, 0.15))
        self.assertEqual(f(EV.PESOS_E3, 44), (0.45, 0.10, 0.35, 0.10))
        self.assertEqual([AgenteOthello.profundidad_E3(n) for n in (43, 44, 51, 52, 56, 60)], [4, 6, 6, 8, 8, 4])


if __name__ == '__main__':
    unittest.main()
