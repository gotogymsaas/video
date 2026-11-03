"""Timeline composition with licensed fonts, reframing and explicit color mode."""
import math,json,re
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
from ..core import ASSETS,PROFILES,local_asset
from ..mathematics import minimum_jerk
from ..color import composite as linear_composite
COLORS={'bg':'#101012','white':'#F8F9FA','turquoise':'#0FBFB0','gold':'#D4B46A','silver':'#E0E3E6'}
def ease(t):return float(minimum_jerk(max(0,min(1,t))))

def wrap(text,f,width):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)))
    lines=[]
    for paragraph in text.split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if d.textlength(candidate,font=f)>width:
                if not line:raise ValueError('Unbreakable text wider than layout')
                lines.append(line);line=word
            else:line=candidate
        lines.append(line)
    return lines

class Movie:
    def __init__(self,m,base,profile):
        self.regular=ASSETS/'fonts/DejaVuSans.ttf'
        self.bold=ASSETS/'fonts/DejaVuSans-Bold.ttf'
        self.m,self.base,self.profile=m,base,profile
        self.w,self.h=PROFILES[profile];self.s=self.w/1080 if self.h>self.w else self.h/1080
        self.sources={};self.bg=self.background();self.decoder=None;self.current=None
        self.fonts={}
        self.linear=m.get('color_pipeline')=='srgb_linear_composite'
        palette=json.loads((ASSETS/'brand.json').read_text(encoding='utf-8'))['colors']
        palette.update(m.get('brand_colors',{}))
        if not all(isinstance(v,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',v) for v in palette.values()):
            raise ValueError('Brand colors must be six-digit hex values')
        self.colors={**COLORS,**palette}
    def font(self,size,bold=False):
        key=(size,bold)
        if key not in self.fonts:self.fonts[key]=ImageFont.truetype(str(self.bold if bold else self.regular),max(1,size))
        return self.fonts[key]
    def composite(self,a,b):
        return linear_composite(b,a) if self.linear else Image.alpha_composite(a,b)
    def background(self):
        # Rasterized once: dark editorial gradient, no random flicker.
        im=Image.new('RGB',(self.w,self.h));d=ImageDraw.Draw(im)
        for y in range(self.h):
            t=y/self.h;d.line((0,y,self.w,y),fill=(int(10+10*t),int(24-8*t),int(32-10*t)))
        return im
    def close_decoder(self):
        if self.decoder:
            self.decoder.stdout.close()
            if self.decoder.poll() is None:self.decoder.terminate()
            self.decoder.wait(timeout=10);self.decoder=None
    def asset(self,shot,t):
        if not shot.get('asset'):return self.bg.copy()
        p=local_asset(self.base,shot['asset'])
        focus=shot.get('focus',{}).get('horizontal' if self.w>self.h else 'vertical',[.5,.5])
        if shot.get('kind','image')=='video':
            if self.current is not shot:
                self.close_decoder();self.current=shot
                vf=f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h}:(iw-ow)*{focus[0]}:(ih-oh)*{focus[1]},fps={self.m['fps']}"
                self.decoder=subprocess.Popen(['ffmpeg','-v','error','-ss',str(shot.get('in',0)),'-i',str(p),'-vf',vf,'-an','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            raw=self.decoder.stdout.read(self.w*self.h*3)
            if len(raw)!=self.w*self.h*3:raise ValueError('Video decoder ended early')
            return Image.frombytes('RGB',(self.w,self.h),raw)
        self.close_decoder();self.current=None
        if p not in self.sources:
            with Image.open(p) as im:self.sources[p]=ImageOps.exif_transpose(im).convert('RGB')
        from ..animation import camera_sample, crop_box
        sample=dict(shot)
        sample['focus']=focus
        point,zoom=camera_sample(sample,t)
        im=self.sources[p]
        return im.resize((self.w,self.h),Image.Resampling.BICUBIC,
                         box=crop_box(im.size,(self.w,self.h),point,zoom))

    def text(self,im,text,x,y,size,width,color,bold=False,max_lines=4):
        f=self.font(round(size*self.s),bold);lines=wrap(text,f,width);step=round(size*self.s*1.25)
        if len(lines)>max_lines or y+len(lines)*step>self.h*.82:raise ValueError('Text overflow: shorten copy')
        d=ImageDraw.Draw(im)
        for i,line in enumerate(lines):d.text((x,y+i*step),line,font=f,fill=color)
        return y+len(lines)*step
    def frame(self,shot,absolute):
        local=absolute-shot['start'];dur=shot['end']-shot['start'];t=local/dur
        im=self.asset(shot,t).convert('RGBA');shade=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(shade)
        # Controlled shade protects text over imagery.
        d.rectangle((0,0,self.w,self.h),fill=(0,0,0,95 if shot.get('asset') else 0));im=self.composite(im,shade)
        layer=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(layer)
        x=round(self.w*.1);width=self.w-2*x
        d.text((x,round(self.h*.075)), 'GOTOGYM / QUANTUM COACH',font=self.font(round(21*self.s),True),fill=self.colors['gold'])
        d.text((x,round(self.h*.10)),self.m.get('label','VISUALIZACIÓN CONCEPTUAL'),font=self.font(round(16*self.s)),fill=self.colors['silver'])
        y=round(self.h*.18+25*self.s*(1-ease(local/.7)))
        y=self.text(layer,shot.get('eyebrow','').upper(),x,y,20,width,self.colors['turquoise'],True,max_lines=2)+round(22*self.s)
        y=self.text(layer,shot.get('title',''),x,y,64 if self.h>self.w else 60,width,self.colors['white'],True,max_lines=3)
        y+=round(30*self.s)
        self.text(layer,shot.get('body',''),x,y,29,width,self.colors['silver'],max_lines=4)
        # Abstract relationships: labels show inputs, never fabricated biometrics.
        if shot.get('nodes'):
            from ..animation import reveal_times, reveal_progress
            starts=reveal_times(shot,self.m.get('subtitles',[]))
            labels=shot['nodes'];cy=self.h*.64
            centers=[(self.w*(.16+.68*i/max(1,len(labels)-1)),cy+math.sin(i*1.5)*self.h*.02) for i in range(len(labels))]
            for i in range(len(centers)-1):
                a,b=centers[i],centers[i+1];progress=reveal_progress(local,starts[i+1],.7)
                d.line((a[0],a[1],a[0]+(b[0]-a[0])*progress,a[1]+(b[1]-a[1])*progress),fill=(15,191,176,160),width=max(1,round(2*self.s)))
            for i,((cx,cy),label) in enumerate(zip(centers,labels)):
                if local < starts[i]:continue
                r=(17+2*reveal_progress(local,starts[i]))*self.s;d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=self.colors['turquoise'])
                f=self.font(round(20*self.s));tw=d.textlength(label,font=f);d.text((cx-tw/2,cy+35*self.s),label,font=f,fill=self.colors['white'])
        # Short, visually calm card for output/limits.
        if shot.get('card'):
            yy=round(self.h*.72);d.rounded_rectangle((x,yy,self.w-x,yy+82*self.s),radius=14*self.s,fill=(23,55,92,230),outline=self.colors['turquoise'],width=1)
            f=self.font(round(22*self.s),True);line=shot['card']
            if d.textlength(line,font=f)>width-30*self.s:raise ValueError('Card text overflow')
            d.text((x+15*self.s,yy+24*self.s),line,font=f,fill=self.colors['white'])
        if self.m.get('logo'):
            p=local_asset(self.base,self.m['logo'])
            if p not in self.sources:
                with Image.open(p) as logo:self.sources[p]=logo.convert('RGBA')
            logo=self.sources[p].copy();logo.thumbnail((round(self.w*.22),round(self.h*.06)));layer.alpha_composite(logo,(self.w-x-logo.width,round(self.h*.06)))
        for sub in self.m.get('subtitles',[]):
            if sub['start']<=absolute<sub['end']:
                f=self.font(round(27*self.s));lines=wrap(sub['text'],f,width)
                if len(lines)>2:raise ValueError('Subtitle needs more than two lines')
                yy=self.h*.835;d.rectangle((x-8,yy-10,self.w-x+8,yy+len(lines)*36*self.s+10),fill=(0,0,0,220))
                for i,line in enumerate(lines):d.text((x,yy+i*36*self.s),line,font=f,fill='white')
        d.line((x,self.h*.94,x+width*absolute/self.m['duration'],self.h*.94),fill=self.colors['turquoise'],width=max(1,round(3*self.s)))
        # Fade graphics on cut; footage keeps continuity.
        alpha=1 if self.m.get('_storyboard_static') else ease(local/min(.45,dur*.18))*ease((dur-local)/min(.25,dur*.12))
        layer.putalpha(layer.getchannel('A').point(lambda a:int(a*alpha)))
        return self.composite(im,layer).convert('RGB')
