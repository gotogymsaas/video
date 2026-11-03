# Revelación relacional QAF vinculada a la narración

Juan Manuel Goenaga Castro · GoToGym Quantum Research · 29 de octubre de 2026

Estado: manuscrito metodológico; referencia implementada, evaluación perceptual pendiente.

## Resumen y pregunta

Un gráfico puede estar correctamente dibujado y aparecer demasiado pronto. Se propone vincular la aparición de cada nodo a un segmento medido de la narración. La hipótesis es que presentar relaciones cuando se explican puede reducir competencia visual. La implementación aporta sincronización determinista; el beneficio cognitivo requiere evaluación humana.

## Fundamento QAF

El manuscrito I articula evidencia, contexto y decisión. El II propone un grafo de continuidad; el IV exige tiempos del audio real. Esta ampliación aplica esas relaciones al orden de presentación. El propósito editorial se representa en la elección explícita de nodos y segmentos; no se declara una medición de atención cerebral ni se asignan fases cuánticas al espectador.

## Modelo temporal

Para el nodo i, se elige el segmento medido c_i. Su inicio local es tau_i=start(c_i)-start(plano). Se exige 0<=tau_i<duracion y orden no decreciente. El progreso de una conexión es r_i(t)=s(clip((t-tau_i)/d,0,1)), con s quintica. La conexión hacia el nodo i comienza cuando aparece ese destino.

## Contrato y abstención

node_cues contiene un índice de subtítulo por nodo. Los índices deben existir; los tiempos deben ser finitos y los segmentos positivos. Si una referencia queda fuera del plano, el validador rechaza el proyecto en lugar de inventar o desplazar tiempos. La calidad del alineador sigue siendo una dependencia externa y debe revisarse.

## Comportamiento del render

Movie.frame del compositor estándar usa reveal_times para resolver las referencias. Los nodos no aparecen antes de su segmento; el radio entra con una interpolación corta y las conexiones se dibujan progresivamente. Sin node_cues se mantiene una cascada temporal de referencia. El compositor cinematográfico especializado no consume este grafo: la integración de revelación corresponde al renderer estándar.

## Qué debe editar el director

Los segmentos deben medirse contra la versión exacta de voz. Al cambiar guion o audio se deben regenerar y revisar los tiempos. El director decide qué relación mostrar y cuánto texto puede leerse. El módulo no comprende automáticamente el significado del diálogo. Un índice válido puede apuntar semánticamente al segmento equivocado.

## Validación ejecutada

Las pruebas nuevas verifican alineación numérica, orden, rechazo de referencias fuera del plano y extremos de interpolación. Una prueba de integración renderiza frames diferentes antes y después de las señales. El conjunto dirigido de cuatro suites aprobó 42 pruebas. La comprobación de desigualdad de frames demuestra una modificación de imagen, no una mejora de comprensión.

## Evaluación propuesta

Comparar gráfico completo, cascada fija y revelación con voz con el mismo episodio. Medir recuerdo de relaciones, comprensión y carga autoinformada; separar preferencia de exactitud. El comparador clásico debe recibir las mismas señales temporales. No se espera ventaja cuántica: es una aplicación convencional del diseño relacional QAF.

## Riesgos y siguiente paso

Demasiadas revelaciones pueden distraer; subtítulos largos compiten con gráficos. Para evitarlo se propondrán límites de densidad y pausas de lectura. Una actualización de audio requiere revisar las referencias. Futuras versiones podrán añadir enlaces por identificador estable y un planificador de densidad, con sus propias pruebas; no se declaran ya implementados.

## Referencias

Goenaga, J. M. (2026). Fundamentos QAF audiovisual; Cinematografía computacional; Voz, sonido e identidad; Validación, competencias y ejecución. Fuentes en docs/manuscripts/source. Antecedente de planificación clásica relacional: qaf_video/generative_research/relational_planner.py. El formalismo MPS/TDVP de Bancells se conserva como antecedente de investigación, no como motor de esta implementación.

