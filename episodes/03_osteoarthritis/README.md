# Episodio 03 · Lo que sientes merece contexto

Animatic cinematográfico de 60 segundos para GoToGym Quantum Coach. Dos imágenes generadas de una protagonista ficticia, gráficos conceptuales exactos, pantalla original de bienvenida, voz de referencia autorizada de la serie y composición DSP original. No representa rodaje ni movimiento neuronal generado.

## Evidencia y alcance

Fuente del motor: `gotogymsaas/appdesplegada`, commit `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`, `backend/api/qaf_osteoarthritis/{contracts,engine}.py` y `specialist_inputs.py`. `python verify_source.py` reproduce el caso ficticio: dolor previo 4, actual 5, diferencia descriptiva +1; acompañamiento de un plan profesional existente; ante imposibilidad declarada de apoyar la articulación, ruta de atención y suspensión de propuestas de ejercicio. No se comprobó una sesión actual de producción ni eficacia clínica.

No se afirma diagnóstico, predicción de brotes, inferencia de causas, medición del daño articular, prescripción de ejercicios ni modificación de tratamiento. Los campos son declarados por la persona. Los gráficos son una representación editorial, no capturas de una interfaz clínica. `sources/health_service_registry.py`, del mismo commit fijado, documenta el alias osteoartritis/artrosis, la invocación explícita, los campos `safety_acknowledgement` y `osteoarthritis_context`, y la secuencia de persistencia y entrega. Esta lectura documenta la activación; no demuestra que el flag o la conversación funcionen hoy en producción.

## Producción

Con el paquete GoToGym Audiovisual v0.5 instalado, ejecutar desde su raíz `PYTHONPATH=. python projects/osteo-03/produce.py finish` para recomponer música y renderizar con la voz ya generada; requiere conservar `evidence/voice-result.json`, `assets/voice-film.wav` y las fuentes. En el repositorio público, sustituir `projects/osteo-03` por `episodes/03_osteoarthritis`. El comando `voice` necesita el motor opcional instalado por `scripts/setup_local_voice.py` y el perfil privado de voz de la serie; `QAF_VOICE_PROFILE` permite indicar su ruta. Los pesos y referencias de voz no se publican en GitHub. Los subtítulos corregidos se entregan como `subtitles-es.srt` y `subtitles-es.vtt`.

La salida incluye vertical 1080×1920 y horizontal 1920×1080, con y sin subtítulos, 30 fps y 1800 cuadros. Los cambios de plano principales se ajustan a palabras reconocidas en el audio, sobre la cuadrícula de 30 fps. Los subtítulos usan anclajes de reconocimiento medidos y texto del guion; sus advertencias permanecen disponibles para revisión. La marca usa una guía fonética solo en la entrada del sintetizador; la escritura pública permanece GoToGym Quantum Coach. La mezcla final se mide a aproximadamente −14 LUFS y pico verdadero ≤−1 dBTP. Las aprobaciones humanas de voz, contenido, imagen y derechos permanecen pendientes; los controles mecánicos no las sustituyen.

El adaptador LTX-2.5 del repositorio requiere un servidor ComfyUI equipado con pesos y GPU. Esta sesión no dispone de ese servidor. La alternativa externa consultada requiere vincular Weave y Figma; no se ejecutó ni se cargaron créditos de video neuronal. La composición DSP es original y procedural: no se presenta como música neuronal entrenada ni se afirma ventaja independiente del modelo QAF.

## Dirección de imagen

Imágenes creadas con la herramienta integrada de generación. Primera escena: mujer colombiana caribeña ficticia de 55 años, blusa teal, escribiendo un diario junto a una ventana de una casa con patio en Barranquilla, luz dorada y sombras esmeralda; sin texto, logos ni visualización médica. Segunda escena: conservar identidad, vestuario y casa; plano junto a la escalera con mano sobre el pasamanos, expresión tranquila, anatomía creíble, sin promesas de recuperación. La imagen seleccionada se inspeccionó antes de generar la continuidad.
