"""Separate offline inference worker. Privacy policy precedes ML imports."""
import json
from pathlib import Path
import sys
import time


def transcribe_recording(path, model_path, language='Spanish', spans=None):
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from faster_whisper import WhisperModel
    from .voice_lab import decode
    from .voice_languages import LANGUAGES,normalize_language
    model = WhisperModel(str(model_path), device='cpu', compute_type='int8',
                         cpu_threads=4, local_files_only=True)
    # FFmpeg decoding avoids PyAV version-dependent open() arguments.
    audio=decode(path,16000).astype('float32');records=[];languages=[]
    spans=spans if spans is not None else [{'start':0.,'end':len(audio)/16000,'language':normalize_language(language)}]
    for index,span in enumerate(spans):
        a=max(0,round(span['start']*16000));z=min(len(audio),round(span['end']*16000))
        if z<=a:continue
        offset=a/16000;duration=(z-a)/16000;requested=normalize_language(span['language'])
        segments, info = model.transcribe(audio[a:z],language=LANGUAGES[requested],task='transcribe',
                                         beam_size=5,word_timestamps=True,vad_filter=False,
                                         condition_on_previous_text=False)
        for s in segments:
            words=[{'start':offset+min(duration,max(0.,float(w.start))),
                    'end':offset+min(duration,max(0.,float(w.end))),'word':w.word.strip(),
                    'probability':float(w.probability)} for w in (s.words or []) if w.end>w.start]
            words=[w for w in words if w['end']>w['start']]
            records.append({'start':offset+min(duration,max(0.,float(s.start))),
                            'end':offset+min(duration,max(0.,float(s.end))),'text':s.text.strip(),
                            'avg_logprob':float(s.avg_logprob),'no_speech_prob':float(s.no_speech_prob),
                            'words':words,'phrase_index':index,'language_requested':requested})
        languages.append({'phrase_index':index,'requested':requested,'asr_language_used':info.language,
                          'automatic_detection':requested=='Auto',
                          'detected_probability':float(info.language_probability) if requested=='Auto' else None})
    del model
    return {'text':' '.join(s['text'] for s in records),'segments':records,
            'timing_source':'local_asr_word_timestamps_unreviewed','model':Path(model_path).name,
            'languages':languages}


def main():
    from .private_runtime import harden_local_runtime
    policy = harden_local_runtime()
    from .core import require,atomic_json,local_asset,sha256
    from .voice_lab import normalize_voice
    from .voice_local import caption_words,word_error_rate
    from .voice_languages import normalize_language,speech_plan,codec_token_budget,script_comparison,retime_spans
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    started = time.perf_counter()
    if request['operation']=='transcribe':
        result=transcribe_recording(request['audio'],request['asr_model'],request.get('language','Spanish'))
    else:
        profile_path=Path(request['profile']).resolve()
        profile=json.loads(profile_path.read_text(encoding='utf-8'))
        reference=local_asset(profile_path.parent,profile['reference_audio'])
        require(sha256(reference)==profile['reference_sha256'],'Voice reference changed; rebuild the profile')
        reference_language=normalize_language(profile.get('language','Spanish'))
        plan=speech_plan(request['text'],request.get('language','Spanish'),request.get('segments'))
        ref_text=profile.get('reference_text')
        if not ref_text:
            transcript=transcribe_recording(reference,request['asr_model'],reference_language);ref_text=transcript['text']
            require(bool(ref_text),'Reference transcription empty; provide a checked transcript')
            profile.update(reference_text=ref_text,reference_text_status='automatic_transcription_unreviewed')
            atomic_json(profile_path,profile)
        import gc
        gc.collect()
        import torch,soundfile as sf,numpy as np
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4);torch.manual_seed(request.get('seed',22))
        device=request.get('device','cpu')
        dtype=torch.float32 if device=='cpu' else torch.float16
        model=Qwen3TTSModel.from_pretrained(request['tts_model'],local_files_only=True,
                  trust_remote_code=False,device_map=device,dtype=dtype,attn_implementation='eager')
        output=Path(request['output']).resolve();output.parent.mkdir(parents=True,exist_ok=True)
        spoken=' '.join(p['text'] for p in plan)
        print('Generating local reference-conditioned speech',flush=True)
        supported={v.casefold() for v in (model.get_supported_languages() or [])}
        require(all(p['language'].casefold() in supported for p in plan),'Loaded model does not support a requested language')
        prompt=model.create_voice_clone_prompt(ref_audio=str(reference),ref_text=ref_text,x_vector_only_mode=False)
        pieces=[];spans=[];cursor=0;budgets=[];sr=None
        # The released model recommends sampling; greedy decoding can repeat
        # very short utterances. A fixed seed records the reproducible choice.
        for index,part in enumerate(plan):
            budget=codec_token_budget(part['text'],request.get('target_seconds'));budgets.append(budget)
            waves,part_sr=model.generate_voice_clone(text=part['text'],language=part['language'],
                             voice_clone_prompt=prompt,do_sample=True,max_new_tokens=budget)
            require(sr is None or sr==part_sr,'Inconsistent speech sample rate');sr=part_sr
            wave=np.asarray(waves[0],dtype=np.float32).copy()
            require(wave.ndim==1 and len(wave)>0 and np.isfinite(wave).all(),'Invalid generated waveform')
            require(len(wave)/sr < budget/12-.08,
                    'Speech generation reached its codec-token budget; shorten or rephrase the script and review the reference')
            # Tiny fades prevent a click at joins; language changes use a short pause.
            fade=min(round(.003*sr),len(wave)//2)
            if fade:wave[:fade]*=np.linspace(0,1,fade);wave[-fade:]*=np.linspace(1,0,fade)
            if index:
                gap=np.zeros(round(.12*sr),dtype=np.float32);pieces.append(gap);cursor+=len(gap)
            spans.append({**part,'start':cursor/sr,'end':(cursor+len(wave))/sr})
            pieces.append(wave);cursor+=len(wave)
            print(f'Generated phrase {index+1}/{len(plan)} ({part["language"]})',flush=True)
        combined=np.concatenate(pieces)
        raw=output.with_suffix('.unmastered.wav');sf.write(str(raw),combined,sr,subtype='PCM_24')
        del model,prompt;gc.collect()
        loudness=normalize_voice(raw,output)
        transcript=transcribe_recording(output,request['asr_model'],spans=spans)
        words=[w for s in transcript['segments'] for w in s['words']]
        timing=None
        if request.get('target_seconds') is not None:
            from .voice_timing import fit_voice
            import os
            timed=output.with_suffix('.timed.wav')
            timing=fit_voice(output,timed,request['target_seconds'],words);os.replace(timed,output)
            transcript=transcribe_recording(output,request['asr_model'],spans=retime_spans(spans,timing))
            words=[w for s in transcript['segments'] for w in s['words']]
        captions=caption_words(words)
        checks=[]
        for index,part in enumerate(plan):
            recognized=' '.join(s['text'] for s in transcript['segments'] if s['phrase_index']==index)
            checks.append(script_comparison(part['text'],recognized,part['language']))
        comparison={'rate':max(c['rate'] for c in checks),'aggregation':'worst_phrase',
                    'phrases':checks,'note':'A longer Spanish phrase cannot hide an omitted foreign phrase.'}
        error=word_error_rate(spoken,transcript['text']) if all(c['unit']=='word' for c in checks) else None
        from .voice import write_captions
        write_captions(output,captions)
        result={'provider':'Qwen3-TTS local reference-conditioned synthesis','synthetic':True,
                'model':Path(request['tts_model']).name,'reference_sha256':sha256(reference),
                'reference_text_status':profile.get('reference_text_status','user_supplied_unreviewed'),
                'text':spoken,'audio_sha256':sha256(output),'seconds':len(combined)/sr if timing is None else timing['target_seconds'],
                'sample_rate':48000,'loudness':loudness if timing is None else timing['loudness'],'transcript':transcript,
                'subtitles':captions,'word_error_rate':error,'script_comparison':comparison,'timing_source':transcript['timing_source'],
                'reference_language':reference_language,'language_mode':'per_phrase' if len(plan)>1 else plan[0]['language'],
                'language_phrases':retime_spans(spans,timing),'pronunciation_human_review':'pending',
                'regional_accent_approved':False,'speaker_similarity_human_review':'pending',
                'delivery_state':'needs_listening_review','seed':request.get('seed',22),'timing_fit':timing,
                'decoding':{'do_sample':True,'token_budget':budgets[0] if len(budgets)==1 else budgets,
                            'model_defaults':'released generation_config.json'}}
        atomic_json(output.with_suffix('.voice.json'),result)
    result.update(privacy=policy,wall_seconds=time.perf_counter()-started)
    if request['operation']!='transcribe':atomic_json(output.with_suffix('.voice.json'),result)
    atomic_json(request['result'],result)


if __name__=='__main__':main()
