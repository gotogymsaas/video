# Vision evidence — Pose / Hands / Depth / Occlusion

`vision_evidence.py` defines `qaf_cinematic_observations_v1`, a complete **per-frame** schema for body landmarks, hand landmarks, silhouette masks and registered depth maps. Each frame has `frame` index, normalized `pose` and `hands`, and optional grayscale `mask`/ `depth` PNG paths.

**Working now:** parse/check frame geometry, masks and depth, locate hand center with confidence threshold, compute depth-tested foreground occlusion, provide optional MediaPipe Tasks PoseLandmarker/HandLandmarker inference from *explicitly installed official* .task model files. Missing detections remain missing instead of being fabricated. No model binaries are included; installing MediaPipe alone is insufficient without compatible models.

**Depth**: cannot be deduced truthfully from two-dimensional pixel positions alone. Supply a depth PNG from camera, rendered Z-pass or an appropriately licensed depth estimator. Pixel value 0 means closer and 255 farther in the configured threshold convention. This relative mask is **not metric depth**, and requires calibration against actor silhouette.

**Output**: per-frame observations can be used by `hybrid_motion.render_motion(..., observations="private/evidence.json")` for mask-occluded effects and hand-following energy anchors. New frames without masks retain the original compositor behavior. Model fitting, exact phone quadrilateral tracking, dynamic light transport and semantics remain distinct unresolved research tasks.

**Privacy**: do not store biometric identity or upload real faces to Git. Underlying footage, model weights and detection data stay in private workspaces.
