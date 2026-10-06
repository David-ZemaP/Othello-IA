# cliente_agente.py
"""
Cliente de red para el Agente Inteligente de Othello.
Permite conectar el agente al servidor de juego para competir en el torneo
o contra jugadores humanos.
"""

import sys
import argparse
import numpy as np
from cliente_base import ClienteBase
from AgenteIA.AgenteJugador import ElEstado
from AgentesEspecificos.AgenteOthello import AgenteOthello


class ClienteAgente(ClienteBase):
    def __init__(self, host='localhost', port=5555, altura=6, modo_evaluacion='adaptativa_dinamica', con_ui=False):
        super().__init__(host, port)
        self.altura = altura
        self.modo_evaluacion = modo_evaluacion
        self.con_ui = con_ui
        self.agente = AgenteOthello(altura=self.altura, modo_evaluacion=self.modo_evaluacion)
        self.ui = None
        self.running = True

        if self.con_ui:
            try:
                from interfaz_grafica import InterfazJuego
                self.ui = InterfazJuego()
            except Exception as e:
                print(f"⚠️  No se pudo inicializar la interfaz gráfica ({e}). Ejecutando en modo consola.")
                self.con_ui = False

    def handle_message(self, message):
        super().handle_message(message)
        msg_type = message.get('type')

        if msg_type in ['game_start', 'game_update']:
            state = message.get('game_state', {})
            if state.get('game_over', False):
                winner = state.get('winner')
                print(f"\n🏁 ¡Partida finalizada! Ganador: {winner} (1=Negro, 2=Blanco, 0=Empate)")
                print(f"Marcador final: {state.get('scores')}")
                return

            # Si es el turno de esta IA
            if state.get('current_player') == self.player_color:
                self.pensar_y_mover(state)

    def pensar_y_mover(self, state):
        tablero = np.array(state['board'], dtype=int)
        valid_moves = [tuple(m) for m in state.get('valid_moves', [])]

        if not valid_moves:
            print("⏳ Sin movimientos legales disponibles.")
            return

        estado_juego = ElEstado(
            jugador=self.player_color,
            tablero=tablero,
            movidas=valid_moves,
            get_utilidad=0
        )
        self.agente.estado = estado_juego
        profundidad_actual = getattr(self.agente, 'altura', self.altura)
        if getattr(self.agente, 'profundidad_dinamica', False):
            total_fichas = int(np.sum(tablero != 0))
            if total_fichas >= 52:
                profundidad_actual = max(self.altura, min(8, 64 - total_fichas))
            elif total_fichas >= 44:
                profundidad_actual = max(self.altura, 6)
        print(f"🧠 IA pensando (profundidad={profundidad_actual}, modo={self.modo_evaluacion})...")
        self.agente.programa()
        accion = self.agente.get_acciones()

        if accion and accion in valid_moves:
            print(f"🎯 IA jugando en: {accion}")
            self.send_move(accion[0], accion[1])
        elif valid_moves:
            print(f"⚠️ Acción fallback tomada: {valid_moves[0]}")
            self.send_move(valid_moves[0][0], valid_moves[0][1])

    def run(self):
        if not self.connect():
            return

        print(f"🤖 Agente iniciado | Modo: {self.modo_evaluacion} | Altura: {self.altura}")
        try:
            while self.connected and self.running:
                if self.con_ui and self.ui:
                    if not self.ui.run_event_loop(on_click=lambda p: None, on_quit=lambda: self.disconnect("Cerrado")):
                        break
                    if not self.connected or self.waiting_for_opponent:
                        color_info = "Negro (1)" if self.player_color == 1 else "Blanco (2)" if self.player_color else ""
                        self.ui.draw_waiting_screen(self.connection_status, color_info)
                    else:
                        self.ui.draw_game_state(self.game_state, self.player_color)
                    self.ui.clock.tick(30)
                else:
                    import time
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Cliente detenido manualmente.")
        finally:
            self.disconnect("Fin de ejecución")
            if self.ui:
                self.ui.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente IA para Othello")
    parser.add_argument("--host", default="localhost", help="Host del servidor (default: localhost)")
    parser.add_argument("--port", type=int, default=5555, help="Puerto del servidor (default: 5555)")
    parser.add_argument("--altura", type=int, default=6, help="Profundidad de búsqueda Alpha-Beta (default: 6)")
    parser.add_argument("--modo", choices=["adaptativa", "estatica", "adaptativa_dinamica"], default="adaptativa_dinamica", help="Función de evaluación (default: adaptativa_dinamica)")
    parser.add_argument("--ui", action="store_true", help="Activar interfaz gráfica Pygame")
    args = parser.parse_args()

    cliente = ClienteAgente(
        host=args.host,
        port=args.port,
        altura=args.altura,
        modo_evaluacion=args.modo,
        con_ui=args.ui
    )
    cliente.run()
