"""Exact bounded QUBO selection. No stochastic/clinical prediction or tensor claim."""
from itertools import product
import math

MAX_CANDIDATES = 12

def solve(candidates, minutes, primary_key, previous_ids=()):
    if not candidates or len(candidates) > MAX_CANDIDATES:
        raise ValueError('candidate_budget_invalid')
    n = len(candidates)
    q = [[0.0] * n for _ in range(n)]
    # Versioned utility design, not fitted human outcome probabilities.
    for i, item in enumerate(candidates):
        q[i][i] = -4.0 - (2.0 if item['agent_key'] == primary_key else 0.0)
        q[i][i] += 1.0 if item['id'] in previous_ids else 0.0
        for j in range(i):
            q[j][i] = 2.0 if candidates[j]['kind'] == item['kind'] else -0.5
    def feasible(bits):
        chosen = [c for c, b in zip(candidates, bits) if b]
        return (1 <= len(chosen) <= 3 and sum(c['minutes'] for c in chosen) <= minutes
                and any(c['agent_key'] == primary_key for c in chosen))
    def energy(bits):
        return sum(q[i][j] * bits[i] * bits[j] for i in range(n) for j in range(i, n))
    choices = [(energy(bits), bits) for bits in product((0,1), repeat=n) if feasible(bits)]
    if not choices:
        return [], {'status':'infeasible','solver':'exact_enumeration','candidate_count':n}
    e, bits = min(choices)
    if not math.isfinite(e) or not feasible(bits):
        raise ValueError('invalid_solver_result')
    return [c for c,b in zip(candidates,bits) if b], {
        'status':'optimal_within_catalog','solver':'exact_enumeration',
        'formulation':'upper_triangular_qubo_with_external_hard_constraints',
        'objective_version':'football_educational_utility_v1','matrix':q,
        'selection':list(bits),'energy':e,'candidate_count':n,
        'evaluated_states':2**n,'feasible_states':len(choices),
        'constraints':{'max_minutes':minutes,'max_blocks':3,'primary_required':True},
        'clinical_probability':None,'tensor_dynamics_enabled':False,
    }

