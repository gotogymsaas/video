# QAF Relational-LoRA — 05A

**GoToGym Quantum Research · Juan Manuel Goenaga · 22 octubre 2026.**

**Estado:** manuscrito científico prospectivo, no validación experimental.

## Pregunta científica
¿En qué condiciones puede el componente Relational-LoRA producir una ganancia real de calidad o de fiabilidad en adaptación eficiente frente a un método fuerte con la misma información y presupuesto?

## Modelo matemático propuesto

```text
W=W0+(alpha/r)*BA; r_l*=argmin L_valid+lambda*sum_l r_l*(m_l+n_l)
```

QAF aporta una representación `Phi_Q(X,C,T,O)` de observaciones, contexto, estado temporal y orden; una clase clásica puede igualarla cuando recibe los mismos observables. El método decisional QAF se justifica únicamente cuando la utilidad adicional se mantiene en los datos nuevos y dentro de recursos.

## Arquitectura y contrato de implementación
**Entradas:** observaciones con permisos, escenas, contexto de la toma, historial, restricciones y presupuesto. **Transformación:** obtener observables o candidatos relevantes, aplicar el modelo anterior, decidir un plan trazable. **Salidas:** diagnóstico serializable, incertidumbre, evidencia y coste. **Reglas de seguridad:** Comparar rango fijo, asignación por capa y gate relacional bajo cómputo igual.

## Entrenamiento y reproducibilidad
Dataset sujeto/prenda disjuntos; semillas explícitas; guardado de pesos, configuraciones y versiones; auditoría de procedencia. Dividir train, validation, test y OOD. Para calidad visual usar pruebas ciegas humanas y métricas semánticas cuando correspondan. Mantener la misma arquitectura neuronal, datos y costo para comparadores salvo la variable de ablation.

## Comparadores e hipótesis falsables
Comparadores predefinidos: LoRA uniforme, full tuning, rank search clásico. Hipótesis: (H1) mejora en métricas primarias; (H2) la mejora persiste ante ruido y cambio de dominio; (H3) no destruye la economía computacional. Ablaciones: sin contexto, sin memoria, sin restricciones, control clásico con exactamente la misma relación. La hipótesis es rechazada si el comparador mejor iguala/supera o si la calidad cae en OOD.

**Métricas a medir:** Parámetros entrenables, VRAM, marcas, calidad OOD. Reportar distribuciones, IC95% bootstrap agrupado, latencia p95, memoria, costo y tasa de fallos críticos. No transferir números de benchmarks QAF de otros dominios a video.

## Aprendizaje creativo
El rango debe invertirse donde la relación entre movimiento y producto es realmente difícil.

## Alcance y propiedad intelectual
Este estudio describe una nueva combinación de módulos; no afirma que VAE, transformers, LoRA, probabilidad bayesiana o la matemática estándar sean invenciones nuevas. Los antecedentes QAF G1–G6 indican valor relacional condicional, incluidos controles clásicos positivos y regiones de ruptura. No hay patente concedida ni publicación arbitrada asociada automáticamente a esta propuesta.

**Evidencia requerida:** artefactos con hash, checkpoint realmente entrenado, evaluación pareada y revisión humana. **Estado actual:** propuesta de método; los módulos sintéticos disponibles son referencias, no rendimiento cinematográfico probado.

## Referencias centrales
Goenaga: QAF CSRA; Motor MPS/TDVP/RDM; G6 Mathematical Atlas; Consolidated Evidence (2026). Lipman et al. (2023), Flow Matching. Peebles & Xie (2023), Diffusion Transformers. Huang et al. (2024), VBench. Repositorio `gotogymsaas/video`.
