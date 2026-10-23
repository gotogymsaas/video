"""Minimal integrity readout for 24-paper external-validation registry."""
from __future__ import annotations
import json
from pathlib import Path

def read_registry(root):
    r=Path(root).resolve()
    path=r/"docs/generative_research/open_science/research_registry.json"
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema")!="qaf_cinematic_open_science_registry_v1":
        raise ValueError("Wrong registry schema")
    papers=doc.get("studies",[])
    expected={f"{i:02}{v}" for i in range(1,13) for v in "AB"}
    ids=[s.get("id") for s in papers]
    if len(ids)!=24 or len(set(ids))!=24 or set(ids)!=expected:
        raise ValueError("Incomplete or duplicate research study")
    for study in papers:
        if not (r/study["source"]).is_file():
            raise ValueError("Missing original study: "+study["id"])
        if not study["baseline"] or not study["primary_metric"]:
            raise ValueError("Missing independent baseline/metric")
        if study.get("status") not in ("NOT_EVALUATED","RESEARCH_ONLY","INDEPENDENTLY_VALIDATED"):
            raise ValueError("Unknown status")
        if study.get("status")=="INDEPENDENTLY_VALIDATED":
            raise ValueError("Human external validation cannot be self-certified in this registry")
    return {"schema":"qaf_open_science_coverage_report_v1","registered":len(papers),
            "paper_sources_present":24,"independently_validated":0,
            "real_cinematic_superiority_demonstrated":False,
            "comment":"Registry is a prospective protocol; tests need real data, reviewers and audit artifacts"}

def main():
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument("repo",nargs="?",default=".")
    a=p.parse_args()
    print(json.dumps(read_registry(a.repo),indent=2))
if __name__=="__main__":main()
