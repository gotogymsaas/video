"""Dataset and checkpoint readiness gates for QAF cinematic fine-tuning.
Training/inference are NOT executed by this module. Data never leave the local workspace.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from PIL import Image
from ..core import require, local_asset, sha256, probe

SCHEMA="qaf_cinematic_training_dataset_v1"
SPLITS={"train","val","test"}
VALID_MODELS={"hunyuan15","ltx"}
def _positive(value, name):
    require(isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>0,name+" must be positive")
    return value

def validate_dataset(manifest, model="hunyuan15", verify_media=True):
    """Checks rights, leakage, media and model-specific frame counts.
    No automatic 'enough training data' certification is possible.
    """
    require(model in VALID_MODELS,"Unknown model")
    path=Path(manifest).resolve()
    spec=json.loads(path.read_text(encoding="utf-8"))
    require(spec.get("schema")==SCHEMA,"Unsupported dataset manifest")
    clips=spec.get("samples")
    require(isinstance(clips,list) and len(clips)>0,"Dataset has no samples")
    seen_ids=set();split_subjects={s:set() for s in SPLITS};split_garments={s:set() for s in SPLITS}
    fingerprints={};splits={s:0 for s in SPLITS};issues=[]
    for index,s in enumerate(clips):
        require(isinstance(s,dict),"Invalid dataset row")
        key=s.get("id");split=s.get("split")
        require(isinstance(key,str) and key and key not in seen_ids,"Duplicate/missing sample ID")
        seen_ids.add(key)
        require(split in SPLITS,"Invalid split")
        splits[split]+=1
        for field in ("subject_id","garment_id","prompt","rights","consent_record"):
            require(isinstance(s.get(field),str) and bool(s[field].strip()),f"{key}: missing {field}")
        # Prevent identity leakage across splits (including garments).
        split_subjects[split].add(s["subject_id"])
        split_garments[split].add(s["garment_id"])
        fps=_positive(s.get("fps"),"fps")
        require(8<=fps<=60,"FPS outside planned range")
        count=s.get("training_frame_count")
        require(isinstance(count,int) and not isinstance(count,bool) and count>=5,"Invalid frame count")
        if model=="hunyuan15":
            require((count-1)%4==0,f"{key}: Hunyuan training uses 4n+1 frames")
        image=local_asset(path.parent,s.get("reference_image",""))
        video=local_asset(path.parent,s.get("video",""))
        require(image.suffix.lower() in (".png",".jpg",".jpeg",".webp"),"Unsupported image")
        require(video.suffix.lower() in (".mp4",".mov",".webm"),"Unsupported video")
        ih=sha256(image);vh=sha256(video)
        for h in (ih,vh):
            if h in fingerprints and fingerprints[h]!=split:
                issues.append(f"Source content shared between {fingerprints[h]} and {split}: {key}")
            fingerprints[h]=split
        if verify_media:
            with Image.open(image) as im:im.verify()
            info=probe(video)
            streams=[t for t in info.get("streams",[]) if t.get("codec_type")=="video"]
            require(len(streams)>=1,f"{key}: missing video stream")
            # Training frames may be sampled from a longer source.
            length=float(info["format"]["duration"])
            require(length>0,f"{key}: empty video")
            if "duration_seconds" in s:
                require(abs(float(s["duration_seconds"])-length)<=0.25,f"{key}: duration mismatch")
    for i,a in enumerate(sorted(SPLITS)):
        for b in sorted(SPLITS)[i+1:]:
            if split_subjects[a]&split_subjects[b]:
                issues.append(f"Subject leakage between {a} and {b}")
            if split_garments[a]&split_garments[b]:
                issues.append(f"Garment leakage between {a} and {b}")
    require(not issues,"; ".join(issues))
    return {"schema":"qaf_cinematic_dataset_report_v1","validated":True,
            "training_not_executed":True,"model":model,"samples":len(clips),
            "splits":splits,"frames_format":"4n+1" if model=="hunyuan15" else "model dependent",
            "sufficient_training_data":"undetermined","manifest_sha256":sha256(path)}

def inspect_checkpoint(workspace, checkpoint, expected_sha256=None):
    """Physical on-disk checkpoint existence, not evidence of a trained model."""
    p=local_asset(Path(workspace),checkpoint)
    require(p.suffix.lower() in (".safetensors",".bin",".pt",".ckpt"),"Unsupported checkpoint file")
    require(p.stat().st_size>1024,"Empty or tiny checkpoint")
    sha=sha256(p) if expected_sha256 else None
    if expected_sha256:
        require(len(expected_sha256)==64 and sha==expected_sha256,"Checkpoint hash mismatch")
    return {"present":True,"bytes":p.stat().st_size,"sha256":sha,
            "trainable_model_verified":False,"inference_verified":False,
            "note":"Weight presence alone does not establish a compatible model or training success"}
