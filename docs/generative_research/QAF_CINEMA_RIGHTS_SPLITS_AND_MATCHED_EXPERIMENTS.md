# QAF Cinema — private rights register, connected groups and matched A/B/C/D protocol

Status: CPU/offline software gate, NOT a human legal certification, a GPU training job, a cinematographic-quality assessment or a deployed QAF conditioner.

## Why this gate is necessary

Prior code checked actor and garment identities, and the 106-video planning document mentioned sessions. The new independent training-governance gate additionally requires verified-by-human session identifiers and near-duplicate grouping, and treats **all three plus near-duplicates as connected components**. A video connected through even one shared actor/session/garment/duplicate relationship must remain in the same split. A complete group can be held out; individual frames from that group may not appear across train/val/test. Exact source-hash duplicates in the approved target library fail closed.

The 106-item metadata inventory has no trustworthy actor, session or garment mappings; **do not infer these from WhatsApp timestamps or file titles**. A claim that rights were previously confirmed by the project owner does not provide a per-person synthesis/likeness consent and asset license. No approval records are committed here.

## Phase 1: create a PRIVATE review register on the authorized Codespace or Mac

Run this from the video repository root:

    python scripts/qaf_cinema_training_governance.py draft \
      --inventory docs/generative_research/gym_corpus/candidate_inventory.json \
      --media-root /private/appdesplegada-source \
      --out /private/qaf-governance/review-106.json

The output path MUST exist outside this public Git repository; the command will refuse overwrite. This creates 106 PENDING rows and **zero** actual approvals. With --media-root it computes SHA-256 checksums for the 106 real original files and rejects mismatched inventory byte sizes. It never fills rights, consent, reviewer, actor, session or garment fields. Omit --media-root to draft a metadata-only template without source hashes. Keep the entire register in a private workspace with access controls, backups, and audit logging. Do not upload consent documents, identifiable actor information, hashes of private footage or final splits to a public PR.

A human film/rights reviewer must fill each row: APPROVED or EXCLUDED with reviewer and evidence reference; source SHA-256; actual actor/session/garment group IDs; near-duplicate review; human captions; visual classification APPROVED vs MOTION_ONLY; motion review; training copyright rights; participant consent; permission for synthetic use of likeness; minor status; clearances for audio and logos. The prototype does not open/validate legal documents and **does not certify** a consent as legally sufficient merely because a field is checked.

EXCLUDED media need a reviewer and evidence reference for the exclusion. APPROVED media require NO_MINORS, all clearances, and references; footage with minors must go through a separate specialist clearance process before being eligible. Special rights edge cases require legal review; do not bypass the gate by using fake record IDs.

Only human visually approved cinematic targets may enter model-gradient data. Motion-only clips are held out of the visual training target pool, and may contribute pose controls later under their own permission protocol. Do not use these recordings to infer faces, voices or brand logos for new ads without appropriate separate permissions.

## Phase 2: grouped leakage-safe split (only when the register is complete)

    python scripts/qaf_cinema_training_governance.py plan \
      --inventory docs/generative_research/gym_corpus/candidate_inventory.json \
      --review /private/qaf-governance/review-106.json \
      --media-root /private/appdesplegada-source \
      --seed 42 \
      --out /private/qaf-governance/grouped-split.json \
      --experiments-out /private/qaf-governance/experiment-plan.json

The private root must preserve the existing Videos_test_gimnasio/<filename>.mp4 structure. Approvals include source SHA-256s that must match the actual local file bytes and inventory sizes. The tool refuses to create a split if any of the 106 rows remains PENDING, if fewer than 3 independently connected visually approved components exist, if there are exact duplicates in gradient targets, or if consent/permissions/group IDs are incomplete.

Split assignment targets approximately 80/10/10 by number of clips, not by frame count; large connected groups may prevent exact ratios. Examine per-split sizes, session/actor/garment distribution, and domain representativeness manually. Split freeze, cross-camera/source near-duplicate analysis, human editorial holdout and validation of out-of-distribution generalization remain separately required. This is a **technical planning artifact**, not yet a full scientifically validated release.

## Phase 3: matched experiments and budget

The experiment output prepares four arms for the SAME private test identifiers and seeds:

- A_BASE: unmodified base model
- B_VISUAL_LORA: licensed high-quality visual LoRA
- C_CLASSIC_POSE: same visual LoRA + classical raster control
- D_QAF_PLAN_POSE: same visual LoRA + same raster control, plus planned QAF mechanism

B, C and D must use the same training dataset when comparing the conditioning contribution, and C/D must share the same LoRA weights, test prompts, seeds, evaluation reference and inference settings. A has no training and serves as a base-model reference. Record both GPU compute and inference costs; do not use unequal budgets to claim a QAF advantage. The D treatment is **not implemented by this tool**; the 8D Phi_Q features remain metadata, not an official LTX conditioning tensor.

The generated plan includes an example GPU-hour ceiling, but it explicitly declares hard_stop_implemented=false and quota_approved=false. This is NOT an enforced Azure billing safeguard. Before any GPU job: independently confirm subscription sponsorship coverage, hardware quota and availability, worker image/CUDA compatibility, bounded job runtime, actual hardware stop/deallocation, storage fees and private-network access. No VM, GPU, AML cluster, endpoint or training job is created.

## Known project measurements (not retested by this change)

- Copilot previously reconciled 106/106 original videos.
- Ten named exercise videos yielded eight usable research 8D QAF vectors, but bench_press/deadlift were insufficient for reliable named-pose extraction.
- Ten target/pose-guide pairs were created privately; further time-window and guide-coverage validation is necessary.
- A100/H100 quota last measured zero; CPU was available.
- A Mac M1 Pro 16 GB and Codespace can support preprocessing and human review, but not the official CUDA-first LTX LoRA training target.

## Test

    python -m unittest discover -s tests -p 'test_qaf_cinema_training_governance.py' -v

All provided test review references are clearly labeled FAKE/SYNTHETIC. Passing tests cannot prove actual rights, complete split readiness, a trained model, or QAF superiority.
