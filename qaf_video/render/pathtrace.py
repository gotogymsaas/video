"""Vectorized CPU path tracer: Lambertian spheres, ideal mirrors, area-light
next-event estimation, shadows, environment and bounded diffuse bounces.
No claim to replace a production cloth/skin renderer. Values are scene-linear.
"""
from pathlib import Path
import time
import numpy as np
from PIL import Image
from ..color import filmic
from ..core import require,atomic_json

def normalize(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-12)

def scene():
    return [
      {'center':[0,-1001,0],'radius':1000,'color':[.12,.17,.20],'material':'diffuse','emission':[0,0,0]},
      {'center':[-1.05,0,-.1],'radius':1.,'color':[.12,.68,.53],'material':'diffuse','emission':[0,0,0]},
      {'center':[1.1,-.25,.2],'radius':.75,'color':[.88,.75,.44],'material':'mirror','emission':[0,0,0]},
      {'center':[.18,-.58,1.45],'radius':.42,'color':[.6,.75,.84],'material':'diffuse','emission':[0,0,0]},
      {'center':[-1.2,4,2],'radius':1.15,'color':[0,0,0],'material':'diffuse','emission':[14,13,11]},
    ]

def intersect(orig,direction,objects):
    size=len(orig);dist=np.full(size,np.inf);obj=np.full(size,-1,dtype=int)
    for i,s in enumerate(objects):
        oc=orig-np.asarray(s['center']);b=np.sum(oc*direction,axis=1);c=np.sum(oc*oc,axis=1)-s['radius']**2;disc=b*b-c
        root=np.sqrt(np.maximum(disc,0));near=-b-root;far=-b+root;t=np.where(near>1e-4,near,far)
        valid=(disc>=0)&(t>1e-4)&(t<dist);dist[valid]=t[valid];obj[valid]=i
    return dist,obj

def render(width=640,height=360,samples=16,seed=22,bounces=5,objects=None):
    require(isinstance(width,int) and isinstance(height,int) and 8<=width<=4096 and 8<=height<=4096,'Invalid render size')
    require(isinstance(samples,int) and 1<=samples<=512 and 1<=bounces<=12,'Invalid samples/bounces')
    objects=objects or scene();rng=np.random.default_rng(seed);pixels=width*height;total=np.zeros((pixels,3));start=time.perf_counter()
    camera=np.array([3.5,1.7,5.7]);target=np.array([0,0,.2]);forward=normalize(target-camera);right=normalize(np.cross(forward,[0,1,0]));up=np.cross(right,forward)
    xx,yy=np.meshgrid(np.arange(width),np.arange(height));light_index=next(i for i,s in enumerate(objects) if max(s['emission'])>0);light=objects[light_index]
    for sample in range(samples):
        x=(2*(xx.ravel()+rng.random(pixels))/width-1)*(width/height)*.44;y=(1-2*(yy.ravel()+rng.random(pixels))/height)*.44
        direction=normalize(forward+x[:,None]*right+y[:,None]*up);orig=np.broadcast_to(camera,(pixels,3)).copy();throughput=np.ones((pixels,3));radiance=np.zeros((pixels,3));alive=np.ones(pixels,dtype=bool);specular=np.ones(pixels,dtype=bool)
        for depth in range(bounces):
            ids=np.flatnonzero(alive)
            if not len(ids):break
            distances,indices=intersect(orig[ids],direction[ids],objects);miss=indices<0
            if miss.any():
                mi=ids[miss];sky=.5*(direction[mi,1]+1);env=(1-sky[:,None])*np.array([.055,.08,.10])+sky[:,None]*np.array([.2,.3,.4])
                radiance[mi]+=throughput[mi]*env;alive[mi]=False
            for j,obj in enumerate(objects):
                local=indices==j
                if not local.any():continue
                active=ids[local];pos=orig[active]+distances[local,None]*direction[active];n=normalize(pos-np.array(obj['center']));n=np.where(np.sum(n*direction[active],axis=1)[:,None]<0,n,-n)
                if max(obj['emission'])>0:
                    emitted=active[specular[active]];radiance[emitted]+=throughput[emitted]*np.array(obj['emission']);alive[active]=False;continue
                color=np.array(obj['color']);orig[active]=pos+n*2e-4
                if obj['material']=='mirror':
                    direction[active]=normalize(direction[active]-2*np.sum(direction[active]*n,axis=1)[:,None]*n);throughput[active]*=color;specular[active]=True
                else:
                    count=len(active);u=rng.random(count);phi=rng.random(count)*2*np.pi;z=1-2*u;r=np.sqrt(np.maximum(0,1-z*z));ln=np.column_stack([r*np.cos(phi),z,r*np.sin(phi)])
                    lp=np.array(light['center'])+light['radius']*ln;delta=lp-pos;d2=np.sum(delta*delta,axis=1);ld=normalize(delta);cs=np.maximum(0,np.sum(n*ld,axis=1));cl=np.maximum(0,np.sum(ln*(-ld),axis=1));shadow,hit=intersect(orig[active],ld,objects)
                    visible=(hit==light_index)&(np.abs(shadow-np.sqrt(d2))<1e-2)
                    amount=cs*cl*4*np.pi*light['radius']**2/np.maximum(d2,1e-8)*visible
                    radiance[active]+=throughput[active]*color/np.pi*np.array(light['emission'])*amount[:,None]
                    u1=rng.random(count);u2=rng.random(count);rad=np.sqrt(u1);angle=2*np.pi*u2;helper=np.tile([0.,1.,0.],(count,1));helper[np.abs(n[:,1])>.9]=[1.,0.,0.]
                    tangent=normalize(np.cross(helper,n));bitangent=np.cross(n,tangent)
                    direction[active]=normalize(tangent*(rad*np.cos(angle))[:,None]+bitangent*(rad*np.sin(angle))[:,None]+n*np.sqrt(1-u1)[:,None]);throughput[active]*=color;specular[active]=False
                if depth>=2:
                    keep=rng.random(len(active))<.85;alive[active[~keep]]=False;throughput[active[keep]]/=.85
        total+=radiance
    return total.reshape(height,width,3)/samples,{'seconds':time.perf_counter()-start,'samples_per_pixel':samples,'seed':seed,'bounces':bounces,'renderer':'native_cpu_lambertian_mirror_reference','color':'scene_linear','limitations':['sphere geometry','finite bounce truncation','no skin/cloth/volume/GGX'],'width':width,'height':height}

def save(path,**kwargs):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);rgb,report=render(**kwargs)
    require(np.isfinite(rgb).all(),'Nonfinite render')
    Image.fromarray(np.uint8(filmic(rgb)*255+.5)).save(path)
    np.save(path.with_suffix('.linear.npy'),rgb.astype(np.float32));atomic_json(path.with_suffix('.render.json'),report);return report
