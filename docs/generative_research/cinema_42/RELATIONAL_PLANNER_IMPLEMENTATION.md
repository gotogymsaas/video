# P031/P021/A02 — first executable relational cinema planner

`relational_planner.py` exposes a transparent weighted scene objective with action, identity, occlusion and GPU cost terms. It optimizes across shots using **exact classical dynamic programming** and computes a greedy baseline as a debugging comparator.

```bash
python -m qaf_video.generative_research.relational_planner private/scene.json --out private/plan.json
```

The scene JSON schema `qaf_cinema_scene_decisions_v1` holds `scenes: [{candidates:[{id, actor_ref, action_error, identity_error, occlusion_error, compute_cost, privacy_cleared, rights_cleared}]}]`; optional `identity_switch_penalty` and `weights`. All errors are declared precomputed measurements; the module does NOT infer physical quality, detect subjects or generate pixels.

**Interpretation:** the DP objective demonstrates how scene-to-scene relational constraints can alter shot choice compared with greedy. However, DP is itself a **classical, globally optimal** baseline for this simplified Markovian objective, so superiority of QAF cannot be inferred from beating greedy alone. Complete QAF evaluation must also compare against DP/MILP with equal inputs and compute.

For production: feed only reviewed action/identity/occlusion measurements and approval records; send selected shots to the existing ComfyUI and hybrid compositor. No online GPU inference is initiated by this module.
