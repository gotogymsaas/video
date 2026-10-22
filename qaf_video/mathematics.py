"""Camera control, small-system MPS/TDVP and constrained quadratic planning.
The tensor engine is a bounded research reference, not a GPU renderer or
an assertion of quantum/computational advantage.
"""
from __future__ import annotations
import itertools,math
from dataclasses import dataclass
import numpy as np
from .core import require,finite

def minimum_jerk(u):
    u=np.clip(u,0,1);return 10*u**3-15*u**4+6*u**5

def camera_position(start,end,t,seconds):
    require(seconds>0,'Camera duration must be positive')
    return np.asarray(start)+(np.asarray(end)-start)*minimum_jerk(t/seconds)

def slerp(a,b,u):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    require(a.shape==(4,) and b.shape==(4,) and np.linalg.norm(a)>0 and np.linalg.norm(b)>0,'Invalid quaternion')
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    if a@b<0:b=-b
    dot=np.clip(a@b,-1,1);u=float(minimum_jerk(u))
    if dot>.9995:q=a+u*(b-a)
    else:
        theta=np.arccos(dot);q=(np.sin((1-u)*theta)*a+np.sin(u*theta)*b)/np.sin(theta)
    return q/np.linalg.norm(q)

@dataclass
class MPS:
    tensors:list
    discarded_weight:float=0.
    @classmethod
    def from_dense(cls,psi,chi=4):
        psi=np.asarray(psi,dtype=complex).reshape(-1);k=int(round(np.log2(len(psi))))
        require(1<=k<=8 and len(psi)==2**k,'Reference MPS supports 1–8 binary sites')
        require(isinstance(chi,int) and 1<=chi<=32,'chi must be 1–32')
        require(np.all(np.isfinite(psi)) and np.linalg.norm(psi)>0,'Invalid state')
        psi=psi/np.linalg.norm(psi);a=[];left=1;v=psi;discard=0.
        for _ in range(k-1):
            u,s,vh=np.linalg.svd(v.reshape(left*2,-1),full_matrices=False);rank=min(chi,len(s))
            discard+=float(np.sum(s[rank:]**2));a.append(u[:,:rank].reshape(left,2,rank));v=s[:rank,None]*vh[:rank];left=rank
        a.append(v.reshape(left,2,1));obj=cls(a,discard)
        norm=np.sqrt(np.trace(obj.rdm([0])).real);obj.tensors[0]/=norm
        return obj
    def dense(self):
        out=self.tensors[0]
        for t in self.tensors[1:]:out=np.tensordot(out,t,axes=(-1,0))
        return out.reshape(-1)
    def rdm(self,sites):
        require(list(sites)==sorted(set(sites)) and all(0<=s<len(self.tensors) for s in sites),'Sites must be sorted, unique and valid')
        result=np.zeros((2**len(sites),)*2,dtype=complex)
        for ket in itertools.product(range(2),repeat=len(sites)):
            for bra in itertools.product(range(2),repeat=len(sites)):
                env=np.ones((1,1),dtype=complex)
                for i,a in enumerate(self.tensors):
                    if i in sites:
                        j=sites.index(i);env=np.einsum('lm,lr,mq->rq',env,a[:,ket[j],:],a[:,bra[j],:].conj())
                    else:env=np.einsum('lm,lsr,msq->rq',env,a,a.conj())
                ki=sum(v*2**(len(ket)-j-1) for j,v in enumerate(ket));bi=sum(v*2**(len(bra)-j-1) for j,v in enumerate(bra));result[ki,bi]=env[0,0]
        return result
    def jacobian(self):
        require(len(self.tensors)<=6,'Explicit tangent reference supports at most 6 sites')
        columns=[]
        for i,a in enumerate(self.tensors):
            for index in np.ndindex(a.shape):
                ts=list(self.tensors);basis=np.zeros_like(a);basis[index]=1;ts[i]=basis
                columns.append(MPS(ts).dense())
        return np.column_stack(columns)
    def tdvp(self,H,dt,chi=4):
        require(finite(dt) and 0<dt<=.25,'Reference TDVP step must be in (0,.25]')
        H=np.asarray(H,dtype=complex);d=2**len(self.tensors)
        require(H.shape==(d,d) and np.allclose(H,H.conj().T),'Hamiltonian must be Hermitian and match state')
        def velocity(obj):
            v=np.linalg.lstsq(obj.jacobian(),-1j*H@obj.dense(),rcond=1e-10)[0];out=[];offset=0
            for a in obj.tensors:out.append(v[offset:offset+a.size].reshape(a.shape));offset+=a.size
            return out
        first=velocity(self);mid=MPS([a+.5*dt*v for a,v in zip(self.tensors,first)]);second=velocity(mid)
        proposed=MPS([a+dt*v for a,v in zip(self.tensors,second)]).dense()
        return MPS.from_dense(proposed,chi)

def coherence_feature(rho,epsilon=1e-10):
    rho=np.asarray(rho);den=float((rho[0,0].real*rho[-1,-1].real)**.5)
    if den<epsilon:return {'available':False,'reason':'insufficient_population'}
    z=rho[0,-1]/den;return {'available':True,'real':float(z.real),'imag':float(z.imag),'magnitude':float(abs(z))}

def compile_qubo(linear,pairwise,groups,budget=None,costs=None):
    """Upper triangular QUBO including one-hot and integer budget slack."""
    q=np.asarray(linear,dtype=float);n=len(q)
    require(np.isfinite(q).all(),'Nonfinite utility')
    require(sorted(i for g in groups for i in g)==list(range(n)),'Groups must partition decisions')
    pairwise={(int(i),int(j)):float(v) for (i,j),v in pairwise.items()}
    require(all(0<=i<j<n and finite(v) for (i,j),v in pairwise.items()),'Invalid pairwise coefficient')
    bound=float(np.abs(q).sum()+sum(abs(v) for v in pairwise.values()));lam=2*bound+1
    weights=[]
    if budget is not None:
        require(isinstance(budget,int) and budget>=0 and costs is not None and len(costs)==n,'Invalid budget')
        require(all(isinstance(c,int) and c>=0 for c in costs),'Costs must be nonnegative integers')
        weights=[2**b for b in range(math.ceil(math.log2(budget+1)))] if budget else []
    U=np.zeros((n+len(weights),)*2);np.fill_diagonal(U[:n,:n],q);constant=0.
    for (i,j),v in pairwise.items():U[i,j]+=v
    def square(indices,values,target):
        nonlocal constant
        constant+=lam*target*target
        for a,(i,wi) in enumerate(zip(indices,values)):
            U[i,i]+=lam*(wi*wi-2*target*wi)
            for j,wj in list(zip(indices,values))[a+1:]:U[min(i,j),max(i,j)]+=2*lam*wi*wj
    for g in groups:square(g,[1]*len(g),1)
    if budget is not None:square(list(range(len(U))),list(costs)+weights,budget)
    return {'matrix':U.tolist(),'offset':constant,'penalty':lam,'decision_variables':n,'slack_weights':weights,'convention':'upper_triangular'}

def solve_choices(choices,pairwise=None,budget=None,limit=1000000):
    """Exact native constrained baseline, with the identical QUBO as audit output."""
    require(choices and all(g for g in choices),'Empty choices')
    count=math.prod(len(g) for g in choices);require(count<=limit,'Choice enumeration limit exceeded; use an external solver')
    flat=[x for g in choices for x in g];groups=[];n=0
    for g in choices:groups.append(list(range(n,n+len(g))));n+=len(g)
    pairs={(int(i),int(j)):v for i,j,v in (pairwise or [])}
    linear=[-float(v['utility']) for v in flat];costs=[v.get('cost',0) for v in flat]
    qubo=compile_qubo(linear,pairs,groups,budget,costs)
    best=None
    for selected in itertools.product(*groups):
        if budget is not None and sum(costs[i] for i in selected)>budget:continue
        value=sum(linear[i] for i in selected)+sum(v for (i,j),v in pairs.items() if i in selected and j in selected)
        if best is None or value<best[0]:best=(value,selected)
    require(best is not None,'No feasible plan')
    return {'solver':'exact_native_enumeration','objective':best[0],'selected_indices':list(best[1]),'selected':[flat[i] for i in best[1]],'candidate_plans':count,'qubo':qubo,'qaf_superiority_claim':False}
