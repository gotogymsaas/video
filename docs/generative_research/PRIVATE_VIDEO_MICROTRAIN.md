# Entrenamiento privado real — capacidad experimental

`train_video_dataset.py` habilita un primer flujo de entrenamiento a partir de **cinco cuadros locales 16×16 a 12 fps** de videos MP4 suministrados por el usuario. No equivale al preentrenamiento de una red cinematográfica a escala.

```sh
python -m pip install -r requirements-neural.txt
python -m qaf_video.generative_research.train_video_dataset /private/dataset.json --out /private/checkpoints/micro --steps 20
```

Se exige manifiesto `qaf_cinematic_training_dataset_v1`, identificadores separados por sujeto/prenda, `train` y `val` distintas, `rights` y `consent_record`. Estas dos cadenas son **declaraciones**, no certifican autorizaciones legales. Una revisión jurídica debe verificar los documentos originales antes de iniciar entrenamiento comercial.

Checkpoint incluye VAE, transformer, optimizadores, RNG, semillas, data manifest SHA256 y pérdidas de entrenamiento/validación. El microentrenador siempre reporta `cinematic_model_trained: false`; no demuestra ventajas QAF.

Para alcanzar alta resolución, el siguiente motor necesita tokenización y entrenamiento GPU a escala, dataset de movimiento humano y tela con derechos, condiciones de cámara/pose y evaluación humana ciega con controles clásicos.
