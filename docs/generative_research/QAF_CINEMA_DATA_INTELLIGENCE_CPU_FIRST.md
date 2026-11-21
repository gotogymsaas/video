# QAF Cinema Data Intelligence — CPU-first implementation
Status: implementation available for review; no real 106-video audit executed here, no model weights trained.

## Implemented
- scripts/qaf_cinema_data_intelligence.py: offline FFprobe/FFmpeg audit of real private MP4 bytes. Samples at most 10 grayscale 160x90 frames at 2 fps. Records resolution, duration, compression metadata, luminance, clipped highlight/shadow proxies, spatial gradient, sampled temporal differences, and SHA-256.
- qaf_video/generative_research/vision_evidence.py: preserve official MediaPipe joint_id in pose extraction. Historical filtered arrays lose their original landmark index; never infer identity from their array order.
- scripts report optional QAF pose evidence: an 8D vector based on coverage, confidence, stable joints, centroid displacement, normalized per-frame motion/acceleration/jerk and bone-length variation. It requires stable named joints and real observed values; otherwise vector is null.
- Tests include fail-closed quality, missing video, unlabeled pose and unsafe path cases.

## Run against the 106 source clips
Inside the video repository with FFmpeg installed and the actual authorized source media in a PRIVATE directory preserving Videos_test_gimnasio/ path structure:

    python scripts/qaf_cinema_data_intelligence.py \
      --inventory docs/generative_research/gym_corpus/candidate_inventory.json \
      --media-root /private/qaf-originals \
      --observations-root /private/qaf-observations \
      --out /private/qaf-reports/cinema-audit-001.json

Optional observations 001.json through 106.json correspond to inventory order, produced with the current joint-id-preserving vision_extract.py. The auditor requires the observation source_mp4_sha256 to match the exact original MP4 SHA-256; missing or mismatched hashes fail closed. Keep observational annotations private and independently inspect pose validity.

For a first sample use --limit 10 and a distinct output path. Output must stay PRIVATE and outside Git. The tool refuses output overwrite, but it is the operator's duty not to commit the report.

## Three library policy
- Motion source: older gym MP4 may yield reliable motion evidence; compression and occlusion may prevent analysis. No inferred or invented joints.
- Visual source: 720p+ original clips with reasonable luma/gradient proxies are queued for HUMAN visual review only, not auto-approved as cinematic. Use authorized professional footage to teach aesthetic direction. No simulated upscaling accepted as true original detail.
- Structural source: Phi_Q pose features describe observed relationships but DO NOT automatically feed LTX, represent 3D cloth physics, or demonstrate QAF superiority.

## Data and training gates
1. Audit all 106 actual files and full-decode where needed, then verify observation/source pairs by hash.
2. Human film review, provenance, actor identity grouping, garment grouping and documented commercial synthetic training permission.
3. Keep actors, garment groups and sessions disjoint across train/val/test; no synthetic duplicates or derived previews leaking into evaluation.
4. Convert measured pose/track signals to the exact, pinned and verified official LTX IC-LoRA video-guide format. The eight-dimensional vector itself is NOT an official LTX conditioning format. No neural model is modified by this PR.
5. Blindly compare A (base model), B (visual LoRA), C (classical structure control) and D (QAF control) with matched seeds, same data and compute. Reject unsupported QAF advantage claims.
6. Validate real MP4 playback, checkpoint, actual compute cost and human review before publishing.

## Azure instructions
Last reported A100/H100 quota was 0, NC/NV family limit 6 with used null. Sponsorship eligibility and pricing remain unverified. CPU inspection creates no Azure resources and does not grant permission to deploy GPU, network, firewall, storage or VM.

## Official references
- https://docs.ltx.io/open-source-model/ltx-trainer/quick-start
- https://docs.ltx.io/open-source-model/feature-guides/structural-control/motion-control/
- https://learn.microsoft.com/azure/machine-learning/how-to-manage-quotas
