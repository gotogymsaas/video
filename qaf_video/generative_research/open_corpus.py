"""Open-license video dataset intake. No downloading or license auto-approval.

Only *individually reviewed* assets may enter training; dataset card license
does not convey underlying footage rights. All data remain outside Git.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image
from ..core import require, sha256

BLOCKED_SOURCES = {
    "pexels-api": "Pexels prohibits API-based AI/ML dataset collection without permission",
    "openvid-1m": "Underlying video licenses vary; card states research/noncommercial",
    "ucf101": "Academic/noncommercial restrictions; commercial clearance absent",
}
SOURCE_REFERENCES = {
    "blender-sprite-fright": {
        "source_page": "https://studio.blender.org/projects/sprite-fright/pages/about/",
        "license_page": "https://creativecommons.org/licenses/by/4.0/",
        "warning": "Review every chosen file, excluded logos/trademarks and attribution."
    },
    "wikimedia-commons": {
        "source_page": "https://commons.wikimedia.org/",
        "warning": "License is per media file; source page/author/attribution required."
    },
}
SCHEMA = "qaf_open_cinematic_asset_v1"

def _confined(root, name):
    root=Path(root).resolve()
    require(isinstance(name,str) and bool(name), "Local path required")
    p=(root/name).resolve()
    require(p.is_relative_to(root) and p.is_file(), "Asset must exist within corpus folder")
    return p

def _nonempty(record,key):
    v=record.get(key)
    require(isinstance(v,str) and bool(v.strip()), "Missing "+key)
    return v

def audit_asset(record, corpus_root, verify_media=True):
    """Return eligibility only after a recorded *external human* clearance.
    This is a provenance/metadata check, not legal certification.
    """
    require(isinstance(record,dict) and record.get("schema")==SCHEMA, "Invalid asset schema")
    source=_nonempty(record,"source_id").lower()
    require(source not in BLOCKED_SOURCES, BLOCKED_SOURCES.get(source,""))
    for field in ("source_url","license_url","license_id","attribution",
                  "reviewer","review_date","commercial_training_permission",
                  "consent_reference","subject_id","garment_id","clip","reference_image"):
        _nonempty(record,field)
    require(record["commercial_training_permission"]=="documented",
            "Commercial ML training permission requires documentary confirmation")
    require(record.get("reviewed_for_training") is True, "Human review required")
    require(record.get("explicit_restrictions_resolved") is True,
            "Unresolved exceptions to terms/license")
    require(record.get("scope")=="commercial_video_model", "Training scope mismatch")
    root=Path(corpus_root).resolve()
    video=_confined(root,record["clip"])
    still=_confined(root,record["reference_image"])
    proof=_confined(root,_nonempty(record,"consent_reference"))
    require(proof.stat().st_size>0,"Missing consent/license evidence")
    require(video.suffix.lower() in (".mp4",".mov",".webm"),"Unsupported source video")
    require(still.suffix.lower() in (".jpg",".jpeg",".png",".webp"),"Unsupported still image")
    if verify_media:
        with Image.open(still) as im:im.verify()
        p=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format",
                          "-of","json",str(video)],capture_output=True,text=True,timeout=30)
        require(p.returncode==0,"FFprobe failed")
        info=json.loads(p.stdout)
        require(any(s.get("codec_type")=="video" for s in info.get("streams",[])),
                "Video stream absent")
        require(float(info["format"]["duration"])>0,"Empty video")
    return {"eligible_for_research_dataset":True,
            "legal_rights_independently_verified":False,
            "source_id":source,"clip_sha256":sha256(video),
            "reference_sha256":sha256(still),"permission_document_sha256":sha256(proof),
            "attribution":record["attribution"],"source_url":record["source_url"]}

def compile_training_manifest(corpus_root, source_records, output, model="hunyuan15",
                              verify_media=True):
    """Materialize only declared/approved local entries, never fetch third-party videos.

    Source record includes split, fps and training_frame_count for preprocessing.
    """
    require(model in ("hunyuan15","ltx"),"Unknown target")
    root=Path(corpus_root).resolve()
    seen=set();subjects={};garments={};digest_splits={}
    examples=[];reviewed=[]
    for record in source_records:
        reviewed_asset=audit_asset(record,root,verify_media)
        split=record.get("split")
        require(split in ("train","val","test"),"Bad split")
        key=_nonempty(record,"id")
        require(key not in seen,"Duplicate sample identifier");seen.add(key)
        for field,tracking in (("subject_id",subjects),("garment_id",garments)):
            entity=record[field]
            require(entity not in tracking or tracking[entity]==split,
                    "Cross-split identity/product leakage")
            tracking[entity]=split
        clip_hash=reviewed_asset["clip_sha256"]
        require(clip_hash not in digest_splits,
                "A video cannot be reused or split into distinct samples without grouping")
        digest_splits[clip_hash]=split
        fps=record.get("fps");frames=record.get("training_frame_count")
        require(isinstance(fps,int) and 8<=fps<=60,"FPS invalid")
        require(isinstance(frames,int) and frames>=5,"Frame count invalid")
        if model=="hunyuan15":
            require((frames-1)%4==0,"Hunyuan requires 4n+1 frames")
        examples.append({"id":key,"split":split,"subject_id":record["subject_id"],
                         "garment_id":record["garment_id"],"prompt":_nonempty(record,"prompt"),
                         "rights":record["license_id"],"consent_record":record["consent_reference"],
                         "fps":fps,"training_frame_count":frames,
                         "reference_image":record["reference_image"],"video":record["clip"]})
        reviewed.append(reviewed_asset)
    require(examples,"No authorized assets")
    require(any(x["split"]=="train" for x in examples) and any(x["split"]=="val" for x in examples),
            "Train and validation sets required")
    output_path=(root/output).resolve()
    require(output_path.is_relative_to(root),"Cannot write outside private corpus")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    result={"schema":"qaf_cinematic_training_dataset_v1","samples":examples}
    output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"samples":len(examples),"manifest":str(output_path),"checksums":reviewed,
            "license_review_certification":"Requires independent legal verification"}

def load_records(path):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(doc,list),"Expected JSON array of asset records")
    return doc
