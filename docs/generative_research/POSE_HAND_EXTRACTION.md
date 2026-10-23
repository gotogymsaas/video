# Extracción real de pose y manos desde MP4

Instalar por separado `mediapipe` en una máquina CPU de investigación y descargar los archivos de modelo **oficiales**, sujetos a sus respectivas licencias: PoseLandmarker (`.task`) y HandLandmarker (`.task`). Estas dependencias no se incorporan al entorno de producción.

```bash
python -m qaf_video.generative_research.vision_extract private/actor.mp4 \
  --pose-task private/models/pose_landmarker.task \
  --hand-task private/models/hand_landmarker.task \
  --out private/observations.json --width 960 --height 540 --fps 24 --frames 192
```

La salida contiene coordenadas normalizadas de cada fotograma realmente reconocido y hashes de los modelos utilizados. Las listas quedan vacías cuando no hay observaciones fiables. Este comando **no estima segmentación ni profundidad**; añadir PNG de máscara y profundidad alineados a los campos `mask` / `depth` de cada entrada. No reemplazar observaciones faltantes por datos inventados.

Composición:
```python
from qaf_video.generative_research.hybrid_motion import render_motion
render_motion("private/shot.json","private/actor.mp4","private/composited.mp4",observations="private/observations.json")
```

`hand_follow_energy: true` activa seguimiento de pulsos por centroides de manos presentes. Para oclusión, proporcionar máscara y profundidad calibrada por cuadro; de lo contrario se procesa sin ese control.

**Límites:** no resuelve manos detrás del teléfono, geometría tridimensional precisa, estima identificaciones biométricas ni reiluminación físicamente exacta. La calidad requiere revisión humana y controles clásicos.
