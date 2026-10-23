# GPU execution gate for official LTX I2V LoRA

For a **private, legally cleared dataset**, available official trainer checkout and reviewed weights, the new `gpu_training_runner.py` can submit the real official training command:

```bash
python -m qaf_video.generative_research.gpu_training_runner program.json --workspace /private --output-dir /private/runs/001
# Only AFTER checking model/data licenses, exact upstream trainer YAML and approving GPU costs:
QAF_CINEMA_ALLOW_GPU_TRAINING=YES python -m qaf_video.generative_research.gpu_training_runner program.json --workspace /private --output-dir /private/runs/002 --execute
```

The default is dry-run. Execution requires a local NVIDIA GPU with declared VRAM and explicit opt-in environment variable. It applies the maximum GPU hours supplied in the program manifest as a subprocess timeout and preserves a trainer log/hash.

**Critical evidence rule:** process exit code 0 does not establish a trained or valid model. The report says `FINISHED_EXIT_ZERO_UNVERIFIED`; an independent operator must review actual exported LoRA weights, validation loss, CUDA telemetry, and matched I2V samples. If training is killed due to timeout, classify it failed; partial checkpoints may be useful scientifically but are not production models.

Trainer configuration is under the operator's authority. The runner never fabricates parameters not supported by the installed upstream trainer.
