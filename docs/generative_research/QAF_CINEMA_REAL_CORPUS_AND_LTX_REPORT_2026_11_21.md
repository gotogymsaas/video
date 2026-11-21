# QAF Cinema Real Corpus and LTX Integration Report
**Date:** 2026-11-21
**Repository commit:** `e0fe2c48c976098e7550e18732f10b4353d649f2`
**Mode:** real-media CPU audit, no GPU training, no Azure provisioning

## 1. Real corpus result

The local source directory contained 100 MP4 files. The inventory match audit found:

- 96 local files with exact inventory names and exact inventory byte sizes.
- 10 inventory entries absent from the local source directory.
- 4 additional local MP4 copies not present in the inventory.
- 217,091,096 bytes copied into a private session media root for the exact 96 matches.
- 0 technical decoder failures among the 96 present files.
- 0 real pose/hand observations extracted; no observation model tasks were supplied.
- 0 files were training-approved.

The Data Intelligence report examined all 106 inventory rows:

| State | Count |
|---|---:|
| Present and decodable | 96 |
| Missing source | 10 |
| Decoder failure | 0 |
| Visual proxy candidates | 0 |
| Motion evidence candidates | 0 |

This is the first real decoded-media audit, but it is not a cinematic-quality certification.

## 2. Visual and movement measurements

The present files resolve as:

- 84 at `576x1024`.
- 9 at `464x832`.
- 3 at `480x848`.

Duration:

- Minimum: 5.000 seconds.
- Median: 19.367 seconds.
- Maximum: 81.600 seconds.

Every present file is flagged with `LOW_RESOLUTION_FOR_CINEMA_REFERENCE` by the repository proxy. No clip was promoted into the visual or motion library from these proxies alone.

No 3D depth, segmentation, joint identity, pose time series or clothing geometry was claimed.

## 3. Library classification

### A. Movement

No clip is currently promoted. The 96 clips are eligible for offline pose extraction only after an approved MediaPipe Tasks pose model is supplied. Heavy occlusion, crop, camera motion and low view scale must be reviewed framewise.

### B. Cinematography

No clip is promoted as a cinematic source. All 96 assessed sources are vertical, with short edges of 464–576 pixels; their frame heights are 832–1024 pixels. The current proxy applies a landscape-oriented threshold to these clips, which is not a valid stand-alone assessment of suitability for 9:16 social content. Luminance and gradient proxies also do not establish human-perceived or professional cinema quality.

Commercially cleared, higher-resolution, professionally lit, actor-consented and garment-consented footage is still required.

### C. QAF control

No named pose observations exist yet. The 8D Phi_Q implementation remains a research representation with coverage, confidence, stable joint density, centroid displacement, normalized motion, acceleration, jerk and bone-length variation.

The 8D vector is not accepted as an LTX control signal.

## 4. LTX-2.5 compatibility

Official LTX documentation confirms:

- LTX-2.5 LoRA uses the matching LTX-specific Gemma 4 text encoder.
- 80 GB VRAM is recommended.
- The low-VRAM path can use 32 GB GPUs with INT8 and other memory optimizations.
- V2V IC-LoRA learns transformations from paired target/reference videos.
- Reference latents participate in bidirectional self-attention and are excluded from loss.
- Depth, pose, Canny and other reference videos are valid conditioning classes.
- Target and reference frame counts must match.
- The 8D QAF vector is not a supported LTX reference-video format.

The new CPU-only adapter:

- validates both target and reference SHA-256 values against their declared hashes;
- verifies frame-count equality;
- verifies dimensions are divisible by 32, and checks equal FPS and decoded frame counts;
- validates the control type;
- records the 8D QAF vector only as manifest metadata;
- rejects direct use of QAF values as an LTX condition;
- emits a separate `*.ltx.json` array containing official `video`, `reference_video` and `caption` fields for the pinned trainer, alongside its internal evidence report;
- never starts training or downloads weights.

Official references:

- [LTX Training Overview](https://docs.ltx.io/open-source-model/ltx-trainer/ltx-training)
- [LTX Quick Start](https://docs.ltx.io/open-source-model/ltx-trainer/quick-start)
- [LTX Training Modes](https://docs.ltx.io/open-source-model/ltx-trainer/training-modes)
- [Union Control Pose/Depth/Canny](https://docs.ltx.io/open-source-model/feature-guides/structural-control/union-control)

## 5. Azure status

Azure CLI and Azure MCP credentials were not available in this environment. No live subscription or quota query could be executed.

The latest verified report from the authorized Mac remains:

- A100/H100 quota: zero.
- VM GPU quota: zero.
- Some NC/NV families: limit 6, use unknown.
- Workspace public access disabled.
- Sponsorship eligibility: unverified.
- Sponsorship pricing: unverified.

The public Azure Retail Prices API returned HTTP 429 during this session, so no hourly price or GPU-hour budget is claimed.

No VM, cluster, GPU compute, endpoint or storage resource was created.

## 6. Missing material

To reach a defensible first real pilot:

1. Recover or restore the 10 missing inventory clips.
2. Remove or document the 4 extra duplicate copies outside the inventory.
3. Supply independent legal/consent records.
4. Assign actor, session and garment groups.
5. Assign leakage-free train/validation/test splits.
6. Supply an official MediaPipe pose task and run framewise pose extraction.
7. Create independently reviewed pose/depth/Canny reference rasters.
8. Create paired target/reference videos with equal frame counts.
9. Match exact LTX checkpoint, Gemma 4 encoder and trainer commit.
10. Obtain GPU quota and written sponsorship approval.

## 7. Four comparable experiments

Only execute after real paired data and GPU approval:

| Experiment | Condition |
|---|---|
| A | Base LTX model |
| B | Visual LoRA |
| C | Classical pose/depth/Canny control |
| D | QAF planning plus the same verified classical control |

All experiments require matched scenes, seeds, data splits, compute budgets and blind human review.

## 8. Current tests

- Data Intelligence: 11 tests PASS.
- LTX control adapter: 4 tests PASS.
- Combined QAF neural verification: 21 tests PASS.
- Optional PyTorch training tests remain skipped because PyTorch/LoRA weights are unavailable.

No test demonstrates trained model quality.
