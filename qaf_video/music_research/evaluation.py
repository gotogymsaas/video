"""M05: paired listener bootstrap and a fail-closed asset provenance contract."""
from pathlib import Path
import hashlib,math
import numpy as np

def paired_report(rows,seed=22,iterations=2000,min_listeners=20,min_episodes=5):
    if (not rows or len(rows)>100000 or not isinstance(iterations,int) or not 100<=iterations<=10000
        or not all(isinstance(v,int) and not isinstance(v,bool) and v>0 for v in (min_listeners,min_episodes))):
        raise ValueError('Invalid study')
    seen=set();groups={};episodes=set()
    for r in rows:
        if not all(isinstance(r.get(k),str) and r[k].strip() for k in ('listener','episode')):
            raise ValueError('Listener and episode IDs required')
        pair=(r['listener'],r['episode'])
        if pair in seen:raise ValueError('Duplicate listener/episode; aggregate repeats first')
        seen.add(pair);episodes.add(r['episode']);a=float(r['baseline']);b=float(r['candidate'])
        if not all(math.isfinite(v) and 0<=v<=100 for v in (a,b)):raise ValueError('Invalid rating')
        groups.setdefault(r['listener'],[]).append(b-a)
    # Each listener has equal weight. Episode generalization is not estimated.
    delta=np.asarray([np.mean(v) for v in groups.values()]);rng=np.random.default_rng(seed)
    boot=np.concatenate([rng.choice(delta,(min(32,iterations-k),len(delta)),replace=True).mean(axis=1)
                         for k in range(0,iterations,32)])
    low,high=np.quantile(boot,[.025,.975]);enough=len(groups)>=min_listeners and len(episodes)>=min_episodes
    return {'listener_count':len(groups),'episode_count':len(episodes),'paired_rows':len(rows),
            'mean_gain_100pt':float(delta.mean()),'listener_bootstrap_ci95':[float(low),float(high)],
            'status':'pilot_signal' if enough and low>0 else 'insufficient_evidence',
            'scope':'listener-cluster bootstrap conditional on tested episodes; no population/causal proof',
            'commercial_uplift_proven':False,'automatic_release':False}

def verify_asset(asset,manifest,as_of):
    """Evidence fields must be supplied by owner; never inferred from an extension."""
    from datetime import date
    p=Path(asset);today=date.fromisoformat(as_of)
    required=('sha256','origin','rights_record','license_id','reviewer','reviewed_at','valid_until')
    if not all(isinstance(manifest.get(k),str) and manifest[k].strip() for k in required):
        raise ValueError('Incomplete provenance')
    if manifest.get('commercial_use') is not True or manifest.get('sync_rights') is not True:
        raise ValueError('Commercial and synchronization permissions required')
    if not date.fromisoformat(manifest['reviewed_at'])<=today<=date.fromisoformat(manifest['valid_until']):
        raise ValueError('Review future-dated or expired')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('Asset changed')
    return {'contract_passed':True,'sha256':manifest['sha256'],
            'scope':'supplied declarations and hash verified; not a legal ownership determination',
            'editorial_approval':False}
