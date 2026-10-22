"""Identifiable finite QAF decisions; the diagonal case is classical."""
import math
import numpy as np
from .core import require

def select(candidates,temperature=.12):
    require(1<=len(candidates)<=256 and math.isfinite(temperature) and temperature>0,'Invalid alternatives or temperature')
    loss=np.array([float(c['loss']) for c in candidates]);require(np.isfinite(loss).all(),'Nonfinite loss')
    feasible=[i for i,c in enumerate(candidates) if c.get('feasible',True)];require(feasible,'No feasible audiovisual candidate')
    p=np.zeros(len(loss));w=np.exp(-(loss[feasible]-loss[feasible].min())/temperature);p[feasible]=w/w.sum()
    chosen=min(feasible,key=lambda i:(loss[i],i));shift=loss-loss.min();a=float(shift.max()+1)
    return {'selected_index':chosen,'selected':candidates[chosen],'alternatives':candidates,'probabilities':p.tolist(),
            'state':'rho=diag(p); PSD, trace one; fixed candidate basis','expected_loss':float(p@loss),
            'classical_baseline_index':chosen,'incremental_advantage_claimed':False,
            'qubo':{'diagonal':(shift-a).tolist(),'off_diagonal':2*a,'constant':a,'penalty':a,
                    'convention':'upper triangular','forbidden_indices':[i for i in range(len(loss)) if i not in feasible],
                    'solver':'native feasible enumeration; forbidden alternatives are hard constraints'}}

def contrast(foreground,background):
    def light(c):
        x=np.array([int(c.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)])
        x=np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4);return float(x@np.array([.2126,.7152,.0722]))
    a,b=sorted([light(foreground),light(background)]);return (b+.05)/(a+.05)

def text_contract(box,canvas,font_px,mobile_width=360,min_mobile_px=12):
    x,y,w,h=box;cw,ch=canvas;size=font_px*mobile_width/cw
    return {'inside_canvas':all(math.isfinite(v) for v in box) and min(box)>=0 and x+w<=cw and y+h<=ch,
            'mobile_px':size,'readable':size>=min_mobile_px,'minimum_mobile_px':min_mobile_px}
