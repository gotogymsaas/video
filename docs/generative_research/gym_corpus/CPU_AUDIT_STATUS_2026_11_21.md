# GoToGym 106-Clip CPU Audit Status
**Date:** 2026-11-21
**Branch/commit:** `main` at `338f18e`
**Training status:** NOT STARTED
**GPU status:** NOT AVAILABLE AND NOT APPROVED

## Verified inventory

- `candidate_count`: 106
- `total_source_bytes`: 226,773,466
- Metadata source: `gotogymsaas/appdesplegada`
- Source tree: `6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62`
- Named exercise candidates: 10
- Unclassified recordings: 96
- Exact Git blob duplicates in metadata: none found
- Full local video decode: not performed
- Rights review: not performed
- Training: not performed

The repository-only audit confirms all 106 source paths and byte sizes in the metadata plan. It does not verify video integrity, visual content, duration, resolution, FPS, participant identity, consent or commercial permission.

## Audit result

Running the repository coverage audit returned:

```text
sources: 106
unreviewed_media: 106
ungrouped: 106
unlabeled: 106
gpu_ready: false
checkpoint_verified: false
```

This result is the correct fail-closed state. No split should be treated as approved until every clip has passed individual review.

## CPU-only workflow

Copy the 106 reviewed MP4 files to an authorized private folder. Keep them outside Git and public artifacts.

Run:

```bash
python -m qaf_video.generative_research.gym_corpus_triage \
  docs/generative_research/gym_corpus/candidate_inventory.json \
  --local-root /private/gotogym-approved-review \
  --out /private/gym_triage_private.json
```

The private report must contain:

- duration;
- width and height;
- FPS;
- local SHA-256;
- exact local duplicate groups;
- missing local media count;
- a separate record for every rejected, unreadable or unreviewed clip.

Then complete human review:

1. Confirm source and copyright/AI-training rights for each clip.
2. Confirm participant likeness consent.
3. Review possible minor appearance.
4. Verify exercise and camera behavior.
5. Assign a real actor group.
6. Assign a real session group.
7. Assign a real garment group.
8. Verify a truthful caption.
9. Mark perceptual duplicates and OOD clips.
10. Assign train, validation and test only by non-overlapping actor, garment and session groups.

Do not infer actor identity, garment or split from filenames.

## Private approval manifest

Use `gym_corpus_adapter.py` to materialize a dataset only after all of these conditions are documented per clip:

- `training_rights_documented: true`
- `participant_consent_documented: true`
- `reviewed_by` is set
- `review_reference` is set
- `actor_group` is set
- `garment_group` is set
- `split` is train, val or test
- `caption` is human verified
- `fps` is verified
- `training_frame_count` is 8n+1

The adapter rejects duplicates, missing files, wrong byte sizes, cross-split actor/garment groups and missing train/validation/test sets.

```bash
python -m qaf_video.generative_research.gym_corpus_adapter \
  docs/generative_research/gym_corpus/candidate_inventory.json \
  /private/gym_corpus_approvals.json \
  --root /private/gotogym-approved-review \
  --out /private/gotogym-approved-review/qaf-cinematic-dataset.json
```

The adapter never downloads media and never verifies rights from GitHub alone.

## Blockers before GPU training

1. Obtain and scan the private approved video originals.
2. Run FFprobe and local SHA-256 generation.
3. Remove unreadable, duplicate or corrupted sources.
4. Complete independent rights and consent records.
5. Complete actor, garment and session grouping.
6. Complete human captions.
7. Assign leakage-controlled splits.
8. Generate a private LTX export.
9. Confirm GPU quota and written budget approval.
10. Confirm base model license, checkpoint hashes and official LoRA configuration.
