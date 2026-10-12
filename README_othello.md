# Agente de Othello (Reversi) con Alpha-Beta

Agente para Othello que decide con Minimax y poda Alpha-Beta y evalúa las hojas con una de tres
funciones de evaluación. El código sigue exactamente la Sección 3 y la Tabla 1 del artículo.

## Funciones de evaluación (`evaluador.py`)

Cuatro componentes normalizados en [-100, 100], desde el punto de vista del jugador que decide (MAX):

| Componente | Qué mide |
|---|---|
| `f_P` paridad | 100·(c_MAX − c_MIN)/(c_MAX + c_MIN) |
| `f_M` movilidad | 100·(m_MAX − m_MIN)/(m_MAX + m_MIN), con m = número de jugadas legales |
| `f_C` esquinas | ±25 por esquina propia/rival; con la esquina vacía, −10/+10 por cada casilla C o X propia/rival, acotado a [−25, 25] |
| `f_T` posicional | suma de la matriz `PESOS_TABLERO` sobre las fichas propias menos las rivales, dividida por Σ\|W\| |

| Función | Pesos (w_P, w_M, w_C, w_T) | Profundidad |
|---|---|---|
| E1 estática (`estatica`) | 0.10, 0.35, 0.35, 0.20 | fija (`altura`) |
| E2 adaptativa (`adaptativa`) | N ≤ 20: 0, .45, .30, .25 · 21–50: .15, .30, .40, .15 · 51–64: .75, .05, .20, 0 | fija (`altura`) |
| E3 adaptativa dinámica (`adaptativa_dinamica`) | N ≤ 20: 0, .45, .30, .25 · 21–43: .15, .30, .40, .15 · 44–64: .45, .10, .35, .10 | d(N): 4 si N < 44; 6 si 44 ≤ N < 52; min(8, 64 − N) si N ≥ 52 |

N = número de fichas en el tablero.

## Búsqueda (`AgenteIA/AgenteJugador.py`, `AgentesEspecificos/AgenteOthello.py`)

- Alpha-Beta con corte por profundidad; el nodo es MAX o MIN según el jugador que mueve, de modo que los
  pases (un jugador mueve dos veces seguidas) se tratan correctamente.
- Las jugadas se ordenan por el valor de `PESOS_TABLERO` en la casilla para adelantar los cortes.
- Generación de jugadas con bitboards (enteros de 64 bits); devuelve las mismas jugadas, en el mismo
  orden, que la verificación casilla por casilla.
- Cada decisión registra `nodos`, `evaluaciones`, `tiempo_decision` y `valor_decision`.

## Ejecutar

```bash
pip install numpy pygame scipy matplotlib
python ejecutar.py                      # menú: partidas con interfaz, red y torneos
python -m unittest -v test_othello      # pruebas
python torneo.py --modo_a estatica --modo_b adaptativa_dinamica --partidas 100 --csv ../../datos/resultados_othello.csv
```

Partidas en red: `python servidor.py`, y en otras terminales
`python cliente_agente.py --modo estatica --altura 4 --ui` o `python cliente_humano.py`.
Ver `GUIA_EJECUCION.md` y, para reproducir todos los experimentos del artículo, `../README.md`.

`ANALISIS_HEURISTICAS_Y_MEJORAS.md` documenta una versión anterior del evaluador (con fichas frontera).
