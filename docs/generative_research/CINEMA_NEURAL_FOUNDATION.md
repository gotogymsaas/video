# CinemaVAE + VideoDiT: modelo propio experimental

El repositorio ahora contiene `qaf_video/generative_research/cinema_neural.py`, un autoencoder 3D variacional y un Transformer espaciotemporal pequeño cuya salida se entrena mediante *flow matching*. Este experimento actualiza pesos sin requerir servicios externos.

## Entrenamiento seguro de humo
```sh
python -m pip install -r requirements-neural.txt
python -m qaf_video.generative_research.cinema_neural --out outputs/smoke --steps 12
python -m unittest tests.test_cinema_neural -v
```

Entradas de entrenamiento: cuadrados móviles sintéticos RGB 16x16. El modelo inicial NO conoce rostros, acciones humanas, textos, prendas, logotipos ni material real. No se integra automáticamente a la web ni a la producción.

## Matematica
- VAE: `L_VAE = MSE(x,D(E(x))) + lambda_t L1(Delta_t x,Delta_t recon) + beta KL(q_phi(z|x)||N(0,I))`
- Flujo: `z_t = (1-t)z_0 + t E(x)`, `L_FM=E||v_theta(z_t,t,imagen_0,Phi_Q)-(E(x)-z_0)||^2`
- Inferencia: `dz/dt=v_theta(z,t,imagen_0,Phi_Q)`, solucion Euler de referencia
- QAF: `Phi_Q(X,C,T,O)` como token contextual; medir utilidad frente al mismo backbone sin token y con baselines equivalentes. El token presente en prueba artificial NO demuestra ventaja.
- Primer fotograma: se fuerza como capa exacta (compositing), no como evidencia de fidelidad de la red.

## Para desarrollo real
Primero dataset y licencia verificables; luego VAE con benchmark recon temporal sobre test real, un DiT escalable y un programa de entrenamiento con estados guardados, mixed precision, DDP/FSDP, seguimiento de costo y privacidad. Después el modelo I2V entrenado debera responder a controles de pose, camera, identity y cloth; es necesario revisarlo con seres humanos y verificar beneficios QAF en pruebas ciegas y OOD.

## Estado de capacidad
- Arquitectura 3D VAE: codigo entrenable experimental.
- Video Transformer: codigo entrenable experimental.
- Flujo condicionado: codigo y entrenamiento sintético.
- Pesos cinematograficos entrenados: **no**.
- Modelo de video de maxima calidad: **no demostrado**.
- El codigo no modifica el compositor existente ni instala PyTorch en entornos de produccion.
