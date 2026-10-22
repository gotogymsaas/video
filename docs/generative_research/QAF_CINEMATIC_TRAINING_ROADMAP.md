# QAF Cinematic Neural Training: execution gates (22 October 2026)

## Status: NO TRAINED CINEMATIC GENERATOR
Repository `gotogymsaas/video` contains 10 numerical research models in `qaf_video/generative_research/models.py`. Paper 05's roll/warp fixture **does not synthesize novel photorealistic motion**. Existing `qaf_video.render.compositor.Movie` accepts real MP4 clips; this update adds research dataset contracts and an audited bridge to that capability. These components **do not run GPU training**, do not download copyrighted media, and do not invent weights/checkpoints.

## Proposed model choice (external research)
Primary: evaluate fine-tuning a pretrained open-weight image-to-video backbone, not from-scratch pretraining. Official references:
- LTX open-source model documentation: https://docs.ltx.io/open-source-model/getting-started/overview/
- LTX trainer: https://docs.ltx.io/open-source-model/ltx-trainer/ltx-training
- HunyuanVideo-1.5 training README: https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5

Use licensed weights subject to model version, intended commercial use, derivative rights and privacy review. Pin revision and checksum in a separate *private* model card. No guarantee of training quality is implied.

## Twelve actual missing pieces, in order
1. Contracted dataset, consent and licensing for identifiable actors, locations and garments.
2. Curate paired still image + motion video with subject/garment IDs and ground-truth descriptions, including running technique.
3. Validate 3-way subject- and garment-disjoint splits; avoid duplicate footage and data leakage.
4. Select an exact pretrained model revision, license, inference backend and compatible frames/resolution.
5. Provision and measure accelerator memory, disk, run budget, and checkpoint retention. LTX documentation recommends 80GB VRAM for training, with a more constrained 32GB LoRA pathway; measure on actual deployment hardware.
6. Create training pipeline using official trainer, fixed seed, dataset loader, and checkpoint logs. This repository does NOT implement the official weight update.
7. Train a scoped GoToGym LoRA for scene/style, then condition on motion/pose and cloth controls if supported.
8. Use reference scene graph, brand/identity embeddings and external pose+depth extraction; the current ten mathematical fixtures cannot extract them from pixels.
9. Integrate an external I2V runner returning H.264 MP4, with model/version/seed/request/provenance manifests.
10. Enforce temporal and identity review: face/person, garment logos, screen UI, hands, foot strike, flicker and continuity across cuts.
11. Compare blinded test clips with baseline unmodified model and LoRA+QAF variants; report subjective quality, error rates, cost, latency, OOD and confidence intervals.
12. Require human approval, rights, claim evidence and technical master checks before publishing. Never write `approved:true` programmatically.

## Implementation in this repository
### Dataset check
`python -m qaf_video.generative_research validate-dataset /private/dataset.json --model hunyuan15`
Manifest schema: `qaf_cinematic_training_dataset_v1`. Each `samples[]` entry:
`id, split, subject_id, garment_id, reference_image, video, prompt, rights, consent_record, fps, training_frame_count`.
Use only paths relative to manifest directory. For Hunyuan 1.5 the sampled training frame count follows `4n+1`; for LTX read its exact current preprocessing spec. The checker validates asset hashes, stream presence, split leakage and input metadata. Passing means **schema checks**, not data adequacy or model quality.

### Existing-weight check
`python -m qaf_video.generative_research inspect-checkpoint /private/models adapter.safetensors --sha256 YOUR_SHA256`
A file and sha match do NOT certify trained weights.

### Ingest real generated MP4 safely
`python -m qaf_video.generative_research ingest-clip projects/episode/project.json --shot 0 --clip assets/neural-output.mp4 --provenance projects/episode/provenance.json`
The externally rendered video and input image must already live inside the project folder. Provenance must include model_id, model_license, input_image, rights, consent_record, prompt and seed. Generated content hashes become project.assets provenance. The selected shot is changed from image to video; the project is validated and its brand/picture/rights approvals are reset. The pipeline can then export a **draft**, not a verified commercial master.

### QAF applicability gate
`python -m qaf_video.generative_research applicability measurements.json`
Inputs: `qaf_quality, baseline_quality, qaf_cost, baseline_cost, max_cost, ood_passed` (plus optional min_pairs/seed).
If matched objective gains are unproven or costs exceed budget, QAF is not automatically preferred. Bootstrap significance is indicative; final preregistration and multiple-comparison controls belong in a separate experiment.

## Prior scientific evidence (not cinematic efficacy)
QAF experiments G1-G6 report conditional advantages for sparse relational observations and explicit classical-positive/failure regions; they do not establish that QAF improves I2V photorealism. MPS/TDVP/QUBO cannot replace a trained spatiotemporal diffusion/flow-transformer. The ten paper implementations remain research references until evaluated with paired authorized footage and a truly neural generator.

## Next work-mode execution
Open ChatGPT **Work** and point it to `gotogymsaas/video`; request an isolated GPU-ready development environment, privately accessible authorized dataset and licensed backbone. First run the dataset, checkpoint and CI gates. Then adapt an official training pipeline, implement inference provider integration, train a first LoRA, generate and evaluate 5-second running clips, use the fail-closed ingest command, and seek human approval before release.
