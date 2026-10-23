from pathlib import Path
import sys,types,importlib.util,json
b=Path(__file__).parent
api=types.ModuleType('api');api.__path__=[str(b/'sources')];sys.modules['api']=api
for n,p in [('api.qaf_sports_evidence','qaf_sports_evidence.py'),('tennis_engine','engine.py')]:
 s=importlib.util.spec_from_file_location(n,b/'sources'/p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m)
data={'message':'Me bloqueo por presión al perder un punto. Quiero volver al presente.','player_profile':{'level':'intermedio','goal':'jugar con más claridad','surface':'dura','competition_mode':'singles'},'mental':{'frustration_pct':70,'anxiety_pct':65},'skills':{'drive':70,'reves':65,'volea':60,'saque':65,'movilidad':65}}
r=sys.modules['tennis_engine'].evaluate_tennis_intelligence(data).payload
assert r['session_plan']['primary_agent']=='mental' and 'respirar' in r['next_best_action']
assert r['data_quality']['prediction_basis']=='insufficient_evidence' and r['agents']['qaf_prediction']['evidence']['injury_risk'] is None
assert r['session_plan']['total_minutes']==sum(x['minutes'] for x in r['session_plan']['blocks'])
(b/'evidence/tennis-example.json').write_text(json.dumps({'fictional':True,'source_commit':'6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62','input':data,'result':r,'scope':'Pure engine execution; no production chat verification'},ensure_ascii=False,indent=2));print('Tennis source verified')
