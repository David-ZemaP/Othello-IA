"""
Módulo EvaluadorOthello
Contiene las funciones heurísticas formalizadas matemáticamente en el artículo científico:
- f_P: Paridad de fichas (Coin Parity)
- f_M: Movilidad relativa (Actual Mobility)
- f_C: Control de esquinas y penalización de casillas de riesgo (Corners & Danger Zones)
- f_T: Control posicional según matriz de pesos (Positional Weight Matrix)

Soporta dos estrategias:
- E1: Component-Wise Estática (pesos fijos invariantes)
- E2: Adaptativa Dinámica por Fases (Apertura, Medio juego, Endgame)
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

    @staticmethod
    def fichas_frontera(tablero, jugador, oponente):
        """
        f_F(s): Estabilidad de frontera normalizada en [-100, 100].
        Una ficha es de frontera si tiene al menos un vecino vacío (en 8 direcciones).
        Tener MENOS fichas frontera es superior: reduce opciones al oponente y consolida el interior.
        Retorna valor positivo si 'jugador' tiene MENOS fichas frontera que 'oponente'.
        """
        vacio = (tablero == 0)
        vecino_de_vacio = np.zeros((8, 8), dtype=bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r_start = max(0, dr)
                r_end = min(8, 8 + dr)
                c_start = max(0, dc)
                c_end = min(8, 8 + dc)

                src_r_start = max(0, -dr)
                src_r_end = min(8, 8 - dr)
                src_c_start = max(0, -dc)
                src_c_end = min(8, 8 - dc)

                vecino_de_vacio[r_start:r_end, c_start:c_end] |= vacio[src_r_start:src_r_end, src_c_start:src_c_end]

        front_max = np.sum((tablero == jugador) & vecino_de_vacio)
        front_min = np.sum((tablero == oponente) & vecino_de_vacio)

        total = front_max + front_min
        if total == 0:
            return 0.0
        return 100.0 * (front_min - front_max) / total

    @classmethod
    def control_esquinas(cls, tablero, jugador, oponente):
        """
        f_C(s): Control de esquinas y estabilidad adyacente en [-100, 100].
        - Si la esquina está vacía: penaliza severamente ocupar casillas de riesgo (C y X).
        - Si la esquina está capturada: las casillas adyacentes del mismo dueño son 100% estables
          y se bonifican como bloque seguro en lugar de castigarse.
        """
        score = 0.0
        for esquina, adyacentes in cls.ESQUINAS_INFO:
            val_esquina = tablero[esquina]
            if val_esquina == jugador:
                score += 25.0
                # Esquina consolidada: adyacencias propias son estables y seguras (+5 c/u)
                for r_adj, c_adj in adyacentes:
                    if tablero[r_adj, c_adj] == jugador:
                        score += 5.0
            elif val_esquina == oponente:
                score -= 25.0
                # Esquina del rival consolidada: sus adyacencias le dan estabilidad (-5 c/u)
                for r_adj, c_adj in adyacentes:
                    if tablero[r_adj, c_adj] == oponente:
                        score -= 5.0
            else:
                # Esquina vacía: penalizar casillas peligrosas ocupadas (-12 c/u)
                for r_adj, c_adj in adyacentes:
                    val_adj = tablero[r_adj, c_adj]
                    if val_adj == jugador:
                        score -= 12.0
                    elif val_adj == oponente:
                        score += 12.0
        return float(np.clip(score, -100.0, 100.0))

    @classmethod
    def valor_posicional(cls, tablero, jugador, oponente):
        """f_T(s): Valor táctico posicional normalizado en [-100, 100]."""
        max_mask = (tablero == jugador)
        min_mask = (tablero == oponente)
        diff = np.sum(cls.PESOS_TABLERO[max_mask]) - np.sum(cls.PESOS_TABLERO[min_mask])
        return 100.0 * (diff / cls.TOTAL_PESOS_ABS)

    @classmethod
    def evaluar_estatica(cls, tablero, jugador, oponente, mov_max, mov_min):
        """Función E1: Component-Wise estática con métrica de frontera integrada."""
        f_P, _, _ = cls.paridad_fichas(tablero, jugador, oponente)
        f_M = cls.movilidad_relativa(mov_max, mov_min)
        f_F = cls.fichas_frontera(tablero, jugador, oponente)
        f_C = cls.control_esquinas(tablero, jugador, oponente)
        f_T = cls.valor_posicional(tablero, jugador, oponente)

        w_P, w_M, w_F, w_C, w_T = 0.05, 0.25, 0.20, 0.35, 0.15
        return (w_P * f_P) + (w_M * f_M) + (w_F * f_F) + (w_C * f_C) + (w_T * f_T)

    @classmethod
    def evaluar_adaptativa(cls, tablero, jugador, oponente, mov_max, mov_min):
        """Función E2: Adaptativa dinámica por fases de partida con control de frontera."""
        f_P, c_max, c_min = cls.paridad_fichas(tablero, jugador, oponente)
        f_M = cls.movilidad_relativa(mov_max, mov_min)
        f_F = cls.fichas_frontera(tablero, jugador, oponente)
        f_C = cls.control_esquinas(tablero, jugador, oponente)
        f_T = cls.valor_posicional(tablero, jugador, oponente)

        total_fichas = c_max + c_min
        if total_fichas <= 20:
            # Apertura: Movilidad y reducción de frontera dominan; paridad nula
            w_P, w_M, w_F, w_C, w_T = 0.00, 0.35, 0.25, 0.25, 0.15
        elif total_fichas <= 50:
            # Medio Juego: Esquinas y movilidad cruciales con frontera activa
            w_P, w_M, w_F, w_C, w_T = 0.10, 0.25, 0.20, 0.35, 0.10
        else:
            # Endgame: La paridad de discos determina la victoria
            w_P, w_M, w_F, w_C, w_T = 0.70, 0.05, 0.05, 0.20, 0.00

        return (w_P * f_P) + (w_M * f_M) + (w_F * f_F) + (w_C * f_C) + (w_T * f_T)

    @classmethod
    def evaluar_adaptativa_dinamica(cls, tablero, jugador, oponente, mov_max, mov_min):
        """Función E3: Adaptativa calibrada con frontera y resolución endgame profunda."""
        f_P, c_max, c_min = cls.paridad_fichas(tablero, jugador, oponente)
        f_M = cls.movilidad_relativa(mov_max, mov_min)
        f_F = cls.fichas_frontera(tablero, jugador, oponente)
        f_C = cls.control_esquinas(tablero, jugador, oponente)
        f_T = cls.valor_posicional(tablero, jugador, oponente)

        total_fichas = c_max + c_min
        if total_fichas <= 20:
            # Apertura: Foco en no exponer frontera y mantener movilidad alta
            w_P, w_M, w_F, w_C, w_T = 0.00, 0.35, 0.25, 0.25, 0.15
        elif total_fichas <= 48:
            # Medio juego: Balance táctico posicional y de esquinas
            w_P, w_M, w_F, w_C, w_T = 0.10, 0.25, 0.20, 0.35, 0.10
        else:
            # Endgame: La paridad de discos y esquinas define la victoria (apaga posición)
            w_P, w_M, w_F, w_C, w_T = 0.70, 0.05, 0.05, 0.20, 0.00

        return (w_P * f_P) + (w_M * f_M) + (w_F * f_F) + (w_C * f_C) + (w_T * f_T)
