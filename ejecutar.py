#!/usr/bin/env python3
"""
ejecutar.py — Lanzador Unificado de Partidas y Torneos para Othello

Permite iniciar con un solo comando:
- Partidas visuales: Humano vs IA (E1, E2, E3), IA vs IA (E1 vs E2, E1 vs E3, etc.), Humano vs Humano.
- Torneos automatizados en memoria con generación de CSV.
Maneja el ciclo de vida del servidor y los clientes, limpiando procesos al terminar.
"""

import sys
import os
import time
import socket
import argparse
import subprocess
import signal

PYTHON = sys.executable
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def esta_puerto_en_uso(host='127.0.0.1', port=5555):
    """Verifica si el puerto del servidor ya está escuchando."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def esperar_servidor(host='127.0.0.1', port=5555, timeout=5.0):
    """Espera activamente a que el servidor acepte conexiones."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        if esta_puerto_en_uso(host, port):
            return True
        time.sleep(0.1)
    return False


def lanzar_servidor(host='127.0.0.1', port=5555):
    """Inicia el servidor como subproceso alimentando inputs por defecto."""
    proc = subprocess.Popen(
        [PYTHON, os.path.join(BASE_DIR, "servidor.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=BASE_DIR
    )
    # Enviar Enter para host y Enter para puerto por defecto
    try:
        proc.stdin.write(f"{host}\n{port}\n")
        proc.stdin.flush()
    except Exception:
        pass

    if not esperar_servidor(host, port):
        proc.terminate()
        raise RuntimeError(f"El servidor no levantó en {host}:{port} tras 5 segundos.")

    return proc


def ejecutar_partida(tipo="e1-vs-e3", altura=4, host="127.0.0.1", port=5555):
    """
    Inicia el servidor y los clientes correspondientes según el tipo de partida.
    Garantiza la finalización ordenada de todos los subprocesos.
    """
    procesos = []
    servidor_proc = None

    try:
        # 1. Levantar servidor si no está ya activo
        if not esta_puerto_en_uso(host, port):
            print(f"🌐 Iniciando servidor Othello en {host}:{port}...")
            servidor_proc = lanzar_servidor(host, port)
            procesos.append(servidor_proc)
        else:
            print(f"ℹ️ Servidor detectado en {host}:{port}, reutilizando...")

        # 2. Configurar participantes
        # El primero en conectarse juega con Negras (1) y el segundo con Blancas (2).
        if tipo == "e1-vs-e2":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Visual: E1 (Estática - Negras) vs E2 (Adaptativa - Blancas)")

        elif tipo == "e2-vs-e1":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Visual: E2 (Adaptativa - Negras) vs E1 (Estática - Blancas)")

        elif tipo == "e1-vs-e3":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Visual: E1 (Estática - Negras) vs E3 (Adaptativa Dinámica - Blancas)")

        elif tipo == "e3-vs-e1":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Visual: E3 (Adaptativa Dinámica - Negras) vs E1 (Estática - Blancas)")

        elif tipo == "e2-vs-e3":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Visual: E2 (Adaptativa - Negras) vs E3 (Adaptativa Dinámica - Blancas)")

        elif tipo == "e1-vs-e1":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Espejo: E1 (Estática - Negras) vs E1 (Estática - Blancas)")

        elif tipo == "e2-vs-e2":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Espejo: E2 (Adaptativa - Negras) vs E2 (Adaptativa - Blancas)")

        elif tipo == "e3-vs-e3":
            p1_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura), "--ui"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura)]
            print(f"⚔️ Enfrentamiento Espejo: E3 (Adaptativa Dinámica - Negras) vs E3 (Adaptativa Dinámica - Blancas)")

        elif tipo == "humano-vs-e1":
            p1_cmd = [PYTHON, "cliente_humano.py"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "estatica", "--altura", str(altura)]
            print(f"👤 Humano (Negras) vs 🤖 E1 Estática (Blancas)")

        elif tipo == "humano-vs-e2":
            p1_cmd = [PYTHON, "cliente_humano.py"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa", "--altura", str(altura)]
            print(f"👤 Humano (Negras) vs 🤖 E2 Adaptativa (Blancas)")

        elif tipo == "humano-vs-e3":
            p1_cmd = [PYTHON, "cliente_humano.py"]
            p2_cmd = [PYTHON, "cliente_agente.py", "--host", host, "--port", str(port), "--modo", "adaptativa_dinamica", "--altura", str(altura)]
            print(f"👤 Humano (Negras) vs 🤖 E3 Adaptativa Dinámica (Blancas)")

        elif tipo == "humano-vs-humano":
            p1_cmd = [PYTHON, "cliente_humano.py"]
            p2_cmd = [PYTHON, "cliente_humano.py"]
            print(f"👤 Humano 1 (Negras) vs 👤 Humano 2 (Blancas)")
        else:
            print(f"❌ Tipo de partida desconocido: '{tipo}'")
            return

        # 3. Lanzar Jugador 1 (Negras)
        env = os.environ.copy()
        if p1_cmd[1] == "cliente_humano.py":
            # Alimentar input del host/puerto automáticamente
            proc_p1 = subprocess.Popen(p1_cmd, stdin=subprocess.PIPE, cwd=BASE_DIR, env=env)
            proc_p1.stdin.write(f"{host}\n{port}\n")
            proc_p1.stdin.flush()
        else:
            proc_p1 = subprocess.Popen(p1_cmd, cwd=BASE_DIR, env=env)
        procesos.append(proc_p1)

        time.sleep(0.6)  # Breve pausa para asegurar el slot de Negras

        # 4. Lanzar Jugador 2 (Blancas)
        if p2_cmd[1] == "cliente_humano.py":
            proc_p2 = subprocess.Popen(p2_cmd, stdin=subprocess.PIPE, cwd=BASE_DIR, env=env)
            proc_p2.stdin.write(f"{host}\n{port}\n")
            proc_p2.stdin.flush()
        else:
            proc_p2 = subprocess.Popen(p2_cmd, cwd=BASE_DIR, env=env)
        procesos.append(proc_p2)

        print("🎮 Partida en curso. Cierra la ventana gráfica de Pygame para terminar.")
        proc_p1.wait()

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo partida...")
    finally:
        # Limpieza exhaustiva de subprocesos
        print("🧹 Limpiando procesos de la partida...")
        for p in procesos:
            if p and p.poll() is None:
                try:
                    p.terminate()
                    p.wait(timeout=1.0)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
        print("✅ Partida finalizada limpiamente.")


def ejecutar_torneo_cli(partidas=100, modo_a="adaptativa_dinamica", modo_b="estatica", altura_a=4, altura_b=4, csv="datos/resultados_othello.csv"):
    """Invoca directamente el script torneo.py optimizado en paralelo."""
    cmd = [
        PYTHON, "torneo.py",
        "--partidas", str(partidas),
        "--modo_a", modo_a,
        "--altura_a", str(altura_a),
        "--modo_b", modo_b,
        "--altura_b", str(altura_b),
        "--csv", csv
    ]
    print(f"🏆 Ejecutando Torneo: {partidas} partidas entre {modo_a} (d={altura_a}) y {modo_b} (d={altura_b})...")
    subprocess.run(cmd, cwd=BASE_DIR)


def menu_interactivo():
    """Menú interactivo en consola si se ejecuta sin argumentos."""
    print("==================================================")
    print("🎮 LANZADOR DE OTHELLO — IA & EVALUACIÓN")
    print("==================================================")
    print("--- ⚔️  Cruces entre Distintas IAs (Visual) ---")
    print(" 1) E3 (Adaptativa Dinámica) vs E1 (Estática)")
    print(" 2) E1 (Estática) vs E2 (Adaptativa)")
    print(" 3) E2 (Adaptativa) vs E3 (Adaptativa Dinámica)")
    print("\n--- 🪞 Enfrentamientos Espejo (Visual) ---")
    print(" 4) E1 vs E1 (Estática vs Estática)")
    print(" 5) E2 vs E2 (Adaptativa vs Adaptativa)")
    print(" 6) E3 vs E3 (Adaptativa Dinámica vs Adaptativa Dinámica)")
    print("\n--- 👤 Partidas con Jugador Humano ---")
    print(" 7) Humano vs E3 (Adaptativa Dinámica)")
    print(" 8) Humano vs E1 (Estática)")
    print(" 9) Humano vs E2 (Adaptativa)")
    print("10) Humano vs Humano")
    print("\n--- 📊 Torneos Automatizados (100 Partidas en Memoria) ---")
    print("11) Torneo: E3 (Adaptativa Dinámica) vs E1 (Estática)")
    print("12) Torneo: E2 (Adaptativa) vs E1 (Estática)")
    print(" 0) 🚪 Salir")
    print("==================================================")
    opcion = input("Selecciona una opción [0-12]: ").strip()

    opciones_map = {
        "1": lambda: ejecutar_partida(tipo="e3-vs-e1"),
        "2": lambda: ejecutar_partida(tipo="e1-vs-e2"),
        "3": lambda: ejecutar_partida(tipo="e2-vs-e3"),
        "4": lambda: ejecutar_partida(tipo="e1-vs-e1"),
        "5": lambda: ejecutar_partida(tipo="e2-vs-e2"),
        "6": lambda: ejecutar_partida(tipo="e3-vs-e3"),
        "7": lambda: ejecutar_partida(tipo="humano-vs-e3"),
        "8": lambda: ejecutar_partida(tipo="humano-vs-e1"),
        "9": lambda: ejecutar_partida(tipo="humano-vs-e2"),
        "10": lambda: ejecutar_partida(tipo="humano-vs-humano"),
        "11": lambda: ejecutar_torneo_cli(partidas=100, modo_a="adaptativa_dinamica", modo_b="estatica", csv="datos/resultados_e3_vs_e1.csv"),
        "12": lambda: ejecutar_torneo_cli(partidas=100, modo_a="adaptativa", modo_b="estatica", csv="datos/resultados_e2_vs_e1.csv"),
    }

    if opcion in opciones_map:
        opciones_map[opcion]()
    elif opcion == "0":
        print("Hasta luego.")
    else:
        print("❌ Opción inválida.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lanzador Unificado de Othello")
    parser.add_argument(
        "--modo",
        choices=[
            "e1-vs-e2", "e2-vs-e1",
            "e1-vs-e3", "e3-vs-e1",
            "e2-vs-e3",
            "e1-vs-e1", "e2-vs-e2", "e3-vs-e3",
            "humano-vs-e1", "humano-vs-e2", "humano-vs-e3",
            "humano-vs-humano",
            "torneo"
        ],
        help="Tipo de enfrentamiento a ejecutar"
    )
    parser.add_argument("--altura", type=int, default=6, help="Profundidad base de los agentes (default: 6)")
    parser.add_argument("--partidas", type=int, default=100, help="Número de partidas para modo torneo (default: 100)")
    parser.add_argument("--modo_a", default="adaptativa_dinamica", help="Agente A para torneo")
    parser.add_argument("--modo_b", default="estatica", help="Agente B para torneo")
    parser.add_argument("--csv", default="datos/resultados_othello.csv", help="Ruta de salida del CSV en torneo")
    parser.add_argument("--host", default="127.0.0.1", help="Host del servidor (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5555, help="Puerto del servidor (default: 5555)")

    args = parser.parse_args()

    if args.modo is None:
        menu_interactivo()
    elif args.modo == "torneo":
        ejecutar_torneo_cli(
            partidas=args.partidas,
            modo_a=args.modo_a,
            modo_b=args.modo_b,
            altura_a=args.altura,
            altura_b=args.altura,
            csv=args.csv
        )
    else:
        ejecutar_partida(
            tipo=args.modo,
            altura=args.altura,
            host=args.host,
            port=args.port
        )
