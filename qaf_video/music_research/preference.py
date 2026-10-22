"""M01: dated references and a contextual, normalized candidate decision."""
from datetime import date
import numpy as np
from ..quality import select

FEATURES = ('energy', 'syncopation', 'brightness', 'density', 'warmth')

def vector(values):
    a=np.asarray(values,dtype=float)
    if a.shape!=(5,) or not np.isfinite(a).all() or np.any((a<0)|(a>1)):
        raise ValueError('Expected five finite features in [0,1]')
    return a

def target(references, as_of, half_life_days=90.):
    """Ratings/features are curator observations; freshness is not popularity."""
    today=date.fromisoformat(as_of)
    if not np.isfinite(half_life_days) or half_life_days<=0 or not 1<=len(references)<=10000:
        raise ValueError('Invalid references or half-life')
    rows=[];weights=[]
    for r in references:
        age=(today-date.fromisoformat(r['observed_at'])).days
        confidence=float(r['confidence'])
        if age<0 or not np.isfinite(confidence) or not 0<confidence<=1:
            raise ValueError('Future reference or invalid confidence')
        rows.append(vector(r['features']));weights.append(confidence*2**(-age/half_life_days))
    w=np.asarray(weights)
    if w.sum()<=0:raise ValueError('No usable references')
    return {'features':np.average(rows,axis=0,weights=w).tolist(), 'weights':(w/w.sum()).tolist(),
            'as_of':as_of,'scope':'curated reference centroid; no automatic trend discovery'}

def choose(candidates, desired, importance=None, relation_weight=.35):
    d=vector(desired);w=vector(importance if importance is not None else [1]*5)
    if w.sum()==0 or not np.isfinite(relation_weight) or relation_weight<0:
        raise ValueError('Invalid weights')
    if not 1<=len(candidates)<=256:raise ValueError('Invalid candidate count')
    alternatives=[]
    for c in candidates:
        z=vector(c['features'])
        local=float(np.sum(w*(z-d)**2)/w.sum())
        # Context interaction: energy x density. The classical control sees it too.
        relational=float((z[0]*z[3]-d[0]*d[3])**2)
        alternatives.append({**c,'local_loss':local,'relational_loss':relational,
                             'loss':local+relation_weight*relational,
                             'feasible':c.get('feasible',False) is True})
    result=select(alternatives)
    result['feature_order']=list(FEATURES)
    result['incremental_advantage_claimed']=False
    return result
