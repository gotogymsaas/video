# Integración local LTX-2.5 → ComfyUI → GoToGym Video

Se publica un **adaptador ejecutable**, sin dependencias adicionales, para preparar y enviar workflows API a un servidor **ComfyUI local** equipado con el template oficial LTX-2.5 I2V. No descarga modelos, no arrienda GPU, no da permiso legal por sí solo y nunca ejecuta inferencia durante CI.

## Preparar GPU y el workflow (paso humano)
1. Instalar ComfyUI siguiendo su documentación oficial: https://docs.comfy.org/ .
2. Abrir Templates y seleccionar `video_ltx2_5_i2v` (I2V) o `video_ltx2_5_flf2v` para primer/último fotograma: https://docs.ltx.io/open-source-model/usage-guides/image-to-video/ .
3. Descargar los modelos solicitados desde fuentes originales; verificar licencia LTX-2.x (umbral de ingresos, transferencia de derivados y condiciones de uso). Ejecutar primero la plantilla en UI.
4. Exportar el workflow como **API format** y registrar los node IDs *exactos* de imagen, prompt, seed, frames y FPS. Esos IDs varían según versión; el adaptador **no los inventa**.
5. Crear documentación privada de aprobación de uso de imagen y modelo. Si ComfyUI corre remotamente, utilizar túnel SSH a `127.0.0.1:8188`; el adaptador prohíbe endpoints arbitrarios.
6. Usar 97 cuadros a 24 fps (≈4,04 s), dimensiones de base múltiplos de 32 y pesos LTX correspondientes. Para cinco segundos aproximados, 121 cuadros a 24 fps es `8n+1`; comprobar si el workflow/VRAM lo admite.
7. El workflow debe tener nodo `SaveVideo` o equivalente que exporte un MP4 en `output`.

## Manifiesto JSON de trabajo
```json
{
 "schema":"qaf_comfy_i2v_job_v1",
 "model_family":"LTX-2.5",
 "license_checked":true,
 "rights_checked":true,
 "review_document":"permits/approved.txt",
 "image":"reference.png",
 "prompt":"A runner moves forward with plausible gait and an elegant lateral camera track",
 "seed":22,
 "frames":97,
 "fps":24,
 "workflow":{"...":"PEGAR WORKFLOW API EXPORTADO COMPLETO"},
 "bindings":{
   "image":{"node":"ID_REAL","input":"image"},
   "prompt":{"node":"ID_REAL","input":"text"},
   "seed":{"node":"ID_REAL","input":"noise_seed"},
   "frames":{"node":"ID_REAL","input":"length"}
 }
}
```
Es un **esquema ilustrativo**, los campos inputs reales deben coincidir con el workflow instalado. Adjuntar en `bindings` el `fps` solo si está presente en el flujo.

## Ejecutar
```bash
python -m qaf_video.generative_research.comfy_local private/job.json --workspace private
# Inspecciona la preparación SIN enviar datos a GPU
python -m qaf_video.generative_research.comfy_local private/job.json --workspace private \
  --execute --out private/results/running_i2v.mp4
```
Antes de ejecutar, leer, verificar y completar `license_checked`, `rights_checked` y `review_document`. Estos son datos declarados por un humano, no certificación automatizada. La salida queda como **generada, no revisada**; el modelo y checkpoint siguen debiendo verificarse independientemente.

## Introducir el MP4 en el episodio
`python -m qaf_video.generative_research ingest-clip projects/episode/project.json --shot 0 --clip assets/neural-output.mp4 --provenance projects/episode/provenance.json`

La importación exige los campos de procedencia y resetea la revisión humana sobre la imagen y los derechos. No hay aprobación automática, no se modifican los controles de producción existentes.

## Limitaciones
La API oficial ComfyUI define `POST /upload/image`, `POST /prompt`, `GET /history/{prompt_id}`, `GET /view`. El adaptador necesita que la instalación genere archivos MP4 en history/output y no cubre nodos privados con contratos distintos. Ni este contrato ni el backend externo validan la supuesta ventaja audiovisual de QAF.
