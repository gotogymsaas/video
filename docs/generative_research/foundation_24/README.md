# Programa QAF Cinema — control de integridad experimental

**Versiones documentadas:** 24 fichas científicas en `docs/generative_research/foundation_24/`; cada ficha contiene modelo matemático, hipótesis, comparadores, criterios de falsación y aplicación de ingeniería. El archivo original de 24 PDF completos se distribuye por separado; las fichas versionadas aquí son textos técnicos adaptados.

**Código realmente ejecutable:** 10 referencias matemáticas NumPy, puertas de dataset/consentimiento, integración de clips ya generados, comparación QAF/baseline y un nuevo prototipo entrenable 3D VAE+VideoDiT para datos sintéticos. Ninguna de las 24 hipótesis se debe declarar demostrada por la existencia de estas piezas.

## Auditoría de cobertura (sin inventar progreso)

```bash
python -m qaf_video.generative_research.program_audit . --output outputs/qaf-program-audit.json
```

El informe reporta dos indicadores separados:
- `documented_papers` (objetivo 24): documentación versionada.
- `empirical_validated_papers_claimed` (objetivo 24): pruebas de hipótesis con evidencia real declarada, comparadores fuertes, hardware y derechos.

`program_100_percent_verified` permanece falso si falta cualquier validación o artefacto verificable. La comprobación es de integridad, no certificación externa de veracidad.

**Puertas externas aún necesarias:** datos reales licenciados, modelo neuronal entrenado con convergencia en test, experimentos OOD, benchmarks fuertes pareados y revisión humana. La calidad máxima es un objetivo de ingeniería, nunca un atributo deducible de fórmulas.

### Principios QAF
`Gamma_obs = I(Y;Phi_Q) - max_m I(Y;classical_m)`. `DeltaJ=J(QAF)-max_m J(classical_m)`. Preferir QAF únicamente cuando ambas mejoras están demostradas bajo recursos iguales y generalizan OOD. QAF no sustituye el preentrenamiento de video; los estudios G1–G6 muestran utilidad condicional.

Véanse las fichas individuales y el informe `docs/generative_research/CINEMA_NEURAL_FOUNDATION.md`.
