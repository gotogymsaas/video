# Hybrid QAF Cinema Engine — controlled VFX draft

Implements reproducible 2.5D camera zoom, procedural emerald/gold/mint energy, glow lighting, foreground mask occlusion, exact original phone screen via existing homography module, MP4 export and source hashes.

**CLI:** `python -m qaf_video.generative_research.hybrid_vfx private/shot.json --out private/draft.mp4`.

**Manifest schema:** `qaf_cinematic_hybrid_pilot_v1`, with `width`, `height`, `fps`, `seconds`, `background`, `phone_screen`, `phone_quad` (four pixel coordinates), optional `subject_mask`, `medical_claims: declared_only`, `camera.zoom: [1,1.05]`, `events: [{type:pulse,start,end,center:[0.4,0.5],color:emerald}]`.

Research mapping: P051/P052 (visual energy), P061/P063 (occlusion), P071 (glow), P081 (original UI projection), P121/P123 (draft/review), synthesis A03/A04.

**Not implemented by this module:** neural action synthesis, independently generated camera depth, physically calibrated relighting, automatic finger masks, text-to-video model training. No QAF superiority claim; proper matched classical comparison required. Actor and phone imagery must be licensed and reviewed, and all medical information must be declared rather than inferred.
