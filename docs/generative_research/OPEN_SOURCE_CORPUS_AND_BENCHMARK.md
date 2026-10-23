# Investigación abierta: Corpus + evaluación QAF (2026-10)

El sistema no descarga archivos de terceros automáticamente ni asume que una ficha de Hugging Face autoriza comercialmente todos los videos subyacentes. Toda entrada de un corpus se revisa **por archivo** y exige evidencia local de licencia, atribución, autorización de aprendizaje automático y consentimiento.

## Recursos contrastados
- Blender Studio Sprite Fright — CC BY en la página oficial con excepciones para marcas y materiales ajenos. Fuente candidata: https://studio.blender.org/projects/sprite-fright/pages/about/ ; Creative Commons BY-4.0 https://creativecommons.org/licenses/by/4.0/ . Para reutilizar vídeo individual, confirmar la ficha exacta y conservar atribución.
- Wikimedia Commons — verificar cada página del fichero y sus atribuciones: https://commons.wikimedia.org/ .
- Pexels API — **BLOQUEADO** sin permiso expreso para recopilación/entrenamiento IA: https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions
- OpenVid-1M — **BLOQUEADO como corpus comercial genérico** por restricciones no comerciales y licencias encadenadas: https://huggingface.co/datasets/nkp37/OpenVid-1M
- UCF101 — académico/no comercial, requiere aclaración de derechos para el uso empresarial.

## Registro local de corpus, sin publicar datos privados
```python
from qaf_video.generative_research.open_corpus import load_records, compile_training_manifest
approved=load_records('/private/videos/approved_records.json')
report=compile_training_manifest('/private/videos', approved, 'train_dataset.json')
```
Los registros contienen `schema=qaf_open_cinematic_asset_v1`, fuente/url/licencia/autor/atribución, documento local de autorización, revisor/fecha, scope, persona, prenda, archivo MP4, imagen y split. `reviewed_for_training` y `explicit_restrictions_resolved` deben marcarse solo **tras revisión humana**. Los metadatos no equivalen a una garantía jurídica; no publicar material personal ni autorizaciones.

## Benchmark pareado simple
```bash
python -m qaf_video.generative_research.paired_benchmark /private/benchmark /private/benchmark/paired.json --out /private/results/proxies.json
```
Formato `qaf_video_paired_benchmark_v1` con `pairs: [{id, seed, scene, qaf, baseline}]`. El comparador extrae diferencias temporales de luminancia, imagen y tercer orden. Es un benchmark instrumental; no certifica fluidez humana ni realismo.

Benchmark externo **VBench-2.0**: https://github.com/Vchitect/VBench/tree/master/VBench-2.0
Ejecutar VBench con las imágenes requeridas y dimensiones `subject_consistency`, `human_action`, `motion_smoothness`, `temporal_flickering`, `spatial_relationship` y evaluadores humanos ciegos. El flujo local no finge haberlo ejecutado.

## Modelo generativo recomendado
LTX-2.5, documentación https://docs.ltx.io/open-source-model/getting-started/overview/ y entrenamiento oficial https://github.com/Lightricks/LTX-2/tree/main/packages/ltx-trainer . Es open-weight sujeto a licencia LTX-2.x y restricciones de derivados; verificar condiciones de licencias según la situación de GoToGym antes de desplegar. Como alternativa técnica, HunyuanVideo-1.5 tiene licencia territorial restrictiva y no permite usar sus outputs para mejorar modelos ajenos a su familia, por lo que no es sustituto neutro.

**Criterios no cumplidos:** no hay dataset especializado de running y prendas propias con autorizaciones verificadas, GPU de entrenamiento activo, checkpoints LoRA grandes ni 24 validaciones externas del programa. Mantener el Issue #1 abierto.
