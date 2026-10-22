"""Optional online TTS adapter; recorded voice remains a first-class input.

Never infer a Barranquilla accent from an es-CO locale identifier. A director
and local speaker must audition and approve the actual recording.
"""
from __future__ import annotations
import asyncio, os, tempfile
from pathlib import Path
from .core import require, ValidationError, atomic_json, sha256, duration


def captions_from_boundaries(boundaries, max_chars=68):
    cues = []; words = []; start = end = 0.
    for b in boundaries:
        text = b['text'].strip()
        require(bool(text) and len(text) <= 90, 'TTS boundary text too long for captions')
        a, z = b['offset'] / 1e7, (b['offset'] + b['duration']) / 1e7
        require(z > a >= 0, 'Invalid TTS timing')
        if words and (len(' '.join(words + [text])) > max_chars or z - start > 4.5):
            cues.append({'start': start, 'end': end, 'text': ' '.join(words)}); words = []
        if not words: start = a
        words.append(text); end = z
    if words: cues.append({'start': start, 'end': end, 'text': ' '.join(words)})
    return cues


def write_captions(base,cues):
    base=Path(base);base.parent.mkdir(parents=True,exist_ok=True)
    """Export measured/imported timings to SRT and WebVTT without stretching."""
    def stamp(t,comma=False):
        ms=round(t*1000);seconds,ms=divmod(ms,1000);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}{"," if comma else "."}{ms:03d}'
    base=Path(base)
    for suffix,comma in [('.srt',True),('.vtt',False)]:
        text='WEBVTT\n\n' if suffix=='.vtt' else ''
        text+='\n\n'.join(f'{i+1}\n{stamp(c["start"],comma)} --> {stamp(c["end"],comma)}\n{c["text"]}' for i,c in enumerate(cues))+'\n'
        base.with_suffix(suffix).write_text(text,encoding='utf-8')


async def available_voices(locale='es-CO'):
    try: import edge_tts
    except ImportError as e: raise ValidationError('Install the voice extra: pip install ".[voice]"') from e
    voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=35)
    return [v for v in voices if v.get('Locale') == locale]


async def synthesize(text, output, voice='es-CO-SalomeNeural', rate='+0%', pitch='+0Hz'):
    require(isinstance(text, str) and 1 <= len(text.strip()) <= 5000, 'Voice text must contain 1–5000 characters')
    output = Path(output).resolve(); require(output.suffix.lower() == '.mp3', 'TTS output must be MP3')
    try: import edge_tts
    except ImportError as e: raise ValidationError('Install the optional voice extra: pip install ".[voice]"') from e
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.voice_', dir=output.parent) as tmp:
        tmp_audio = Path(tmp) / 'speech.mp3'
        async def stream():
            boundaries = []
            with tmp_audio.open('wb') as f:
                async for part in edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                                     boundary='WordBoundary').stream():
                    if part['type'] == 'audio': f.write(part['data'])
                    elif part['type'] == 'WordBoundary': boundaries.append(part)
            return boundaries
        try: boundaries = await asyncio.wait_for(stream(), timeout=90)
        except Exception as e: raise ValidationError(f'Online voice service unavailable: {type(e).__name__}. Supply a recorded voice instead.') from e
        require(tmp_audio.exists() and tmp_audio.stat().st_size > 0, 'Empty TTS result')
        seconds = duration(tmp_audio); captions = captions_from_boundaries(boundaries)
        require(bool(captions), 'TTS returned no real timing metadata; no captions were invented')
        require(captions[-1]['end'] <= seconds + .08, 'TTS timing exceeds audio duration')
        os.replace(tmp_audio, output)
    report = {'provider': 'edge-tts online service', 'voice': voice, 'rate': rate, 'pitch': pitch,
              'audio_sha256': sha256(output), 'seconds': seconds, 'subtitles': captions,
              'timing_source': 'service_word_boundaries', 'regional_accent_approved': False,
              'accent_note': 'Colombian locale is not a certified Barranquilla accent; requires local audition.'}
    atomic_json(output.with_suffix('.voice.json'), report)
    write_captions(output,captions)
    return report
