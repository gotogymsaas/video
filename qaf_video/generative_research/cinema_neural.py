"""Own trainable experimental video system: 3D VAE + conditional Video DiT.
Research-only: synthetic training does NOT prove cinematic performance.
Optional PyTorch import; no effect on the existing production application.
"""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

class CinemaVAE(nn.Module):
    """3D variational video autoencoder: 4x spatial compression, time retained."""
    def __init__(self, latent=4, width=16):
        super().__init__()
        self.encoder=nn.Sequential(
            nn.Conv3d(3,width,3,padding=1),nn.SiLU(),
            nn.Conv3d(width,width,3,stride=(1,2,2),padding=1),nn.SiLU(),
            nn.Conv3d(width,width,3,stride=(1,2,2),padding=1),nn.SiLU())
        self.posterior=nn.Conv3d(width,2*latent,1)
        self.decoder=nn.Sequential(
            nn.Conv3d(latent,width,3,padding=1),nn.SiLU(),
            nn.ConvTranspose3d(width,width,(3,4,4),stride=(1,2,2),padding=(1,1,1)),nn.SiLU(),
            nn.ConvTranspose3d(width,width,(3,4,4),stride=(1,2,2),padding=(1,1,1)),nn.SiLU(),
            nn.Conv3d(width,3,3,padding=1),nn.Sigmoid())
        self.latent=latent
    def encode(self,x,sample=True):
        if x.ndim!=5 or x.shape[1]!=3 or min(x.shape[-2:])<8 or x.shape[-2]%4 or x.shape[-1]%4:
            raise ValueError("Expected (B,3,T,H,W), H/W >=8 divisible by 4")
        mu,logv=self.posterior(self.encoder(x)).chunk(2,dim=1)
        logv=logv.clamp(-12,8)
        z=mu+torch.exp(.5*logv)*torch.randn_like(mu) if sample else mu
        return z,mu,logv
    def decode(self,z):return self.decoder(z)
    def forward(self,x):
        z,mu,logv=self.encode(x)
        return self.decode(z),mu,logv

class VideoDiT(nn.Module):
    """Small Transformer flow field, conditioned on first-frame and optional QAF features.
    This is a learning architecture prototype, not a foundation-scale trained model.
    """
    def __init__(self,latent=4,width=48,heads=4,layers=2,context_dim=8):
        super().__init__()
        if width%heads:raise ValueError("width must be divisible by heads")
        self.latent=latent
        self.embed=nn.Linear(latent,width)
        self.condition=nn.Linear(latent,width)
        self.qaf_context=nn.Linear(context_dim,width,bias=False)
        self.time=nn.Sequential(nn.Linear(1,width),nn.SiLU(),nn.Linear(width,width))
        block=nn.TransformerEncoderLayer(d_model=width,nhead=heads,dim_feedforward=2*width,
            dropout=0,batch_first=True,activation="gelu",norm_first=True)
        self.backbone=nn.TransformerEncoder(block,num_layers=layers,enable_nested_tensor=False)
        self.output=nn.Linear(width,latent)
    def forward(self,zt,t,first_latent,qaf=None):
        if zt.ndim!=5 or zt.shape[1]!=self.latent or first_latent.shape!=zt[:,:,:1].shape:
            raise ValueError("Invalid latent tensors")
        b,c,frames,h,w=zt.shape
        if t.shape!=(b,):raise ValueError("Time must be (B,)")
        tokens=zt.permute(0,2,3,4,1).reshape(b,frames*h*w,c)
        prefix=first_latent.expand(-1,-1,frames,-1,-1).permute(0,2,3,4,1).reshape(b,-1,c)
        y=self.embed(tokens)+self.condition(prefix)+self.time(t[:,None]).unsqueeze(1)
        if qaf is not None:
            if qaf.shape!=(b,self.qaf_context.in_features):raise ValueError("Invalid QAF context")
            y=y+self.qaf_context(qaf).unsqueeze(1)
        return self.output(self.backbone(y)).reshape(b,frames,h,w,c).permute(0,4,1,2,3)

def vae_loss(vae,video,kl_weight=.0001,temporal_weight=.05):
    recon,mu,logv=vae(video)
    pixels=F.mse_loss(recon,video)
    temporal=F.l1_loss(torch.diff(recon,dim=2),torch.diff(video,dim=2)) if video.shape[2]>1 else pixels*0
    kl=(-.5*(1+logv-mu.square()-logv.exp())).mean()
    return pixels+temporal_weight*temporal+kl_weight*kl,{"reconstruction":float(pixels.detach()),"kl":float(kl.detach())}

def flow_loss(vae,dit,video,*,use_qaf=False,qaf=None):
    with torch.no_grad():z,_,_=vae.encode(video,sample=False)
    noise=torch.randn_like(z)
    tau=torch.rand(len(z),device=z.device,dtype=z.dtype)
    t=tau.view(-1,1,1,1,1)
    zt=(1-t)*noise+t*z
    velocity=dit(zt,tau,z[:,:,:1],qaf=qaf if use_qaf else None)
    return F.mse_loss(velocity,z-noise)

def moving_shapes(batch=2,frames=5,height=16,width=16,seed=22):
    """Tiny deterministic and copyright-free synthetic motion task."""
    rng=np.random.default_rng(seed)
    out=np.zeros((batch,3,frames,height,width),np.float32)
    for b in range(batch):
        color=rng.uniform(.3,.9,size=3)
        x=int(rng.integers(1,max(2,width-4)))
        y=int(rng.integers(1,max(2,height-4)))
        vx=int(rng.choice((-1,1)))
        for f in range(frames):
            out[b,:,f]=np.array([.05,.06,.08])[:,None,None]
            xx=int(np.clip(x+vx*f,0,width-3))
            out[b,:,f,y:y+3,xx:xx+3]=color[:,None,None]
    return torch.from_numpy(out)

@torch.no_grad()
def generate(vae,dit,first_frame,frames=5,steps=12,seed=17,qaf=None):
    """Euler integration in learned latents; first frame explicitly composited."""
    if first_frame.ndim!=5 or first_frame.shape[2]!=1:raise ValueError("Expected single frame")
    if frames<2 or steps<1:raise ValueError("Frames or Euler steps invalid")
    vae.eval();dit.eval()
    first,_,_=vae.encode(first_frame,sample=False)
    gen=torch.Generator(device=first_frame.device).manual_seed(seed)
    z=torch.randn((len(first_frame),vae.latent,frames,*first.shape[-2:]),
                  device=first_frame.device,generator=gen)
    for i in range(steps):
        tau=torch.full((len(z),),i/steps,device=z.device)
        z=z+dit(z,tau,first,qaf=qaf)/steps
    images=vae.decode(z).clamp(0,1)
    images[:,:,0]=first_frame[:,:,0]  # no neuronal first-frame fidelity claim
    return images

def train_smoke(out,steps=5,seed=22,device="cpu"):
    """Actually update weights for numerical validation, NEVER claim cinema trained."""
    if not 1<=steps<=1000:raise ValueError("steps must be 1..1000")
    if device=="cuda" and not torch.cuda.is_available():raise RuntimeError("CUDA unavailable")
    torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    torch.set_num_threads(min(2,torch.get_num_threads()))
    vae=CinemaVAE().to(device);dit=VideoDiT().to(device)
    ov=torch.optim.AdamW(vae.parameters(),lr=.002)
    od=torch.optim.AdamW(dit.parameters(),lr=.001)
    hist=[]
    for i in range(steps):
        video=moving_shapes(seed=seed+i).to(device)
        ov.zero_grad(set_to_none=True)
        loss,details=vae_loss(vae,video);loss.backward();ov.step()
        od.zero_grad(set_to_none=True)
        loss_f=flow_loss(vae,dit,video);loss_f.backward();od.step()
        hist.append({"step":i,"vae_loss":float(loss.detach()),"flow_loss":float(loss_f.detach()),**details})
    output=Path(out);output.mkdir(parents=True,exist_ok=True)
    checkpoint=output/"toy_foundation.pt"
    torch.save({"model_type":"synthetic_smoke_only","vae":vae.state_dict(),"dit":dit.state_dict(),
               "seed":seed,"steps":steps,"history":hist},checkpoint)
    with torch.no_grad():
        first=moving_shapes(batch=1,seed=seed+123).to(device)[:,:,:1]
        frames=generate(vae,dit,first,steps=4,seed=seed+20)
        np.save(output/"sample_synthetic.npy",frames.cpu().numpy())
    digest=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    report={"status":"synthetic_train_smoke","foundation_cinema_trained":False,
            "real_video_training":False,"checkpoint_sha256":digest,"seed":seed,"steps":steps,
            "loss_first":hist[0],"loss_last":hist[-1],"output_shape":list(frames.shape),
            "architecture":"3D VAE + tiny transformer flow",
            "limitations":"No real video, no proven convergence, no cinematic validation"}
    (output/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",default="outputs/cinematic-smoke")
    p.add_argument("--steps",type=int,default=5)
    p.add_argument("--seed",type=int,default=22)
    p.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    a=p.parse_args()
    print(json.dumps(train_smoke(a.out,a.steps,a.seed,a.device),indent=2))

if __name__=="__main__":main()
