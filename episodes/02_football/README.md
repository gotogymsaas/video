# Episodio 02 / Fútbol / Comprende tu juego

60 segundos, 30 FPS; entrega prevista vertical 1080x1920 y horizontal 1920x1080, con y sin subtítulos. Este proyecto público es el montaje visual sin voz privada. La versión hablada y los MP4 se entregan en el paquete descargable del episodio.

## Historia y venta
Problema humano: un lateral duda entre cerrar dentro y acompañar la banda. Mecanismo: especialidad, objetivo, experiencia y tiempo declarado alimentan actividades educativas. Transformación verificable: propuesta de 15 minutos para comprender y revisar, cuya continuación consume el resultado anterior. CTA: «Escribe Activa fútbol». No se promete eficacia deportiva ni análisis de partidos.

## Verificación
El fixture `evidence/football-example.json` procede de ejecutar motor, contratos, catálogo y planner del producto fijado en `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`. `source_snapshot/` conserva la fuente consultada y su atribución. Se comprueban presupuesto, presencia de rol principal, ausencia de prescripción de carga y consumo del resultado anterior. Es ejecución local; no se ha verificado la disponibilidad actual de producción para una cuenta.

Las tarjetas son una visualización conceptual rotulada. La pantalla de bienvenida es la captura original proporcionada por el usuario: la copia pública optimiza el PNG conservando los mismos píxeles RGB. Los actores son ficticios. No hay rodaje ni movimiento humano neuronal: la película usa reencuadres, gráficos y composición del teléfono.

## Reproducir
1. Instala el repositorio (`python -m pip install .`) y FFmpeg.
2. Abre el estudio con `python -m qaf_video serve --workspace episodes` y selecciona `02_football/project.json`.
3. Importa una narración autorizada y adjúntala con tiempos medidos; guion en `narration-es.txt`.
4. En Cine y pantalla móvil, selecciona Coastal pulse y pulsa Componer y mezclar con mi voz. O usa `python -m qaf_video.music_research produce episodes/02_football/project.json --preset coastal_pulse` después de adjuntar voz.
5. Revisa storyboard y audio, exporta ambos formatos. La aprobación humana del audio debe vincular su hash; referencias, pesos y contratos no se publican.

## Imágenes y prompts
Herramienta integrada de generación de imágenes, tres llamadas independientes con referencia de personaje; semilla no expuesta por el proveedor. Prompts abreviados fieles al brief ejecutado:
- 01 / plano general: futbolista adulto colombiano ficticio de 27 años, cabello corto rizado negro, camiseta esmeralda sin marca y pantalón negro; cancha barrial de Bogotá al amanecer; balón en cintura, mirada reflexiva; luz dorada y sombras teal, aparente 50 mm, fotografía realista, sin texto ni logo.
- 02 / reflexión: mismo personaje y entorno como referencia; sentado en banco, escribiendo un cuaderno táctico, balón al lado de sus botas; manos plausibles, composición central para ambos formatos; sin interfaz ni marcas.
- 03 / resolución: mismo personaje de pie con postura relajada y una bota junto/al balón, mirada tranquila y sonrisa contenida; misma cancha y luz; sin esfuerzo extremo, texto, logos u hologramas.

Los prompts completos de la conversación se ejecutaron con la herramienta integrada, no con una API alternativa. JPEG de producción conserva el resultado para el montaje. Logo y pantalla originales se componen por código; no se regeneran. Licencias tipográficas en `assets/fonts/`.

Música elegida como dirección creativa: Coastal pulse, 112 BPM, bajo sincopado, cuatro capas editables y control de energía por secciones. No implica tendencia validada por audiencia ni entrenamiento neuronal propio.

## Verificación de entrega
`delivery-audit.json` registra cuatro MP4, medidas del audio codificado, hashes, subtítulos y fuentes. Se inspeccionaron 30 cuadros exportados en los dos formatos. La suite base pasa 111 casos y omite tres opcionales sin PyTorch; esos tres se ejecutaron y aprobaron por separado en el runtime de voz. La aprobación auditiva y editorial del productor/usuario permanece pendiente; ASR y métricas no certifican naturalidad regional ni preferencia musical.
