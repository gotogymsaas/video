import sys,types,importlib.util,json
from pathlib import Path
b=Path(__file__).parent
for n in ['api','api.qaf_osteoarthritis']:
 m=types.ModuleType(n);m.__path__=[str(b/'sources')];sys.modules[n]=m
for n,f in [('api.specialist_inputs','specialist_inputs.py'),('api.qaf_osteoarthritis.contracts','contracts.py'),('api.qaf_osteoarthritis.engine','engine.py')]:
 s=importlib.util.spec_from_file_location(n,b/'sources'/f);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m)
c=dict(goal='Registrar mi experiencia para conversar con mi profesional',joint='rodilla',pain_0_10=5,pain_duration_days=180,morning_stiffness_minutes=15,sleep_hours=7,activity_minutes=20,trigger_note='Registro personal',professional_plan_note='Seguir los límites del plan de mi fisioterapeuta',diagnosis_confirmed=True,**{k:False for k in ['hot_swollen_joint','fever_or_unwell','unable_to_bear_weight','recent_injury','new_numbness','worsening','daily_life_affected']})
f=sys.modules['api.qaf_osteoarthritis.engine'].evaluate_osteoarthritis
a=f({'osteoarthritis_context':c,'_history':[{'saved_at':'2026-10-21','result':{'check_in':{'joint':'rodilla','pain_0_10':4}}}]}).payload
z=f({'osteoarthritis_context':dict(c,unable_to_bear_weight=True)}).payload
assert a['assessment_status']=='continue_coaching' and a['algorithms']['QAF-PAIN-MAP']['pain_change_since_previous']==1
assert a['algorithms']['QAF-MOB']['status']=='support_existing_plan' and a['session_plan'] is None
assert z['assessment_status']=='urgent_medical_attention' and z['algorithms']['QAF-MOB']['status']=='withheld'
(b/'evidence/osteo-example.json').write_text(json.dumps({'fictional':True,'source_commit':'6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62','support':a,'safety':z},ensure_ascii=False,indent=2))
p=b/'project.json';m=json.loads(p.read_text());m['claims']={'support':{'source':'https://github.com/gotogymsaas/appdesplegada/blob/6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62/backend/api/qaf_osteoarthritis/engine.py','scope':'Local execution of pinned source with fictional self-report. No production verification, diagnosis, exercise prescription or cure.','status':'verified_local','evidence_asset':'evidence/osteo-example.json'}}
for s in m['shots']:
 if s['start'] in [0,5,36,42]:s['asset']='assets/staircase.png'
 if s['layout'] in ['inputs','choice','diary'] or 24<=s['start']<48:s['claim_ids']=['support']
for x in list((b/'assets').rglob('*'))+[b/'evidence/osteo-example.json']:
 if x.is_file() and (x.name in ['scene.png','staircase.png','logo-gotogym.png','pantalla-inicio.png','osteo-example.json'] or 'fonts' in x.parts):
  import hashlib
  m['assets'][x.relative_to(b).as_posix()]={'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'origin':'Generated fictional image' if x.name=='scene.png' else 'GoToGym original asset or fictional source fixture','rights':'Commissioned production; bundled font licenses retained','privacy':'public'}
p.write_text(json.dumps(m,ensure_ascii=False,indent=2));print('source verified and assets bound')
