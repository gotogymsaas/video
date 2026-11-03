# Trayectorias QAF para una cámara editorial verificable

Juan Manuel Goenaga Castro · GoToGym Quantum Research · 29 de octubre de 2026

Estado: manuscrito metodológico; referencia implementada, evaluación perceptual pendiente.

## Resumen y pregunta

Se propone ampliar el movimiento entre dos valores de zoom mediante puntos clave de posición focal y escala. La pregunta es si un control explícito reduce errores de encuadre y permite un movimiento más pertinente. Se implementa una referencia clásica y se verifican continuidad y geometría. La preferencia cinematográfica permanece por evaluar.

## Antecedente y contribución

Los manuscritos I y II de GoToGym Quantum Research separan propósito, representación y calidad. El segundo deriva el mínimo de jerk. Esta ampliación convierte ese método en un contrato reutilizable por los dos renderers. No inventa la interpolación quintica ni atribuye ventaja cuántica a un desplazamiento de cámara.

## Modelo matemático

Entre dos claves a y b se define u=(t-ta)/(tb-ta), limitado a [0,1]. La función s(u)=10u^3-15u^4+6u^5 interpola cada componente: p(t)=pa+(pb-pa)s(u). Se fijan velocidad y aceleración nulas al entrar y salir de cada segmento. Esto produce continuidad C2 en las claves, pero también una pausa: no es una spline con velocidad libre.

## Geometría y restricciones

Para imagen iw por ih y salida w por h, scale=max(w/iw,h/ih)*zoom. El recorte tiene cw=w/scale y ch=h/scale. Su centro se limita a [cw/2,iw-cw/2] y [ch/2,ih-ch/2]. No aparecen bordes externos. Cerca de los límites puede variar la velocidad del recorte: la continuidad del estado solicitado no prueba suavidad de todas las trayectorias recortadas.

## Contrato implementado

El campo opcional motion.keyframes admite 2 a 32 claves. Cada clave declara at entre 0 y 1, focus normalizado y zoom entre 1 y 1.7. Los tiempos deben aumentar y cubrir ambos extremos. Se rechazan NaN, infinitos, booleanos y valores fuera del dominio. Sin motion se conserva el método de dos valores y el foco existente.

## Integración

qaf_video/animation.py contiene camera_sample, validate_motion y crop_box. cinema.Film.photo y render.compositor.Movie.asset usan el mismo cálculo. core.validate y cinema_project.validate_cinema admiten y validan el campo opcional antes del render. El método reencuadra imágenes; no genera movimiento humano ni parallax 3D.

## Validación ejecutada

La ejecución dirigida aprobó 42 pruebas entre animación, matemáticas, cine y planificación relacional. Las pruebas nuevas comprueban 202 recortes en formatos vertical y horizontal, aspecto correcto, extremos, velocidad aproximadamente nula en una clave interior, rechazo de entradas y render de frames con el compositor. Son controles de software; no un estudio de espectadores.

## Experimento perceptual propuesto

Comparar cámara fija, zoom anterior y puntos clave con iguales imágenes, texto y sonido. Usar episodios y espectadores independientes, asignación contrabalanceada y evaluación ciega de claridad, comodidad y preferencia. Reportar dispersión, tamaño de muestra y costo por cuadro. La hipótesis se rechaza si no mejora las métricas o introduce movimiento molesto.

## Uso y límites

El ejemplo del README reproduce el contrato. El encuadre seguro protege límites de imagen, no detecta rostros ni garantiza visibilidad del sujeto. Una trayectoria debe elegirse según la escena. El próximo desarrollo podría añadir máscaras autorizadas y una spline de velocidad libre, tras definir pruebas y controles.

## Referencias

Goenaga, J. M. (2026). Fundamentos de un sistema audiovisual QAF; Cinematografía computacional y narrativa verificable. Fuentes en docs/manuscripts/source. Bancells, A. (2026), formalismo operacional QAF, antecedente citado en la serie; no se ejecutan MPS/TDVP en este módulo. Código base: gotogymsaas/video, commit f086af1b8b26. Métodos clásicos conservan su atribución.

