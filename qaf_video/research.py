"""Explicit small-system models from manuscripts I, III and V.

These routines implement equations and validate their domains. They are not
trained audience models and cannot certify creativity or quantum advantage.
"""
from __future__ import annotations
import math
from statistics import NormalDist
import numpy as np
from .core import require


def robust_normalize(values, low, high, present):
    z,a,b=np.broadcast_arrays(np.asarray(values,float),np.asarray(low,float),np.asarray(high,float))
    mask=np.broadcast_to(np.asarray(present,bool),z.shape)
    require(np.isfinite(a).all() and np.isfinite(b).all() and (b>a).all(), 'Invalid fixed normalization bounds')
    require(np.isfinite(z[mask]).all(),'Nonfinite observed value')
    # Preserve the mask: absence is never silently assigned semantic zero.
    return {'values':np.where(mask,np.clip((np.where(mask,z,a)-a)/(b-a),0,1),0).tolist(),
            'present':mask.tolist()}


def density(probabilities,phases=None):
    p=np.asarray(probabilities,float)
    require(p.ndim==1 and p.size>0 and np.isfinite(p).all() and (p>=0).all() and p.sum()>0,'Invalid probabilities')
    phase=np.zeros_like(p) if phases is None else np.asarray(phases,float)
    require(phase.shape==p.shape and np.isfinite(phase).all(),'Invalid phases')
    psi=np.sqrt(p/p.sum())*np.exp(1j*phase)
    return np.outer(psi,psi.conj())


def validate_density(rho):
    r=np.asarray(rho,complex)
    require(r.ndim==2 and r.shape[0]==r.shape[1] and np.isfinite(r).all(),'Invalid density shape')
    require(np.allclose(r,r.conj().T,atol=1e-10) and np.linalg.eigvalsh(r).min()>=-1e-10 and
            abs(np.trace(r)-1)<1e-10,'Density must be Hermitian, positive and trace one')
    return r


def povm_read(rho,effects):
    r=validate_density(rho);es=[np.asarray(e,complex) for e in effects]
    require(bool(es) and all(e.shape==r.shape and np.isfinite(e).all() and
            np.allclose(e,e.conj().T) and np.linalg.eigvalsh(e).min()>=-1e-10 for e in es),'Invalid POVM effects')
    require(np.allclose(sum(es),np.eye(len(r)),atol=1e-10),'POVM must sum to identity')
    p=np.maximum(0,np.array([np.trace(e@r).real for e in es]));return (p/p.sum()).tolist()


def replan_event(previous,current,evidence_changed=False,new_constraint=False,threshold=.05):
    require(0<=threshold<=1,'Invalid trace-distance threshold')
    a=validate_density(previous);b=validate_density(current)
    if a.shape!=b.shape:
        return {'replan':True,'reason':'state_encoding_changed','trace_distance':None}
    distance=float(np.abs(np.linalg.eigvalsh(a-b)).sum()/2)
    return {'replan':bool(evidence_changed or new_constraint or distance>threshold),
            'trace_distance':distance,'evidence_invalidation':bool(evidence_changed),
            'new_constraint':bool(new_constraint),'threshold':threshold}


def allocate_samples(variances,importance,costs,budget,minimum=1,maximum=100000):
    """Neyman-type continuous allocation, floor then greedy integer refinement.

    The integer refinement is a transparent heuristic, not an optimality proof
    for unequal costs. Variances must come from independent pilot samples.
    """
    v,w,c=[np.asarray(a,float) for a in [variances,importance,costs]]
    require(v.ndim==1 and v.shape==w.shape==c.shape and len(v)>0,'Allocation vectors must match')
    require(np.isfinite(v).all() and np.isfinite(w).all() and np.isfinite(c).all() and
            (v>=0).all() and (w>=0).all() and (c>0).all(),'Invalid variance, importance or cost')
    require(isinstance(minimum,int) and isinstance(maximum,int) and 1<=minimum<=maximum<=1000000,'Invalid sample bounds')
    require(math.isfinite(budget) and budget>=float(c.sum()*minimum),'Budget below minimum sampling cost')
    remaining=budget-float(c.sum()*minimum);a=v*w
    scale=float(np.sqrt(a*c).sum())
    fractional=np.sqrt(a/c)*remaining/scale if scale>0 else np.zeros_like(a)
    n=np.minimum(maximum,minimum+np.floor(fractional).astype(int))
    # Large allocations are bounded by vector maxima and at most 100k refinements.
    for _ in range(100000):
        available=(n<maximum)&(c<=budget-float(n@c)+1e-10)
        gains=np.where(available,a/(n*(n+1)*c),-1.)
        j=int(np.argmax(gains))
        if gains[j]<=0:break
        n[j]+=1
    return {'samples':n.tolist(),'spent':float(n@c),'budget':budget,
            'expected_variance_proxy':float(np.sum(a/n)),
            'method':'continuous_square_root_plus_greedy_integer','global_integer_optimality':False}


def paired_sample_size(delta,sigma,alpha=.05,power=.8):
    require(delta>0 and sigma>0 and 0<alpha<1 and .5<power<1,'Invalid power-analysis assumptions')
    normal=NormalDist();n=((normal.inv_cdf(1-alpha/2)+normal.inv_cdf(power))*sigma/delta)**2
    return {'independent_pairs':math.ceil(n),'approximate':True,'alpha':alpha,'power':power,
            'delta':delta,'assumed_sigma_difference':sigma,
            'note':'Requires independent paired units and suitable distribution assumptions; not clustered ratings.'}
