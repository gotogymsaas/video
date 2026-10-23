"""Inspectable QAF relational planner over cinematic action alternatives.

A transparent discrete solver; this is NOT a quantum device, neural generator
or a demonstrated improvement over dynamic programming/MILP baselines.
"""
from __future__ import annotations
import json,math
from pathlib import Path
from ..core import require,sha256

def _check(data):
    require(data.get("schema")=="qaf_cinema_scene_decisions_v1","Bad scene schema")
    scenes=data.get("scenes")
    require(isinstance(scenes,list) and 1<=len(scenes)<=32,"Invalid scene count")
    for scene in scenes:
        candidates=scene.get("candidates",[])
        require(isinstance(candidates,list) and 1<=len(candidates)<=12,"Missing shots")
        names=set()
        for c in candidates:
            key=c.get("id")
            require(isinstance(key,str) and key not in names,"Invalid candidate id")
            names.add(key)
            for name in ("action_error","identity_error","occlusion_error","compute_cost"):
                val=c.get(name)
                require(type(val) in (int,float) and math.isfinite(val) and 0<=val<=100,"Bad cost")
            require(c.get("privacy_cleared") is True and c.get("rights_cleared") is True,
                    "No candidate without human rights/privacy clearance")
    return scenes

def _local_cost(candidate,weights):
    return sum(float(weights[k])*float(candidate[k]) for k in weights)

def choose_shots(data):
    """Exact Bellman dynamic programming with relational identity continuity."""
    scenes=_check(data)
    weights=data.get("weights",{"action_error":1.0,"identity_error":1.0,
        "occlusion_error":1.0,"compute_cost":0.25})
    require(set(weights)=={"action_error","identity_error","occlusion_error","compute_cost"},"Weights mismatch")
    require(all(type(v) in (int,float) and 0<=v<=10 and math.isfinite(v) for v in weights.values()),"Invalid weight")
    penalty=data.get("identity_switch_penalty",2.0)
    require(type(penalty) in (int,float) and 0<=penalty<=100,"Invalid continuity penalty")
    previous=None
    for scene in scenes:
        current={}
        for c in scene["candidates"]:
            basic=_local_cost(c,weights)
            if previous is None:
                current[c["id"]]=(basic,[c["id"]],str(c.get("actor_ref","")))
            else:
                choices=[]
                for score,seq,actor in previous.values():
                    continuity=penalty if actor!=str(c.get("actor_ref","")) else 0.0
                    choices.append((basic+score+continuity,seq+[c["id"]],str(c.get("actor_ref",""))))
                current[c["id"]]=min(choices,key=lambda x:(x[0],x[1]))
        previous=current
    best=min(previous.values(),key=lambda x:(x[0],x[1]))
    greedy=[];actor=None;greedy_score=0
    for scene in scenes:
        cand=min(scene["candidates"],key=lambda c:(_local_cost(c,weights),c["id"]))
        greedy_score+=_local_cost(cand,weights)+(penalty if actor is not None and actor!=str(cand.get("actor_ref","")) else 0)
        greedy.append(cand["id"]);actor=str(cand.get("actor_ref",""))
    return {"schema":"qaf_scene_plan_report_v1","chosen_shots":best[1],
        "objective_cost":best[0],"greedy_baseline_shots":greedy,
        "greedy_baseline_cost":greedy_score,
        "solver":"exact_classical_dynamic_programming_with_relational_cost",
        "qaf_quantum_advantage_proven":False,
        "caution":"DP is a classical strong baseline; relational semantics do not demonstrate QAF outperforming a classical optimizer."}

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("scene_json");p.add_argument("--out",required=True)
    a=p.parse_args()
    input=Path(a.scene_json).resolve();res=choose_shots(json.loads(input.read_text(encoding="utf8")))
    res["scene_sha256"]=sha256(input)
    Path(a.out).write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
