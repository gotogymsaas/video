# GoToGym Quantum Coach · Sistema audiovisual

Estudio local para producir explicativos de 60 segundos con evidencia, guion, cámara, imagen, sonido y revisión. Implementa una **versión de referencia ejecutable** de los cinco manuscritos científicos de Juan Manuel Goenaga Castro. El formalismo tensorial QAF se atribuye en los documentos a Antoni Bancells.

![Storyboard de la demostración](examples/storyboard.jpg)

## Empezar

Requisitos: **Python 3.11 o superior**, **FFmpeg y FFprobe** disponibles en PATH. Funciona sin GPU, claves de nube ni Blender. La instalación inicial de dependencias requiere conexión.

1. Descarga y extrae el proyecto.
2. Windows: abre `start_studio.bat`. macOS/Linux: ejecuta `bash start_studio.sh`.
3. Abre **http://127.0.0.1:8765** y pulsa **Nuevo episodio**.
4. Genera el storyboard, modifica el proyecto y exporta un MP4.

El primer episodio es conceptual: ocho planos, música original y un estudio de luz generado por el render CPU. Puedes importar tus imágenes, clips, logo y grabación. El montaje admite vertical y horizontal; los recursos grandes se copian a `projects/<episodio>/assets`.

Instalación manual:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install .
python -m qaf_video doctor
python -m qaf_video serve --workspace projects
```

## Qué funciona

| Manuscrito | Implementación incluida |
|---|---|
| I · Fundamentos QAF | Registros de afirmaciones y fuentes, compuerta documental, normalización con máscara, estados densidad/POVM, MPS, RDM por contracción, referencia TDVP y QUBO con restricciones. |
| II · Cinematografía | Timeline a cuadros enteros, guion editable, cámara minimum jerk, SLERP, recorte por formato, tipografía, subtítulos y storyboard. |
| III · Render híbrido | Path tracer CPU de esferas difusas y espejos, luces de área, sombras y rebotes; adaptador local a Blender/Cycles; composición lineal sRGB; DAG y caché por contenido. |
| IV · Voz y sonido | Voz grabada o TTS opcional, tiempos reales del proveedor, SRT/VTT, cuatro stems, ducking y normalización medida en dos pasadas. |
| V · Validación | Catálogo de 56 perfiles con artefactos de revisión, controles de entrega, pruebas automatizadas, benchmark y registro de revisión humana. |

La matriz detallada, límites y rutas de código están en [docs/IMPLEMENTACION.md](docs/IMPLEMENTACION.md). Los [cinco PDF y sus fuentes editables](docs/manuscripts/) forman parte del proyecto.

## Generar un episodio por consola

```bash
python -m qaf_video init projects/episodio-01
python -m qaf_video validate projects/episodio-01/project.json
python -m qaf_video plan projects/episodio-01/project.json --out projects/episodio-01/outputs/plan.json
python -m qaf_video storyboard projects/episodio-01/project.json --out projects/episodio-01/outputs/storyboard.jpg
python -m qaf_video render projects/episodio-01/project.json --profile proxy --out projects/episodio-01/outputs/video.mp4
```

Para 1080 × 1920 usa `--profile vertical`; para 1920 × 1080, `--profile horizontal`. Las pruebas de ambos formatos usan `proxy` y `landscape-proxy`. Una exportación a resolución completa sigue siendo un borrador si no registra revisiones.

La opción `--final` exige composición lineal, afirmaciones vinculadas y verificadas, voz y logo originales, subtítulos vinculados al hash del audio, procedencia de recursos y revisiones fechadas de marca, voz, afirmaciones, derechos, imagen y accesibilidad. Estos son **controles de registros**, no una verificación semántica automática de la verdad, derechos o calidad artística. Consulta [docs/PRODUCCION.md](docs/PRODUCCION.md).

## Voz colombiana

Puedes usar una locutora de Barranquilla y cargar la grabación. Para probar el adaptador en línea:

```bash
python -m pip install ".[voice]"
python -m qaf_video voice --list --locale es-CO
python -m qaf_video voice --text-file projects/episodio-01/narration-es.txt --out projects/episodio-01/assets/voice.mp3
python -m qaf_video attach-voice projects/episodio-01/project.json --asset assets/voice.mp3 --captions projects/episodio-01/assets/voice.voice.json
```

El candidato por defecto es `es-CO-SalomeNeural`. El catálogo depende del servicio externo. **La etiqueta colombiana no acredita acento barranquillero**: la grabación necesita audición local. No se incluye un modelo de voz entrenado ni clonación de voces. El adaptador envía únicamente el texto indicado al proveedor cuando se ejecuta explícitamente.

## Render, investigación y automatización

```bash
python -m qaf_video native-render --out projects/luz.png --samples 64
# Solo si Blender está instalado:
python -m qaf_video blender-render --out projects/cycles.png --samples 64
python -m qaf_video benchmark --out projects/benchmark.json
# Primero crea projects/episodio-01:
python -m qaf_video build examples/workflow.json --workspace projects
python -m unittest discover -s tests -v
```

El planificador aplica una referencia clásica exacta a alternativas editoriales; los pesos son ilustrativos y no cambian las afirmaciones. La dinámica tensorial se limita a sistemas pequeños y no se presenta como una ventaja cuántica. El asignador de muestras es un asesor matemático independiente, no muestreo adaptativo integrado al path tracer.

## Alcance de esta entrega

- El sistema exporta MP4 H.264/AAC SDR; conserva informes, hashes y mediciones. La composición de entrega es lineal entre capas sRGB de 8 bits, sin certificación ACES/HDR.
- El render CPU es una referencia acotada: esferas, reflexión ideal y materiales difusos. No incluye piel, telas, pelo, volúmenes o geometría arbitraria. Blender amplía el flujo cuando se instala por separado.
- No contiene un generador neuronal de video, un modelo de voz regional entrenado ni un benchmark que demuestre liderazgo mundial. La producción cinematográfica necesita material, dirección y revisión profesional.
- El servidor escucha solo en `127.0.0.1`. Está diseñado para un equipo local, sin autenticación multiusuario ni despliegue público. Las escrituras exigen token y origen local; las rutas están confinadas al espacio de proyectos.
- No publica videos ni contacta personas automáticamente. No incorpora el código privado de la app GoToGym.

Ver [docs/VALIDACION.md](docs/VALIDACION.md), [CHANGELOG.md](CHANGELOG.md) y [NOTICE.md](NOTICE.md). Código y manuscritos: todos los derechos reservados al titular correspondiente; las tipografías mantienen su licencia propia.
