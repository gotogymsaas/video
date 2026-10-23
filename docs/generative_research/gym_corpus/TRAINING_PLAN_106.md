# 106/106 video LoRA plan

The 106 original MP4 source files in gotogymsaas/appdesplegada are included in the metadata-only plan. Rights were confirmed by the user on 2026-10-23. No video bytes or faces were transferred to the video repo.

1. Run the FFprobe/decode audit from appdesplegada workflow `qaf-gym-media-audit.yml` on all 106 files. The triggered Actions run 39961868586 **failed before recording steps**, hence media inspection is not yet verified.
2. Group by real actor, session and garment; write human-verified descriptions for each clip.
3. Allocate 80% train, 10% validation, 10% test **by group**, accounting for all 106. Not all 106 should be used for gradient training if you need an unbiased test.
4. Extract reference images, enforce legal evidence, validate `training_readiness.py` and export with `ltx_dataset_export.py` (official 8n+1 temporal bucket).
5. Provision supported NVIDIA CUDA GPU and matching LTX-2.5 I2V LoRA checkpoints. Execute `gpu_training_runner.py` after confirming model license, compatible config and budget.
6. Evaluate against base LTX and same-backbone QAF/classical planning at matching seeds and compute. Include human blinded comparison and defects.

Current runtime confirmed `torch 2.10.0+cpu`, CUDA unavailable. Training/weights are NOT completed. Source audit failed with no executed job steps; source app auto deploy also reported a failure after the audit commit, so production deploy was **not** confirmed successful. Do not claim video readiness or model training until verified.
