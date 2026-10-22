# Guía de producción de un minuto

## Preparación del equipo

Instala Python 3.11+ desde [python.org](https://www.python.org/downloads/) y FFmpeg desde sus [distribuciones oficiales enlazadas](https://ffmpeg.org/download.html). En Debian/Ubuntu puede instalarse con `sudo apt install ffmpeg`; en macOS con Homebrew, `brew install ffmpeg`. En Windows añade la carpeta `bin` de FFmpeg a PATH. Comprueba `python --version`, `ffmpeg -version` y `ffprobe -version` en una terminal nueva.

Los lanzadores crean un entorno Python del proyecto, instalan el paquete y abren el servidor local en la terminal. Abre la dirección mostrada en tu navegador. Conserva la terminal abierta durante los trabajos; Ctrl+C detiene el estudio. Los proyectos permanecen en la carpeta `projects`.

## Del documento a la pieza

1. **Define una sola promesa demostrable.** Separa qué dice el artículo, qué implementa el repositorio y qué recibe la persona hoy. Un antecedente científico no prueba una integración de producto.
2. **Registra la evidencia.** Cada entrada de `claims` necesita fuente, estado y alcance. Una afirmación verificada requiere `verified_at` y `reviewer`; usa una referencia a commit, prueba o documento preciso cuando corresponda.
3. **Escribe un guion para 60 segundos.** Empieza por una situación concreta, explica el mecanismo, muestra una prueba y termina con un siguiente paso. El archivo `narration-es.txt` es una muestra sobre el sistema audiovisual; sustitúyelo por el episodio.
4. **Prepara voz y material.** Importa la toma original, la voz consentida, el logo y recursos visuales. La imagen conceptual debe conservar su rótulo. Verifica producto, manos, interfaz y vestuario en clips externos.
5. **Compón y revisa.** Ajusta `shots`, `focus`, `zoom`, textos y paleta; genera storyboard y un proxy. Cambia de orientación y comprueba que no se recorte información.
6. **Cierra la entrega.** Registra derechos, subtítulos, revisiones y configuración; exporta y reproduce el archivo final completo en el dispositivo de destino.

## Estructura del proyecto

```text
episodio-01/
  project.json
  narration-es.txt
  assets/
  outputs/
```

Ejemplo de afirmación y vínculo de plano:

```json
{
  "claims": {
    "c1": {
      "status": "verified",
      "source": "URL, documento o commit preciso",
      "scope": "Qué se verificó, entorno y límites",
      "reviewer": "Nombre de quien revisó la evidencia",
      "verified_at": "AAAA-MM-DD"
    }
  },
  "shots": [
    {"start": 0, "end": 60, "title": "Frase respaldada", "claim_ids": ["c1"], "evidence_required": true}
  ]
}
```

El fragmento se integra al proyecto completo; no constituye por sí solo un proyecto válido. Si el video funciona como demostración de producto, elige `mode: demonstration`. Todo plano con texto necesita una afirmación vinculada y verificada en ese modo o al usar `--final`.

## Recursos y mezcla

`asset` de cada plano es relativo a su carpeta de proyecto. `kind` admite `image` o `video`. Un clip usa `in` en segundos y debe cubrir la duración del plano. `focus.vertical` y `focus.horizontal` son pares entre 0 y 1. El zoom está limitado a 1–1.3. No se descargan recursos remotos desde el manifiesto.

Las pistas `voice`, `music`, `ambience` y `effects` son opcionales en borrador. El mezclador ajusta ganancias de partida y baja el fondo con la voz. Estas ganancias no sustituyen al diseño de sonido: escucha inteligibilidad, respiraciones, cortes, clics y enmascaramiento.

Importa subtítulos como lista de `{start, end, text}` con tiempos reales, intervalos no superpuestos y hasta 90 caracteres por cue. La composición admite dos líneas; una línea demasiado larga genera un error para que se corrija el texto. Al vincular voz desde la CLI se exportan SRT y VTT; el JSON del proyecto conserva la referencia al hash de esa grabación.

Para la síntesis en línea usa el comando `voice` del README. Si el servicio no responde, el programa da un error: no sustituye la voz ni inventa subtítulos. Antes de un uso comercial, confirma el permiso y condiciones del proveedor. Una locutora real permite dirigir de forma precisa la identidad barranquillera.

## Paleta y color

La paleta de referencia contiene grafito, esmeralda, zafiro, plata, oro, cobalto, turquesa, púrpura, carbón y blanco. `assets/brand.json` incluye una extensión editorial marcada como propuesta. Alinea los roles de color con el equipo de marca antes de una campaña.

`brand_colors` cambia colores del gráfico y texto, sin recolorear automáticamente una fotografía o materiales iluminados. El render físico y el compositor mantienen funciones distintas. Para composición lineal configura:

```json
{"color_pipeline": "srgb_linear_composite"}
```

`srgb_preview` acelera la preparación. La salida lineal tarda más y exige memoria adicional porque calcula mezclas por píxel. La versión actual no es un pipeline ACES/HDR ni un máster flotante completo.

## Revisión final

Incluye `logo`, `voice`, `subtitles`, `caption_audio_sha256`, procedencia de todos los recursos utilizados y seis registros de revisión. Ejemplo de estructura, que debe rellenar cada responsable real:

```json
{
  "reviews": {
    "brand": {"approved": false, "reviewer": "", "at": ""},
    "voice": {"approved": false, "reviewer": "", "at": ""},
    "claims": {"approved": false, "reviewer": "", "at": ""},
    "rights": {"approved": false, "reviewer": "", "at": ""},
    "picture": {"approved": false, "reviewer": "", "at": ""},
    "accessibility": {"approved": false, "reviewer": "", "at": ""}
  },
  "assets": {
    "assets/toma.mp4": {"origin": "Autor o fuente", "rights": "Permiso o licencia", "sha256": "hash real"}
  }
}
```

No cambies `approved` a true para omitir la revisión. El programa valida registros y bytes; una persona debe comprobar la coincidencia entre evidencia, narración, imagen y oferta de producto.

El informe `.report.json` declara siempre `rendered_pending_playback_review`: completar controles documentales no significa que el programa haya visto y aprobado artísticamente el video. Antes de publicar, reproduce el MP4, comprueba rótulos, cortes, sincronía, color y sonoridad en el dispositivo real.

## Producción por DAG

`examples/workflow.json` muestra luz → validación → storyboard/entrega. Ejecuta únicamente operaciones incluidas en el paquete, en orden topológico serial. Cada nodo declara entradas, ajustes y dependencias; su caché verifica los archivos completos de salida. Al cambiar una fuente, un recurso, un ajuste o el código se invalida lo correspondiente.

El DAG no sube ni publica contenido. Para trabajos externos y render distribuido se necesita una integración posterior. Evita editar recursos mientras corre una exportación por consola; la interfaz bloquea sus propias modificaciones durante el trabajo.
