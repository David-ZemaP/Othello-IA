"""
agente.py — punto de entrada del agente de Othello (estructura de entrega de la consigna).

El agente está implementado en AgentesEspecificos/AgenteOthello.py y la búsqueda
Alpha-Beta en AgenteIA/AgenteJugador.py; las funciones de evaluación E1, E2 y E3
están en evaluador.py.

Uso:
    from agente import AgenteOthello
    ia = AgenteOthello(altura=4, modo_evaluacion='estatica')   # E1
    ia = AgenteOthello(altura=4, modo_evaluacion='adaptativa') # E2
    ia = AgenteOthello(altura=4, modo_evaluacion='adaptativa_dinamica')  # E3
"""
from AgentesEspecificos.AgenteOthello import AgenteOthello

__all__ = ["AgenteOthello"]
