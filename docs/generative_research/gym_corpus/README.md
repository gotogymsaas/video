# GoToGym original gym video corpus audit — 2026-10-23

**Live repository inspection:** `gotogymsaas/appdesplegada`, `main`, tree `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`. The folder `Videos_test_gimnasio/` contains **106 MP4 originals/candidates**, totaling **226,773,466 bytes** (226.8 MB). Elsewhere in the repository there are 12 MP4 previews/derived outputs, which are excluded to avoid train/test contamination.

`candidate_inventory.json` contains Git paths, blob SHAs and byte sizes ONLY: **zero films transferred, zero training performed, zero commercial learning rights approved**. All `rights_status` values are `UNREVIEWED`.

The clip names consist of 96 WhatsApp-date filename takes plus ten exercise-name files. The named exercise files include `bench_press`, `bent_over_row`, `bodyweight_squat`, `deadlift`, `lunge`, `overhead_press`, `plank`, `pull_up`, `push_up`, `single_leg_rdl`. This naming supports sports motion learning, NOT cinematic actor-phone/scene training.

## Human rights review

Before using footage for commercial generative training, verify who filmed, who owns camera footage, scope of original recording consent, whether a recorded athlete/coach consented to synthetic reproduction of body/appearance/voice, the WhatsApp sharing terms, any music/logos, and whether minors are present. Restrict the resulting dataset by actor and garment. **Do not invent consents or re-use source GitHub access as an ML authorization.**

## Private training export

1. Copy all approved source clips locally into a PRIVATE, access-controlled folder, preserving `Videos_test_gimnasio/<original filename>.mp4` and verifying byte size.
2. Maintain a **private** `qaf_gym_corpus_approvals_v1` JSON with `approved` rows: source_path, training_rights_documented:true, participant_consent_documented:true, reviewed_by, review_reference, actor_group, garment_group, split, caption, fps, training_frame_count.
3. After authorizations are actually filed, run:
```sh
python -m qaf_video.generative_research.gym_corpus_adapter \
 docs/generative_research/gym_corpus/candidate_inventory.json /private/approvals.json \
 --root /private/approved-videos --out /private/approved-videos/training_dataset.json
```
4. Feed approved dataset into `ltx_dataset_export.py` and LTX Trainer official I2V LoRA config, check test holdout and GPU. Do not train on duplicate previews or unverified actor groups.

## External free sources

Official Blender Studio and individual Wikimedia Commons assets may be candidates where license terms allow the precise ML training use, the depicted people have relevant privacy/likeness rights, and excluded components are respected. **Pexels API collection for ML training is explicitly disallowed without permission**. LTX trainer code and model weights can be downloaded subject to LTX model licensing, but high-memory NVIDIA GPU rental is not normally free. 
