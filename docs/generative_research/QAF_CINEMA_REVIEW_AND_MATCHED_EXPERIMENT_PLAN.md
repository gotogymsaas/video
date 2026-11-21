# QAF Cinema Human Review and Matched Experiment Plan

## Scope

This document describes CPU-only preparation contracts. It does not approve
training footage, certify commercial rights or execute GPU training.

## Human review registry

Use:

```bash
python -m qaf_video.generative_research.review_and_experiment \
  create-review \
  docs/generative_research/gym_corpus/candidate_inventory.json \
  --out /private/qaf-cinema-review.json
```

The output has `human_training_approval=false`. Every row begins in `PENDING`.
Before a row can enter the approved split it requires:

- technical media review;
- human visual review;
- human reviewer identity;
- review/reference record;
- individual rights record;
- participant consent record;
- commercial synthetic-training permission;
- actor, session and garment groups;
- human-written caption;
- exact frame count and FPS.

No GitHub access, source size or pose evidence is itself training approval.

## Reproducible split

After direct human and legal review, edit the private registry and run:

```bash
python -m qaf_video.generative_research.review_and_experiment \
  build-split /private/qaf-cinema-review.json \
  --seed 20261121 \
  --out /private/qaf-gym-approved-splits.json
```

The split is deterministic per actor/session/garment group. The module rejects
actor, session or garment leakage across train, val and test. It requires
non-empty train, val and test sets. It still does not claim independent legal
certification.

## Matched experiments

Define private scenes with source SHA-256 values and prompts, then run:

```bash
python -m qaf_video.generative_research.review_and_experiment \
  plan-experiment /private/qaf-experiment-scenes.json \
  --seed 20261121 \
  --gpu-hours 24 \
  --out /private/qaf-matched-experiment-plan.json
```

The plan defines:

- **A — base_ltx:** no LoRA, no QAF planning.
- **B — visual_lora:** visual LoRA adaptation only.
- **C — classical_control:** official pose/depth/Canny IC-LoRA control.
- **D — qaf_control:** the same classical control plus separate QAF planning
  metadata.

Every arm requires:

- the same checkpoint;
- the same scenes;
- the same prompts;
- the same seed;
- the same duration;
- the same target/reference geometry;
- the same compute budget;
- blinded human evaluation;
- real MP4 playback;
- independent checkpoint hash verification.

The plan records `training_executed=false`, `human_evaluation=false`,
`cinematic_superiority_proven=false` and `qaf_advantage_proven=false`.
It does not establish a result until the paired runs and human review exist.
