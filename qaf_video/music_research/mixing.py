"""M04: explicit beat-relative release using existing measured four-stem mix."""
import math
from ..audio import mix_audio

def release_ms(bpm,beats=.75):
    if not all(math.isfinite(v) for v in (bpm,beats)) or not 60<=bpm<=200 or not .1<=beats<=4:
        raise ValueError('Invalid beat timing')
    return max(100.,min(1500.,60000*beats/bpm))

def mix(output,voice,music,seconds=60.,bpm=124.,music_gain=.24):
    result=mix_audio(output,seconds,voice=voice,music=music,
                     profile={'gains':{'music':music_gain},'release_ms':release_ms(bpm)})
    # The existing function measures loudness; this wrapper does not certify taste.
    result['bpm']=bpm;result['release_beats']=.75;result['perceptual_approval']=False
    from ..core import atomic_json
    atomic_json(__import__('pathlib').Path(output).with_suffix('.audio.json'),result)
    return result
