# Football Intelligence: implementación operativa inicial

Esta entrega implementa el núcleo educativo P1 de los siete artículos de fútbol. No equivale a completar todas sus líneas de investigación ni a demostrar eficacia deportiva.

## Disponible en el código

- Servicio `exp-018_football_intelligence`, separado de las quince experiencias canónicas.
- Cuarenta especialistas con currículo distinto para cuerpo técnico, defensa, ataque, contexto humano y arbitraje.
- Selección explícita de especialidad y modalidad, objetivo, experiencia y tiempo mediante el panel existente.
- Actividades educativas de comprensión, aplicación y revisión. No prescripción de carga física.
- Optimización cuadrática binaria exacta de alternativas: utilidad declarada, repetición e interacciones, tiempo y presencia del especialista principal como restricciones duras. La energía no representa probabilidad humana.
- ExperienceTask, publicación atómica, continuidad referencial, proyección de límites y fuentes al Coach. Ningún nuevo estado conversacional o emisor.
- Interruptor `QAF_FOOTBALL_ENABLED=false`: oculta capacidad y botón, bloquea nuevas tareas y publicación de ejecuciones en vuelo; conserva resultados históricos.
- Smoke autenticado de producción para descubrimiento, selección de rol, ejecución, persistencia, reintento y entrega usando la cuenta técnica existente.

## Trazabilidad de los siete artículos

| Artículos | Implementado | Pendiente para el alcance completo |
|---|---|---|
| I: cuerpo técnico | Ocho currículos y planificación educativa | Planes colectivos con permisos verificados y validación en campo |
| II: portería/defensa | Ocho roles, tareas y criterios observables | Tracking, geometría temporal, calibración y evaluación por posición |
| III: ataque | Ocho roles, alternativas pedagógicas | Modelos de xG/valor de acciones, percepción y transferencia prospectiva |
| IV: sistema humano | Ocho roles educativos y revisión de restricciones | Medición validada, prescripción supervisada, integración longitudinal de señales |
| V: arbitraje | Ocho currículos con referencias; alcance sólo educativo | Corpus normativo íntegro versionado, revisión profesional, RAG y evaluación por competición |
| VI: algoritmos | QUBO acotado exacto con diagnóstico y pruebas | MPS/TDVP/RDM, modelos entrenados, ablaciones y comparación prospectiva |
| VII: arquitectura | Registro, formularios, tareas, evidencia, handoff, aislamiento personal y rollback | Permisos de equipo, consentimientos de terceros, estudios de retención y canary científico |

No se dispone en esta entrega de datasets autorizados y anotados, modelos entrenados o validación profesional para declarar operativas las capacidades pendientes. No se sustituyen por predicciones inventadas. El inventario del Coach y los resultados explican el alcance real.

## Verificación

La suite `api.test_qaf_football_intelligence` recorre las cuarenta especialidades con tres presupuestos temporales, verifica entradas inválidas, restricciones, óptimo por enumeración independiente, normas de publicación, aislamiento, repetición y continuidad. Se ejecutan además las regresiones deportivas y ExperienceTask y los tests de acciones firmadas y formularios del frontend. PostgreSQL y despliegue se verifican en CI, no se infieren de SQLite local.

Para probar: preguntar «¿Tienes agentes de fútbol?»; activar «Activa fútbol»; escoger especialidad y completar el panel; recibir actividades; preguntar «Explícamelo mejor». Los resultados anteriores siguen siendo evidencia y no una certificación de haber realizado entrenamiento.

Los diez manuscritos de running/fútbol están publicados en `QAF/08_agentes_coach` tras fusionar #774 y #775. Running no está implementado por este cambio.

