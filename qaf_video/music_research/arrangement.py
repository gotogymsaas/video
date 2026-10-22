"""M03: joint beat-grid cue placement via dynamic programming."""
import math
import numpy as np

ENERGY=(.42,.62,.90,.55)

def align(cues, seconds=60., bpm=124., phase=0., tolerance=.22, gap=.25):
    vals=[seconds,bpm,phase,tolerance,gap,*cues]
    if not all(math.isfinite(x) for x in vals) or not 0<seconds<=600 or not 60<=bpm<=200:
        raise ValueError('Invalid timing')
    if not 0<=phase<60/bpm or not 0<=tolerance<=1 or gap<=0 or not 1<=len(cues)<=64:
        raise ValueError('Invalid phase, tolerance, gap or cues')
    if any(c<=0 or c>=seconds for c in cues) or any(b<=a for a,b in zip(cues,cues[1:])):
        raise ValueError('Cues must be strictly increasing inside duration')
    grid=np.arange(phase,seconds,60/bpm)
    sets=[grid[np.abs(grid-c)<=tolerance+1e-9] for c in cues]
    if any(len(a)==0 for a in sets):raise ValueError('No beat within cue tolerance')
    costs=(sets[0]-cues[0])**2;links=[]
    for i in range(1,len(cues)):
        matrix=costs[:,None]+(sets[i][None,:]-cues[i])**2
        matrix[sets[i][None,:]-sets[i-1][:,None]<gap]=np.inf
        parent=np.argmin(matrix,axis=0);costs=matrix[parent,np.arange(len(sets[i]))]
        links.append(parent)
    j=int(np.argmin(costs))
    if not np.isfinite(costs[j]):raise ValueError('No ordered feasible cue sequence')
    loss=float(costs[j]);path=[j]
    for p in reversed(links):j=int(p[j]);path.append(j)
    aligned=[float(s[k]) for s,k in zip(sets,reversed(path))]
    return {'bpm':bpm,'phase_seconds':phase,'duration':seconds,'input_cues':list(cues),
            'aligned_cues':aligned,'loss_seconds_squared':loss,
            'max_error_seconds':max(abs(a-b) for a,b in zip(aligned,cues)),
            'solver':'exact chain dynamic programming; classical baseline identical',
            'scope':'music cues only; does not move picture edits or voice'}

def energy_at(t,cues):
    return ENERGY[min(int(np.searchsorted(cues,t,side='right')),len(ENERGY)-1)]
