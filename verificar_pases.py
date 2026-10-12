"""
verificar_pases.py
Cuenta en cuántas posiciones la búsqueda Alpha-Beta anterior (MAX/MIN por paridad de la
profundidad) elige una jugada distinta de la corregida (MAX/MIN según el jugador que mueve,
lo que importa cuando hay un pase dentro del árbol).
600 posiciones aleatorias (semilla 7, de 4 a 56 jugadas al azar), E1, profundidad 4.
Uso: python verificar_pases.py
"""
from AgenteIA.AgenteJugador import ElEstado
from AgentesEspecificos.AgenteOthello import AgenteOthello
from test_othello import posiciones


def alphabeta_por_paridad(ag, estado):
    def mx(e, a, b, p):
        if ag.testTerminal(e) or p >= ag.altura:
            return ag.funcion_evaluacion(e)
        v = -float('inf')
        for x in ag.jugadas(e):
            v = max(v, mn(ag.getResultado(e, x), a, b, p + 1))
            if v >= b:
                return v
            a = max(a, v)
        return v

    def mn(e, a, b, p):
        if ag.testTerminal(e) or p >= ag.altura:
            return ag.funcion_evaluacion(e)
        v = float('inf')
        for x in ag.jugadas(e):
            v = min(v, mx(ag.getResultado(e, x), a, b, p + 1))
            if v <= a:
                return v
            b = min(b, v)
        return v
    mejor, accion = -float('inf'), None
    for x in ag.jugadas(estado):
        v = mn(ag.getResultado(estado, x), mejor, float('inf'), 1)
        if v > mejor:
            mejor, accion = v, x
    return accion


if __name__ == '__main__':
    ag = AgenteOthello(altura=4, modo_evaluacion='estatica')
    total = distintas = 0
    for t, j in posiciones(600, semilla=7):
        m = ag._get_valid_moves(t, j)
        if not m:
            continue
        total += 1
        ag.estado = ElEstado(j, 0, t, m)
        if alphabeta_por_paridad(ag, ag.estado) != ag.podaAlphaBeta_eval(ag.estado):
            distintas += 1
    print(f"posiciones: {total}  decisiones distintas: {distintas} ({100 * distintas / total:.1f} %)")
    import csv, os
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'datos', 'verificacion_pases_othello.csv')
    with open(ruta, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['posiciones', 'decisiones_distintas', 'porcentaje', 'funcion', 'profundidad', 'semilla'])
        w.writerow([total, distintas, round(100 * distintas / total, 2), 'E1', 4, 7])
