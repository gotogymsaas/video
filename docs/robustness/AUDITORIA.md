# Auditoría y robustecimiento audiovisual 0.4

Autor de las propuestas e integración: **Juan Manuel Goenaga Castro**. Fecha: 22 de octubre de 2026.

Se revisaron código, cinco artículos anteriores, scripts del episodio, voz, stems, subtítulos, gráficos, marca, pantalla aportada y exportación. Los hallazgos se consolidan en ocho áreas; cada área tiene un artículo y una implementación ejecutable.

| ID | Debilidades encontradas | Mejora implementada | Artículo |
|---|---|---|---|
| A01 | Tempo 0,82; once pausas añadidas; habla forzada a ocupar 60 s; dirección desde script externo | Voz continua, selección QAF de tasa, conservación de pausas, duración independiente de película y ASR recalculado | Prosodia continua |
| A02 | Pronunciación de marcas inestable; cifras con falsa discrepancia; errores extranjeros diluibles; subtítulos huérfanos o rápidos | Control por frase e idioma, cola de términos, equivalencias numéricas explícitas, anclas reales, fusiones cortas y CPS | Inteligibilidad multilingüe |
| A03 | Manifiesto distinto de SHOTS ejecutados; voz y planos desacoplados; falta de invalidación de subtítulos | Proyecto canónico de trece planos, límites exactos de cuadro, hash de audio y evidencia por plano | Secuencia canónica |
| A04 | Teléfonos vacíos; pantalla real ausente; riesgo de letras regeneradas y recorte del pie | Captura original completa, bisel geométrico, homografía e inversa, trazabilidad y selección desde el estudio | Pantalla móvil exacta |
| A05 | Rótulos pequeños en móvil; densidad de tarjetas; titulares fuera de ancho; diferencias por formato y color poco explícitas | Tarjetas apiladas, fuente mayor, titulares envueltos, cajas verificadas, reencuadres específicos y salida SDR declarada | Composición y marca |
| A06 | Ganancias fijas; bombeos posibles; pasos sin marcha observada; control insuficiente del códec | Selección de balance por stems, perfiles validados, ducking de 450 ms, retirada de pasos sin ancla y medida del AAC final | Mezcla adaptativa |
| A07 | Confusión entre investigación y funciones actuales; sensado visual sugerible; activos privados y públicos cercanos; atribución indistinta | Fuentes y alcance fijados, fixtures para claims locales, QAF identificable, inventario público con bloqueo de voz/pesos y atribuciones conservadas | Evidencia y PI |
| A08 | Episodio fuera del estudio; doble codificación; caché incompleta; archivo corrupto reutilizable; instalación indirecta | Motor integrado, una generación de video, caché por contenido y entorno, verificación y reemplazo atómico, lanzadores y ASR independiente de TTS | Operación reproducible |

## Alcance de finalización

Las ocho propuestas computacionales se implementan y se vinculan a pruebas. El informe `docs/validation/robustness-v0.4.json` conserva resultados ejecutados. Se verifican software, integración, tipografía, cuadros, duración, decodificación y audio. El proyecto es un **animatic fotográfico** con cámara y gráficos animados; no se presenta como rodaje o generación de movimiento corporal.

Naturalidad, acento barranquillero, preferencia artística y efecto comercial tienen protocolos propios pendientes de evaluación humana. Los avisos de alineación ASR permanecen visibles; no se fabrican firmas de aprobación para alcanzar un porcentaje.

## Modelo QAF y propiedad intelectual

Se implementa la región clásica identificable: alternativas factibles, estado diagonal positivo de traza uno, observables y compilación QUBO con constante y convención triangular. El comparador clásico recibe los mismos datos y coincide. No se reclama ventaja cuántica ni liderazgo mundial demostrado. MPS y TDVP siguen disponibles como referencias anteriores y requieren evidencia incremental para ampliar su uso.

Los antecedentes técnicos de Antoni Bancells conservan atribución. Qwen3-TTS, Whisper, FFmpeg, NumPy, Pillow y fuentes conservan autores y licencias. La integración se prepara a nombre de Juan Manuel Goenaga Castro; no se declara haber entrenado un nuevo modelo de voz ni realizado búsqueda de patentes.

## Reproducción

- Suite: `python -m unittest discover -s tests -v`.
- Artículos: `python -m scripts.build_robustness_papers` (requiere XeLaTeX).
- Voz, pantalla y medios del episodio se entregan en el paquete privado. Los perfiles originales no entran en GitHub.
- La instalación opcional del motor de voz se ejecuta con `python scripts/setup_local_voice.py`.
