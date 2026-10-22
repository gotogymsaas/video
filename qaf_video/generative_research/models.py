"""QAF Generative Video: 10 auditable mathematical reference models.
Author: Juan Manuel Goenaga / GoToGym Quantum Research, October 2026.
These are numerical research prototypes, NOT trained neural I2V models.
No graphics, face recognition, model weights or rights approval is claimed.
"""
from __future__ import annotations
import numpy as np
EPS=1e-9
def _a(value):
    x=np.asarray(value,dtype=float)
    if not np.isfinite(x).all(): raise ValueError('Only finite arrays are accepted')
    return x
def minimum_jerk(t):
    t=np.clip(_a(t),0,1)
    return 10*t**3-15*t**4+6*t**5

def m01_pose_motion(keypoints,times,nframes=24,edges=(),rigidity=.85):
    """Observed 2D poses -> interpolated skeleton; optional bone constraints."""
    P=_a(keypoints);times=_a(times)
    assert P.ndim==3 and P.shape[-1]==2 and len(P)==len(times)>=2 and np.all(np.diff(times)>0)
    target=np.linspace(times[0],times[-1],nframes)
    X=np.stack([np.interp(target,times,P[:,j,c]) for j in range(P.shape[1]) for c in range(2)],axis=-1).reshape(nframes,P.shape[1],2)
    for i,j in edges:
        L=np.median(np.linalg.norm(P[:,j]-P[:,i],axis=1))
        for t in range(nframes):
            d=X[t,j]-X[t,i]
            X[t,j]+=rigidity*(X[t,i]+L*d/max(np.linalg.norm(d),EPS)-X[t,j])
    jerk=np.diff(X,n=3,axis=0) if nframes>3 else np.zeros_like(X[:1])
    return {'trajectory':X,'jerk_rms':float(np.sqrt(np.mean(jerk**2)))}

def m02_cloth_step(x,v,edges,rests,mass=1.,dt=.01,k=2.,damping=.15,anchors=()):
    """Reference mass-spring cloth step with fixed anchor constraints."""
    X=_a(x);V=_a(v);E=np.asarray(edges,int);L=_a(rests)
    assert X.shape==V.shape and X.ndim==2 and X.shape[1]==3 and len(E)==len(L) and dt>0 and mass>0
    F=np.zeros_like(X);F[:,1]-=9.81*mass
    for (i,j),rest in zip(E,L):
        delta=X[j]-X[i]
        f=k*(np.linalg.norm(delta)-rest)*delta/max(np.linalg.norm(delta),EPS)
        F[i]+=f;F[j]-=f
    W=V+dt*(F/mass-damping*V);Y=X+dt*W
    for i in anchors:Y[i]=X[i];W[i]=0
    strain=np.mean([abs(np.linalg.norm(Y[j]-Y[i])-r)/max(r,EPS) for (i,j),r in zip(E,L)]) if len(E) else 0.
    return {'positions':Y,'velocities':W,'mean_strain':float(strain)}

def m03_scene_graph(boxes,labels,sigma=.35):
    """Spatial graph from externally supplied boxes; not a semantic detector."""
    B=_a(boxes)
    assert B.ndim==2 and B.shape[1]==4 and len(B)==len(labels)
    centers=np.column_stack(((B[:,0]+B[:,2])/2,(B[:,1]+B[:,3])/2))
    D=np.linalg.norm(centers[:,None]-centers[None,:],axis=2)
    affinity=np.exp(-D/max(sigma,EPS));np.fill_diagonal(affinity,0)
    relationships=[{'subject':labels[i],'object':labels[j],'spatial_confidence':float(affinity[i,j])} for i in range(len(B)) for j in range(len(B)) if i!=j]
    return {'affinity':affinity,'relations':relationships}

def m04_grounding(claims,evidence,reliability,contradiction=None):
    """Approximate logistic evidence model; scores do not certify truth."""
    E=_a(evidence);R=np.clip(_a(reliability),.001,.999)
    assert E.shape==(len(claims),len(R))
    logits=np.sum((2*E-1)*np.log(R/(1-R)),axis=1)
    p=1/(1+np.exp(-np.clip(logits,-30,30)))
    C=np.zeros((len(claims),len(claims))) if contradiction is None else _a(contradiction)
    assert C.shape==(len(claims),len(claims))
    contextual=np.clip(p-.2*(np.maximum(C,0)@p),0,1)
    return {'support':p,'contextual_support':contextual,'needs_review':contextual<.75}

def m05_latent_dynamics(image,flow=(1,0),steps=12,seed=22,noise=.035):
    """Deterministic warp fixture; NOT a trained diffusion/flow video generator."""
    I=_a(image);assert I.ndim==3 and steps>=2
    T=np.roll(I,shift=(int(flow[1]),int(flow[0])),axis=(0,1))
    N=np.random.default_rng(seed).normal(0,noise,I.shape)
    frames=[]
    for t in np.linspace(0,1,steps):
        s=float(minimum_jerk(t))
        frames.append(np.clip((1-s)*I+s*T+np.sin(np.pi*s)*N,0,1))
    return np.stack(frames)

def m06_keyframe_bridge(start,end,nframes=24):
    """Bidirectional keyframe interpolation reference; no neural inpainting."""
    A=_a(start);B=_a(end);assert A.shape==B.shape and A.ndim==3 and nframes>=4
    F=np.stack([np.clip((1-float(minimum_jerk(t)))*A+float(minimum_jerk(t))*B,0,1) for t in np.linspace(0,1,nframes)])
    return {'frames':F,'endpoint_mse':float(np.mean((F[-1]-B)**2)),
            'jerk_rms':float(np.sqrt(np.mean(np.diff(F,n=3,axis=0)**2)))}

def m07_identity_update(prototype,observation,confidence=.9,alpha=.2,threshold=.72):
    """Conservative EMA of externally computed identity descriptors."""
    p=_a(prototype).ravel();q=_a(observation).ravel();assert p.shape==q.shape
    p=p/max(np.linalg.norm(p),EPS);q=q/max(np.linalg.norm(q),EPS)
    score=float(np.dot(p,q));matched=score>=threshold
    step=alpha*np.clip(confidence,0,1) if matched else 0.
    z=(1-step)*p+step*q;z/=max(np.linalg.norm(z),EPS)
    return {'prototype':z,'cosine_similarity':score,'matched':bool(matched),'requires_review':not matched}

def m08_continuity_plan(node_cost,transition_cost,forbidden=None):
    """Exact dynamic programming baseline for local cross-shot constraints."""
    U=_a(node_cost);C=_a(transition_cost);T,K=U.shape
    assert C.shape==(T-1,K,K)
    bad=np.zeros_like(C,dtype=bool) if forbidden is None else np.asarray(forbidden,dtype=bool)
    dp=np.full((T,K),np.inf);prev=np.zeros((T,K),int);dp[0]=U[0]
    for t in range(1,T):
        edge=dp[t-1,:,None]+C[t-1]+np.where(bad[t-1],np.inf,0)
        dp[t]=U[t]+np.min(edge,axis=0);prev[t]=np.argmin(edge,axis=0)
    idx=int(np.argmin(dp[-1]));cost=float(dp[-1,idx]);path=[idx]
    for t in range(T-1,0,-1):
        idx=int(prev[t,idx]);path.append(idx)
    return {'path':path[::-1],'cost':cost,'feasible':bool(np.isfinite(cost))}

def m09_temporal_quality(frames):
    """Flicker and frame temporal differences; not a trained VQA judge."""
    F=_a(frames);assert F.ndim==4 and len(F)>=4
    Y=F[...,:3].mean(axis=-1)
    return {'global_flicker':float(np.mean(np.abs(np.diff(Y.mean(axis=(1,2)))))),
            'temporal_third_difference':float(np.mean(np.abs(np.diff(Y,n=3,axis=0)))),
            'mean_motion':float(np.mean(np.abs(np.diff(Y,axis=0))))}

def m10_release_gate(scores,costs,budget,hard_pass,weights):
    """Noncompensatory eligibility + utility; always requires human release."""
    S=_a(scores);C=_a(costs);W=_a(weights)
    assert S.ndim==2 and S.shape==(len(C),len(W))
    eligible=(C<=budget)&np.asarray(hard_pass,dtype=bool)
    utility=S@W
    selected=int(np.argmax(np.where(eligible,utility,-np.inf))) if np.any(eligible) else None
    return {'selected':selected,'scores':utility,'eligible':eligible,
            'abstain':selected is None,'requires_human_review':True}
