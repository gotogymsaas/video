"""Constrained shot alternatives and reproducible small-system benchmarks."""
from __future__ import annotations
import time
import numpy as np
from .core import load, require
from .mathematics import MPS, solve_choices, coherence_feature


def plan_project(project, budget=None):
    m=load(project)
    # Selection only changes editorial motion alternatives, never claim wording.
    choices=[]
    for i,s in enumerate(m['shots']):
        choices.append([{'shot':i,'option':'locked','utility':1.,'cost':0,'zoom':[1.,1.]},
                        {'shot':i,'option':'minimum_jerk_push','utility':1.4 if i%2==0 else 1.1,
                         'cost':1,'zoom':[1.,1.08]}])
    pairs=[]
    for i in range(len(choices)-1):pairs.append((2*i+1,2*(i+1)+1,.5))
    result=solve_choices(choices,pairs,budget if budget is not None else (len(choices)+1)//2)
    result.update({'scope':'editorial camera alternatives only',
                   'evidence_gate':'Source project validated before planning; wording unchanged',
                   'automatic_apply':False,'utility_weights':'illustrative editorial weights; calibrate with reviewers'})
    return result


def benchmark(seed=22):
    rng=np.random.default_rng(seed);started=time.perf_counter();k=3
    psi=rng.normal(size=2**k)+1j*rng.normal(size=2**k);psi/=np.linalg.norm(psi)
    state=MPS.from_dense(psi,chi=4)
    dense=psi.reshape(2,-1);rho=dense@dense.conj().T;local=state.rdm([0])
    raw=rng.normal(size=(8,8))+1j*rng.normal(size=(8,8));H=(raw+raw.conj().T)/8
    values,vectors=np.linalg.eigh(H);errors=[]
    for dt in [.04,.02,.01]:
        exact=vectors@(np.exp(-1j*dt*values)*(vectors.conj().T@psi))
        trial=state.tdvp(H,dt,chi=4).dense()
        errors.append({'dt':dt,'state_l2_error':float(np.linalg.norm(trial-exact))})
    plan=solve_choices([[{'name':'A','utility':2,'cost':2},{'name':'B','utility':1,'cost':1}],
                        [{'name':'C','utility':3,'cost':2},{'name':'D','utility':1,'cost':0}]],budget=3)
    local_error=float(np.max(np.abs(local-rho)))
    require(local_error<1e-10 and errors[-1]['state_l2_error']<errors[0]['state_l2_error'],
            'Mathematical reference benchmark failed')
    from .research import density,povm_read,replan_event,allocate_samples,paired_sample_size
    base=density([.5,.5]);phase=density([.5,.5],[0,np.pi]);effects=[base,phase]
    return {'seed':seed,'sites':k,'chi':4,'local_rdm_max_error':local_error,
            'tdvp_reference':errors,'classical_exact_reference':'Hermitian eigendecomposition; same H and initial state',
            'qubo_selected':[v['name'] for v in plan['selected']],
            'coherence_fixture':coherence_feature(rho),
            'povm_phase_fixture':{'plus':povm_read(base,effects),'minus':povm_read(phase,effects)},
            'evidence_event_fixture':replan_event(base,base,evidence_changed=True),
            'sampling_advisor_fixture':allocate_samples([1,9],[1,1],[1,1],100),
            'power_example':paired_sample_size(.4,.8),'wall_seconds':time.perf_counter()-started,
            'scope':'small-system numerical smoke benchmark; no claim of production speed or perceptual superiority',
            'qaf_superiority_claim':False}
