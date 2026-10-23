# QAF RunPhysics — manuscrito 08A

**Programa:** GoToGym Quantum Research · Juan Manuel Goenaga · 22-10-2026

**Estado:** modelo matemático de investigación prospectiva; no constituye una ventaja cinematográfica comprobada.

## Problema
Investigar si el módulo de **cinemática del corredor** añade información o mejora decisiones en una cadena de producción I2V condicionada por sujeto, contexto, tiempo y recursos. Requiere datos autorizados y evaluaciones independientes.

## Ecuación de trabajo
```text
M(q)q_ddot+C(q,q_dot)+g(q)=tau+J(q)^T lambda; L_contact=sum(stance*||vfoot||²)
```

`Phi_Q(X,C,T,O)` organiza relaciones contextuales y orden temporal, pero no sustituye ni el entrenamiento de pesos ni la síntesis neuronal de píxeles.

## Implementación
1. Validar el origen de los activos y el consentimiento.
2. Extraer observaciones y relaciones orientadas, preservando incertidumbre.
3. Ejecutar el algoritmo definido por la ecuación y registrar semillas, reloj y parámetros.
4. Aplicar controles duros: Contacto con suelo, fase aérea y articulaciones requieren evidencias y límites físicos.
5. Registrar salidas numéricas, confianza, uso de GPU/RAM y costo.
6. Comparar contra una alternativa clásica que observa los mismos inputs.
7. Abstenerse y solicitar revisión humana ante fallos críticos.

## Hipótesis y falsación
H1: calidad superior a baselines fuertes. H2: el resultado se reproduce en sujetos y prendas retenidos fuera de train. H3: la mejora no se elimina al contabilizar coste y latencia. **Baselines:** Interpolación, IK, optimización biomecánica. Evaluar ablaciones sin contexto, sin relación orientada, sin memoria y con la misma capacidad neuronal. Rechazar la ventaja QAF si el mejor método clásico iguala o supera bajo recursos comparables.

**Métricas primarias:** Foot sliding, penetración, jerk y evaluación deportiva. Medir media, distribución, intervalos de confianza por sujetos, revisión humana ciega, fallos críticos y OOD. Entrenar/tunar con datos separados del test de forma estricta.

## Aprendizaje científico y creativo
Un video fluido no siempre representa un paso físicamente posible.

## Validez y propiedad intelectual
La novedad es una arquitectura combinada sometida a prueba, no la invención de física, LoRA, Transformers, entrenamiento variacional o optimización clásica. La evidencia previa QAF (CSRA, Motor MPS/TDVP/RDM y Atlas G1–G6) favorece aplicaciones relacionales condicionales y contiene controles donde los métodos clásicos ganan. Ningún número QAF anterior es una métrica de calidad de video de este experimento.

## Criterio de entrega
Código testeado, dataset versionado por hash con licencia, checkpoint auténtico, comparación pareada externa, resultados negativos publicados y autorización humana previa a release. Actualmente esta ficha no demuestra ese umbral.

**Bibliografía:** Goenaga (2026), programa QAF G1–G6; Lipman et al. (2023), Flow Matching; Peebles y Xie (2023), DiT; Huang et al. (2024), VBench; documentación `gotogymsaas/video`.
