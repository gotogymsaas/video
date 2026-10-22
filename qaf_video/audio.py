"""Four-stem mix, voice-driven ducking and measured two-pass loudness.

FFmpeg performs resampling, sidechain compression and ITU/EBU measurements.
The -14 LUFS web profile is an editorial choice, not EBU's -23 LUFS target.
"""
from __future__ import annotations
import json, math, os, re, tempfile, wave
from pathlib import Path
import numpy as np
from .core import require, run, atomic_json, sha256

TARGET_I = -14.0
TARGET_TP = -1.5  # Headroom for the subsequent AAC encode.


def measure(path, target_i=TARGET_I, target_tp=TARGET_TP):
    result = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-vn',
                  '-af', f'loudnorm=I={target_i}:TP={target_tp}:LRA=11:print_format=json',
                  '-f', 'null', '-'])
    records = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, re.S)
    require(bool(records), 'FFmpeg did not return loudness measurements')
    return json.loads(records[-1])


def mix_audio(output, seconds, voice=None, music=None, ambience=None, effects=None,profile=None):
    require(isinstance(seconds, (float, int)) and math.isfinite(seconds) and 0 < seconds <= 600,
            'Invalid audio duration')
    stems = {k: Path(v).resolve() for k, v in dict(voice=voice, music=music,
             ambience=ambience, effects=effects).items() if v is not None}
    require(bool(stems) and all(p.is_file() for p in stems.values()), 'Audio stems missing')
    output = Path(output).resolve()
    require(output.suffix.lower() == '.wav', 'Mix output must be WAV')
    output.parent.mkdir(parents=True, exist_ok=True)
    args = ['ffmpeg', '-y', '-v', 'error']
    graph = []
    gains = {'voice': 1., 'music': .18, 'ambience': .2, 'effects': .45}
    profile=profile or {};require(isinstance(profile,dict) and set(profile)<={'gains','release_ms'},'Invalid mix profile')
    overrides=profile.get('gains',{});require(isinstance(overrides,dict) and set(overrides)<=set(gains),'Unknown gain')
    require(all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=2 for v in overrides.values()),'Invalid gain')
    gains.update(overrides);release=float(profile.get('release_ms',450));require(math.isfinite(release) and 100<=release<=1500,'Invalid duck release')
    for i, (name, path) in enumerate(stems.items()):
        if name in ['music', 'ambience']:
            args += ['-stream_loop', '-1']
        args += ['-i', str(path)]
        graph.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,'
                     f'volume={gains[name]},apad,atrim=duration={seconds},asetpts=PTS-STARTPTS[{name}]')
    bed = [s for s in stems if s != 'voice']
    if bed:
        graph.append(''.join(f'[{s}]' for s in bed) +
                     f'amix=inputs={len(bed)}:normalize=0:duration=longest[bed]')
    if voice and bed:
        graph += ['[voice]asplit=2[mainvoice][sidechain]',
                  f'[bed][sidechain]sidechaincompress=threshold=0.025:ratio=8:attack=15:release={release}[ducked]',
                  '[mainvoice][ducked]amix=inputs=2:normalize=0:duration=longest[mix]']
    else:
        graph.append('[voice]anull[mix]' if voice else '[bed]anull[mix]')
    with tempfile.TemporaryDirectory(prefix='.audio_', dir=output.parent) as tmp:
        tmp = Path(tmp); raw = tmp / 'raw.wav'; normalized = tmp / 'normalized.wav'
        run(args + ['-filter_complex', ';'.join(graph), '-map', '[mix]', '-t', str(seconds),
                    '-ar', '48000', '-c:a', 'pcm_f32le', raw], timeout=180)
        first = measure(raw)
        require(all(math.isfinite(float(first[k])) for k in ['input_i', 'input_tp', 'input_lra', 'input_thresh']),
                'Silent or unmeasurable audio; supply a real recording or non-silent score')
        filt = (f'loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA=11:'
                f'measured_I={first["input_i"]}:measured_TP={first["input_tp"]}:'
                f'measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}:'
                f'offset={first["target_offset"]}:linear=true:print_format=json')
        run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', filt, '-ar', '48000',
             '-ac', '2', '-c:a', 'pcm_s24le', normalized], timeout=180)
        measured = measure(normalized)
        require(abs(float(measured['input_i']) - TARGET_I) <= 1.5 and
                float(measured['input_tp']) <= -1.0, 'Mix outside loudness/peak tolerance')
        os.replace(normalized, output)
    report = {'profile': 'web_editorial', 'target_lufs': TARGET_I, 'target_dbtp': TARGET_TP,
              'sample_rate': 48000, 'channels': 2, 'two_pass': True,
              'ducking': bool(voice and bed), 'input_measurement': first,
              'output_measurement': measured, 'stems_sha256': {s: sha256(p) for s, p in stems.items()},
              'output_sha256': sha256(output), 'requires_listening_review': True}
    report.update(gains=gains,duck_release_ms=release)
    atomic_json(output.with_suffix('.audio.json'), report)
    return report


def procedural_score(output, seconds=60, sample_rate=48000):
    """Original deterministic ambient fixture. No borrowed music or voice."""
    require(0 < seconds <= 600, 'Invalid score duration')
    t = np.arange(round(seconds * sample_rate), dtype=np.float64) / sample_rate
    chord = sum(np.sin(2 * np.pi * f * t + .15 * np.sin(.31 * t + i)) / (i + 2)
                for i, f in enumerate([130.8128, 196., 261.6256, 329.6276]))
    pulse = (.75 + .25 * np.sin(2 * np.pi * .25 * t))
    fade = np.minimum(1, t / 2) * np.minimum(1, (seconds - t) / 3)
    left = chord * pulse * fade * .12
    right = np.roll(chord, round(.007 * sample_rate)) * pulse * fade * .12
    pcm = np.int16(np.clip(np.column_stack([left, right]), -1, 1) * 32767)
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(sample_rate); f.writeframes(pcm.tobytes())
    return output
