# Guía de Ejecución — Othello IA & Servidor

Esta guía detalla los comandos para ejecutar partidas interactivas con interfaz gráfica (locales y en red), torneos automatizados de evaluación estadística y la compilación del artículo científico.

---

## 1. Requisitos Previos

Asegúrate de contar con Python 3.10+ y activar el entorno virtual del proyecto:

```bash
source .venv/bin/activate
```

*(Si instalas en un entorno limpio: `pip install numpy pygame`).*

---

## 2. Método Rápido: Lanzador Unificado (`ejecutar.py`)

Para no tener que abrir 3 terminales manualmente, dispones del script [ejecutar.py](file:///home/davidzp/Documents/Cato/2026/II-2026/Inteligencia-Artificial/Othello-main/ejecutar.py). Este script levanta automáticamente el servidor, gestiona la conexión de los jugadores y limpia todos los procesos al cerrar la ventana.

### A. Menú Interactivo
Simplemente ejecuta:
```bash
python ejecutar.py
```
Se desplegará un menú interactivo en consola para elegir el enfrentamiento con una tecla.

### B. Comandos Directos por Modo

#### ⚔️ IA vs IA (Partidas Visuales en Vivo)
* **$E_3$ (Adaptativa Dinámica) vs $E_1$ (Estática):**
  ```bash
  python ejecutar.py --modo e3-vs-e1
  ```
* **$E_1$ (Estática) vs $E_2$ (Adaptativa original):**
  ```bash
  python ejecutar.py --modo e1-vs-e2
  ```
* **$E_2$ (Adaptativa original) vs $E_3$ (Adaptativa Dinámica):**
  ```bash
  python ejecutar.py --modo e2-vs-e3
  ```

#### 🪞 Enfrentamientos Espejo (Misma Heurística)
* **$E_1$ vs $E_1$ (Estática vs Estática):**
  ```bash
  python ejecutar.py --modo e1-vs-e1
  ```
* **$E_2$ vs $E_2$ (Adaptativa vs Adaptativa):**
  ```bash
  python ejecutar.py --modo e2-vs-e2
  ```
* **$E_3$ vs $E_3$ (Adaptativa Dinámica vs Adaptativa Dinámica):**
  ```bash
  python ejecutar.py --modo e3-vs-e3
  ```

#### 👤 Humano vs IA (Interfaz Gráfica)
* **Humano (Negras) vs $E_3$ Adaptativa Dinámica (Blancas):**
  ```bash
  python ejecutar.py --modo humano-vs-e3
  ```
* **Humano (Negras) vs $E_1$ Estática (Blancas):**
  ```bash
  python ejecutar.py --modo humano-vs-e1
  ```
* **Humano (Negras) vs $E_2$ Adaptativa (Blancas):**
  ```bash
  python ejecutar.py --modo humano-vs-e2
  ```

#### 👥 Humano vs Humano
* **Dos jugadores locales en la misma máquina:**
  ```bash
  python ejecutar.py --modo humano-vs-humano
  ```

#### 📊 Torneos Automatizados (100 Partidas en Paralelo)
* **Torneo $E_3$ (Adaptativa Dinámica) vs $E_1$ (Estática):**
  ```bash
  python ejecutar.py --modo torneo --partidas 100 --modo_a adaptativa_dinamica --modo_b estatica --csv datos/resultados_othello.csv
  ```
* **Torneo $E_2$ (Adaptativa) vs $E_1$ (Estática):**
  ```bash
  python ejecutar.py --modo torneo --partidas 100 --modo_a adaptativa --modo_b estatica --csv datos/resultados_e2_vs_e1.csv
  ```

---

## 3. Método Manual: Partidas por Terminales Separadas (o Red LAN)

Si deseas correr cada componente de forma explícita o jugar entre dos computadoras distintas en red local:

El archivo `servidor.py` actúa como árbitro central. **Siempre debe iniciarse antes que cualquier cliente.** El primer jugador en conectarse juega con fichas **Negras (1)** y el segundo con **Blancas (2)**.

### A. En la misma computadora (Localhost)

1. **Terminal 1 — Servidor:**
   ```bash
   python servidor.py
   ```
   *(Presiona `Enter` dos veces para aceptar `127.0.0.1` y puerto `5555`).*

2. **Terminal 2 — Jugador 1 (Negras):**
   * **Humano:** `python cliente_humano.py`
   * **IA $E_3$ (con UI):** `python cliente_agente.py --modo adaptativa_dinamica --altura 4 --ui`
   * **IA $E_1$ (con UI):** `python cliente_agente.py --modo estatica --altura 4 --ui`
   * **IA $E_2$ (con UI):** `python cliente_agente.py --modo adaptativa --altura 4 --ui`

3. **Terminal 3 — Jugador 2 (Blancas):**
   * **Humano:** `python cliente_humano.py`
   * **IA $E_1$ (sin UI):** `python cliente_agente.py --modo estatica --altura 4`
   * **IA $E_2$ (sin UI):** `python cliente_agente.py --modo adaptativa --altura 4`
   * **IA $E_3$ (sin UI):** `python cliente_agente.py --modo adaptativa_dinamica --altura 4`

---

### B. Partida entre dos computadoras distintas (LAN / Wi-Fi)

1. **En la computadora Anfitriona (Servidor):**
   * Obtén tu IP local (en Linux: `ip a` o `hostname -I`; en Windows: `ipconfig`), por ejemplo `192.168.1.15`.
   * Inicia el servidor escuchando en todas las interfaces:
     ```bash
     python servidor.py
     ```
   * En `🌐 Host [127.0.0.1]:` ingresa `0.0.0.0`. En puerto presiona `Enter` (`5555`).

2. **En la computadora 1 (Jugador 1):**
   * Humano: `python cliente_humano.py` (ingresa `192.168.1.15`).
   * IA: `python cliente_agente.py --host 192.168.1.15 --port 5555 --modo adaptativa_dinamica --altura 4 --ui`

3. **En la computadora 2 (Jugador 2 - Compañero):**
   * Humano: `python cliente_humano.py` (ingresa `192.168.1.15`).
   * IA: `python cliente_agente.py --host 192.168.1.15 --port 5555 --modo estatica --altura 4 --ui`

---

## 4. Comparativa de Heurísticas Implementadas

En [evaluador.py](file:///home/davidzp/Documents/Cato/2026/II-2026/Inteligencia-Artificial/Othello-main/evaluador.py) y [`AgenteOthello.py`](file:///home/davidzp/Documents/Cato/2026/II-2026/Inteligencia-Artificial/Othello-main/AgentesEspecificos/AgenteOthello.py):

| Heurística | Modo | Profundidad | Comportamiento |
| :--- | :--- | :--- | :--- |
| **$E_1$ (Estática)** | `estatica` | $d = 4$ constante | Pesos fijos: $35\%$ movilidad, $35\%$ esquinas, $20\%$ posición, $10\%$ paridad. |
| **$E_2$ (Adaptativa)** | `adaptativa` | $d = 4$ constante | Pesos dinámicos por fases; apaga posición en endgame ($w_P=0.75, w_T=0.00$). |
| **$E_3$ (Adaptativa Dinámica)** | `adaptativa_dinamica` | $d=4 \to 6 \to \text{terminal}$ | Endgame Solver: mantiene esquinas ($35\%$), posición ($10\%$) y profundiza a $d \ge 6$ al final. |

---

## 5. Compilación del Artículo Científico en LaTeX

El código fuente del paper formal se encuentra en `articulo/`:

```bash
cd articulo
pdflatex articulo.tex
bibtex articulo
pdflatex articulo.tex
pdflatex articulo.tex
```

El PDF resultante se genera en `articulo/articulo.pdf`.
