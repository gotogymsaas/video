# QAF Cinematic Intelligence — 24 manuscritos para el modelo fundacional propio

**Autor:** Juan Manuel Goenaga · GoToGym Quantum Research · **Fecha:** 2026-10-22

## Estado real
Investigación y arquitectura matemática propuestas. Los diez módulos numéricos previos de `qaf_video/generative_research/models.py` no constituyen un generador neuronal de video. La implementación cinematográfica exige datos con derechos, una red generativa 3D entrenada, GPU, checkpoints y pruebas de calidad con escenas reales. No se ha validado una ventaja audiovisual QAF.

## Índice de tecnologías y 24 manuscritos
- **01 · Dataset audiovisual y derechos**. A: ProvenanceGraph: grafo de licencias y linaje. B: ActiveData: adquisición activa por información contextual.
- **02 · Preparación de datos**. A: TemporalTokenizer: selección temporal de eventos. B: LeakageShield: particiones causales sin fuga.
- **03 · Modelo neuronal fundacional**. A: CinemaVAE: representación espaciotemporal entrenada. B: CinemaFlow-DiT: backbone flow matching entrenable desde cero.
- **04 · GPU y escalabilidad**. A: ComputePlanner: asignación de GPU por utilidad. B: FaultTolerantTraining: recuperación reproducible.
- **05 · Adaptación y actualización**. A: Relational-LoRA: rango contextual por capa. B: ContinualCinema: regularización antiolvido, replay y canary.
- **06 · Comprensión visual**. A: ContextSceneGraph: grafo relacional orientado. B: UncertainVision: fusión pose, profundidad e incertidumbre.
- **07 · Image-to-Video**. A: ConditionalVideoFlow: generación condicionada en fotografía. B: MultishotDynamics: coherencia entre planos.
- **08 · Física corporal y textil**. A: RunPhysics: contacto pie-suelo y cinemática. B: NeuralCloth: residual físico aprendido.
- **09 · Memoria cinematográfica**. A: IdentityTensorMemory: memoria selectiva por persona y prenda. B: StoryStateGraph: continuidad narrativa no local.
- **10 · Evaluación perceptual**. A: PerceptualErrorAtlas: localización temporal de defectos. B: HumanAlignedReward: entrenamiento de preferencias humanas.
- **11 · Benchmark y falsación**. A: CinematicApplicability: fronteras QAF positivas y negativas. B: MatchedBudgetCausalBenchmark: ablación y comparación causal.
- **12 · Integración productiva**. A: CinematicMOS: jobs con privilegios mínimos. B: EvidenceRelease: provenance, canary y aprobación humana.

## Arquitectura matemática principal

**Núcleo neuronal, aprendido con gradientes:** 3D video autoencoder Eφ / Dψ y video Transformer vθ con *rectified flow*:

```text
z1 = E_phi(video)
z0 ~ Normal(0, I)
z_tau = (1-tau)*z0 + tau*z1
L_FM = E || v_theta(z_tau,tau, image + pose + text + camera + QAF_context) - (z1-z0) ||^2
generated_video = D_psi(ODESolve(v_theta, z0, conditions))
```

**QAF observación / decisión, no sustitución de la generación neuronal:**

```text
Phi_Q = Phi_Q(observations, context, temporal_state, order)
Gamma_obs = I(target;Phi_Q) - sup_(f in strong_classical_baselines) I(target;f(same_inputs))
Delta_J = utility(QAF + same_backbone) - max_m utility(classical_m + same_backbone)
Accept QAF-only claims if delta is robust out-of-distribution AND cost is within budget.
```

CSRA identificó una posible ventaja de sesgo inductivo/representación cuando la información está en relaciones orientadas seleccionadas por contexto; los controles clásicos con el mismo estadístico pueden igualarla. G1–G6 incluyen regiones Classical-positive y Computational-breakdown, por lo que no debe afirmarse superioridad universal o física cuántica.

## Secuencia de experimentos
1. Corpus con permisos y cadenas de procedencia por video / sujeto / prenda; particiones limpias.
2. Entrenar 3D VAE y medir reconstrucción temporal en test congelado.
3. Entrenar un video DiT/flow condicional pequeño sobre clips auténticos y autorizados; escalar con currículo y memoria medida.
4. Incorporar comprensión visual, controles de cámara, poses, tela y memoria; mantener interfaces reales como capas exactas.
5. Comparar idénticos pesos, imágenes, semillas, pasos, VRAM y presupuesto entre backbone simple, backbone+controles clásicos, backbone+QAF.
6. Recoger evaluaciones a ciegas, VBench dimensiones, errores críticos por objeto, OOD y costos; documentar resultados negativos.
7. Promocionar a producción solo con consentimiento, derechos y revisión editorial humana; versionar/rollback.

## Alcance del prototipo científico
Además de los manuscritos se creó localmente un **smoke test neuronal sintético** con PyTorch: 3D CNN VAE + red de velocidad 3D flow, 22 pasos sobre cuadrados móviles 16×16. Produjo pesos y tensores de salida, pero no entrenó el DiT de producción ni demostró movimiento fotorealista. La pérdida flow no convergió en esa prueba.

## Referencias para implementación
- Documentos QAF facilitados: CSRA, MPS/MPO/TDVP, G1–G6, atlas de aplicabilidad y validación relacional.
- Ho et al. (2022), Video Diffusion Models, NeurIPS: https://arxiv.org/abs/2204.03458
- Lipman et al. (2023), Flow Matching, ICLR: https://arxiv.org/abs/2210.02747
- Peebles & Xie (2023), DiT, ICCV: https://openaccess.thecvf.com/content/ICCV2023/html/Peebles_Scalable_Diffusion_Models_with_Transformers_ICCV_2023_paper.html
- Blattmann et al. (2023), Stable Video Diffusion: https://arxiv.org/abs/2311.15127
- Huang et al. (2024), VBench: https://openaccess.thecvf.com/content/CVPR2024/html/Huang_VBench_Comprehensive_Benchmark_Suite_for_Video_Generative_Models_CVPR_2024_paper.html
- Hu et al. (2021), LoRA: https://arxiv.org/abs/2106.09685

> Los PDF completos y el código de prototipado se entregaron como archivos descargables de esta conversación. Este índice versiona la investigación en GitHub; **no afirma que esos 24 PDF estén adjuntos al repositorio**.
