"""Explicit SDR sRGB/linear transforms and premultiplied alpha composition."""
import numpy as np
from PIL import Image

def srgb_to_linear(c):
    c=np.asarray(c,dtype=np.float32);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def linear_to_srgb(c):
    c=np.maximum(np.asarray(c,dtype=np.float32),0);return np.where(c<=.0031308,12.92*c,1.055*c**(1/2.4)-.055)
def composite(fg,bg):
    f=np.asarray(fg.convert('RGBA'),dtype=np.float32)/255;b=np.asarray(bg.convert('RGBA'),dtype=np.float32)/255
    af=f[...,3:4];ab=b[...,3:4];a=af+(1-af)*ab
    prem=srgb_to_linear(f[...,:3])*af+(1-af)*srgb_to_linear(b[...,:3])*ab
    rgb=linear_to_srgb(prem/np.maximum(a,1e-8));out=np.concatenate([rgb,a],axis=-1)
    return Image.fromarray(np.uint8(np.clip(out*255+.5,0,255)),'RGBA')
def filmic(rgb,exposure=0):
    # A documented SDR Reinhard view; not an ACES certification.
    x=np.maximum(np.asarray(rgb,dtype=np.float32),0)*2**exposure
    return np.clip(linear_to_srgb(x/(1+x)),0,1)
