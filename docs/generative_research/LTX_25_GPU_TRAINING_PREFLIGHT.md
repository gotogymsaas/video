# Preparación para entrenamiento REAL LTX-2.5 — exportador reproducible

`ltx_dataset_export.py` convierte el manifiesto QAF con video y caption, derechos revisados y splits libres de fuga a los archivos JSON que consume `ltx-trainer`. **No consume GPU, no descarga pesos ni inicia entrenamiento.**

## Flujo

1. Preparar videos privados con consentimiento y procedencia validados en `open_corpus.py`.
2. Exportar `train.ltx.json`, `val.ltx.json`, `test.ltx.json` (columnas oficiales `video` y `caption`).
3. Clonar manualmente **el repositorio oficial** `https://github.com/Lightricks/LTX-2` en máquina GPU, revisar commit/requisitos/licencia.
4. Para entrenamiento I2V utilizar **checkpoint dev**, Gemma 4 ajustado por LTX y VAEs correspondientes. NO entrenar sobre el checkpoint distilled. Documentación oficial: https://docs.ltx.io/open-source-model/ltx-trainer/quick-start .
5. Desde `packages/ltx-trainer`, preprocesar datos de TRAIN solo con los componentes de la versión de pesos seleccionada:
   ```bash
   uv run python scripts/process_dataset.py /private/exports/train.ltx.json \
     --resolution-buckets "768x448x49" \
     --model-path /models/ltx-2.5-22b-dev-transformer-bf16.safetensors \
     --text-encoder-path /models/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
     --video-vae-path /models/ltx-2.5-video-vae-bf16.safetensors \
     --audio-vae-path /models/ltx-2.5-audio-vae-bf16.safetensors
   ```
6. En `configs/i2v_lora.yaml` (archivo de ejemplo oficial) configurar rutas de modelo, datos, output, validation y optimizador según documentación de la versión. Para GPU limitada adaptar los parámetros low-VRAM oficiales. Ejecutar `uv run python scripts/train.py configs/i2v_lora.yaml` solo después de un presupuesto/permiso concreto.
7. Conservar `val` y `test` fuera de train; registrar métricas, prompts, hashes de pesos y datos, GPUh, VRAM, fallo OOD y comparadores del mismo backbone sin LoRA/QAF.

```bash
python -m qaf_video.generative_research.ltx_dataset_export /private/videos/dataset.json \
  --out /private/exports --bucket 768x448x49
```

**Requisitos orientativos oficiales de LTX-2.5:** Linux/CUDA, Python 3.12+, CUDA 12.7+, 32 GB VRAM mínimo con ajustes y 80 GB recomendado para entrenamiento estándar, RAM 32–64 GB y almacenamiento mínimo 100 GB. Verificar la disponibilidad real de la máquina antes de comprometer gastos.

## Advertencias
- El estado comercial depende de términos LTX-2.x, incluyendo el umbral de 10 millones USD anuales de ingresos y condiciones sobre derivados/fine-tunes.
- No presumir que OpenVid/Pexels ofrecen permiso de entrenamiento comercial. No ingresar datasets que no superen `open_corpus.audit_asset`.
- El modelo experimental CinemaVAE+VideoDiT del repositorio sigue siendo una ruta científica independiente sin pesos fotorrealistas entrenados.
- Un LoRA sobre LTX es una adaptación de pesos licenciados, **no un modelo fundacional independiente entrenado desde cero**. QAF puede añadir controles de calidad y planificación, pero sus beneficios requieren pruebas frente a un planificador clásico fuerte y datos OOD.
