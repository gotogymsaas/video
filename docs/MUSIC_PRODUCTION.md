# Música integrada y episodio 02: Fútbol

La ampliación incorpora Music Lab al proyecto canónico y al estudio local; los artículos M01-M05 se encuentran en `docs/music`.

## Uso desde el estudio
1. Selecciona un episodio cinematográfico con narración WAV importada o generada.
2. Abre **Cine y pantalla móvil**, elige dirección musical y pulsa **Componer y mezclar con mi voz**.
3. El trabajo genera cuatro stems, preview musical, plan de cues y mezcla medida. Actualiza `music` y `mix` atómicamente.
4. Escucha la mezcla desde el reproductor, revisa comprensión y groove y exporta el formato elegido.
5. La aprobación de audio se invalida al crear una mezcla. Para exportar con revisión registrada, la revisión humana `reviews.audio` debe incluir revisor, fecha y `asset_sha256` del mix exacto.

CLI equivalente:
```bash
python -m qaf_video.music_research produce projects/episodio/project.json --preset coastal_pulse --seed 22
```

Sin `music_brief`, el preset es dirección creativa explícita. Con un `music_brief` en el proyecto, se calcula el perfil fechado y se selecciona entre presets factibles mediante M01; el resultado queda en `selection.json`. Valores de ejemplo no certifican tendencia. `python -m qaf_video.music_research evaluate ratings.json` ejecuta el protocolo M05 sobre valoraciones aportadas; no inventa oyentes ni aprueba la campaña.

La música es síntesis DSP original y editable; no se ha entrenado el generador neuronal futuro descrito en M02. El módulo reutiliza mezcla sidechain y normalización real de FFmpeg, con liberación relativa al beat. Un archivo técnicamente válido puede requerir cambios artísticos. El nuevo flujo comprueba el proyecto antes de reemplazarlo, evita sobreescribir otra edición, conserva la mezcla previa ante fallo e impide aprobación de un mix con hash distinto.

## Fútbol: alcance verificable
El episodio 02 se apoya en `gotogymsaas/appdesplegada` commit `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`, específicamente contratos, catálogo, planner y motor `qaf_football_intelligence`. Una ejecución local del motor puro con lateral, objetivo de cobertura y 15 minutos produce actividades educativas que caben en ese tiempo. La continuación consume el resultado anterior. Esto no acredita que el flag de producción esté habilitado ni prueba disponibilidad actual para toda cuenta.

La película es un **animatic fotográfico cinematográfico**: tres keyframes de un futbolista adulto ficticio, reencuadres animados, gráficos explicativos exactos y pantalla original en teléfono. No es rodaje de acción ni generación neuronal de movimiento humano. La pantalla de bienvenida es auténtica; las tarjetas pedagógicas se rotulan como visualización conceptual, no como una captura de interfaz que no se ha verificado.

No se anuncian tracking de partidos, xG, diagnóstico físico, planes de carga ni eficacia deportiva. CTA del episodio: «Activa fútbol», sustentado en el flujo documentado del producto; no se realiza contacto externo ni se modifica el backend deportivo.

## Reproducibilidad y privacidad
La carpeta `episodes/02_football` contiene receta visual, guion, fuentes fijadas, fixture, storyboard y configuración musical. Su proyecto público funciona como montaje sin voz privada. Para reproducir la versión hablada, importa una narración autorizada y sus subtítulos medidos, genera la música y exporta. El paquete privado descargable incluye el proyecto completo y MP4; las referencias de voz y los pesos permanecen fuera de GitHub.

Las nuevas imágenes fueron creadas con la herramienta integrada de generación de imágenes; los prompts y la continuidad se documentan con el episodio. La síntesis de voz usa el runtime local aislado, la referencia previamente autorizada y los pesos preentrenados Qwen/Whisper de terceros; no es entrenamiento propio.

## Memoria de la voz
El adaptador acepta precisión explícita `bfloat16` o `float32` en CPU y conserva el código de salida del worker al fallar. El estudio ofrece BF16 para menor memoria y FP32 para compatibilidad; se debe escuchar la salida en el hardware real. No se eluden los controles de privacidad ni se permite FP16 en CPU. Los pesos y el runtime se instalan por separado; SoX puede requerir instalación del sistema según el backend.
