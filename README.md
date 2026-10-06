# Agente Inteligente para Othello (Reversi)

> 📘 **¿Cómo ejecutar partidas y torneos?** Consulta la [Guía de Ejecución Rápida](GUIA_EJECUCION.md) para ver los comandos de servidor, juego local/red y torneos automatizados.

Este repositorio contiene el código fuente de un agente de Inteligencia Artificial diseñado para jugar Othello (también conocido como Reversi). El agente utiliza el algoritmo de poda Alfa-Beta para tomar decisiones y una función de evaluación heurística avanzada que adapta su estrategia según la fase del juego.
El proyecto está estructurado con un agente principal (AgenteOthello_Oficial) y un cliente (ClienteAgenteOficial) que le permite conectarse a un servidor de juego y competir contra otros jugadores o agentes.

Características Principales
Inteligencia Artificial Avanzada: Implementa el algoritmo Minimax con poda Alfa-Beta para explorar el árbol de posibles jugadas de manera eficiente.
Función de Evaluación Heurística Compleja: La evaluación del tablero no se basa solo en el número de fichas, sino que considera múltiples factores estratégicos:
Control de Esquinas: Prioriza la captura de las esquinas, que son las posiciones más estables y valiosas del juego.
Movilidad: Maximiza el número de movimientos propios mientras minimiza los del oponente.
Estabilidad de Fichas: Evalúa la estabilidad de las fichas, penalizando aquellas que están en posiciones "frontera" (adyacentes a casillas vacías) y que son vulnerables a ser capturadas.
Valor Posicional: Utiliza una matriz de pesos (PESOS_ESTRATEGICOS) para asignar un valor a cada casilla del tablero, favoreciendo posiciones estratégicamente superiores.
Estrategia Adaptativa por Fases: La función de evaluación ajusta la importancia de los factores anteriores (movilidad, estabilidad, etc.) dependiendo de la fase del juego:
Apertura (< 20 fichas): Se enfoca en la movilidad y el control de esquinas.
Medio Juego (< 45 fichas): Las esquinas se vuelven críticas y la estabilidad de las fichas gana importancia.
Final (>= 45 fichas): La estabilidad y el valor posicional se vuelven cruciales para asegurar la victoria.
Ordenamiento de Movimientos: Para optimizar la poda Alfa-Beta, los movimientos se ordenan de mejor a peor usando una evaluación simple, lo que permite que el algoritmo encuentre los cortes más rápido.
Cliente de Juego con Interfaz Gráfica: Incluye una clase cliente construida sobre pygame que permite visualizar el tablero, conectarse a un servidor y jugar partidas en tiempo real.

¿Cómo Funciona?
1. El Agente (AgenteOthello_Oficial)
El núcleo del proyecto. Esta clase hereda de AgenteJugador y define la lógica para jugar Othello.
programa(): Es el método principal que inicia la búsqueda Alfa-Beta para encontrar la mejor jugada.
funcion_evaluacion(estado): Llama a evaluar_estado_unificado para calcular el valor heurístico de una posición del tablero. Este valor guía al algoritmo Alfa-Beta.
jugadas(estado): Devuelve una lista de movimientos válidos, ordenados según su valor estratégico para mejorar la eficiencia de la poda.
getResultado(estado, jugada): Genera un nuevo estado del juego que resulta de aplicar una jugada.

2. La Heurística (evaluar_estado_unificado)
Esta es la función más importante para la inteligencia del agente. Combina cuatro métricas clave con pesos que cambian según el número de fichas en el tablero:
Puntuación de Esquinas: Diferencia entre las esquinas capturadas por el agente y el oponente.
Puntuación de Movilidad: Diferencia en el número de movimientos disponibles.
Puntuación de Estabilidad: Diferencia en el número de fichas "frontera". Menos fichas en la frontera significa una posición más estable.
Puntuación Posicional: Suma de los valores de las casillas ocupadas según la matriz PESOS_ESTRATEGICOS.

3. El Cliente (ClienteAgenteOficial)
Esta clase maneja la comunicación con el servidor y la interfaz gráfica.
Se conecta al host y puerto especificados.
Recibe actualizaciones del estado del juego (game_update).
Cuando es su turno, crea un objeto ElEstado a partir de la información del servidor.
Invoca al agente para que decida la mejor jugada.
Envía la jugada seleccionada de vuelta al servidor.
Renderiza el tablero y el estado del juego usando pygame.


Cómo Empezar
Para ejecutar el agente, necesitas tener las dependencias del proyecto instaladas (como numpy y pygame).
Clona el repositorio:
code
Bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio


Instala las dependencias:
code
Bash
pip install numpy pygame


Ejecuta el cliente:
Abre una terminal y ejecuta el script principal. El programa te pedirá la dirección del servidor, el puerto y la profundidad de búsqueda de la IA.
code
Bash
python cliente_agente_oficial.py


Servidor: Introduce la IP del servidor de juego (por defecto: localhost).
Puerto: Introduce el puerto del servidor (por defecto: 5555).
Profundidad de la IA: Es el parámetro altura del agente. Un valor más alto hará que el agente "piense" más y juegue mejor, pero también tardará más en responder (por defecto: 5). Un valor entre 4 y 6 es recomendable.
¡A Jugar!


Una vez conectado, se abrirá una ventana de pygame donde podrás ver la partida en tiempo real. El agente jugará automáticamente cuando sea su turno.


Estructura del Código
AgenteOthello_Oficial.py: Contiene la lógica principal del agente de IA, incluyendo la función de evaluación y la matriz de pesos.
cliente_agente_oficial.py (o como se llame tu archivo principal): Contiene la clase ClienteAgenteOficial que se conecta al servidor, maneja la interfaz gráfica y coordina el juego.
AgenteIA/AgenteJugador.py: Clases base (AgenteJugador, ElEstado) de las que hereda el agente.
interfaz_grafica.py: Módulo que gestiona el renderizado del juego con pygame.
cliente_base.py: Clase base para la conexión de red del cliente.
