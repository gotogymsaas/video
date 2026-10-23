# Tenis 04: integración y puerta de ejecución neuronal

Revisión: `abcda4d71d59af02da4cd95eb1c5512a4b2a62cc`, 23 de octubre de 2026.

El episodio descargable actual es un animatic fotográfico con voz generativa local y VFX procedurales propios. No contiene acción humana neuronal generada. Sus cuatro exportaciones de 60 segundos pasan decodificación, geometría, duración y audio; queda pendiente aprobación humana editorial y de pronunciación.

## Componentes nuevos revisados

- `neural_program`: valida manifiesto, separación de actores/prendas entre train/val/test, recursos locales y autorización antes de preparar el entrenamiento.
- `gpu_training_runner`: ejecución opt-in con presupuesto y comprobación NVIDIA. Un proceso exitoso todavía exige verificar pesos, pérdidas y muestras reales.
- `relational_planner`: continuidad entre alternativas con programación dinámica clásica; no es un generador ni demuestra ventaja cuántica.
- `editorial_timeline`: teléfono con cuadriláteros por cuadro y afirmaciones temporizadas; requiere clips y aprobación editorial, no inventa observaciones.
- `scientific_overlay`: diferencia hipótesis, propuesta y evidencia al componer gráficos.

## Integración ejecutada en el animatic

Los planos del compositor del episodio aceptan eventos VFX conceptuales validados, con estelas interpoladas por longitud de arco. La máscara sigue el zoom del fondo. Texto, subtítulos y pantalla original permanecen por encima de los efectos. La API de video real y su evidencia opcional se conserva.

Se corrigió un error de sintaxis y una importación entre pruebas en `test_gpu_training_runner.py`, sin cambiar las salvaguardas de ejecución.

## Puerta pendiente para una nueva versión neuronal

La máquina de esta revisión no dispone de `nvidia-smi`; no se verificaron pesos LTX, entrenador instalado, corpus autorizado ni una autorización de coste GPU. No se arrancó entrenamiento ni se asumió aprobación de derechos. El material ficticio del episodio conserva revisión humana pendiente; no debe declararse aprobado para alimentar el planificador o entrenamiento.

Para pasar de animatic a acción neuronal: aportar un entorno NVIDIA compatible, corpus con derechos de entrenamiento y consentimiento, pesos/configuración oficiales revisados, y un presupuesto explícito. Después generar un plano breve de tenis, comparar continuidad, manos, raqueta y pelota contra el backbone y un planificador clásico con igual presupuesto, y aprobarlo antes de sustituir planos del minuto final. Un LoRA sobre LTX es una adaptación licenciada, no un modelo fundacional propio desde cero.

No afirmar que esta entrega ya incorpora movimiento humano neuronal o que el entrenamiento está completado.
