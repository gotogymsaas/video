# Correspondencia entre ciencia y software

Edición de referencia 0.1.0. Los manuscritos son documentos de diseño científico; no todas sus propuestas equivalen a un modelo entrenado o un experimento realizado. Esta matriz distingue código ejecutable, adaptadores y trabajo experimental pendiente.

**Actualización 0.2.0:** la ruta de voz se amplió con referencias OGG, procesamiento restringido, comparaciones A/B, síntesis Qwen3-TTS local y transcripción temporal. Esa ruta se ejecutó con las muestras aportadas y un guion nuevo; ver [VOZ.md](VOZ.md) y [VALIDACION.md](VALIDACION.md). El adaptador Cycles sigue requiriendo instalación y validación externa.

## I · Fundamentos QAF audiovisuales

| Componente | Código y verificación | Alcance |
|---|---|---|
| Fuentes, afirmaciones y compuerta editorial | `core.validate`, `project.claims`, `shots.claim_ids`; pruebas de registros incompletos | La revisión la registra una persona. El código no verifica por sí solo que la fuente respalde la frase ni que una capacidad esté disponible. |
| Normalización robusta y ausencias | `research.robust_normalize` | Límites fijados por el usuario; no se ajustan a resultados de prueba. Conserva la máscara. |
| Densidad y POVM | `research.density`, `validate_density`, `povm_read` | Valida positividad, hermiticidad, traza y completitud. No interpreta utilidades arbitrarias como probabilidades. |
| MPS y observables locales | `mathematics.MPS.from_dense`, `rdm`, `coherence_feature` | Entrada densa de 1–8 sitios binarios; enlace hasta 32. La RDM se contrae desde los tensores sin reconstruir el estado denso. |
| Dinámica proyectada | `MPS.tdvp`, `planning.benchmark` | Referencia explícita de tangente para hasta 6 sitios: mínimos cuadrados, midpoint y retracción TT-SVD. No es un integrador escalable de barrido ni garantiza conservación exacta de energía. |
| QUBO y restricciones | `compile_qubo`, `solve_choices` | Penalización one-hot y presupuesto con slack binario. La ejecución usa enumeración clásica exacta hasta un millón de combinaciones. Se prueba contra el mínimo global del QUBO pequeño. |
| Replanificación por eventos | `research.replan_event` | Distancia de traza, invalidación por evidencia y nuevas restricciones. El cambio de dimensión invalida la comparación. |

La fase de los ejemplos es una construcción conocida, no una inferencia validada sobre espectadores. El planificador de cámara usa una referencia clásica con interacciones idénticas; no cambia el texto ni proclama superioridad QAF. Para conectar dinámica a decisiones creativas hay que fijar observables, datos y comparadores antes de evaluarla.

## II · Cinematografía computacional

| Componente | Implementación | Alcance |
|---|---|---|
| Montaje temporal | `core.validate`, `render.compositor.Movie`, `pipeline.render_project` | Cuadros enteros, cobertura exacta, cortes y fundidos de gráficos. Las tomas de video se decodifican en orden. |
| Movimiento suave | `minimum_jerk`, `camera_position`, `slerp` | El compositor aplica minimum jerk al zoom 2D. Las utilidades 3D están disponibles como API; el adaptador Cycles incluido produce una escena fija. |
| Dirección de atención | `Movie.text`, `nodes`, `card`, `focus`, `zoom` | Jerarquía editorial determinística, validación de desbordamiento y recorte por orientación. No es un modelo de atención visual entrenado. |
| Identidad y formatos | `assets/brand.json`, `project.brand_colors`, `Movie` | Paleta provisional editable; rótulos y texto se componen por separado de la imagen. El logo debe ser un recurso original autorizado. |
| Storyboard y accesibilidad | `pipeline.storyboard`, subtítulos del proyecto | Hoja de composición con gráficos visibles. La comprensión, contraste en todos los fondos y lectura real requieren revisión humana. |

No se incluyen personajes generados, una simulación anatómica, captura de movimiento ni métricas de percepción inventadas. La misma imagen en ocho planos es un fixture para comprobar el sistema, no una campaña terminada.

## III · Render híbrido

| Componente | Implementación | Alcance |
|---|---|---|
| Transporte de luz | `render.pathtrace` | Trazado Monte Carlo vectorizado CPU, Lambert, espejo ideal, muestreo de luz esférica de área, sombras, entorno, ruleta rusa reponderada y profundidad máxima. No implementa MIS general, GGX, volúmenes o textiles. |
| Adaptador PBR externo | `render.blender_adapter`, `blender_scene` | Invoca Blender/Cycles local con materiales Principled y luces de área. Blender no se distribuye ni está instalado en el entorno de esta entrega; adaptador sin prueba de ejecución aquí. |
| Asignación de muestras | `research.allocate_samples` | Solución continua por raíz cuadrada y refinamiento entero greedy bajo presupuesto. Es un asesor de referencia independiente; no está integrado al muestreo del renderer. El entero con costes desiguales no tiene certificado global. |
| Composición y color | `color`, `Movie.composite`, `color_pipeline` | Transferencia sRGB, alfa compuesto en lineal y vista Reinhard documentada para el render. Entre capas se usan entradas de 8 bits. No se afirma ACES, OCIO, HDR o máster EXR. |
| DAG e invalidación | `graph.build`, `order_nodes`, `examples/workflow.json` | Operaciones permitidas explícitas, orden topológico serial, claves por código/ajustes/entradas/dependencias y verificación de hashes de salida. Rechaza ciclos, shell y rutas externas. |
| Entrega atómica | `pipeline.render_project` | Temporal, MP4 completo, comprobación y cambio atómico. Reutilización de un render completo si coincide la clave y su hash. No hay recuperación por frame después de una interrupción. |

La salida MP4 es H.264 8-bit YUV420 limitado, matriz/primarias BT.709 y transferencia sRGB etiquetada. La escena lineal nativa se conserva adicionalmente en `.linear.npy`. Un máster flotante de composición, intercambio OTIO, denoising temporal, recursos generativos de identidad y benchmarking perceptual amplio quedan fuera de esta versión.

## IV · Voz, sonido e identidad

| Componente | Implementación | Alcance |
|---|---|---|
| Voz grabada | `project.voice`, comando `attach-voice`, interfaz de recursos | La vía recomendada para controlar un acento costeño específico es una locutora real y su audición. |
| TTS opcional | `voice.synthesize`, `available_voices` | edge-tts en línea, tiempo límite y error explícito. Candidato es-CO-SalomeNeural sujeto al catálogo vigente. No entrenado, licenciado o certificado por este proyecto. |
| Alineación | `captions_from_boundaries`, `write_captions` | Usa límites de palabras del servicio o intervalos importados. Exporta JSON/SRT/VTT sin repartir frases artificialmente en partes iguales. No se incluye alineador forzado de audio grabado. |
| Mezcla | `audio.mix_audio` | Voz, música, ambiente y efectos; resampling estéreo 48 kHz, ducking por sidechain, medición y normalización en dos pasadas. Música/ambiente pueden repetirse; voz/efectos se rellenan y recortan al episodio. |
| QA sonoro | `audio.measure`, medición posterior a AAC | Perfil editorial -14 LUFS, objetivo de mezcla -1.5 dBTP para margen de codificación. Tolerancia final ±1.5 LU y pico ≤ -0.8 dBTP. Audio silencioso se rechaza. La escucha real sigue pendiente. |

No se implementa un nuevo sintetizador neuronal, evaluación perceptual automática de autenticidad regional o clonación de una persona. El programa de casting y revisión de los documentos sigue siendo un trabajo humano.

## V · Validación y organización profesional

| Componente | Implementación | Alcance |
|---|---|---|
| 56 profesiones | `assets/professions.json` y `docs/PROFESIONES.md` | Cada perfil declara responsabilidad y artefacto. No se afirma que 56 agentes expertos hayan realizado o aprobado el trabajo. |
| Registros de aprobación | `core.validate(..., final=True)` | Marca, voz, afirmaciones, derechos, imagen y accesibilidad: aprobación, responsable y fecha. Los hashes identifican bytes, no acreditan derechos ni verdad. |
| Entrega técnica | `pipeline.delivery_check` | Frame count, duración, orientación, fps, codec H.264, AAC cuando procede y decodificación completa sin errores. |
| Evaluación reproducible | `tests`, `planning.benchmark`, CI | Casos pequeños contra referencias numéricas y flujo de medios real. No son un estudio con audiencia. |
| Plan estadístico | `research.paired_sample_size` | Aproximación de tamaño para pares independientes: el ejemplo del manuscrito da 32. No trata evaluaciones agrupadas como unidades independientes. |

El diseño jerárquico de audiencia de 12 episodios, 36 versiones y 60 participantes **no se ha ejecutado**. No se incluyen valoraciones sintéticas presentadas como datos humanos ni conclusiones de eficacia comercial. El liderazgo técnico y la calidad artística deben demostrarse con material y evaluaciones reales.

## Fuentes técnicas de implementación

- [FFmpeg: loudnorm y sidechaincompress](https://www.ffmpeg.org/ffmpeg-filters.html).
- [edge-tts: streaming y límites de palabras](https://github.com/rany2/edge-tts/blob/master/src/edge_tts/communicate.py).
- [Physically Based Rendering, 4.ª edición: path tracing](https://www.pbr-book.org/4ed/Light_Transport_I_Surface_Reflection/Path_Tracing).
- Los cinco manuscritos incluyen sus referencias científicas y la distinción entre antecedentes aportados y propuestas de transferencia audiovisual.
