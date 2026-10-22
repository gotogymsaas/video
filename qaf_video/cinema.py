"""El próximo paso: a 60-second photographic cinematic animatic, not live footage."""
from __future__ import annotations
import argparse,bisect,json,math,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance

from .core import local_asset,PROFILES,require
from .phone import place_phone

GOLD='#D4B46A';MINT='#0FBFB0';WHITE='#F8F9FA';SILVER='#E0E3E6';BG='#101012'


def ease(x):
    x=min(1.,max(0.,x));return x*x*x*(10+x*(-15+6*x))


class Film:
    def __init__(self,manifest,base,format='vertical'):
        self.manifest=manifest;self.base=Path(base);self.shots=manifest['shots']
        self.format=format;self.vertical=format in ['vertical','proxy'];self.w,self.h=PROFILES[format]
        self.s=self.w/1080 if self.vertical else self.h/1080;self.fonts={};self.images={};self.backgrounds={}
        self.logo=Image.open(local_asset(self.base,manifest['logo'])).convert('RGB')
        self.screen=Image.open(local_asset(self.base,manifest['phone_screen'])).convert('RGB') if manifest.get('phone_screen') else None
        self.phone_reports=[]
        self.layout_boxes=[]
        self.shade=self.gradient('bottom');self.side_shade=self.gradient('right')
        for name in {s['asset'] for s in self.shots if s.get('asset')}:
            im=Image.open(local_asset(self.base,name)).convert('RGB')
            im=ImageEnhance.Color(im).enhance(.96);im=ImageEnhance.Contrast(im).enhance(1.035)
            self.images[name]=im
        self.subtitles=manifest.get('subtitles',[])
    def font(self,size,bold=False,serif=False):
        key=(round(size*self.s),bold,serif)
        if key not in self.fonts:
            name='serif' if serif else 'bold' if bold else 'regular'
            self.fonts[key]=ImageFont.truetype(str(local_asset(self.base,self.manifest['fonts'][name])),max(1,key[0]))
        return self.fonts[key]
    def gradient(self,direction):
        if direction=='bottom':
            a=np.linspace(0,1,self.h);alpha=np.maximum(.13*np.maximum(0,1-a*3),.83*np.maximum(0,(a-.42)/.58))
            strip=Image.fromarray(np.uint8(alpha[:,None]*255),'L').resize((self.w,self.h))
        else:
            a=np.linspace(0,1,self.w);strip=Image.fromarray(np.uint8((.66*np.maximum(0,(a-.36)/.64))*255)[None,:],'L').resize((self.w,self.h))
        out=Image.new('RGBA',(self.w,self.h),(0,0,0,0));out.putalpha(strip);return out
    def text(self,d,text,xy,size=50,color=WHITE,bold=False,serif=False,anchor=None,width=None,leading=1.13):
        f=self.font(size,bold,serif);x,y=xy;lines=text.split('\n');step=size*self.s*leading
        for i,line in enumerate(lines):
            if width and d.textlength(line,font=f)>width:raise ValueError('Text too wide: '+line)
            pos=(round(x),round(y+i*step));box=d.textbbox(pos,line,font=f,anchor=anchor)
            self.layout_boxes.append({'text':line,'box':list(box),'inside_canvas':box[0]>=0 and box[1]>=0 and box[2]<=self.w and box[3]<=self.h,'font_px':f.size})
            d.text(pos,line,font=f,fill=color,anchor=anchor,stroke_width=0)
        return y+len(lines)*step
    def small(self,d,text,x,y,color=GOLD):self.text(d,text,(x,y),36 if self.vertical else 34,color,True)
    def photo(self,shot,u):
        if not shot.get('asset'):return Image.new('RGB',(self.w,self.h),'black')
        im=self.images[shot['asset']];z=shot.get('zoom',[1,1])[0]+np.diff(shot.get('zoom',[1,1]))[0]*ease(u)
        focus=shot.get('focus',[.5,.5]);iw,ih=im.size
        cover=max(self.w/iw,self.h/ih)*z;cw,ch=self.w/cover,self.h/cover
        cx=np.clip(focus[0]*iw,cw/2,iw-cw/2);cy=np.clip(focus[1]*ih,ch/2,ih-ch/2)
        return im.resize((self.w,self.h),Image.Resampling.BICUBIC,box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2))
    def headline(self,d,eyebrow,title,detail='',right=False):
        if self.vertical:x,y,width=self.w*.08,self.h*.65,self.w*.84
        else:x,y,width=(self.w*.61,self.h*.34,self.w*.32) if right else (self.w*.075,self.h*.37,self.w*.47)
        self.small(d,eyebrow,x,y);y+=56*self.s
        size=79 if self.vertical else 70;lines=[]
        for para in title.split('\n'):
            current=''
            for word in para.split():
                candidate=(current+' '+word).strip()
                if current and d.textlength(candidate,font=self.font(size,True))>width:lines.append(current);current=word
                else:current=candidate
            if current:lines.append(current)
        require(len(lines)<=3,'Shorten headline')
        y=self.text(d,'\n'.join(lines),(x,y),size,WHITE,True,width=width)
        if detail:self.text(d,detail,(x,y+20*self.s),37 if self.vertical else 35,SILVER,width=width)
    def card(self,d,box,label,value,active=True):
        x,y,w,h=box;r=15*self.s
        d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=(11,24,27,235),outline=MINT if active else '#435256',width=max(1,round(self.s*2)))
        self.text(d,label,(x+22*self.s,y+17*self.s),36,MINT if active else SILVER,True,width=w-44*self.s)
        self.text(d,value,(x+22*self.s,y+64*self.s),39 if self.vertical else 35,WHITE if active else '#8C9A97',True,width=w-44*self.s)
    def context_graph(self,d,local,choose=False):
        x=self.w*.08;y=self.h*.18
        self.small(d,'RUNNING / CONTEXTO DECLARADO',x,y)
        self.text(d,'Compara opciones.' if choose else 'Tu día, conectado.',(x,y+60*self.s),69,WHITE,True)
        if self.vertical:
            boxes=[(x,self.h*(.33+i*.087),self.w*.84,140*self.s) for i in range(3)];target=(x,self.h*.64,self.w*.84,235*self.s)
        else:
            boxes=[(x,self.h*(.35+i*.15),self.w*.34,122*self.s) for i in range(3)];target=(self.w*.55,self.h*.41,self.w*.37,255*self.s)
        values=self.manifest.get('comparison_cards' if choose else 'input_cards',[])
        for i,(box,entry) in enumerate(zip(boxes,values)):
            if local>i*.23:self.card(d,box,entry['label'],entry['value'],entry.get('active',True))
        tx,ty,tw,th=target;d.rounded_rectangle((tx,ty,tx+tw,ty+th),radius=20*self.s,fill=(7,31,29,248),outline=GOLD,width=max(1,round(2*self.s)))
        self.text(d,'PROPUESTA PARA REVISAR',(tx+24*self.s,ty+23*self.s),36 if self.vertical else 29,GOLD,True)
        self.text(d,'15 min',(tx+24*self.s,ty+72*self.s),76,WHITE,True)
        self.text(d,'Caminata cómoda',(tx+24*self.s,ty+164*self.s),39 if self.vertical else 35,WHITE)
        self.text(d,'Datos declarados · caso ficticio',(x,self.h*.80 if self.vertical else self.h*.84),36 if self.vertical else 30,SILVER)
    def diary(self,d,local,continuity=False,shot=None):
        if self.vertical:x,y,w=self.w*.08,self.h*.18,self.w*.84
        else:x,y,w=self.w*.62,self.h*.24,self.w*.31
        self.small(d,'DESPUÉS DE LA SESIÓN',x,y);y+=44*self.s
        self.text(d,(shot or {}).get('title','Tu historia\ncuenta.' if continuity else 'Lo que\nrealmente hiciste.'),(x,y),70 if self.vertical else 62,WHITE,True,width=w)
        y+=180*self.s if not self.vertical else 210*self.s
        labels=['Tiempo realizado','Esfuerzo percibido','Cómo te sentiste'] if not continuity else ['Tu objetivo','Tu experiencia','Tu siguiente conversación']
        for i,label in enumerate(labels):
            if local>i*.45:
                yy=y+i*70*self.s
                d.rounded_rectangle((x,yy,x+w,yy+54*self.s),radius=12*self.s,fill=(9,19,21,228))
                d.ellipse((x+18*self.s,yy+20*self.s,x+28*self.s,yy+30*self.s),fill=MINT)
                self.text(d,label,(x+45*self.s,yy+13*self.s),36,WHITE,width=w-60*self.s)
    def outro(self,d,local):
        cx=self.w/2;size=200*self.s if self.vertical else 170*self.s
        y=self.h*.22 if self.vertical else self.h*.14
        logo=self.logo.resize((round(size),round(size)),Image.Resampling.LANCZOS)
        d._image.paste(logo,(round(cx-size/2),round(y)))
        y+=size+55*self.s
        self.text(d,'GoToGym',(cx,y),89 if self.vertical else 83,WHITE,True,anchor='mt')
        y+=112*self.s
        self.text(d,'QUANTUM COACH',(cx,y),30,GOLD,True,anchor='mt')
        y+=74*self.s
        self.text(d,'Tu próximo paso\nempieza hoy.' if self.vertical else 'Tu próximo paso empieza hoy.',(cx,y),56,WHITE,True,anchor='mt')
        y+=174*self.s if self.vertical else 106*self.s
        w=self.w*.76 if self.vertical else 650*self.s
        d.rounded_rectangle((cx-w/2,y,cx+w/2,y+86*self.s),radius=15*self.s,fill='#103B34',outline=MINT,width=2)
        self.text(d,'Escribe «Activa running»',(cx,y+27*self.s),32,WHITE,True,anchor='mt')
        self.text(d,'app.gotogym.store',(cx,y+120*self.s),28,SILVER,anchor='mt')
        self.text(d,'ANIMATIC CINEMATOGRÁFICO',(cx,self.h*.95),18,'#84918F',anchor='mt')
    def phone(self,im,local,shot):
        if self.vertical:x,y,w,h=self.w*.22,self.h*.20,self.w*.56,self.h*.56
        else:x,y,w,h=self.w*.16,self.h*.12,self.h*.40,self.h*.75
        quad=[(x,y),(x+w,y+12*self.s),(x+w-8*self.s,y+h),(x-8*self.s,y+h-12*self.s)]
        plate,r=place_phone(im,self.screen,quad);im.paste(plate);self.phone_reports=[r];d=ImageDraw.Draw(im,'RGBA')
        if self.vertical:
            self.text(d,shot.get('title','Bienvenido a GoToGym.'),(self.w/2,self.h*.09),62,WHITE,True,anchor='mt')
            self.text(d,shot.get('body','Tu próximo paso empieza aquí.'),(self.w/2,self.h*.79),39,WHITE,anchor='mt')
        else:self.headline(d,shot.get('eyebrow','TU PUNTO DE PARTIDA'),shot.get('title','Bienvenido a GoToGym.'),shot.get('body',''),right=True)

    def frame(self,t,subtitles=False):
        self.layout_boxes=[]
        index=min(len(self.shots)-1,max(0,bisect.bisect_right([s['start'] for s in self.shots],t)-1));shot=self.shots[index]
        local=t-shot['start'];u=local/(shot['end']-shot['start']);layout=shot['layout'];im=self.photo(shot,u).convert('RGBA')
        if layout in ['inputs','choice']:im=Image.alpha_composite(im,Image.new('RGBA',im.size,(0,7,11,225)))
        elif layout=='diary':im=Image.alpha_composite(im,Image.new('RGBA',im.size,(0,0,0,110)))
        if layout not in ['outro','phone']:
            im=Image.alpha_composite(im,self.shade)
            if not self.vertical and shot.get('right'):im=Image.alpha_composite(im,self.side_shade)
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        if layout=='headline':self.headline(d,shot.get('eyebrow',''),shot['title'],shot.get('body',''),right=shot.get('right',False))
        elif layout in ['inputs','choice']:self.context_graph(d,local,choose=layout=='choice')
        elif layout=='diary':self.diary(d,local,continuity=shot.get('continuity',False),shot=shot)
        elif layout=='phone':self.phone(im,local,shot)
        else:self.outro(d,local)
        if layout not in ['outro','phone']:
            self.text(d,'GOTOGYM / QUANTUM COACH',(self.w*.08,self.h*.055),36 if self.vertical else 30,WHITE,True)
            if shot.get('claim_ids'):self.text(d,'EJEMPLO FICTICIO',(self.w*.08,self.h*.088),36 if self.vertical else 30,SILVER)
        alpha=ease(local/.35)*ease((shot['end']-t)/.15);layer.putalpha(layer.getchannel('A').point(lambda v:round(v*alpha)))
        im=Image.alpha_composite(im,layer)
        if subtitles:self.caption(im,t)
        if t<.3:im=Image.blend(Image.new('RGBA',im.size,'black'),im,ease(t/.3))
        return im.convert('RGB')
    def caption(self,im,t):
        cue=next((c for c in self.subtitles if c['start']<=t<c['end']),None)
        if not cue:return
        d=ImageDraw.Draw(im,'RGBA');size=40 if self.vertical else 38;f=self.font(size)
        width=self.w*(.84 if self.vertical else .75);words=cue['text'].split();lines=[];line=''
        for word in words:
            candidate=(line+' '+word).strip()
            if d.textlength(candidate,font=f)>width and line:lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if len(lines)>2:raise ValueError('Caption needs more than two lines')
        yy=self.h*.865 if self.vertical else self.h*.875;step=size*self.s*1.25
        boxw=max(d.textlength(x,font=f) for x in lines)+38*self.s
        d.rounded_rectangle((self.w/2-boxw/2,yy-12*self.s,self.w/2+boxw/2,yy+len(lines)*step+6*self.s),radius=10*self.s,fill=(0,0,0,205))
        for i,line in enumerate(lines):self.text(d,line,(self.w/2,yy+i*step),size,WHITE,anchor='mt')
