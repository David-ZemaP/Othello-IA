from AgenteIA.Agente import Agente
from collections import namedtuple
import time

ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')


class AgenteJugador(Agente):
    def __init__(self, altura=3):
        Agente.__init__(self)
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta"  # Por defecto
        # Métricas de la última decisión (las usa torneo.py)
        self.nodos = 0            # nodos expandidos (llamadas a la búsqueda)
        self.evaluaciones = 0     # llamadas a funcion_evaluacion en las hojas
        self.tiempo_decision = 0.0
        self.valor_decision = 0.0  # valor minimax de la jugada elegida

    def jugadas(self, estado):
        raise NotImplementedError

    def get_utilidad(self, estado, jugador):
        raise NotImplementedError

    def testTerminal(self, estado):
        return not estado.movidas

    def getResultado(self, estado, m):
        raise NotImplementedError

    def funcion_evaluacion(self, estado):
        raise NotImplementedError

    def podaAlphaBeta_eval(self, estado):
        """
        Minimax con poda Alpha-Beta y corte por profundidad (self.altura).

        El tipo de nodo (MAX o MIN) se decide por el jugador que mueve en cada estado
        y no por la paridad de la profundidad: en Othello un jugador puede pasar y
        mover dos veces seguidas, y en ese caso el nodo sigue siendo MAX.
        """
        raiz = estado.jugador

        def valor(e, alpha, beta, profundidad):
            self.nodos += 1
            if self.testTerminal(e) or profundidad >= self.altura:
                self.evaluaciones += 1
                return self.funcion_evaluacion(e)
            if e.jugador == raiz:                      # nodo MAX
                v = -float('inf')
                for accion in self.jugadas(e):
                    v = max(v, valor(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                    if v >= beta:
                        return v
                    alpha = max(alpha, v)
                return v
            v = float('inf')                           # nodo MIN
            for accion in self.jugadas(e):
                v = min(v, valor(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v

        acciones = self.jugadas(estado)
        mejor_score = -float('inf')
        mejor_accion = acciones[0] if acciones else None
        self.nodos += 1
        for accion in acciones:
            v = valor(self.getResultado(estado, accion), mejor_score, float('inf'), 1)
            if v > mejor_score:
                mejor_score = v
                mejor_accion = accion
        self.valor_decision = mejor_score
        return mejor_accion

    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return
        self.nodos = 0
        self.evaluaciones = 0
        inicio = time.perf_counter()
        self.set_acciones(self.podaAlphaBeta_eval(self.estado))
        self.tiempo_decision = time.perf_counter() - inicio
