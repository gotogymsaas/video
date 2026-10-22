# Voz regional y pronunciación multilingüe · 0.3.0

El objetivo es conservar una identidad vocal aportada, preparar audio utilizable y generar guiones nuevos. El origen regional es una descripción del usuario, no una inferencia automática del código.

## Modelo operativo

La ruta completa es **OGG/WAV → análisis → comparación restringida → referencia → síntesis local → sonoridad → transcripción temporal → revisión → mezcla y video**.

`voice_lab.py` mide actividad por energía, periodicidad, frecuencia fundamental aproximada, cambios espectrales, duración, clipping y nivel relativo de intervalos tranquilos. Este último es un proxy: no equivale a SNR verdadero sin una referencia limpia. Una señal sin suficiente silencio hace que la atenuación de ruido se abstenga.

El procesamiento preserva fase y número de muestras. Emplea una reducción espectral tipo Wiener con suelo de ganancia en la banda de voz y un filtro suave de graves. No cambia deliberadamente el tono ni crea palabras. La masterización posterior controla sonoridad y picos; las notas cortas con transitorios pueden necesitar limitación adicional.

Para cada muestra se consideran cuatro intensidades. La utilidad combina reducción del proxy de ruido y penalización del cambio espectral; las restricciones limitan el cambio mediano de tono a 0.6 semitonos y el cambio espectral medio de 140–4000 Hz a 3 dB. Los pesos son heurísticos, versionados y revisables. El presupuesto usa unidades de complejidad del preset, no una estimación certificada de milisegundos de CPU.

Se resuelve una selección clásica exacta con el mismo compilador QUBO del manuscrito I. Si las alternativas fallan los límites se conserva la señal original. La selección de referencia elige un fragmento continuo de 4–10 segundos, sujeto a presupuesto de duración. No se introducen fases MPS sin observaciones que las identifiquen, ni se atribuye a QAF la creación de fonemas por sí mismo.

## Síntesis de textos nuevos

`voice_local.py` inicia un proceso separado con Qwen3-TTS-12Hz-0.6B-Base. El motor recibe el fragmento real y su transcripción para acondicionar la identidad de voz. No se entrena un modelo nuevo por locutora. La transcripción automática inicial permanece marcada como no revisada y puede corregirse en `reference_text` del perfil antes de producir.

El perfil conserva el hash del WAV. Si se modifica la referencia, el sistema rechaza la síntesis hasta reconstruir o actualizar de forma explícita el perfil. La salida se etiqueta como sintética y pendiente de escuchar. Qwen y faster-whisper mantienen sus respectivas autorías y licencias.

La decodificación usa el muestreo recomendado en la configuración publicada del modelo, con semilla registrada y presupuesto de tokens de audio ligado a guion/duración. Una prueba corta con decodificación greedy se prolongó y fue rechazada por el control de duración. Alcanzar el presupuesto de generación también se considera un fallo para revisión: no se presenta una salida truncada como una locución completa. La demostración larga se conserva como una toma experimental cuyo ajuste de decodificación se registra en su informe.

La inferencia CPU funciona sin GPU, con un coste de tiempo considerable. El parámetro CLI `--device` admite `cpu`, `cuda:0` y `mps`; en esta entrega se ejecuta y valida CPU. Los otros dispositivos requieren hardware y pruebas adicionales. El código y dependencias se instalan por separado de los pesos.

## Palabras y frases en otros idiomas

El motor publicado admite español, inglés, portugués, francés, italiano, alemán, chino, japonés, coreano y ruso. La versión 0.3 elimina el español fijo de síntesis y reconocimiento. El idioma del perfil sigue describiendo la **grabación de referencia**; elegir inglés como destino no hace que esa grabación española se transcriba como inglés. No se traduce el guion automáticamente.

En **Tu voz de marca**, elige **Idioma de la narración**. Para nombres o expresiones extranjeras activa **Definir el idioma de cada frase**, escribe las frases en orden y elige el idioma de cada una. Se reutiliza el mismo prompt de referencia; las frases se sintetizan consecutivamente, con una pausa de 120 ms y fundidos de borde de 3 ms. La continuidad tímbrica y prosódica entre frases requiere audición. Conviene agrupar una expresión completa en lugar de cambiar de idioma en cada palabra.

**Automático** deja la decisión al motor y al reconocedor. Es útil para ensayar texto mezclado, pero no garantiza que un nombre de marca se pronuncie como se desea. La selección explícita por frase ofrece control reproducible sobre el idioma solicitado; tampoco certifica fonemas, variedad regional o acento nativo. La guía de marca debe fijar cómo se dicen GoToGym y Quantum Coach, las siglas y los términos técnicos. Escribe los nombres correctamente en el guion; cualquier variante fonética experimental debe audicionarse y no sustituir silenciosamente el texto de marca en pantalla.

Ejemplos de consola:

```bash
python -m qaf_video voice-clone --profile projects/episodio-01/voice-profiles/barranquilla/voice-profile.json --text-file narration-en.txt --language en --out projects/episodio-01/assets/voice-en.wav
python -m qaf_video voice-clone --profile projects/episodio-01/voice-profiles/barranquilla/voice-profile.json --segments-file examples/narration-multilingual.json --out projects/episodio-01/assets/voice-es-en.wav
```

El JSON contiene hasta 24 objetos con `text` e `language`; el total no supera 5000 caracteres. Se aceptan nombres del motor o códigos ISO (`es`, `en`, `pt`, etc.). Las variantes de país no se presentan como voces regionales certificadas. El presupuesto de audio considera caracteres CJK, evitando tratar una frase sin espacios como una sola palabra.

El ASR analiza cada intervalo de audio con su idioma, sin traducirlo; el informe conserva los tiempos y el idioma utilizado. Solo el modo automático registra probabilidad de detección; elegir un idioma explícito no demuestra que se haya detectado. Después del ajuste temporal vuelve a reconocer los intervalos del audio final. Para chino/japonés se utiliza distancia por caracteres; para los demás, por palabras. `script_comparison.rate` toma la peor frase: una expresión inglesa omitida no se diluye en una narración española larga. `word_error_rate` se conserva para compatibilidad en textos evaluados por palabras y es `null` cuando corresponde evaluar por caracteres.

La aceptación inicial exige ≤25% en **cada frase**. Es una señal de integridad del guion basada en ASR; no mide pronunciación fonética ni prueba que el timbre conserve la identidad. `pronunciation_human_review` permanece `pending`. Antes de publicar, escuchar nombres, acentuación, consonantes, ritmo, respiraciones y uniones, y aprobar el carácter barranquillero con una persona familiarizada con esa voz.

## Sonoridad, guion y subtítulos

Las comparaciones se preparan a -18 LUFS, mono 48 kHz, con objetivo de pico real -2 dBTP. Esa es una referencia de voz previa a mezcla. La distribución audiovisual mantiene el perfil editorial -14 LUFS definido en el sistema general.

La transcripción del audio generado produce tiempos de palabras. Se agrupan en cues legibles y se exportan SRT/VTT. Los tiempos se calculan a partir del audio; no se inventan distribuyendo frases por minuto. Son estimaciones de ASR, no un alineamiento forzado certificado.

Se compara el guion con lo reconocido mediante distancia de edición por palabras o caracteres según el idioma. Un error de ASR puede aumentar esa tasa; una tasa baja no prueba naturalidad, identidad o veracidad. La interfaz solo vincula automáticamente una toma con tasa ≤25% en cada frase, subtítulos presentes y duración dentro del episodio. Esa compuerta es de revisión inicial, no aprobación editorial final.

Para un minuto, escribe el guion, genera, mide y ajusta la redacción o la dirección vocal. El ajuste `--seconds 60` limita el tempo a 0.8–1.08 sin desplazamiento deliberado de tono, verifica pausas reales y reserva espacio de cierre. Después vuelve a transcribir el audio resultante. Rechaza guiones cuya duración no pueda acomodarse dentro de esos límites; no recorta palabras. La audición decide si la cadencia ajustada sirve para la campaña.

## Procesamiento local y telemetría

La descarga inicial obtiene únicamente pesos públicos. Los archivos de voz no se envían para esa descarga. Durante inferencia se configuran **antes de inicializar bibliotecas** `ORT_DISABLE_TELEMETRY=1`, `HF_HUB_DISABLE_TELEMETRY=1`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `DO_NOT_TRACK=1` y `GRADIO_ANALYTICS_ENABLED=False`. Se desactivan además los eventos de ONNX Runtime por su API.

En Linux, el proceso de inferencia instala una política seccomp que deniega socket, connect y envío de datos. La prueba automatizada verifica que no puede crear un socket. El servidor local conserva su conectividad de loopback porque la política se aplica únicamente al proceso hijo. En Windows/macOS se aplican las opciones offline y de telemetría, sin afirmar el mismo aislamiento de sistema operativo.

Los originales no se modifican. Los perfiles, transcripciones de referencia y comparaciones pertenecen al proyecto privado; se excluyen del repositorio público. El usuario debe aprobar la grabación y su uso para la campaña antes de publicar una voz sintética.

## Comandos y artefactos

`voice-prepare` produce `voice-profile.json`, `reference.wav`, pares A/B y `escuchar.html` sin recursos remotos. `voice-clone` produce WAV, informe `.voice.json`, SRT y VTT. El informe separa transcripción, comparación con guion, mediciones y revisión humana.

La preparación usa NumPy y FFmpeg. La síntesis necesita ejecutar primero `python scripts/setup_local_voice.py`, con conexión para descargar aproximadamente 3 GB de pesos y las dependencias del motor. El instalador no lee grabaciones ni guiones. En Linux se requiere libseccomp.

## Referencias primarias

- [Qwen3-TTS: API de clonación condicionada por referencia y licencia](https://github.com/QwenLM/Qwen3-TTS).
- [faster-whisper: transcripción y tiempos por palabra](https://github.com/SYSTRAN/faster-whisper).
- [ONNX Runtime: control de telemetría](https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md).
- [Hugging Face: modo offline y desactivación de telemetría](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables).
