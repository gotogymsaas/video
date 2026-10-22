"""Separate offline inference worker. Privacy policy precedes ML imports."""
import json
from pathlib import Path
import sys
import time


def transcribe_recording(path, model_path):
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from faster_whisper import WhisperModel
    from .voice_lab import decode
    model = WhisperModel(str(model_path), device='cpu', compute_type='int8',
                         cpu_threads=4, local_files_only=True)
    # FFmpeg decoding avoids PyAV version-dependent open() arguments.
    segments, info = model.transcribe(decode(path, 16000).astype('float32'), language='es',
                                     beam_size=5, word_timestamps=True, vad_filter=False,
                                     condition_on_previous_text=False)
    records = [{'start':float(s.start),'end':float(s.end),'text':s.text.strip(),
                'avg_logprob':float(s.avg_logprob),'no_speech_prob':float(s.no_speech_prob),
                'words':[{'start':float(w.start),'end':float(w.end),'word':w.word.strip(),
                          'probability':float(w.probability)} for w in (s.words or [])]}
               for s in segments]
    del model
    return {'text':' '.join(s['text'] for s in records),'segments':records,
            'timing_source':'local_asr_word_timestamps_unreviewed','model':Path(model_path).name}


def main():
    from .private_runtime import harden_local_runtime
    policy = harden_local_runtime()
    from .core import require,atomic_json,local_asset,sha256
    from .voice_lab import normalize_voice
    from .voice_local import caption_words,word_error_rate
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    started = time.perf_counter()
    if request['operation']=='transcribe':
        result=transcribe_recording(request['audio'],request['asr_model'])
    else:
        profile_path=Path(request['profile']).resolve()
        profile=json.loads(profile_path.read_text(encoding='utf-8'))
        reference=local_asset(profile_path.parent,profile['reference_audio'])
        require(sha256(reference)==profile['reference_sha256'],'Voice reference changed; rebuild the profile')
        ref_text=profile.get('reference_text')
        if not ref_text:
            transcript=transcribe_recording(reference,request['asr_model']);ref_text=transcript['text']
            require(bool(ref_text),'Reference transcription empty; provide a checked transcript')
            profile.update(reference_text=ref_text,reference_text_status='automatic_transcription_unreviewed')
            atomic_json(profile_path,profile)
        import gc
        gc.collect()
        import torch,soundfile as sf
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4);torch.manual_seed(request.get('seed',22))
        device=request.get('device','cpu')
        dtype=torch.float32 if device=='cpu' else torch.float16
        model=Qwen3TTSModel.from_pretrained(request['tts_model'],local_files_only=True,
                  trust_remote_code=False,device_map=device,dtype=dtype,attn_implementation='eager')
        output=Path(request['output']).resolve();output.parent.mkdir(parents=True,exist_ok=True)
        spoken=request['text']
        print('Generating local reference-conditioned speech',flush=True)
        token_budget=min(1500,max(96,len(spoken.split())*7+48))
        if request.get('target_seconds'):
            import math
            token_budget=min(token_budget,math.ceil((request['target_seconds']*1.08+1)*12))
        # The released model recommends sampling; greedy decoding can repeat
        # very short utterances. A fixed seed records the reproducible choice.
        waves,sr=model.generate_voice_clone(text=spoken,language='Spanish',ref_audio=str(reference),
                         ref_text=ref_text,x_vector_only_mode=False,do_sample=True,
                         max_new_tokens=token_budget)
        require(len(waves[0])/sr < token_budget/12-.08,
                'Speech generation reached its codec-token budget; shorten or rephrase the script and review the reference')
        raw=output.with_suffix('.unmastered.wav');sf.write(str(raw),waves[0],sr,subtype='PCM_24')
        del model;gc.collect()
        loudness=normalize_voice(raw,output)
        transcript=transcribe_recording(output,request['asr_model'])
        words=[w for s in transcript['segments'] for w in s['words']]
        timing=None
        if request.get('target_seconds') is not None:
            from .voice_timing import fit_voice
            import os
            timed=output.with_suffix('.timed.wav')
            timing=fit_voice(output,timed,request['target_seconds'],words);os.replace(timed,output)
            transcript=transcribe_recording(output,request['asr_model'])
            words=[w for s in transcript['segments'] for w in s['words']]
        captions=caption_words(words)
        error=word_error_rate(spoken,transcript['text'])
        from .voice import write_captions
        write_captions(output,captions)
        result={'provider':'Qwen3-TTS local reference-conditioned synthesis','synthetic':True,
                'model':Path(request['tts_model']).name,'reference_sha256':sha256(reference),
                'reference_text_status':profile.get('reference_text_status','user_supplied_unreviewed'),
                'text':spoken,'audio_sha256':sha256(output),'seconds':len(waves[0])/sr if timing is None else timing['target_seconds'],
                'sample_rate':48000,'loudness':loudness if timing is None else timing['loudness'],'transcript':transcript,
                'subtitles':captions,'word_error_rate':error,'timing_source':transcript['timing_source'],
                'regional_accent_approved':False,'speaker_similarity_human_review':'pending',
                'delivery_state':'needs_listening_review','seed':request.get('seed',22),'timing_fit':timing,
                'decoding':{'do_sample':True,'token_budget':token_budget,'model_defaults':'released generation_config.json'}}
        atomic_json(output.with_suffix('.voice.json'),result)
    result.update(privacy=policy,wall_seconds=time.perf_counter()-started)
    if request['operation']!='transcribe':atomic_json(output.with_suffix('.voice.json'),result)
    atomic_json(request['result'],result)


if __name__=='__main__':main()
