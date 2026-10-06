"""
torneo.py
Script para ejecutar enfrentamientos automatizados entre agentes de Othello
y generar el archivo de datos estadísticos oficial exigido por la práctica:
datos/resultados_othello.csv
"""

import os
import sys
import time
import csv
import argparse
import numpy as np

# Asegurar importación de módulos
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from AgenteIA.AgenteJugador import ElEstado
from AgentesEspecificos.AgenteOthello import AgenteOthello


class SimuladorPartida:
    """Simula una partida completa de Othello entre dos instancias de AgenteOthello."""

    def __init__(self, agente_negro, agente_blanco, nombre_negro="Agente_Negro", nombre_blanco="Agente_Blanco"):
        self.agente_negro = agente_negro
        self.agente_blanco = agente_blanco
        self.nombre_negro = nombre_negro
        self.nombre_blanco = nombre_blanco
        self.board_size = 8

    def iniciar_tablero(self):
        tablero = np.zeros((self.board_size, self.board_size), dtype=int)
        mid = self.board_size // 2
        tablero[mid - 1, mid - 1] = 2  # Blanco
        tablero[mid, mid] = 2          # Blanco
        tablero[mid - 1, mid] = 1      # Negro
        tablero[mid, mid - 1] = 1      # Negro
        return tablero

    def jugar(self):
        tablero = self.iniciar_tablero()
        jugador_actual = 1  # 1 = Negro, 2 = Blanco

        tiempos = {1: [], 2: []}

        # Usamos los métodos de validación de uno de los agentes
        validador = self.agente_negro

        while True:
            movidas = validador._get_valid_moves(tablero, jugador_actual)

            if not movidas:
                # Verificar si el rival tiene jugadas
                siguiente = 3 - jugador_actual
                movidas_rival = validador._get_valid_moves(tablero, siguiente)
                if not movidas_rival:
                    # Ninguno puede mover -> Fin del juego
                    break
                else:
                    # Pase de turno
                    jugador_actual = siguiente
                    continue

            agente = self.agente_negro if jugador_actual == 1 else self.agente_blanco

            # Preparar estado para la IA
            estado = ElEstado(
                jugador=jugador_actual,
                tablero=tablero,
                movidas=movidas,
                get_utilidad=0
            )
            agente.estado = estado

            t0 = time.time()
            agente.programa()
            t_mov = time.time() - t0
            tiempos[jugador_actual].append(t_mov)

            accion = agente.get_acciones()
            if not accion or accion not in movidas:
                accion = movidas[0]  # Fallback de seguridad

            # Ejecutar movimiento y voltear fichas
            nuevo_estado = agente.getResultado(estado, accion)
            tablero = nuevo_estado.tablero

            jugador_actual = 3 - jugador_actual

        fichas_negro = int(np.sum(tablero == 1))
        fichas_blanco = int(np.sum(tablero == 2))

        if fichas_negro > fichas_blanco:
            ganador = self.nombre_negro
        elif fichas_blanco > fichas_negro:
            ganador = self.nombre_blanco
        else:
            ganador = "Empate"

        dif_fichas = abs(fichas_negro - fichas_blanco)
        t_prom_negro = float(np.mean(tiempos[1])) if tiempos[1] else 0.0
        t_prom_blanco = float(np.mean(tiempos[2])) if tiempos[2] else 0.0

        return {
            "agente_a": self.nombre_negro,
            "agente_b": self.nombre_blanco,
            "ganador": ganador,
            "diferencia_fichas": dif_fichas,
            "fichas_a": fichas_negro,
            "fichas_b": fichas_blanco,
            "profundidad_a": self.agente_negro.altura,
            "profundidad_b": self.agente_blanco.altura,
            "tiempo_a": round(t_prom_negro, 4),
            "tiempo_b": round(t_prom_blanco, 4)
        }


from concurrent.futures import ProcessPoolExecutor, as_completed


def _simular_una_partida(args):
    i, altura_a, modo_a, altura_b, modo_b, nombre_a, nombre_b = args
    if i % 2 != 0:
        agente_negro = AgenteOthello(altura=altura_a, modo_evaluacion=modo_a)
        agente_blanco = AgenteOthello(altura=altura_b, modo_evaluacion=modo_b)
        simulador = SimuladorPartida(agente_negro, agente_blanco, nombre_a, nombre_b)
    else:
        agente_negro = AgenteOthello(altura=altura_b, modo_evaluacion=modo_b)
        agente_blanco = AgenteOthello(altura=altura_a, modo_evaluacion=modo_a)
        simulador = SimuladorPartida(agente_negro, agente_blanco, nombre_b, nombre_a)
    return i, simulador.jugar()


def ejecutar_torneo(num_partidas=10, altura_a=6, modo_a="adaptativa_dinamica", altura_b=6, modo_b="estatica", salida_csv="datos/resultados_othello.csv"):
    os.makedirs(os.path.dirname(salida_csv), exist_ok=True)

    if modo_a == modo_b and altura_a == altura_b:
        nombre_a = f"IA_{modo_a.capitalize()}_d{altura_a}_P1"
        nombre_b = f"IA_{modo_b.capitalize()}_d{altura_b}_P2"
    else:
        nombre_a = f"IA_{modo_a.capitalize()}_d{altura_a}"
        nombre_b = f"IA_{modo_b.capitalize()}_d{altura_b}"

    print(f"\n==========================================")
    print(f"🏆 INICIANDO TORNEO: {nombre_a} vs {nombre_b}")
    print(f"📊 Total de partidas: {num_partidas}")
    print(f"==========================================\n")

    victorias_a = 0
    victorias_b = 0
    empates = 0

    filas = []
    tareas = [
        (i, altura_a, modo_a, altura_b, modo_b, nombre_a, nombre_b)
        for i in range(1, num_partidas + 1)
    ]

    max_workers = min(num_partidas, max(1, (os.cpu_count() or 4) - 2))
    resultados = [None] * num_partidas

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(_simular_una_partida, t): t[0] for t in tareas}
        for futuro in as_completed(futuros):
            i, res = futuro.result()
            resultados[i - 1] = res

            if res["ganador"] == nombre_a:
                victorias_a += 1
            elif res["ganador"] == nombre_b:
                victorias_b += 1
            else:
                empates += 1

            print(f"Partida {i:02d}/{num_partidas:02d} | Ganador: {res['ganador']} | Dif: {res['diferencia_fichas']} fichas | T_prom: A={res['tiempo_a']}s, B={res['tiempo_b']}s")

    for res in resultados:
        if res is not None:
            filas.append({
                "agente_a": res["agente_a"],
                "agente_b": res["agente_b"],
                "ganador": res["ganador"],
                "diferencia_fichas": res["diferencia_fichas"],
                "profundidad_a": res["profundidad_a"],
                "profundidad_b": res["profundidad_b"],
                "tiempo_a": res["tiempo_a"],
                "tiempo_b": res["tiempo_b"]
            })

    # Escribir CSV
    with open(salida_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "agente_a", "agente_b", "ganador", "diferencia_fichas",
            "profundidad_a", "profundidad_b", "tiempo_a", "tiempo_b"
        ])
        writer.writeheader()
        writer.writerows(filas)

    print(f"\n==========================================")
    print(f"📈 RESULTADOS FINALES:")
    print(f"  - {nombre_a}: {victorias_a} victorias ({(victorias_a / num_partidas) * 100:.1f}%)")
    print(f"  - {nombre_b}: {victorias_b} victorias ({(victorias_b / num_partidas) * 100:.1f}%)")
    print(f"  - Empates: {empates}")
    print(f"📁 CSV generado en: {salida_csv}")
    print(f"==========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Torneo de IAs para Othello")
    parser.add_argument("--partidas", type=int, default=10, help="Número de partidas a simular (default: 10)")
    parser.add_argument("--altura_a", type=int, default=6, help="Profundidad del Agente A (default: 6)")
    parser.add_argument("--modo_a", choices=["adaptativa", "estatica", "adaptativa_dinamica"], default="adaptativa_dinamica", help="Evaluación Agente A")
    parser.add_argument("--altura_b", type=int, default=6, help="Profundidad del Agente B (default: 6)")
    parser.add_argument("--modo_b", choices=["adaptativa", "estatica", "adaptativa_dinamica"], default="estatica", help="Evaluación Agente B")
    parser.add_argument("--csv", default="datos/resultados_othello.csv", help="Ruta del archivo CSV de salida")
    args = parser.parse_args()

    ejecutar_torneo(
        num_partidas=args.partidas,
        altura_a=args.altura_a,
        modo_a=args.modo_a,
        altura_b=args.altura_b,
        modo_b=args.modo_b,
        salida_csv=args.csv
    )
