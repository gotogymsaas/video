"""Convert cleared QAF local dataset manifests into the OFFICIAL LTX Trainer format.

This only prepares JSON metadata. It does not download weights, copy private
media to the repository, invoke the trainer, or certify licenses.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from ..core import require,sha256
from .training_readiness import validate_dataset

def export_ltx25(manifest,output_dir,bucket="768x448x49",verify_media=True):
    root=Path(manifest).resolve().parent
    m=json.loads(Path(manifest).read_text(encoding="utf-8"))
    require(m.get("schema")=="qaf_cinematic_training_dataset_v1","Not a cleared QAF manifest")
    parts=bucket.lower().split("x")
    require(len(parts)==3 and all(x.isdigit() for x in parts),"Bucket expected WIDTHxHEIGHTxFRAMES")
    width,height,frames=map(int,parts)
    require(width%32==0 and height%32==0 and (frames-1)%8==0 and frames>=9,
            "Default LTX-2.5 bucket requires 32-spatial and 8n+1 temporal dimensions")
    # Cross-split identity/garment duplication, checksum and media-level gates.
    validation=validate_dataset(manifest,"ltx",verify_media=verify_media)
    require(validation["splits"]["train"]>0 and validation["splits"]["val"]>0,
            "Train/val required")
    target=Path(output_dir).resolve()
    require(target!=root and not root.is_relative_to(target),
            "Cannot export into ancestor of the private corpus")
    target.mkdir(parents=True,exist_ok=True)
    export={s:[] for s in ("train","val","test")};sources=[]
    for row in m["samples"]:
        require((row["training_frame_count"]-1)%8==0,
                "LTX clips use sampled 8n+1 frames")
        file=(root/row["video"]).resolve()
        require(file.is_relative_to(root) and file.is_file(),"Video outside private folder")
        # Absolute paths permitted by official preprocessor; all inputs remain local.
        export[row["split"]].append({"caption":row["prompt"],"video":str(file)})
        sources.append({"id":row["id"],"split":row["split"],"video_sha256":sha256(file)})
    filenames={}
    for split,records in export.items():
        if records:
            out=target/(split+".ltx.json")
            out.write_text(json.dumps(records,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            filenames[split]=str(out)
    report={"schema":"qaf_ltx_data_export_report_v1","model_family":"LTX-2.5",
            "bucket":bucket,"sample_counts":{key:len(v) for key,v in export.items()},
            "metadata_files":filenames,"checksums":sources,
            "source_manifest_sha256":sha256(manifest),"training_run_executed":False,
            "rights_legally_certified":False,
            "note":"Check split, caption truth, audio rights and actual GPU config before training"}
    (target/"export_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def prepare_ltx25_commands(trainer_dir,export_report,weights,gemma,video_vae,audio_vae,
                           license_review,low_vram=True):
    """Validate local resources and emit commands corresponding to official LTX docs.
    These commands are never executed by this function.
    """
    base=Path(trainer_dir).resolve()
    require((base/"scripts/process_dataset.py").is_file() and
            (base/"scripts/train.py").is_file(),"Official LTX trainer checkout not found")
    plan=json.loads(Path(export_report).read_text(encoding="utf-8"))
    require(plan.get("schema")=="qaf_ltx_data_export_report_v1","Bad LTX export")
    files={}
    for key,name in (("weights",weights),("gemma",gemma),("video_vae",video_vae),
                     ("audio_vae",audio_vae),("legal_review",license_review)):
        p=Path(name).resolve()
        require(p.is_file() and p.stat().st_size>0,"Missing "+key+" resource")
        files[key]=str(p)
    commands={}
    for split,meta in plan["metadata_files"].items():
        cmd=["uv","run","python","scripts/process_dataset.py",meta,
             "--resolution-buckets",plan["bucket"],
             "--model-path",files["weights"],
             "--text-encoder-path",files["gemma"],
             "--video-vae-path",files["video_vae"],
             "--audio-vae-path",files["audio_vae"]]
        commands[split]=cmd
    # Trainer configuration must be edited in official checkout and validated,
    # never silently invent unknown YAML keys or start costly GPU training.
    return {"schema":"qaf_ltx_training_preflight_v1","cwd":str(base),
            "preprocess_argv":commands,"example_train_config":
                "configs/i2v_lora.yaml" if not low_vram else "configs/i2v_lora.yaml (adapt official low-VRAM settings)",
            "train_argv":["uv","run","python","scripts/train.py","configs/i2v_lora.yaml"],
            "review_sha256":sha256(files["legal_review"]),"not_executed":True,
            "warnings":["Use official I2V config and matching Gemma 4",
                        "Verify CUDA 12.7+, Python 3.12+, VRAM 32GB minimum (80GB recommended)",
                        "Preprocessed text features are not portable across encoder versions",
                        "Modify config output_dir, data.preprocessed_data_root, and model component paths explicitly",
                        "Never put copyrighted footage, credentials or checkpoints into public GitHub"]}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("dataset");p.add_argument("--out",required=True)
    p.add_argument("--bucket",default="768x448x49")
    a=p.parse_args()
    print(json.dumps(export_ltx25(a.dataset,a.out,a.bucket),indent=2))

if __name__=="__main__":main()
