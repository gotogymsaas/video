"""Run the pinned football kernel locally; never touches accounts or production."""
import importlib.util,json,sys,types
from pathlib import Path

def main():
 base=Path(__file__).resolve().parent;source=base/'source_snapshot'
 package='gtg_football_episode_fixture';module=types.ModuleType(package);module.__path__=[str(source)];sys.modules[package]=module
 for name in ['catalog','contracts','planner','engine']:
  spec=importlib.util.spec_from_file_location(package+'.'+name,source/(name+'.py'))
  item=importlib.util.module_from_spec(spec);sys.modules[spec.name]=item;spec.loader.exec_module(item)
 expected=json.loads((base/'evidence/football-example.json').read_text())
 engine=sys.modules[package+'.engine'];first=engine.evaluate_football_intelligence({'football_context':expected['input']}).payload
 context={**expected['input'],'previous_feedback':'Quiero comprender mejor la cobertura interior'}
 following=engine.evaluate_football_intelligence({'football_context':context,'_previous_result':first}).payload
 assert first==expected['first_result'],'First result changed'
 assert following==expected['continuation_result'],'Continuation changed'
 assert all(expected['checks'].values()),'Recorded checks failed'
 print(json.dumps({'fixture_matches':True,'checks':expected['checks'],'scope':expected['scope']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
