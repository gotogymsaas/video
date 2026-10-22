"""QAF-like observational/decision value only where it beats strong baselines.
No synthetic quality claim or trained checkpoint is implied.
"""
from __future__ import annotations
import numpy as np

def qaf_applicability(qaf_quality, baseline_quality, qaf_cost, baseline_cost,
                      max_cost, ood_passed, min_pairs=10, seed=22, min_gain=0.0):
    q=np.asarray(qaf_quality,dtype=float); b=np.asarray(baseline_quality,dtype=float)
    if q.shape!=b.shape or q.ndim!=1 or not np.isfinite(q).all() or not np.isfinite(b).all():
        raise ValueError("Paired finite quality measurements required")
    if not len(q): raise ValueError("No comparison samples")
    delta=q-b
    mean=float(delta.mean())
    if max(qaf_cost,baseline_cost)>max_cost:
        region="Computational-breakdown"
    elif len(q)<min_pairs:
        region="Insufficient-evidence"
    elif not ood_passed:
        region="Insufficient-evidence"
    else:
        rng=np.random.default_rng(seed)
        boots=np.mean(rng.choice(delta,size=(500,len(delta)),replace=True),axis=1)
        low,hi=np.quantile(boots,[.025,.975])
        if low>min_gain:region="QAF-positive"
        elif hi<0:region="Classical-positive"
        else:region="Non-identifiable"
    return {"region":region,"paired_cases":len(q),"delta_quality":mean,
            "quality_units":"caller-defined, identical for both methods",
            "warning":"No benefit can be asserted without an appropriate blinded OOD benchmark",
            "hard_budget_passed":bool(max(qaf_cost,baseline_cost)<=max_cost),
            "ood_passed":bool(ood_passed)}
