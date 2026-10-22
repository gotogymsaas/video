"""Deterministic production DAG with per-node content hashes and atomic reports.

Only named built-in operations are accepted. No shell, arbitrary Python,
network providers or dynamic plugins are executed by a workflow file.
"""
from __future__ import annotations
import json,re,time
from pathlib import Path
from .core import require, digest, sha256, atomic_json, local_asset


def order_nodes(nodes):
    require(isinstance(nodes,list) and 1<=len(nodes)<=100,'DAG requires 1–100 nodes')
    by_id={}
    for node in nodes:
        require(isinstance(node,dict) and isinstance(node.get('id'),str) and
                re.fullmatch(r'[A-Za-z0-9_-]{1,64}',node['id']), 'Invalid DAG node identifier')
        require(node['id'] not in by_id,'Duplicate DAG node identifier');by_id[node['id']]=node
    require(all(isinstance(n.get('depends',[]),list) and all(d in by_id for d in n.get('depends',[]))
                for n in nodes),'Missing DAG dependency')
    done=[];pending=list(by_id)
    while pending:
        ready=[key for key in pending if all(d in done for d in by_id[key].get('depends',[]))]
        require(bool(ready),'DAG contains a cycle')
        for key in ready:done.append(key);pending.remove(key)
    return [by_id[key] for key in done]


def build(workflow,workspace):
    from .server import confined
    from .pipeline import render_project,storyboard
    from .audio import mix_audio
    from .render.pathtrace import save
    from .core import load,validate
    root=Path(workspace).resolve();root.mkdir(parents=True,exist_ok=True)
    spec=json.loads(Path(workflow).read_text(encoding='utf-8'))
    require(spec.get('schema')=='qaf_production_graph_v1','Unsupported DAG schema')
    nodes=order_nodes(spec.get('nodes'));results={};keys={};started=time.perf_counter()
    package=Path(__file__).parent
    engine=digest({str(p.relative_to(package)):sha256(p) for p in package.rglob('*')
                   if p.is_file() and p.suffix in ['.py','.json','.ttf']})
    for node in nodes:
        kind=node.get('kind');require(kind in ['native_render','mix','validate','storyboard','render'],'Unsupported DAG operation')
        inputs={};outputs=[];project=None;output=None
        if kind in ['validate','storyboard','render']:
            project=confined(root,node.get('project',''));raw=json.loads(project.read_text(encoding='utf-8'))
            inputs[str(project.relative_to(root))]=sha256(project)
            for shot in raw.get('shots',[]):
                if shot.get('asset'):
                    p=local_asset(project.parent,shot['asset']);inputs[str(p.relative_to(root))]=sha256(p)
            for k in ['voice','music','ambience','effects','logo']:
                if raw.get(k):
                    p=local_asset(project.parent,raw[k]);inputs[str(p.relative_to(root))]=sha256(p)
        if kind=='mix':
            for stem,name in node.get('stems',{}).items():
                require(stem in ['voice','music','ambience','effects'],'Unsupported audio stem')
                p=confined(root,name);require(p.is_file(),'Missing stem');inputs[name]=sha256(p)
        if kind!='validate':
            output=confined(root,node.get('output',''));outputs=[output]
            if kind=='native_render':outputs += [output.with_suffix('.linear.npy'),output.with_suffix('.render.json')]
            if kind=='mix':outputs += [output.with_suffix('.audio.json')]
            if kind=='render':outputs += [output.with_suffix('.report.json')]
            require(str(output.relative_to(root)) not in inputs,'Output would overwrite an input asset')
        key=digest({'node':node,'inputs':inputs,'dependencies':{d:keys[d] for d in node.get('depends',[])},'engine':engine})
        record=root/'.qaf-cache'/f'{node["id"]}.json';old={}
        if record.is_file():
            try:old=json.loads(record.read_text(encoding='utf-8'))
            except (ValueError,OSError):pass
        hit=old.get('key')==key and all(p.is_file() and old.get('outputs',{}).get(str(p.relative_to(root)))==sha256(p) for p in outputs)
        if hit:result=old['result']
        else:
            if kind=='native_render':result=save(output,**node.get('settings',{}))
            elif kind=='mix':result=mix_audio(output,node.get('seconds',60),**{s:confined(root,n) for s,n in node.get('stems',{}).items()})
            elif kind=='validate':result=validate(load(project),project.parent,final=node.get('final') is True)
            elif kind=='storyboard':result={'image':str(storyboard(project,output,node.get('profile','proxy')).relative_to(root))}
            else:result=render_project(project,output,node.get('profile','proxy'),node.get('final') is True)
            atomic_json(record,{'key':key,'result':result,'outputs':{str(p.relative_to(root)):sha256(p) for p in outputs}})
        keys[node['id']]=key;results[node['id']]={'kind':kind,'key':key,'cache_hit':hit,'result':result}
    report={'schema':'qaf_production_graph_report_v1','nodes':results,'wall_seconds':time.perf_counter()-started,
            'execution':'serial topological order','publication':'no automatic publication'}
    atomic_json(root/'.qaf-cache/last-build.json',report);return report
