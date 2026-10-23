"""Reproducible, fail-closed QAF Cinema neural training and validation protocol.

Implements the orchestration and evidence gates for three research manuscripts.
Does not claim the model was trained unless a real signed run attestation
with compatible artifacts has been independently checked by an operator.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,subprocess
from pathlib import Path
from ..core import require,sha256

SCHEMA="qaf_neural_program_v1"
PHASES=("DATA_READY","MODEL_READY","GPU_READY","TRAINED","BENCHMARKED","REPLICATED","APPROVED")
def inside(root,rel):
    root=Path(root).resolve()
    require(isinstance(rel,str) and bool(rel),"Required workspace path")
    p=(root/rel).resolve()
    require(p.is_relative_to(root) and p.is_file(),"Missing or unsafe local resource: "+rel)
    return p
def plan_program(manifest_path,workspace):
    """Generate verifiable training plan, NEVER launch GPU or download weights."""
    root=Path(workspace).resolve()
    path=inside(root,str(manifest_path))
    plan=json.loads(path.read_text(encoding="utf8"))
    require(plan.get("schema")==SCHEMA,"Unknown research program")
    data=inside(root,plan.get("dataset_manifest"))
    ds=json.loads(data.read_text(encoding="utf8"))
    require(ds.get("schema")=="qaf_cinematic_training_dataset_v1","Uncleared dataset format")
    samples=ds.get("samples",[])
    require(isinstance(samples,list) and len(samples)>=2,"Need dataset examples")
    per={"train":0,"val":0,"test":0};subjects={};garments={};clips=set()
    for row in samples:
        split=row.get("split")
        require(split in per,"Invalid holdout split")
        per[split]+=1
        for attr,index in (("subject_id",subjects),("garment_id",garments)):
            val=row.get(attr)
            require(isinstance(val,str) and val,"Missing actor/garment grouping")
            require(val not in index or index[val]==split,"Data leakage across splits")
            index[val]=split
        video=inside(data.parent,row.get("video"))
        digest=sha256(video);require(digest not in clips,"Duplicate video leakage")
        clips.add(digest)
        require(isinstance(row.get("prompt"),str) and row["prompt"].strip(),"Caption missing")
        require(isinstance(row.get("rights"),str) and bool(row["rights"].strip()),"Rights record missing")
        require(isinstance(row.get("consent_record"),str) and bool(row["consent_record"].strip()),"Consent evidence reference missing")
    require(per["train"]>=1 and per["val"]>=1 and per["test"]>=1,"Train/val/test all required")
    review=inside(root,plan.get("legal_review"))
    require(review.stat().st_size>0,"Legal review empty")
    models=plan.get("model_files",{})
    for key in ("transformer","text_encoder","video_vae"):
        inside(root,models.get(key))
    trainer_dir=(root/plan.get("trainer_dir","")).resolve()
    require(trainer_dir.is_relative_to(root) and (trainer_dir/"scripts/train.py").is_file() and
            (trainer_dir/"scripts/process_dataset.py").is_file(),"Official LTX trainer not present")
    trainer_config=inside(root,plan.get("trainer_config"))
    require(trainer_config.suffix in (".yaml",".yml"),"Training YAML required")
    budget=plan.get("max_gpu_hours")
    require(type(budget) in (int,float) and math.isfinite(budget) and 0<budget<=1000,
            "Explicit finite budget needed")
    require(plan.get("backbone")=="LTX-2.5" and plan.get("training_mode")=="i2v_lora",
            "Only reviewed LTX-2.5 I2V LoRA protocol supported")
    require(plan.get("approved_to_train") is True,"Operator training approval required")
    details={"schema":"qaf_neural_program_plan_v1","program_sha256":sha256(path),
      "dataset_sha256":sha256(data),"review_sha256":sha256(review),
      "trainer_config_sha256":sha256(trainer_config),
      "model_hashes":{key:sha256(inside(root,models[key])) for key in ("transformer","text_encoder","video_vae")},
      "split_counts":per,"max_gpu_hours":budget,"backbone":"LTX-2.5",
      "training_mode":"i2v_lora","training_performed":False,"quality_claims_verified":False,
      "gpu_hardware_verified":False,
      "preflight_argv":["uv","run","python","scripts/train.py",str(trainer_config)],
      "cwd":str(trainer_dir),"next_step":"Verify official trainer config and available CUDA/GPU independently"}
    return details

def compare_matched_trials(manifest,root):
    """Make strict scene/seed/backend-matched evidence readout from HUMAN SCORES.

    No invented scores or automatic assertion of QAF causal superiority.
    """
    root=Path(root).resolve()
    path=inside(root,str(manifest))
    doc=json.loads(path.read_text(encoding="utf8"))
    require(doc.get("schema")=="qaf_cinema_matched_trials_v1","Invalid benchmark")
    trials=doc.get("trials",[])
    require(isinstance(trials,list) and len(trials)>=2,"Paired trials required")
    diffs=[];ids=set()
    for row in trials:
        ident=row.get("id");require(isinstance(ident,str) and ident not in ids,"Duplicate trial")
        ids.add(ident)
        require(type(row.get("seed"))==int and row.get("same_backbone") is True and
                row.get("same_compute_budget") is True and row.get("blind_review") is True,
                "Matched conditions and human blinding required")
        for side in ("qaf","baseline"):
            entry=row.get(side,{})
            inside(root,entry.get("video"))
            score=entry.get("human_score")
            require(type(score) in (int,float) and math.isfinite(score) and 0<=score<=10,
                    "Actual bounded human score required")
        diffs.append(float(row["qaf"]["human_score"]-row["baseline"]["human_score"]))
    import numpy as np
    vals=np.asarray(diffs)
    rng=np.random.default_rng(20261023)
    boot=rng.choice(vals,(1000,len(vals)),replace=True).mean(axis=1)
    ci=[float(x) for x in np.quantile(boot,[.025,.975])]
    return {"schema":"qaf_cinema_matched_report_v1","pairs":len(vals),
        "delta_mean":float(vals.mean()),"bootstrap_ci95":ci,
        "real_video_pairs_present":True,
        "independent_reviewer_identity_verified":False,
        "independent_replication_verified":False,
        "qaf_superiority_proven":False,
        "note":"Scores are user-supplied; an independent auditor must validate raters, grouping, weights and quality metrics."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["plan","compare"])
    ap.add_argument("manifest")
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    data=plan_program(a.manifest,a.workspace) if a.mode=="plan" else compare_matched_trials(a.manifest,a.workspace)
    dest=Path(a.out).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
