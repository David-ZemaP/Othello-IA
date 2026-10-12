"""
Módulo EvaluadorOthello
Contiene las funciones heurísticas formalizadas matemáticamente en el artículo científico:
- f_P: Paridad de fichas (Coin Parity)
- f_M: Movilidad relativa (Actual Mobility)
- f_C: Control de esquinas y penalización de casillas de riesgo (Corners & Danger Zones)
- f_T: Control posicional según matriz de pesos (Positional Weight Matrix)

Funciones de evaluación (Sección 3.3 y Tabla 1 del artículo):
- E1: Component-Wise Estática      E1 = 0.10 f_P + 0.35 f_M + 0.35 f_C + 0.20 f_T
- E2: Adaptativa por fases          pesos según N = fichas en el tablero (4-20, 21-50, 51-64)
- E3: Adaptativa con solver final   pesos según N (4-20, 21-43, 44-64) + profundidad d(N)
                                    (la profundidad d(N) se aplica en AgenteOthello.programa)
"""

import numpy as np


class EvaluadorOthello:
    # Matriz posicional estática estándar de la literatura (8x8)
    PESOS_TABLERO = np.array([
        [ 100, -20,  10,   5,   5,  10, -20,  100],
        [ -20, -50,  -2,  -2,  -2,  -2, -50,  -20],
        [  10,  -2,  -1,  -1,  -1,  -1,  -2,   10],
        [   5,  -2,  -1,   0,   0,  -1,  -2,    5],
        [   5,  -2,  -1,   0,   0,  -1,  -2,    5],
        [  10,  -2,  -1,  -1,  -1,  -1,  -2,   10],
        [ -20, -50,  -2,  -2,  -2,  -2, -50,  -20],
        [ 100, -20,  10,   5,   5,  10, -20,  100]
    ], dtype=float)

    # Esquinas y sus casillas adyacentes de riesgo (casillas C y X)
    ESQUINAS_INFO = [
        ((0, 0), [(0, 1), (1, 0), (1, 1)]),
        ((0, 7), [(0, 6), (1, 7), (1, 6)]),
        ((7, 0), [(6, 0), (7, 1), (6, 1)]),
        ((7, 7), [(7, 6), (6, 7), (6, 6)])
    ]

    TOTAL_PESOS_ABS = np.sum(np.abs(PESOS_TABLERO))

    @staticmethod
    def paridad_fichas(tablero, jugador, oponente):
        """f_P(s): Paridad de fichas normalizada en [-100, 100]."""
        c_max = np.sum(tablero == jugador)
        c_min = np.sum(tablero == oponente)
        total = c_max + c_min
        if total == 0:
            return 0.0, c_max, c_min
        return 100.0 * (c_max - c_min) / total, c_max, c_min

    @staticmethod
    def movilidad_relativa(mov_max, mov_min):
        """f_M(s): Movilidad relativa normalizada en [-100, 100]."""
        total = mov_max + mov_min
        if total == 0:
            return 0.0
        return 100.0 * (mov_max - mov_min) / total

    @classmethod
    def control_esquinas(cls, tablero, jugador, oponente):
        """
        f_C(s) = sum_e v(e), con v(e) en [-25, 25] (ecuaciones de f_C y v(e) del artículo):
          v(e) = +25 si la esquina es de MAX, -25 si es de MIN; si está vacía,
          v(e) = sum_{d en D(e)} pen(d), con pen(d) = -10 si la casilla C/X es de MAX
          y +10 si es de MIN, acotado a [-25, 25]. Resultado en [-100, 100].
        """
        score = 0.0
        for esquina, adyacentes in cls.ESQUINAS_INFO:
            val_esquina = tablero[esquina]
            if val_esquina == jugador:
                v = 25.0
            elif val_esquina == oponente:
                v = -25.0
            else:
                v = 0.0
                for r_adj, c_adj in adyacentes:
                    val_adj = tablero[r_adj, c_adj]
                    if val_adj == jugador:
                        v -= 10.0
                    elif val_adj == oponente:
                        v += 10.0
                v = max(-25.0, min(25.0, v))
            score += v
        return score

    @classmethod
    def valor_posicional(cls, tablero, jugador, oponente):
        """f_T(s): Valor táctico posicional normalizado en [-100, 100]."""
        max_mask = (tablero == jugador)
        min_mask = (tablero == oponente)
        diff = np.sum(cls.PESOS_TABLERO[max_mask]) - np.sum(cls.PESOS_TABLERO[min_mask])
        return 100.0 * (diff / cls.TOTAL_PESOS_ABS)

    # ------------------------------------------------------------------
    # Pesos (w_P, w_M, w_C, w_T) — Ecuación de E1 y Tabla 1 del artículo
    # ------------------------------------------------------------------
    PESOS_E1 = (0.10, 0.35, 0.35, 0.20)
    PESOS_E2 = (((20, (0.00, 0.45, 0.30, 0.25)),      # apertura   4 <= N <= 20
                 (50, (0.15, 0.30, 0.40, 0.15)),      # medio      21 <= N <= 50
                 (64, (0.75, 0.05, 0.20, 0.00))))     # final      51 <= N <= 64
    PESOS_E3 = (((20, (0.00, 0.45, 0.30, 0.25)),      # apertura   4 <= N <= 20
                 (43, (0.15, 0.30, 0.40, 0.15)),      # medio      21 <= N <= 43
                 (64, (0.45, 0.10, 0.35, 0.10))))     # final      44 <= N <= 64

    @staticmethod
    def _pesos_por_fase(tabla, n_fichas):
        for limite, pesos in tabla:
            if n_fichas <= limite:
                return pesos
        return tabla[-1][1]

    @classmethod
    def _combinar(cls, pesos, tablero, jugador, oponente, mov_max, mov_min, f_P=None):
        w_P, w_M, w_C, w_T = pesos
        if f_P is None:
            f_P = cls.paridad_fichas(tablero, jugador, oponente)[0]
        f_M = cls.movilidad_relativa(mov_max, mov_min)
        f_C = cls.control_esquinas(tablero, jugador, oponente)
        f_T = cls.valor_posicional(tablero, jugador, oponente)
        return w_P * f_P + w_M * f_M + w_C * f_C + w_T * f_T

    @classmethod
    def evaluar_estatica(cls, tablero, jugador, oponente, mov_max, mov_min):
        """E1(s) = 0.10 f_P + 0.35 f_M + 0.35 f_C + 0.20 f_T (pesos invariables)."""
        return cls._combinar(cls.PESOS_E1, tablero, jugador, oponente, mov_max, mov_min)

    @classmethod
    def evaluar_adaptativa(cls, tablero, jugador, oponente, mov_max, mov_min):
        """E2(s) = w_P(N) f_P + w_M(N) f_M + w_C(N) f_C + w_T(N) f_T con los pesos de E2 en la Tabla 1."""
        f_P, c_max, c_min = cls.paridad_fichas(tablero, jugador, oponente)
        pesos = cls._pesos_por_fase(cls.PESOS_E2, c_max + c_min)
        return cls._combinar(pesos, tablero, jugador, oponente, mov_max, mov_min, f_P)

    @classmethod
    def evaluar_adaptativa_dinamica(cls, tablero, jugador, oponente, mov_max, mov_min):
        """E3(s): misma forma que E2 con los pesos de E3 en la Tabla 1 (final desde N = 44)."""
        f_P, c_max, c_min = cls.paridad_fichas(tablero, jugador, oponente)
        pesos = cls._pesos_por_fase(cls.PESOS_E3, c_max + c_min)
        return cls._combinar(pesos, tablero, jugador, oponente, mov_max, mov_min, f_P)
