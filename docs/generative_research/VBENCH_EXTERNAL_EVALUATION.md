# VBench / VBench-2.0 — evaluador externo de videos generados

Las métricas simples FFmpeg disponibles en `paired_benchmark.py` no constituyen evaluación perceptual completa. Este adaptador ejecuta opcionalmente **VBench original** (si está instalado por el usuario) para consistencia de sujeto, movimiento, acciones humanas y flicker; lo hace como procesos locales con argumentos permitidos.

Fuente oficial: https://github.com/Vchitect/VBench . VBench-2.0 (https://github.com/Vchitect/VBench/tree/master/VBench-2.0) cubre errores más avanzados de física, anatomía y composición. Por ser un proyecto con comandos y pesos particulares, ejecutar VBench-2.0 mediante su propio README, no mediante supuestos de compatibilidad con VBench v1.

```sh
python -m qaf_video.generative_research.vbench_external \
   /private/VBench /private/evaluations/clip_pairs/baseline
# Solo inspección de plan. Al instalar dependencias y pesos oficiales:
python -m qaf_video.generative_research.vbench_external \
   /private/VBench /private/evaluations/clip_pairs/qaf --execute
```

Cada comparación debe usar los mismos fotogramas iniciales, prompts, semilla, duración, pesos base y costo computacional. El resultado de VBench requiere revisión humana ciega y métricas de identidad/ropa/logos y derechos de uso.

**No hay puntuaciones VBench reales registradas aún.** Es una interfaz opcional para ejecutar el benchmark cuando se disponga de videos finales y entorno GPU.
