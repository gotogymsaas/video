# Motor neuronal QAF Cinema — tres manuscritos, implementación de protocolo (2026-10-23)

Se incorporan tres diseños científicos entregados también en PDF:
1. Motor neuronal audiovisual entrenable: datos comerciales autorizados, checkpoint, LoRA, reproducibilidad.
2. Control relacional QAF: estado de escena con incertidumbre, decisiones y comparadores clásicos.
3. MLOps y evaluación: experimentos pareados, panel ciego, VBench-2.0, liberación gobernada.

## Código implementado
`neural_program.py`: exige corpus con train/val/test separados por actor/prenda; comprueba archivos, checksum de datos, derechos declarados, checkpoint y config oficial local; prepara argv del entrenador sin arrancar la GPU. `compare_matched_trials` recoge puntuaciones ciegas en pares de MP4 del mismo backbone y presupuesto y calcula diferencia bootstrap (no certifica estadística externa).

```bash
python -m qaf_video.generative_research.neural_program plan program.json --workspace /private --out /private/plan.json
python -m qaf_video.generative_research.neural_program compare trials.json --workspace /private --out /private/quality.json
```

## Integración real de entrenamiento
1. Obtener los datos con derechos para ML mediante `open_corpus.py`, sin subir personas o consentimientos a GitHub.
2. Exportar al formato oficial video/caption con `ltx_dataset_export.py`; revisar duración y etiqueta real de escenas.
3. Instalar LTX Trainer (https://github.com/Lightricks/LTX-2/tree/main/packages/ltx-trainer) con pesos **dev** y Gemma/VAEs de la misma familia, establecer config I2V LoRA exacta de su checkout. Consultar configuración oficial https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-trainer/docs/configuration-reference.md
4. Ejecutar manualmente solo después de revisar presupuesto y GPU; guardar checkpoint real y logs.
5. Comparar LoRA, backbone sin adaptación, QAF+LoRA y planificador clásico+LoRA bajo mismo hardware y semillas, y auditar resultados con VBench-2.0 (https://github.com/Vchitect/VBench/blob/master/VBench-2.0/README.md) y jurado humano.

## Restricciones científicas
No se ha entrenado aquí un modelo neuronal cinematográfico de gran escala ni se han descargado pesos o corpora comerciales. Preflight es software ejecutable pero no prueba superioridad QAF. Las métricas de pares se basan en reportes de usuarios, no en evaluadores autenticados; las pruebas CI usan archivos sintéticos y nunca se deben presentar como benchmark de video real.

El modelo conceptual QAF usa grafos temporales y funciones objetivo relacionales: su posible ventaja se falsará con comparadores clásicos de igual costo, no con lenguaje de marketing. La identidad de GoToGym se diferencia de propiedades visuales protegidas de otras franquicias.
