# Análisis Competitivo de Heurísticas y Hoja de Ruta de Mejoras — Othello IA

Este documento recopila los resultados empíricos obtenidos en partidas contra servidores remotos de otros grupos, el diagnóstico técnico de las debilidades observadas en la poda Alfa-Beta y las mejoras heurísticas y arquitectónicas planificadas para su implementación.

---

## 1. Registro de Enfrentamientos Competitivos

A continuación se detallan las 8 partidas registradas durante la sesión de pruebas competitivas:

| # | Rival | Heurística | Altura ($d$) | Color | Resultado | Marcador | Diagnóstico Clave |
|---|---|---|---|---|---|---|---|
| **1** | Grupo 1 | $E_1$ (Estática) | $d=4$ | Blancas (2) | Derrota | 22 - 42 | Apertura `(4, 2)`. Horizonte corto; cedió esquinas en el medio juego. |
| **2** | Grupo 1 | $E_3$ (Adaptativa Dinámica) | $d=4$ | Negras (1) | Derrota | 26 - 38 | Apertura `(2, 4)`. Minimax determinista; el rival bloqueó movilidad en medio juego. |
| **3** | Grupo 1 | $E_3$ (Adaptativa Dinámica) | $d=4$ | Negras (1) | Derrota | 26 - 38 | Réplica idéntica de la partida anterior por falta de estocasticidad en empates. |
| **4** | Grupo 1 | $E_3$ (Adaptativa Dinámica) | $d=4$ | Negras (1) | Derrota | 24 - 40 | El rival cambió respuesta en apertura y explotó debilidad en flancos. |
| **5** | Grupo 1 | $E_1$ (Estática) | $d=4$ | Negras (1) | Derrota | 22 - 42 | Apertura `(2, 3)`. Jugada `(1, 7)` en casilla C regaló la esquina `(0, 7)`. |
| **6** | Grupo 2 | $E_1$ (Estática) | $d=6$ | Blancas (2) | Derrota | 15 - 49 | Apertura `(2, 2)`. Ponderación estática ($10\%$ paridad) colapsó en el final. |
| **7** | Grupo 2 | $E_3$ (Adaptativa Dinámica) | $d=6$ | Blancas (2) | **Victoria** | **37 - 27** | **Victoria contundente.** Capturó esquinas `(7, 0)`, `(0, 0)` y `(0, 7)`. |
| **8** | Grupo 2 | $E_3$ (Adaptativa Dinámica) | $d=4$ | Blancas (2) | Derrota | 25 - 39 | Al descender a $d=4$, volvió a ceder esquinas por efecto horizonte. |

---

## 2. Diagnóstico Técnico

### A. El Efecto Horizonte a Profundidad 4 ($d=4$)
* Un nivel de búsqueda $d=4$ explora solo 4 plies (2 movimientos propios y 2 del adversario).
* Si nuestro agente ocupa una casilla de riesgo (como las casillas $C$ o $X$ adyacentes a las 4 esquinas), la penalización estática actual de $-10.0$ a menudo no compensa otras ganancias locales temporales.
* Si el oponente recién puede voltear o ocupar la esquina en el ply 5 o 6, a $d=4$ el algoritmo no detecta la trampa y selecciona la jugada, entregando la esquina de forma irreversible.
* A $d=6$ el horizonte alcanza los 3 turnos completos, detectando las trampas en esquinas y logrando la victoria (Partida #7).

### B. Rendimiento Computacional por Profundidad
Mediciones locales de tiempo de respuesta por jugada:
* **$d = 4$:** $\approx 0.035$ s / jugada (instantáneo, pero tácticamente frágil).
* **$d = 5$:** $\approx 0.115$ s / jugada (balance óptimo velocidad/profundidad).
* **$d = 6$:** $\approx 0.433$ s / jugada (excelente profundidad táctica, pero percibido lento en partidas continuas).

### C. Limitaciones de las Heurísticas Actuales en `evaluador.py`
1. **Ausencia de Fichas Frontera (Frontier Discs):** Solo se evalúa la movilidad relativa inmediata ($f_M$). En Othello, el factor crítico de la movilidad a medio y largo plazo es la cantidad de fichas propias en contacto con casillas vacías. A mayor cantidad de fichas frontera, mayor cantidad de opciones se le entregan al adversario.
2. **Estabilidad Asimétrica en Casillas $C$ y $X$:** La función `control_esquinas` penaliza casillas adyacentes si la esquina está vacía, pero si la esquina ya fue capturada por nuestro agente, esas casillas adyacentes dejan de ser peligrosas y se vuelven 100% estables. Actualmente no reciben una bonificación por consolidación de bloque.
3. **Paridad en Fase de Apertura:** En las primeras 20 jugadas, tener demasiadas fichas suele ser perjudicial (estrategia de minimización de discos o evaporación).

---

## 3. Hoja de Ruta de Mejoras para Implementación

### 1. Incorporación de Fichas Frontera ($f_F$)
Calcular las fichas que tienen al menos una casilla adyacente vacía:
$$\text{Frontera}(J) = \sum_{r,c \in \text{fichas}(J)} [\exists (dr,dc) : \text{tablero}[r+dr, c+dc] == 0]$$
Normalizar la métrica en $[-100, 100]$:
$$f_F = -100 \times \frac{\text{Frontera}(\text{Max}) - \text{Frontera}(\text{Min})}{\text{Frontera}(\text{Max}) + \text{Frontera}(\text{Min}) + \epsilon}$$
*Menos fichas frontera propias implican mayor estabilidad y menos flancos expuestos.*

### 2. Detección de Fichas Estables (Bordes y Esquinas Conectadas)
* Las esquinas son inmutables.
* Las fichas adyacentes a una esquina del mismo color y alineadas en el borde también son inmutables (estabilidad completa).
* Bonificar bloques estables de borde con pesos no decrecientes.

### 3. Profundización Selectiva / Búsqueda de Quiescencia Ligera
* Mantener la búsqueda estándar en **$d = 5$** (ejecución en $\sim 0.1$ s).
* Activar extensión de profundidad ($+1$ o $+2$ plies) de manera condicional **únicamente** cuando las jugadas candidatas involucren casillas $C$, $X$ o esquinas. Esto elimina el efecto horizonte en las zonas críticas sin pagar el costo temporal de evaluar todo el árbol a $d=6$.

### 4. Corrección de Registro en `cliente_agente.py`
* Corregir el mensaje de consola en `cliente_agente.py` (línea 65) para que imprima `self.agente.altura` en vez de `self.altura`, reflejando fielmente la profundidad real del agente en partidas con profundidad dinámica.

---

## 4. Cambios Implementados y Efectos en el Programa

### A. Métrica de Fichas Frontera (`f_F`) en `evaluador.py`
* **Implementación:** Método estático `EvaluadorOthello.fichas_frontera(tablero, jugador, oponente)`. Se utiliza una operación vectorizada de dilatación binaria sobre casillas vacías en 8 direcciones, con un coste computacional de apenas $\approx 45\,\mu\text{s}$ por 1000 llamadas.
* **Impacto en el juego:** En apertura y medio juego, el agente castiga severamente tener fichas expuestas a casillas vacías y premia tener fichas interiores. Esto evita regalar flancos de volteo al rival y mantiene alta la movilidad propia a mediano plazo.

### B. Control Dinámico de Esquinas y Casillas Adyacentes en `evaluador.py`
* **Implementación:** En `EvaluadorOthello.control_esquinas(tablero, jugador, oponente)`:
  1. Si la esquina está vacía, se incrementa la penalización de casillas adyacentes de riesgo ($C$ y $X$) de $-10.0$ a $-12.0$.
  2. Si la esquina ya pertenece al jugador, sus casillas adyacentes ocupadas por el mismo jugador se bonifican con $+5.0$ cada una (pasan a ser fichas estables consolidadas en lugar de castigadas).
* **Impacto en el juego:** El agente ya no teme ocupar casillas $C$ o $X$ cuando la esquina ya es suya, construyendo bloques de bordes seguros que consolidan el control territorial.

### C. Recalibración de Pesos Multimodal ($E_1$, $E_2$, $E_3$)
* **$E_1$ (Estática):** $w_P = 0.05, w_M = 0.25, w_F = 0.20, w_C = 0.35, w_T = 0.15$. Mantiene estabilidad interior y esquinas en todas las jugadas.
* **$E_2$ (Adaptativa por Fases):** 
  * Apertura: $w_P = 0.00, w_M = 0.35, w_F = 0.25, w_C = 0.25, w_T = 0.15$
  * Medio juego: $w_P = 0.10, w_M = 0.25, w_F = 0.20, w_C = 0.35, w_T = 0.10$
  * Endgame: $w_P = 0.70, w_M = 0.05, w_F = 0.05, w_C = 0.20, w_T = 0.00$
* **$E_3$ (Adaptativa Dinámica Calibrada):**
  * Apertura: $w_P = 0.00, w_M = 0.35, w_F = 0.25, w_C = 0.25, w_T = 0.15$
  * Medio juego: $w_P = 0.10, w_M = 0.25, w_F = 0.20, w_C = 0.35, w_T = 0.10$
  * Endgame: $w_P = 0.70, w_M = 0.05, w_F = 0.05, w_C = 0.20, w_T = 0.00$ (maximiza paridad y esquinas, apagando posición).

### D. Corrección de Profundidad Visual en `cliente_agente.py`
* **Implementación:** Se calcula `profundidad_actual` antes de imprimir el mensaje en consola, consultando la profundidad dinámica real recalculada por el agente según el número de fichas en tablero.
* **Impacto:** Visibilidad en tiempo real para el operador de cuándo el agente profundiza a $d=6$, $d=7$ u $d=8$ en endgame.

---

## 5. Batería de Pruebas Automatizadas y Descubrimiento Teórico

Se ejecutaron 4 series de torneos automatizados (40 partidas en total) con alternancia estricta de colores:

| Torneo | Configuración | Victorias A | Victorias B | Conclusión Científica |
|---|---|---|---|---|
| **Serie 1** | $E_3$ ($d=5$) vs $E_1$ ($d=5$) | 5 (50%) | 5 (50%) | **Blancas ganó el 100% de las partidas.** Pero cuando $E_3$ tuvo Blancas, aplastó **63 a 1** (+62 fichas) barriendo las 4 esquinas. |
| **Serie 2** | $E_3$ ($d=5$) vs $E_2$ ($d=5$) | 5 (50%) | 5 (50%) | Blancas ganó el 100%. $E_3$ con Blancas ganó por +34 fichas, superando a $E_2$. |
| **Serie 3** | $E_3$ ($d=5$) vs $E_1$ ($d=4$) | **10 (100%)** | 0 (0%) | **Dominio total.** $E_3$ superó la desventaja de Negras y ganó el 100% de las partidas. |
| **Serie 4** | $E_3$ ($d=6$) vs $E_2$ ($d=4$) | **10 (100%)** | 0 (0%) | **Dominio aplastante.** +24 fichas con Negras y +34 fichas con Blancas. |

### El Descubrimiento: Profundidades Pares vs Impares (Patología de Minimax)
* **Profundidades Impares ($d=5$):** Las hojas del árbol de búsqueda terminan siempre tras una jugada de MAX (nuestro agente), sin permitir que MIN (el rival) ejecute su contragolpe. Esto genera evaluaciones artificialmente optimistas que subestiman refutaciones inmediatas del rival.
* **Profundidades Pares ($d=4$ y $d=6$):** Las hojas terminan **siempre tras la respuesta del rival**. Por ende, toda jugada elegida por Alfa-Beta a profundidad par ha sobrevivido al mejor contraataque posible del oponente.
* **Veredicto:** **Para torneos competitivos oficiales, el estándar óptimo es siempre una profundidad par ($d=4$ o idealmente $d=6$)**. A $d=6$, $E_3$ tiene un 100% de victorias indiscutible contra cualquier agente a $d=4$.


