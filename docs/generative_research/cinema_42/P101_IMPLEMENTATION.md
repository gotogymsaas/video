# P101 — Motor de evidencia tipada, primera implementación ejecutable

Uso previsto: renderizar cifras verificables sobre una escena GoToGym sin pedir a un generador de video que escriba textos o fabrique estadísticas.

`scientific_overlay.py` exige `qaf_scientific_overlay_v1` y registra por dato ID, etiqueta, valor numérico finito, unidad permitida, fecha de observación, tipo de evidencia (`user_reported`, `device_measured`, `clinician_documented`) y referencia a un registro privado. Dos barreras explícitas impiden declaraciones diagnósticas o de tratamiento no respaldadas.

Ejemplo de ejecución Python:
```python
from qaf_video.generative_research.scientific_overlay import render_overlay
render_overlay("scene.png","claims.json","scene_with_claims.png")
```

Limitaciones: la presencia de `source_record` constituye procedencia declarada, no autenticación de la medición ni autorización de divulgación. Esta salida es solo imagen PNG de prueba y aún necesita integración de eventos/tiempo al compositor audiovisual. Los contenidos clínicos requieren revisión profesional y control de privacidad. Este módulo no demuestra la eficacia del análisis relacional QAF ni implementa íntegramente P102/P103.
