"""Measured reference-voice preparation, with bounded classical/QUBO selection.

No speaker identification, accent classifier or learned denoiser is implied.
The reference comes from the user's recording; DSP never invents its speech.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np

from .audio import measure
from .core import ValidationError, atomic_json, require, run, sha256
from .mathematics import solve_choices


def decode(path, sample_rate=16000, maximum_seconds=300):
    from .core import duration
    path = Path(path).resolve()
    require(path.is_file(), 'Voice recording not found')
    require(0 < duration(path) <= maximum_seconds, 'Voice recording must be 0–300 seconds')
    args = ['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-vn', '-ac', '1',
            '-ar', str(sample_rate), '-f', 'f32le', 'pipe:1']
    try:
        result = subprocess.run(args, check=True, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise ValidationError('Could not decode voice recording') from e
    x = np.frombuffer(result.stdout, dtype='<f4').astype(np.float64)
    require(x.size >= sample_rate * .15 and np.isfinite(x).all(), 'Invalid or empty voice recording')
    require(float(np.max(np.abs(x))) > 1e-7, 'Voice recording is silent')
    return x


def write_wav(path, x, sample_rate=48000):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    require(np.isfinite(x).all(), 'Nonfinite audio samples')
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sample_rate)
        f.writeframes(np.int16(np.clip(x, -1, 1) * 32767).tobytes())


def frames(x, sample_rate, milliseconds=40, hop_ms=10):
    size = round(sample_rate * milliseconds / 1000)
    hop = round(sample_rate * hop_ms / 1000)
    require(len(x) >= size, 'Audio too short for analysis')
    return np.lib.stride_tricks.sliding_window_view(x, size)[::hop]


def acoustic_metrics(x, sample_rate=16000):
    x = np.asarray(x, dtype=np.float64)
    f = frames(x, sample_rate)
    rms = np.sqrt(np.mean(f * f, axis=1) + 1e-18)
    db = 20 * np.log10(rms + 1e-12)
    active = db > max(-60., float(np.percentile(db, 90)) - 28.)
    window = np.hanning(f.shape[1])
    transform = np.fft.rfft((f - f.mean(axis=1, keepdims=True)) * window,
                            n=2 ** math.ceil(math.log2(f.shape[1] * 2)), axis=1)
    ac = np.fft.irfft(transform * transform.conj(), axis=1).real
    ac /= np.maximum(ac[:, :1], 1e-12)
    lo, hi = round(sample_rate / 420), round(sample_rate / 65)
    # Favor the first strong local peak, reducing octave-down errors.
    band = ac[:, lo:hi]
    local = (band[:, 1:-1] > band[:, :-2]) & (band[:, 1:-1] >= band[:, 2:])
    scored = np.where(local, band[:, 1:-1], -1.)
    maximum = scored.max(axis=1)
    acceptable = scored >= np.maximum(.52, maximum[:, None] * .90)
    lag = np.argmax(acceptable, axis=1) + lo + 1
    voiced = active & (maximum >= .52) & acceptable.any(axis=1)
    pitch = sample_rate / lag[voiced] if voiced.any() else np.array([])
    power = np.abs(transform) ** 2
    hz = np.fft.rfftfreq((transform.shape[1] - 1) * 2, 1 / sample_rate)
    centroid = np.sum(power * hz, axis=1) / np.maximum(power.sum(axis=1), 1e-12)
    active_db = float(np.median(db[active])) if active.any() else float(np.median(db))
    quiet_db = float(np.percentile(db, 15))
    return {
        'seconds': len(x) / sample_rate,
        'sample_peak_dbfs': float(20 * np.log10(max(np.max(np.abs(x)), 1e-12))),
        'clipped_fraction': float(np.mean(np.abs(x) >= .999)),
        'rms_dbfs': float(20 * np.log10(np.sqrt(np.mean(x*x)) + 1e-12)),
        'active_fraction': float(active.mean()),
        'voiced_fraction': float(voiced.mean()),
        'pitch_median_hz': float(np.median(pitch)) if len(pitch) >= 5 else None,
        'pitch_iqr_hz': float(np.percentile(pitch, 75) - np.percentile(pitch, 25)) if len(pitch) >= 5 else None,
        'active_centroid_hz': float(np.median(centroid[active])) if active.any() else 0.,
        'quiet_relative_to_active_db': quiet_db - active_db,
        'dynamic_range_proxy_db': float(np.percentile(db, 95) - np.percentile(db, 10)),
        'noise_estimate_available': bool(quiet_db < active_db - 9),
        'measurement_note': 'Energy/activity and quiet-level proxies; not ground-truth SNR, intelligibility, identity or accent.'
    }


def spectral_enhance(x, sample_rate=48000, strength=.4):
    """Wiener-style spectral attenuation with a protected speech-band floor.

    If there is no sufficiently quiet interval, noise attenuation abstains.
    Output length, phase and pitch grid remain unchanged. Highpass is gentle.
    """
    require(0 <= strength <= .8, 'Denoise strength must be 0–0.8')
    x = np.asarray(x, dtype=float)
    size = round(sample_rate * .032); hop = size // 4
    padding = size + ((-len(x)) % hop)
    padded = np.pad(x, (size, padding), mode='reflect')
    f = np.lib.stride_tricks.sliding_window_view(padded, size)[::hop]
    window = np.hanning(size)
    spectrum = np.fft.rfft(f * window, axis=1)
    power = np.abs(spectrum) ** 2
    energy = np.sqrt(np.mean(f*f, axis=1) + 1e-18)
    quiet = energy <= np.percentile(energy, 15)
    noise_available = np.percentile(energy, 15) < np.median(energy) * 10**(-9/20)
    noise = np.mean(power[quiet], axis=0) if noise_available else np.zeros(power.shape[1])
    gain = np.maximum(0, 1 - strength * noise / np.maximum(power, 1e-15)) ** .5
    hz = np.fft.rfftfreq(size, 1/sample_rate)
    floor = np.where((hz >= 100) & (hz <= 6000), .58, .32)
    gain = np.maximum(gain, floor)
    gain = (np.roll(gain, 1, axis=1) + 2*gain + np.roll(gain, -1, axis=1)) / 4
    gain = (np.vstack([gain[:1], gain[:-1]]) + 2*gain + np.vstack([gain[1:], gain[-1:]])) / 4
    highpass = hz / np.sqrt(hz*hz + 65**2)
    lowpass = 1 / np.sqrt(1 + (hz/14000)**8)
    gain *= highpass * lowpass
    recovered = np.fft.irfft(spectrum * gain, n=size, axis=1) * window
    out = np.zeros(len(padded)); norm = np.zeros(len(padded))
    for i, frame in enumerate(recovered):
        start = i*hop;out[start:start+size] += frame;norm[start:start+size] += window*window
    out /= np.maximum(norm, 1e-12)
    return out[size:size+len(x)]


def preservation_metrics(original, processed, sample_rate=16000):
    before, after = acoustic_metrics(original, sample_rate), acoustic_metrics(processed, sample_rate)
    a, b = frames(original, sample_rate), frames(processed, sample_rate)
    window = np.hanning(a.shape[1])
    aa, bb = np.abs(np.fft.rfft(a*window, axis=1)), np.abs(np.fft.rfft(b*window, axis=1))
    hz = np.fft.rfftfreq(a.shape[1],1/sample_rate)
    active = np.sqrt(np.mean(a*a,axis=1)) > np.max(np.sqrt(np.mean(a*a,axis=1))) * .05
    band = (hz >= 140) & (hz <= 4000)
    drift = float(np.mean(np.abs(20*np.log10((bb[active][:,band]+1e-6)/(aa[active][:,band]+1e-6)))))
    semitones = None
    if before['pitch_median_hz'] and after['pitch_median_hz']:
        semitones = float(12*np.log2(after['pitch_median_hz']/before['pitch_median_hz']))
    quiet_change = before['quiet_relative_to_active_db']-after['quiet_relative_to_active_db']
    return {'speech_band_mean_change_db':drift,'pitch_median_change_semitones':semitones,
            'relative_quiet_reduction_db':quiet_change,
            'length_preserved':len(original)==len(processed),
            'passed':bool(drift<=3 and (semitones is None or abs(semitones)<=.6) and len(original)==len(processed)),
            'note':'Preservation constraints are engineering proxies; listening is still required.'}


def normalize_voice(source, output, target_i=-18., target_tp=-2.):
    first = measure(source, target_i=target_i, target_tp=target_tp)
    require(math.isfinite(float(first['input_i'])), 'Cannot normalize silent voice')
    filt = (f'loudnorm=I={target_i}:TP={target_tp}:LRA=11:'
            f'measured_I={first["input_i"]}:measured_TP={first["input_tp"]}:'
            f'measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}:'
            f'offset={first["target_offset"]}:linear=true')
    run(['ffmpeg','-y','-v','error','-i',source,'-af',filt,'-ar','48000','-ac','1','-c:a','pcm_s24le',output])
    final=measure(output,target_i=target_i,target_tp=target_tp)
    corrections=0
    # Very short, high-crest voice notes may hit TP before the integrated target.
    # Correct gain behind an explicit lookahead limiter, then measure again.
    for _ in range(3):
        if abs(float(final['input_i'])-target_i)<=.5 and float(final['input_tp'])<=target_tp+.1:break
        correction=target_i-float(final['input_i'])
        with tempfile.TemporaryDirectory(prefix='.peak_',dir=Path(output).parent) as tmp:
            stage=Path(tmp)/'limited.wav'
            limit=10**((target_tp-.35)/20)
            run(['ffmpeg','-y','-v','error','-i',output,'-af',
                 f'aresample=192000,volume={correction}dB,alimiter=limit={limit}:level=false:latency=true,aresample=48000',
                 '-ar','48000','-ac','1','-c:a','pcm_s24le',stage])
            os.replace(stage,output)
        corrections+=1;final=measure(output,target_i=target_i,target_tp=target_tp)
    final['peak_control_passes']=corrections
    require(abs(float(final['input_i'])-target_i)<=.8 and float(final['input_tp'])<=target_tp+.2,
            'Processed voice exceeds loudness or true-peak tolerance')
    return final


def prepare_voice(files, output, name='Voz de referencia · Barranquilla', progress=None):
    require(1<=len(files)<=12,'Provide 1–12 voice recordings')
    output=Path(output).resolve();require(not (output/'voice-profile.json').exists(),'Voice profile already exists; choose a new folder')
    output.mkdir(parents=True,exist_ok=True)
    originals=[];candidates=[];choices=[]
    strengths=[0.,.25,.5,.75]
    for i,path in enumerate(files):
        path=Path(path).resolve();x=decode(path,48000);a=decode(path,16000)
        baseline=acoustic_metrics(a);originals.append((path,x,baseline));group=[];signals=[]
        for j,strength in enumerate(strengths):
            y=spectral_enhance(x,48000,strength)
            # Anti-alias safely for measurements instead of plain decimation.
            # Analysis uses an FFT resampling lowpass at 7.5 kHz.
            spec=np.fft.rfft(y);freq=np.fft.rfftfreq(len(y),1/48000)
            measured=np.fft.irfft(spec*(freq<=7500),n=len(y))[::3][:len(a)]
            aa=a[:len(measured)];preserve=preservation_metrics(aa,measured)
            utility=preserve['relative_quiet_reduction_db']-.45*preserve['speech_band_mean_change_db']-.05*j
            if not preserve['passed']:utility=-1000
            group.append({'sample':i+1,'preset':['neutral','gentle','clean','studio'][j],
                          'strength':strength,'utility':float(utility),'cost':j+1,'preservation':preserve})
            signals.append(y)
        # Neutral still has a highpass; if all constraints fail use exact original.
        if not any(g['preservation']['passed'] for g in group):
            group[0].update(utility=0.,preservation=preservation_metrics(a,a),preset='original_preserved');signals[0]=x.copy()
        candidates.append(signals);choices.append(group)
        if progress:progress(.5*(i+1)/len(files))
    plan=solve_choices(choices,budget=3*len(files))
    reports=[];references=[]
    with tempfile.TemporaryDirectory(prefix='.voice_',dir=output) as tmp:
        tmp=Path(tmp)
        for i,(path,x,baseline) in enumerate(originals):
            chosen=plan['selected'][i];j=plan['selected_indices'][i]-4*i;y=candidates[i][j]
            stem=f'sample-{i+1:02d}';raw=tmp/(stem+'.wav');write_wav(raw,x)
            equal=output/(stem+'-original-matched.wav');before=normalize_voice(raw,equal)
            write_wav(raw,y);clean=output/(stem+'-processed.wav');after=normalize_voice(raw,clean)
            report={'sample':i+1,'source_name':path.name,'source_sha256':sha256(path),'baseline':baseline,
                    'chosen':chosen,'original_matched':equal.name,'processed':clean.name,
                    'original_loudness':before,'processed_loudness':after,'processed_sha256':sha256(clean)}
            reports.append(report)
            seconds=len(y)/48000
            if seconds>=4:
                width=min(10.,seconds);starts=np.linspace(0,max(0,seconds-width),3)
                for start in sorted(set(starts.tolist())):
                    cut=y[round(start*48000):round((start+width)*48000)]
                    down=cut[::3];m=acoustic_metrics(down)
                    score=4*m['voiced_fraction']+m['active_fraction']-.03*abs(width-8)-100*m['clipped_fraction']
                    references.append({'sample':i+1,'start':float(start),'end':float(start+width),
                                       'utility':float(score),'cost':math.ceil(width),'source':clean.name})
            if progress:progress(.5+.4*(i+1)/len(files))
        require(bool(references),'Need at least one recording of four seconds for a useful voice reference')
        reference_plan=solve_choices([references],budget=12)
        selected=reference_plan['selected'][0]
        clean=decode(output/selected['source'],48000)
        reference=clean[round(selected['start']*48000):round(selected['end']*48000)]
        raw=tmp/'reference.wav';write_wav(raw,reference)
        normalize_voice(raw,output/'reference.wav')
    profile={'schema':'qaf_voice_profile_v1','name':name,'language':'Spanish','region_description':'Barranquilla, Colombia; supplied by user',
             'reference_audio':'reference.wav','reference_sha256':sha256(output/'reference.wav'),
             'reference_selection':selected,'reference_text':None,'reference_text_status':'not_transcribed',
             'speaker_identity':'user-supplied single-speaker assumption, not machine verified',
             'regional_accent_approved':False,'synthesis_status':'reference_prepared; no trained model claimed',
             'review_required':['reference content and speaker','naturalness','Barranquilla accent','pronunciation'],
             'samples':reports,'planner':plan,'reference_planner':reference_plan,
             'optimization_note':'Constrained exact classical baseline and equivalent QUBO; heuristic weights; no quantum superiority claim.'}
    atomic_json(output/'voice-profile.json',profile)
    write_review_page(profile,output)
    if progress:progress(1.)
    return profile


def write_review_page(profile,output,generated=None):
    """Self-contained offline A/B review; no analytics, scripts or remote assets."""
    from html import escape
    output=Path(output);cards=[]
    for sample in profile['samples']:
        p=sample['chosen']['preservation']
        cards.append('<article><h2>Muestra '+str(sample['sample'])+'</h2><div class="pair">'+
            '<div><p>Original con volumen igualado</p><audio controls preload="none" src="'+escape(sample['original_matched'],quote=True)+'"></audio></div>'+
            '<div><p>Procesada · '+escape(sample['chosen']['preset'])+'</p><audio controls preload="none" src="'+escape(sample['processed'],quote=True)+'"></audio></div></div>'+
            '<details><summary>Controles medidos</summary><p>Cambio mediano de tono: '+
            f'{p["pitch_median_change_semitones"] or 0:.3f} semitonos. Duración conservada: '+str(p['length_preserved'])+
            '. Las medidas acústicas no certifican naturalidad ni acento.</p></details></article>')
    preview=''
    if generated:
        preview='<article><h2>Locución nueva · voz sintética</h2><audio controls src="'+escape(generated,quote=True)+'"></audio><p>Guion nuevo generado con la referencia. Aprobación de timbre, acento y pronunciación pendiente.</p></article>'
    text='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GoToGym · Revisión de voz</title><style>body{background:#101418;color:#ecf5f1;font:16px/1.6 system-ui;margin:0 auto;max-width:1000px;padding:30px}h1{font-size:38px;line-height:1.15}h2{font-size:20px;color:#54d5bb}article{padding:22px;background:#192329;margin:20px 0;border:1px solid #34474b;border-radius:14px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}audio{width:100%}p{color:#bccfc9}summary{cursor:pointer;color:#d4b46a}small{color:#adbcba}@media(max-width:650px){.pair{grid-template-columns:1fr}body{padding:18px}}</style><h1>Tu voz. Una referencia real.</h1><p>Compara cada par al mismo volumen. Revisa claridad, respiraciones, timbre y naturalidad. Las notas originales son una referencia privada; el contenido del anuncio se genera a partir de otro guion.</p>'''+preview+'''
<article><h2>Referencia seleccionada</h2><audio controls src="reference.wav"></audio><p>Fragmento seleccionado con restricciones de señal y presupuesto. El origen barranquillero procede de la descripción aportada; requiere tu aprobación al escuchar.</p></article>'''+''.join(cards)+'''<small>GoToGym Quantum Coach · selección matemática clásica con auditoría QUBO · revisión humana pendiente.</small></html>'''
    (output/'escuchar.html').write_text(text,encoding='utf-8')
