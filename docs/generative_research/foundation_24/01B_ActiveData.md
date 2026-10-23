# QAF ActiveData — 01B

**GoToGym Quantum Research · Juan Manuel Goenaga · 22 octubre 2026.**

**Estado:** manuscrito científico prospectivo, no validación experimental.

## Pregunta científica
¿En qué condiciones puede el componente ActiveData producir una ganancia real de calidad o de fiabilidad en adquisición inteligente frente a un método fuerte con la misma información y presupuesto?

## Modelo matemático propuesto

```text
s*=argmax_s I(Y;Phi_Q(s,C)|D)-lambda*c_s-mu*privacy_risk(s)
```

QAF aporta una representación `Phi_Q(X,C,T,O)` de observaciones, contexto, estado temporal y orden; una clase clásica puede igualarla cuando recibe los mismos observables. El método decisional QAF se justifica únicamente cuando la utilidad adicional se mantiene en los datos nuevos y dentro de recursos.

## Arquitectura y contrato de implementación
**Entradas:** observaciones con permisos, escenas, contexto de la toma, historial, restricciones y presupuesto. **Transformación:** obtener observables o candidatos relevantes, aplicar el modelo anterior, decidir un plan trazable. **Salidas:** diagnóstico serializable, incertidumbre, evidencia y coste. **Reglas de seguridad:** Detener adquisición si la mejora frente a muestreo aleatorio no compensa su costo.

## Entrenamiento y reproducibilidad
Dataset sujeto/prenda disjuntos; semillas explícitas; guardado de pesos, configuraciones y versiones; auditoría de procedencia. Dividir train, validation, test y OOD. Para calidad visual usar pruebas ciegas humanas y métricas semánticas cuando correspondan. Mantener la misma arquitectura neuronal, datos y costo para comparadores salvo la variable de ablation.

## Comparadores e hipótesis falsables
Comparadores predefinidos: Muestreo aleatorio, incertidumbre clásica y k-center. Hipótesis: (H1) mejora en métricas primarias; (H2) la mejora persiste ante ruido y cambio de dominio; (H3) no destruye la economía computacional. Ablaciones: sin contexto, sin memoria, sin restricciones, control clásico con exactamente la misma relación. La hipótesis es rechazada si el comparador mejor iguala/supera o si la calidad cae en OOD.

**Métricas a medir:** Ganancia de calidad por 100 clips, diversidad, costo y OOD. Reportar distribuciones, IC95% bootstrap agrupado, latencia p95, memoria, costo y tasa de fallos críticos. No transferir números de benchmarks QAF de otros dominios a video.

## Aprendizaje creativo
Pedir una toma de apoyo puede aumentar más la calidad que agregar muchas imágenes redundantes.

## Alcance y propiedad intelectual
Este estudio describe una nueva combinación de módulos; no afirma que VAE, transformers, LoRA, probabilidad bayesiana o la matemática estándar sean invenciones nuevas. Los antecedentes QAF G1–G6 indican valor relacional condicional, incluidos controles clásicos positivos y regiones de ruptura. No hay patente concedida ni publicación arbitrada asociada automáticamente a esta propuesta.

**Evidencia requerida:** artefactos con hash, checkpoint realmente entrenado, evaluación pareada y revisión humana. **Estado actual:** propuesta de método; los módulos sintéticos disponibles son referencias, no rendimiento cinematográfico probado.

## Referencias centrales
Goenaga: QAF CSRA; Motor MPS/TDVP/RDM; G6 Mathematical Atlas; Consolidated Evidence (2026). Lipman et al. (2023), Flow Matching. Peebles & Xie (2023), Diffusion Transformers. Huang et al. (2024), VBench. Repositorio `gotogymsaas/video`.
