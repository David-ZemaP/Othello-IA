import sys
import os
import numpy as np

# Asegurar importación de módulos base
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AgenteIA.AgenteJugador import AgenteJugador, ElEstado
from evaluador import EvaluadorOthello


class AgenteOthello(AgenteJugador):
    """
    Agente de Inteligencia Artificial para Othello / Reversi.
    Implementa búsqueda adversarial Alpha-Beta con funciones de evaluación:
    - 'estatica' (E1): component-wise con pesos invariables, profundidad fija `altura`
    - 'adaptativa' (E2): pesos por fase, profundidad fija `altura`
    - 'adaptativa_dinamica' (E3): pesos por fase de E3 y profundidad d(N) del artículo
    """

    def __init__(self, altura=6, modo_evaluacion='adaptativa_dinamica', profundidad_dinamica=None):
        super().__init__(altura)
        self.BOARD_SIZE = 8
        self.altura_base = altura
        self.modo_evaluacion = modo_evaluacion
        if profundidad_dinamica is None:
            self.profundidad_dinamica = (modo_evaluacion in ['adaptativa_dinamica', 'e3'])
        else:
            self.profundidad_dinamica = profundidad_dinamica

    @staticmethod
    def profundidad_E3(n_fichas):
        """d(N) del artículo: 4 si N < 44; 6 si 44 <= N < 52; min(8, 64 - N) si N >= 52."""
        if n_fichas < 44:
            return 4
        if n_fichas < 52:
            return 6
        return min(8, 64 - n_fichas)

    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return
        if self.profundidad_dinamica:
            self.altura = self.profundidad_E3(int(np.sum(self.estado.tablero != 0)))
        else:
            self.altura = self.altura_base
        super().programa()

    def jugadas(self, estado):
        """
        Devuelve los movimientos válidos desde el estado actual.
        Ordena movimientos por su valor posicional intrínseco (Move Ordering)
        para maximizar los cortes de la poda Alpha-Beta.
        """
        if not estado.movidas:
            return []
        return sorted(
            estado.movidas,
            key=lambda m: EvaluadorOthello.PESOS_TABLERO[m[0], m[1]],
            reverse=True
        )

    def testTerminal(self, estado):
        """Un estado es terminal si ningún jugador tiene movimientos válidos."""
        return not estado.movidas

    def get_utilidad(self, estado, jugador):
        """Calcula la utilidad de un estado terminal."""
        if not self.testTerminal(estado):
            return 0
        
        score_jugador = np.sum(estado.tablero == jugador)
        score_oponente = np.sum(estado.tablero == (3 - jugador))
        
        if score_jugador > score_oponente:
            return 10000.0 + (score_jugador - score_oponente)
        elif score_oponente > score_jugador:
            return -10000.0 - (score_oponente - score_jugador)
        else:
            return 0.0

    def getResultado(self, estado, jugada):
        """Devuelve el nuevo estado del juego tras aplicar una jugada."""
        if jugada not in estado.movidas:
            return estado

        nuevo_tablero = np.copy(estado.tablero)
        jugador_actual = estado.jugador
        
        # Realizar la jugada
        nuevo_tablero[jugada] = jugador_actual

        # Volteo de fichas en 8 direcciones
        oponente = 3 - jugador_actual
        direcciones = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dr, dc in direcciones:
            r, c = jugada[0] + dr, jugada[1] + dc
            fichas_a_voltear = []
            
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and nuevo_tablero[r, c] == oponente:
                fichas_a_voltear.append((r, c))
                r += dr
                c += dc
            
            if 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and nuevo_tablero[r, c] == jugador_actual:
                for fr, fc in fichas_a_voltear:
                    nuevo_tablero[fr, fc] = jugador_actual

        # Calcular siguiente jugador y sus movimientos
        siguiente_jugador = 3 - jugador_actual
        movidas_siguiente = self._get_valid_moves(nuevo_tablero, siguiente_jugador)

        # Si el oponente no tiene movimientos, el turno vuelve al jugador actual (regla de pase)
        if not movidas_siguiente:
            siguiente_jugador = jugador_actual
            movidas_siguiente = self._get_valid_moves(nuevo_tablero, siguiente_jugador)

        return ElEstado(
            jugador=siguiente_jugador,
            tablero=nuevo_tablero,
            movidas=movidas_siguiente,
            get_utilidad=0
        )

    def funcion_evaluacion(self, estado):
        """
        Función heurística que evalúa el estado del tablero desde la perspectiva
        del agente que toma la decisión (self.estado.jugador).
        """
        jugador_max = self.estado.jugador
        oponente_min = 3 - jugador_max

        # Si se alcanza un estado terminal en la búsqueda
        if self.testTerminal(estado):
            score_max = np.sum(estado.tablero == jugador_max)
            score_min = np.sum(estado.tablero == oponente_min)
            if score_max > score_min:
                return 10000.0 + (score_max - score_min)
            elif score_min > score_max:
                return -10000.0 - (score_min - score_max)
            else:
                return 0.0

        # Calcular movilidad disponible para ambos jugadores
        mov_max = len(self._get_valid_moves(estado.tablero, jugador_max))
        mov_min = len(self._get_valid_moves(estado.tablero, oponente_min))

        if self.modo_evaluacion == 'estatica':
            return EvaluadorOthello.evaluar_estatica(
                estado.tablero, jugador_max, oponente_min, mov_max, mov_min
            )
        elif self.modo_evaluacion in ['adaptativa_dinamica', 'e3']:
            return EvaluadorOthello.evaluar_adaptativa_dinamica(
                estado.tablero, jugador_max, oponente_min, mov_max, mov_min
            )
        else:
            return EvaluadorOthello.evaluar_adaptativa(
                estado.tablero, jugador_max, oponente_min, mov_max, mov_min
            )

    # --- Métodos auxiliares de validación de jugadas ---
    # Generación de jugadas con bitboards (enteros de 64 bits, bit i = casilla r*8+c).
    # Devuelve exactamente las mismas jugadas y en el mismo orden (fila por fila) que la
    # versión anterior casilla por casilla, pero ~20 veces más rápido.
    _FULL = (1 << 64) - 1
    _NO_COL0 = sum(1 << i for i in range(64) if i % 8 != 0)
    _NO_COL7 = sum(1 << i for i in range(64) if i % 8 != 7)
    _DIRS = ((1, _NO_COL0), (-1, _NO_COL7), (8, _FULL), (-8, _FULL),
             (9, _NO_COL0), (-9, _NO_COL7), (7, _NO_COL7), (-7, _NO_COL0))
    _POT = (np.uint64(1) << np.arange(64, dtype=np.uint64))

    @classmethod
    def _bitboards(cls, board, player):
        plano = board.ravel()
        p = int(np.dot((plano == player).astype(np.uint64), cls._POT))
        o = int(np.dot((plano == 3 - player).astype(np.uint64), cls._POT))
        return p, o

    @classmethod
    def _desplazar(cls, b, d, mascara):
        return ((b << d) if d > 0 else (b >> -d)) & mascara

    @classmethod
    def _mascara_jugadas(cls, p, o):
        """Bitboard de jugadas legales para el jugador con fichas p contra o."""
        vacias = ~(p | o) & cls._FULL
        jugadas = 0
        for d, m in cls._DIRS:
            if d > 0:
                x = (p << d) & m & o
                x |= (x << d) & m & o
                x |= (x << d) & m & o
                x |= (x << d) & m & o
                x |= (x << d) & m & o
                x |= (x << d) & m & o
                jugadas |= (x << d) & m & vacias
            else:
                e = -d
                x = (p >> e) & m & o
                x |= (x >> e) & m & o
                x |= (x >> e) & m & o
                x |= (x >> e) & m & o
                x |= (x >> e) & m & o
                x |= (x >> e) & m & o
                jugadas |= (x >> e) & m & vacias
        return jugadas

    def _is_valid_move(self, board, player, row, col):
        p, o = self._bitboards(board, player)
        return bool((self._mascara_jugadas(p, o) >> (row * 8 + col)) & 1)

    def _get_valid_moves(self, board, player):
        p, o = self._bitboards(board, player)
        b = self._mascara_jugadas(p, o)
        movs = []
        while b:
            low = b & -b
            i = low.bit_length() - 1
            movs.append((i >> 3, i & 7))
            b ^= low
        return movs
