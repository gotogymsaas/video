"""QAF editorial adapters: constrained camera paths and evidence-timed reveals.

Classical interpolation and deterministic scheduling, not quantum advantage.
Normalized crop geometry is shared by both renderers.
"""
import math
from .core import require
from .mathematics import minimum_jerk


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def validate_motion(motion):
    require(isinstance(motion, dict) and set(motion) == {'keyframes'}, 'Motion needs keyframes')
    keys = motion['keyframes']
    require(isinstance(keys, list) and 2 <= len(keys) <= 32, '2–32 keyframes required')
    previous = -1
    for key in keys:
        require(isinstance(key, dict) and set(key) == {'at', 'focus', 'zoom'}, 'Invalid motion key')
        at, focus, zoom = key['at'], key['focus'], key['zoom']
        require(number(at) and previous < at <= 1, 'Motion time must increase in [0,1]')
        require(isinstance(focus, list) and len(focus) == 2 and all(number(v) and 0 <= v <= 1 for v in focus), 'Invalid motion focus')
        require(number(zoom) and 1 <= zoom <= 1.7, 'Invalid motion zoom')
        previous = at
    require(keys[0]['at'] == 0 and keys[-1]['at'] == 1, 'Motion must cover [0,1]')
    return keys


def camera_sample(shot, u):
    require(number(u), 'Invalid sample time')
    u = min(1., max(0., u))
    if 'motion' not in shot:
        z = shot.get('zoom', [1., 1.]);f = shot.get('focus', [.5, .5])
        return tuple(f), z[0] + (z[1]-z[0])*float(minimum_jerk(u))
    keys = validate_motion(shot['motion'])
    a, b = next(((a,b) for a,b in zip(keys, keys[1:]) if a['at'] <= u <= b['at']))
    w = float(minimum_jerk((u-a['at'])/(b['at']-a['at'])))
    return tuple(x+(y-x)*w for x,y in zip(a['focus'],b['focus'])), a['zoom']+(b['zoom']-a['zoom'])*w


def crop_box(source, target, focus, zoom):
    iw, ih = source;w,h = target
    require(all(number(v) and v > 0 for v in (iw,ih,w,h)), 'Invalid image dimensions')
    require(number(zoom) and 1 <= zoom <= 1.7, 'Invalid crop zoom')
    require(len(focus)==2 and all(number(v) and 0<=v<=1 for v in focus), 'Invalid crop focus')
    scale=max(w/iw,h/ih)*zoom;cw,ch=w/scale,h/scale
    cx=min(iw-cw/2,max(cw/2,focus[0]*iw));cy=min(ih-ch/2,max(ch/2,focus[1]*ih))
    return (max(0.,cx-cw/2),max(0.,cy-ch/2),min(iw,cx+cw/2),min(ih,cy+ch/2))


def reveal_times(shot, subtitles):
    """Resolve local starts from measured captions, never infer speech timing."""
    nodes=shot.get('nodes', []);cues=shot.get('node_cues')
    if cues is None:return [i*.23 for i in range(len(nodes))]
    require(isinstance(cues,list) and len(cues)==len(nodes), 'One cue per node required')
    duration=shot['end']-shot['start'];result=[]
    for index in cues:
        require(type(index) is int and 0<=index<len(subtitles), 'Invalid subtitle cue')
        cue=subtitles[index]
        require(number(cue['start']) and number(cue['end']) and cue['start']<cue['end'], 'Invalid measured cue')
        start=cue['start']-shot['start']
        require(0<=start<duration, 'Node cue outside shot')
        result.append(start)
    require(result==sorted(result), 'Node cues must preserve order')
    return result


def reveal_progress(local, start, seconds=.45):
    require(number(seconds) and seconds>0, 'Invalid reveal duration')
    return float(minimum_jerk((local-start)/seconds))
