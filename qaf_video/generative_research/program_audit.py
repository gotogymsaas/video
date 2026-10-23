"""Fail-closed coverage and evidence audit for the 24-paper QAF cinema programme.

Documentation completeness must never be confused with peer-reviewed evidence,
trained cinematographic weights, benchmark success or legal approval.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

PAPERS = tuple(f"{domain:02d}{variant}" for domain in range(1,13) for variant in "AB")
SCHEMA="qaf_cinematic_evidence_v1"
REQUIRED = ("checkpoint","dataset_manifest","evaluation_report",
            "hardware_report","human_review")
CHECKPOINT_EXCLUDE={"synthetic_smoke_only","toy","warp_fixture"}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as file:
        for data in iter(lambda:file.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def _safe_artifact(root,entry):
    if not isinstance(entry,dict):return False
    name=entry.get("path");sha=entry.get("sha256")
    if not isinstance(name,str) or not name or not isinstance(sha,str) or len(sha)!=64:
        return False
    base=root.resolve()
    path=(base/name).resolve()
    if not path.is_relative_to(base) or not path.is_file():return False
    return digest(path)==sha

def audit_program(repository_root, evidence_file=None):
    root=Path(repository_root).resolve()
    path=root/"docs/generative_research/foundation_24"
    found={p.name[:3] for p in path.glob("*.md") if p.name[:3] in PAPERS}
    missing=sorted(set(PAPERS)-found)
    system={
        "foundation_prototype":(root/"qaf_video/generative_research/cinema_neural.py").is_file(),
        "dataset_gate":(root/"qaf_video/generative_research/training_readiness.py").is_file(),
        "video_ingest":(root/"qaf_video/generative_research/production_bridge.py").is_file(),
        "applicability_gate":(root/"qaf_video/generative_research/applicability.py").is_file(),
    }
    evidence_checks={k:False for k in REQUIRED}
    observed=0
    reasons=[]
    if evidence_file is None:
        reasons.append("No independent real-video evaluation dossier supplied")
    else:
        f=Path(evidence_file).resolve()
        # Human-facing reports are inspected, not generated from local test fixtures.
        if not f.is_file():
            reasons.append("Evaluation dossier missing")
        else:
            evidence=json.loads(f.read_text(encoding="utf-8"))
            if evidence.get("schema")!=SCHEMA:
                reasons.append("Unsupported evidence schema")
            elif evidence.get("dataset_origin")=="synthetic" or evidence.get("model_type") in CHECKPOINT_EXCLUDE:
                reasons.append("Synthetic/toy checkpoint cannot validate a cinematic model")
            else:
                evidence_checks={k:_safe_artifact(root,evidence.get(k)) for k in REQUIRED}
                if not all(evidence_checks.values()):reasons.append("Missing artifact or checksum mismatch")
                if evidence.get("real_video_training") is not True:
                    reasons.append("No proof of authorized real-video training")
                if evidence.get("ood_evaluation") is not True:
                    reasons.append("Out-of-distribution evaluation missing")
                if evidence.get("matched_budget_baseline") is not True:
                    reasons.append("No strong same-budget classical baseline")
                if evidence.get("reviewer_approved") is not True:
                    reasons.append("Human review incomplete")
                # Avoid inferring that papers were scientifically validated from a generic model score.
                validated=evidence.get("validated_papers",[])
                if isinstance(validated,list):
                    observed=len(set(validated).intersection(PAPERS))
    return {
        "schema":"qaf_cinematic_program_audit_v1",
        "scientific_papers_expected":24,
        "documented_papers":len(found),
        "missing_documentation":missing,
        "empirical_validated_papers_claimed":observed,
        "software_gates":system,
        "evidence_checks":evidence_checks,
        "documented_complete":not missing,
        "claimed_evidence_record_complete":bool(not reasons and observed==24 and all(evidence_checks.values())),
        "program_100_percent_verified":False,
        "independent_verification_required":True,
        "limitations":"This is an integrity audit, not independent certification of video quality",
        "blocked_reasons":reasons if reasons else ([] if observed==24 else ["Fewer than 24 paper-specific validations recorded"]),
    }

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("repo",nargs="?",default=".")
    p.add_argument("--evidence")
    p.add_argument("--output")
    args=p.parse_args()
    value=audit_program(args.repo,args.evidence)
    content=json.dumps(value,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(content+"\n",encoding="utf-8")
    print(content)

if __name__=="__main__":main()
