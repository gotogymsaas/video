# Episodio 04 · Tu próximo punto

Animatic fotográfico híbrido de 60 segundos con imágenes ficticias generadas, voz local basada en la referencia de la serie, música DSP original y efectos procedurales propios. Los efectos son conceptuales: no representan escaneos, mediciones de estados mentales ni trayectorias observadas. No se utilizaron Weave ni Figma.

Fuente del producto: `gotogymsaas/appdesplegada`, commit `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`. `verify_source.py` reproduce un caso ficticio de presión declarada, selección del foco mental y sugerencia de rutina de 12 segundos entre puntos. Comprueba que el motor declara evidencia insuficiente para predicción y no expone riesgo calculado desde valores por defecto. `sources/sports_service_registry.py` documenta la activación de tenis; no se verificó una sesión actual de producción.

Arquitectura audiovisual revisada: `fa879d600073a3dfc72c88c36c53075264453d3d`. Incluye compositor de video real y entrada para evidencias de pose/manos; necesitan material autorizado y modelos compatibles. El generador neuronal propio continúa siendo experimental con pruebas sintéticas, no pesos cinematográficos entrenados para humanos. Este episodio usa fotografía animada y VFX, sin inventar movimiento humano ni detecciones.

La integración añade VFX por plano a `cinema.py`, valida tiempos y coordenadas, anima estelas por longitud de arco y aplica el mismo zoom a la máscara de oclusión. Se conserva la API de `hybrid_motion` para video real. Las capas de texto, subtítulos y teléfono se componen después de los efectos.

Para reconstruir desde el paquete: instalar el estudio y ejecutar desde su raíz `PYTHONPATH=. python projects/tenis-04/build.py` y `PYTHONPATH=. python projects/tenis-04/render.py`. En el repositorio público, usar `episodes/04_tennis`. La reconstrucción con voz requiere los archivos privados de audio y anclajes incluidos en el paquete descargable; se excluyen de GitHub. Para regenerar voz, instalar `scripts/setup_local_voice.py` y proporcionar el perfil autorizado mediante `QAF_VOICE_PROFILE`.

El paquete final incluye cuatro MP4, proyecto, fuentes verificadas, audio separado y subtítulos SRT/VTT. La revisión humana de voz, contenido, derechos y acabado permanece pendiente. Los controles mecánicos no constituyen aprobación editorial.

Dirección de imagen: tenista colombiana ficticia de 30 años, coleta rizada, polo esmeralda, falda negra, cancha dura al anochecer con luces doradas y montañas; plano inicial de concentración con raqueta y segundo plano en banco mirando un teléfono. Generación integrada, prompts separados, referencia visual inspeccionada para continuidad. Logo y pantalla GoToGym originales compuestos por código.
