"""Original UI texture on a geometric device, without regenerating its text."""
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from .core import require

def homography(source,target):
    a=[];b=[]
    for (x,y),(u,v) in zip(source,target):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
    a=np.asarray(a,dtype=float);require(a.shape==(8,8) and np.linalg.matrix_rank(a)==8,'Degenerate phone geometry')
    return np.append(np.linalg.solve(a,b),1).reshape(3,3)

def phone_plate(screen,height=1500):
    require(isinstance(height,int) and 200<=height<=4096,'Invalid phone height')
    screen=screen.convert('RGB');ratio=screen.width/screen.height;edge=round(height*.022);sw=round((height-2*edge)*ratio);w=sw+2*edge
    plate=Image.new('RGBA',(w,height));d=ImageDraw.Draw(plate);radius=round(w*.09)
    d.rounded_rectangle((0,0,w-1,height-1),radius=radius,fill='#777F83');d.rounded_rectangle((3,3,w-4,height-4),radius=radius-2,fill='#080A0B')
    texture=screen.resize((sw,height-2*edge),Image.Resampling.LANCZOS);mask=Image.new('L',texture.size)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,sw-1,texture.height-1),radius=max(1,radius-edge),fill=255);plate.paste(texture,(edge,edge),mask)
    return plate,{'screen_box':[edge,edge,sw,texture.height],'source_size':list(screen.size),'screen_size':list(texture.size),
                  'aspect_error':abs(sw/texture.height-ratio),'method':'full original screenshot; rounded corners only'}

def place_phone(canvas,screen,quad):
    require(len(quad)==4 and all(len(p)==2 for p in quad),'Four corners required');points=np.asarray(quad,dtype=float)
    require(np.isfinite(points).all(),'Nonfinite coordinates');a=np.roll(points,-1,axis=0)-points;b=np.roll(points,-2,axis=0)-np.roll(points,-1,axis=0)
    cross=a[:,0]*b[:,1]-a[:,1]*b[:,0];require(np.all(cross>0) or np.all(cross<0),'Phone quad must be convex')
    plate,r=phone_plate(screen);h=homography([(0,0),(plate.width-1,0),(plate.width-1,plate.height-1),(0,plate.height-1)],quad)
    inv=np.linalg.inv(h);inv/=inv[2,2];layer=plate.transform(canvas.size,Image.Transform.PERSPECTIVE,tuple(inv.flat)[:8],Image.Resampling.BICUBIC)
    shadow=Image.new('RGBA',canvas.size);shadow.putalpha(layer.getchannel('A').filter(ImageFilter.GaussianBlur(13)).point(lambda a:round(a*.55)))
    out=Image.alpha_composite(Image.alpha_composite(canvas.convert('RGBA'),shadow),layer);r.update(homography=h.tolist(),quad=[list(p) for p in quad]);return out,r
