# Auditoría del corpus de 106 videos — 23 octubre 2026

La inspección Git del repositorio `gotogymsaas/appdesplegada` identificó **106** MP4 en `Videos_test_gimnasio/`, **10** identificables por nombre de ejercicio, y **96** grabaciones sin etiqueta deportiva fiable. Tamaño total: **226773466 bytes**.

Se publicó `triage_report.json` con **106 filas**, ruta SHA Git, tamaño, prioridad de revisión y estado inicial. No se descargó ni analizó el contenido visual; todos los derechos/consentimientos siguen **UNREVIEWED**, todas las secuencias permanecen fuera del entrenamiento y no se asignaron aleatoriamente identidades.

Para completar el inventario local sin enviar videos al repositorio:

```bash
python -m qaf_video.generative_research.gym_corpus_triage \
 docs/generative_research/gym_corpus/candidate_inventory.json \
 --local-root /private/gotogym-approved-review --out /private/gym_triage_private.json
```

El modo local usa FFprobe para duración, resolución, FPS y SHA-256, y detecta duplicados exactos por contenido. Los hashes Git de 40 caracteres se comparan separadamente: no son SHA-256. Este proceso no extrae rostros ni presume consentimiento. Duplicados visuales, semejanza de deportistas y calidad de movimiento requieren decodificación y revisión humana supervisada.

Para entrenar: reunir los consentimientos de uso generativo para cada atleta, anotaciones verdaderas de ejercicios, y partición train/val/test **por deportista, ropa y sesiones correlacionadas**; entonces ejecutar `gym_corpus_adapter.py`, `ltx_dataset_export.py` y el runner GPU privado. No publicar rostros, videos ni identificadores personales en Git.

**Resultado actual:** preparación de auditoría y etiquetas sugeridas. No dataset legalmente habilitado ni checkpoint entrenado.
