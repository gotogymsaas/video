# Validación de la entrega

## Idiomas por frase · 0.3.0

La versión 0.3 pasó **54 pruebas locales** en Python 3.12.14. Se añadieron controles de idioma de referencia independiente del idioma de salida, reconocimiento por frase con desplazamientos temporales, presupuesto CJK, comparación por caracteres, transformación de límites con pausas y rechazo de una expresión extranjera omitida aunque el error global fuera bajo. El JavaScript de la interfaz pasó revisión sintáctica; no se ejecutó revisión visual en navegador en esta actualización porque el ejecutable no estaba disponible.

Se sintetizaron dos tomas reales en CPU con la misma referencia privada y lenguas español/inglés/español. La primera duró 7.68 s: la comparación ASR global fue 20%, pero la frase inglesa tuvo 60% y el nuevo control la retuvo para revisión. No se corrigió el reconocedor mediante un prompt que incluyera la respuesta esperada. La segunda toma aportó una frase inglesa más completa y cambió la semilla de 22 a 42; duró **13.52 s**. El reconocedor recuperó todas las palabras de las tres frases, incluidos **Quantum Coach** y **machine learning**, con error ASR 0 en esta muestra. No se atribuye la mejora a un único cambio porque variaron contexto y semilla.

Estas mediciones demuestran ejecución e integridad del guion en dos idiomas sobre una muestra; no acreditan pronunciación nativa, identidad vocal, continuidad artística o acento barranquillero. Los otros ocho idiomas del motor no se sintetizaron en esta actualización. El informe agregado `validation/voice-multilingual-v0.3.json` conserva alcance y límites. Las grabaciones, el perfil y los audios clonados se mantienen fuera del repositorio público.

También se ajustó esa locución a 17 s (816000 muestras PCM a 48 kHz), con tempo 0.965714 y cierre de 2.86 s. La nueva transcripción mantuvo error 0 en inglés y en la última frase española; la primera tuvo 12.5%, dentro de la compuerta inicial. El MP3 de escucha conserva la toma de 13.52 s y mide -14.79 LUFS / -1.76 dBTP. La CI del código de esta versión pasó en Python 3.11 y 3.12; su ejecución se enlaza en el informe agregado. El ejemplo de consola utiliza el texto completo y semilla 42 de la toma que pasó la comparación.

## Edición de voz 0.2.0

La edición 0.2 pasó 48 pruebas locales, incluidas preservación de tono, reducción contra un fixture con señal limpia conocida, picos entre muestras, duración exacta, transcripción temporal y bloqueo de red del proceso de inferencia. Se ejecutó Qwen3-TTS Base en CPU con una referencia aportada; el guion nuevo contiene 137 palabras. La salida se ajustó a 60 s con tempo 0.87158, sin recortar palabras, y se volvió a transcribir. Las métricas agregadas están en `validation/voice-v0.2.json`.

La locución de voz previa a mezcla mide -18.00 LUFS y -2.17 dBTP. El video de prueba de 60 s pasó frame count, duración, formato, fps, H.264/AAC y decodificación; después de AAC midió -14.02 LUFS y -1.49 dBTP. La tasa de edición respecto a la transcripción ASR fue 6/137 (4.38%): es una comparación automática que puede incluir errores del reconocedor, no una evaluación de naturalidad o de acento.

Las notas originales, el perfil y la transcripción de referencia no se publican en GitHub. La aprobación de identidad, pronunciación y acento sigue pendiente de escucha del usuario. Las 37 pruebas citadas más abajo documentan la edición inicial 0.1.

## Pruebas reproducibles

```bash
python -m unittest discover -s tests -v
python -m qaf_video benchmark --out projects/benchmark.json
```

Las pruebas incluyen referencias independientes: traza parcial densa para RDM no adyacente, entrelazamiento conocido y truncación, propagación exacta con el mismo Hamiltoniano, medidas POVM sensibles a fase, enumeración global del QUBO con restricciones y condiciones de extremos de cámara.

La entrega pasó 37 pruebas locales en Python 3.12.14. Incluyen recuperación de un contenedor deliberadamente incompleto: un único remux adicional y decodificación completa antes de publicar el resultado. Una primera prueba de 60 s produjo un error de contenedor que no se reprodujo en la repetición; se añadió esta recuperación acotada sin omitir la validación.

El flujo real de medios comprueba mezcla de cuatro pistas, ducking, rechazo de silencio, normalización, encode/decode H.264/AAC, cuadros, resolución, fps y caché que detecta un archivo modificado. El servidor se comprueba por HTTP local: token, origen, Host, confinamiento de rutas, protección ante enlaces simbólicos, guardado validado y rangos de video. El DAG se prueba con ciclos, operación no permitida, modificación de salida y cambios de ajustes.

La CI ejecuta el sistema en Ubuntu con Python 3.11 y 3.12. Los adaptadores opcionales Blender y TTS no se ejecutan en CI; su disponibilidad se declara con `doctor` y sus errores son explícitos. No se suministran credenciales.

## Referencia matemática registrada

El benchmark fija semilla 22, tres sitios y enlace máximo 4. Compara RDM con la misma información densa y dinámica con eigendecomposición Hermitiana exacta. Los errores esperados son del orden de precisión de máquina para RDM y decrecen al reducir el paso de integración; no implican ventaja de velocidad, fidelidad artística ni superioridad comercial.

`docs/validation/benchmark.json` y `release-checks.json` guardan los resultados medidos de esta entrega. Los tiempos de ejecución dependen del equipo; los hashes prueban identidad de archivos, no calidad estética.

## Pendientes explícitos

Se necesita una grabación aprobada de Barranquilla, material de cada tecnología, evidencia operacional precisa y revisión de marca para una campaña final. El fixture no demuestra capacidades clínicas o del producto. No se ha ejecutado el estudio de audiencia del manuscrito V, una comparación perceptual de render, ni una evaluación externa de liderazgo mundial.

El servidor es exclusivamente local. No está diseñado para usuarios remotos, archivos hostiles no confiables o exposición a internet. Los límites de memoria y tiempo del render físico deben ajustarse al equipo; una escena de 4K y cientos de muestras puede requerir mucho tiempo de CPU.
