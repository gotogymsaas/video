# Scientific falsification registry — all 24 QAF cinema hypotheses

This register makes a strict distinction between *scientific manuscripts present* and *experiments completed*. It is attached to the independent evidence task in [Issue #1](https://github.com/gotogymsaas/video/issues/1).

Run:
```bash
python -m qaf_video.generative_research.open_science_registry .
```
The `research_registry.json` enumerates 24 primary metrics and strong baselines; all results initially report `NOT_EVALUATED`. A study may be promoted only after an independent artifact set records actual data rights, test/OOD split, matched compute, backbone, human review where needed, seeds/checkpoint, and the full distribution of results. Negative QAF deltas are valid results.

Proposed open-source tools:
- `VBench-2.0` for human anatomy, physics and creative composition; `VBench` for flicker, motion and identity.
- `MediaPipe`/OpenPose/MMPose for human action; check each model's license and representation bias.
- `OpenCV` for flow and tracking baselines; classical DP, MILP, Kalman/PBD remain serious comparators.
- `ffmpeg`, `ffprobe`, `numpy` for deterministic encoded-media diagnostics.
- `LTX Trainer` for I2V LoRA, IC-LoRA control and matching pretrained weights.

**Warning:** these tools are not auto-installed or run by the current module. A matched same-backbone baseline is essential for any QAF-specific claim; VBench does not alone certify product/logo or copyright safety. The train/val/test sets for running must exclude the same actor and garment between splits and be held private with rights documentation.

Scientific failure regions carry forward the original QAF G1–G6 caveats: classical-positive, non-identifiable and computational-breakdown must remain publishable outcomes.
## Verified resource matrix — October 22, 2026

| Source | What it enables | Restriction |
|---|---|---|
| [Blender Studio Sprite Fright](https://studio.blender.org/projects/sprite-fright/pages/about/) | Animated motion reference | CC BY project assets, exceptions for excluded trademarks and certain components; inspect specific file |
| [Wikimedia Commons example](https://commons.wikimedia.org/wiki/File:Sprite_Fright_-_Open_Movie_by_Blender_Studio.webm) | Exact film file with CC BY 4.0 per-file declaration | Credit Blender Studio, preserve license + modification notice; film does not substitute running footage |
| [LTX-2.5](https://docs.ltx.io/open-source-model/getting-started/overview/) | Open-weight I2V / multishot / audio video | Community license including $10M annual turnover threshold; possible restrictions on transfers of fine-tunes |
| [LTX Trainer](https://docs.ltx.io/open-source-model/ltx-trainer/quick-start) | LoRA, I2V, IC-LoRA and full tuning | Official GPU requirement minimum ~32GB and 80GB recommendation for standard training |
| [ComfyUI server API](https://github.com/Comfy-Org/docs/blob/main/development/comfyui-server/comms_routes.mdx) | Local GPU job dispatch + output retrieval | User must provision server and model workflow |
| [VBench](https://github.com/Vchitect/VBench) and [VBench-2.0](https://github.com/Vchitect/VBench/tree/master/VBench-2.0) | Independent visual and anatomical benchmark tools | Must run external evaluation with human review |
| [OpenVid-1M](https://huggingface.co/datasets/nkp37/OpenVid-1M) | Research corpus | Mixed underlying licenses; upstream card explicitly states research/noncommercial |
| [Pexels ToS](https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions) | No training dataset use through API | Prohibits ML dataset compilation/training without explicit permission |
| [HunyuanVideo-1.5 License](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE) | Open-weights technical alternative | Territory restrictions, output restrictions for training other models |

Runbook: [OPEN_SOURCE_CORPUS_AND_BENCHMARK.md](../OPEN_SOURCE_CORPUS_AND_BENCHMARK.md), [LTX_COMFY_INTEGRATION.md](../LTX_COMFY_INTEGRATION.md), [LTX_25_GPU_TRAINING_PREFLIGHT.md](../LTX_25_GPU_TRAINING_PREFLIGHT.md).
