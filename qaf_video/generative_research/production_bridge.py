"""Fail-closed promotion of externally generated I2V clips into QAF Video projects.

A real, licensed neural backend must output the MP4 first. This module never
pretends synthetic warps are generative footage or auto-approves a final video.
"""
from __future__ import annotations
import copy, json, os, shutil, tempfile
from pathlib import Path
from PIL import Image
from ..core import local_asset, sha256, require, validate, load, atomic_json, probe

def ingest_generated_clip(project_file, shot_index, clip, provenance):
    project_path=Path(project_file).resolve()
    base=project_path.parent
    project=load(project_path)
    require(isinstance(shot_index,int) and not isinstance(shot_index,bool),"Invalid shot index")
    require(0<=shot_index<len(project["shots"]),"Shot does not exist")
    require(isinstance(provenance,dict),"Provenance must be an object")
    for key in ("model_id","model_license","input_image","rights","consent_record","prompt","seed"):
        require(key in provenance and provenance[key] is not None,f"Missing provenance: {key}")
    for key in ("model_id","model_license","rights","consent_record","prompt"):
        require(isinstance(provenance[key],str) and provenance[key].strip(),"Incomplete provenance: "+key)
    require(isinstance(provenance["seed"],int) and not isinstance(provenance["seed"],bool),"Seed must be integer")
    # User/project owner must provide consent evidence; it cannot be self-certified by the AI.
    image=local_asset(base,provenance["input_image"])
    require(image.suffix.lower() in (".png",".jpg",".jpeg",".webp"),"Reference must be a local image")
    with Image.open(image) as pic:pic.verify()
    video=local_asset(base,clip)
    require(video.suffix.lower()==".mp4","Expected local MP4 from external neural backend")
    info=probe(video)
    stream=next((s for s in info.get("streams",[]) if s.get("codec_type")=="video"),None)
    require(stream is not None and stream.get("codec_name") in ("h264","hevc","av1","vp9"),
            "Unsupported or absent video stream")
    shot=project["shots"][shot_index]
    length=float(info["format"]["duration"])
    require(length+.04>=shot["end"]-shot["start"],"Clip is shorter than the shot")
    if provenance.get("input_image_sha256"):
        require(provenance["input_image_sha256"]==sha256(image),"Reference image changed")
    if provenance.get("checkpoint_sha256"):
        require(isinstance(provenance["checkpoint_sha256"],str) and len(provenance["checkpoint_sha256"])==64,
                "Invalid checkpoint digest")
    digest=sha256(video)
    dest="assets/generated-"+digest[:20]+".mp4"
    target=base/dest
    require(target.resolve().is_relative_to(base),"Output escapes project")
    copy_project=copy.deepcopy(project)
    original=copy_project["shots"][shot_index]
    # The source image stays traceable but is no longer the shot media.
    original["source_still"]=original.get("asset")
    original["kind"]="video"
    original["asset"]=dest
    original["in"]=0
    copy_project.setdefault("assets",{})[dest]={
        "origin":"External neural I2V generation: "+provenance["model_id"],
        "rights":provenance["rights"],"sha256":digest,
        "model_license":provenance["model_license"],
        "consent_record":provenance["consent_record"],
        "reference_image":provenance["input_image"],"reference_sha256":sha256(image),
        "generation":{"model_id":provenance["model_id"],"prompt":provenance["prompt"],
                      "seed":provenance["seed"],"checkpoint_sha256":provenance.get("checkpoint_sha256")},
        "human_approved":False
    }
    # Editing any picture invalidates prior final editorial approvals.
    copy_project["reviews"]={**copy_project.get("reviews",{}),
        "picture":{"approved":False,"reviewer":"","at":""},
        "brand":{"approved":False,"reviewer":"","at":""},
        "rights":{"approved":False,"reviewer":"","at":""}}
    created=False
    try:
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent,prefix=".generated_",suffix=".mp4",delete=False) as tmp:
                temp=Path(tmp.name)
            try:
                shutil.copyfile(video,temp)
                require(sha256(temp)==digest,"Copy verification failed")
                os.replace(temp,target);created=True
            finally:temp.unlink(missing_ok=True)
        require(sha256(target)==digest,"Existing generated media hash mismatch")
        validate(copy_project,base,final=False)
        atomic_json(project_path,copy_project)
    except Exception:
        if created:target.unlink(missing_ok=True)
        raise
    return {"attached":True,"asset":dest,"sha256":digest,"shot_index":shot_index,
            "reference_image_sha256":sha256(image),"requires_editorial_review":True,
            "neural_backend_executed_here":False}
