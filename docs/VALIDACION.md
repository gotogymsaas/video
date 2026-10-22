# Validación de la entrega

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
