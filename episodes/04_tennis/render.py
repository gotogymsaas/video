from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from qaf_video.cinema_pipeline import render_cinema,cinema_storyboard,layout_audit
from qaf_video.music_production import produce_music
b=Path(__file__).parent;p=b/'project.json'
print(produce_music(p,preset='run_club',seed=24),flush=True)
for profile in ['vertical','horizontal']:
 print(layout_audit(p,profile),flush=True);cinema_storyboard(p,b/('storyboard-'+profile+'.jpg'),profile)
jobs=[(a,c) for a in ['vertical','horizontal'] for c in [True,False]]
def go(job):
 a,c=job;name='GoToGym_Tenis_04_'+a+('' if c else '_limpio')+'.mp4'
 return render_cinema(p,b/'outputs'/name,a,cc=c,progress=lambda v:print(a,c,round(v,2),flush=True) if round(v*100)%20==0 else None)
with ThreadPoolExecutor(4) as ex:list(ex.map(go,jobs))
print('Four verified renders ready',flush=True)
