import json,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
import numpy as np
from unittest.mock import patch
from types import SimpleNamespace
from qaf_video.core import ValidationError
from qaf_video.voice_lab import acoustic_metrics,spectral_enhance,preservation_metrics
from qaf_video.voice_local import caption_words,word_error_rate,runtime_settings,synthesize_local
from qaf_video.voice_languages import normalize_language,speech_plan,codec_token_budget,script_comparison,retime_spans


class VoiceSignalTests(unittest.TestCase):
    def test_known_fundamental_and_pitch_preservation(self):
        sr=16000;t=np.arange(sr*2)/sr
        x=.15*np.sin(2*np.pi*200*t)+.05*np.sin(2*np.pi*400*t)
        before=acoustic_metrics(x,sr);y=spectral_enhance(x,sr,.5)
        self.assertAlmostEqual(before['pitch_median_hz'],200,delta=3)
        self.assertEqual(len(x),len(y));self.assertTrue(np.isfinite(y).all())
        p=preservation_metrics(x,y,sr);self.assertTrue(p['passed'])
        self.assertLess(abs(p['pitch_median_change_semitones']),.3)
    def test_noise_only_regions_improve_against_known_clean_fixture(self):
        sr=16000;t=np.arange(sr*3)/sr;rng=np.random.default_rng(2)
        envelope=((t>.6)&(t<2.4)).astype(float)
        clean=.14*np.sin(2*np.pi*220*t)*envelope
        x=clean+rng.normal(0,.012,len(t));y=spectral_enhance(x,sr,.7)
        quiet=(t<.4)|(t>2.6)
        self.assertLess(np.mean(y[quiet]**2),np.mean(x[quiet]**2))
        self.assertGreater(np.sqrt(np.mean(y[envelope>0]**2)),.08)
    def test_invalid_strength_and_silent_decode_rejected(self):
        with self.assertRaises(ValidationError):spectral_enhance(np.ones(16000),16000,5)
    def test_word_error_does_not_hide_missing_script(self):
        self.assertEqual(word_error_rate('Hola, QUÉ tal.','hola que tal')['rate'],0)
        self.assertEqual(word_error_rate('hola mundo nuevo','hola nuevo')['edits'],1)
        with self.assertRaises(ValidationError):word_error_rate('','algo')
    def test_captions_use_measured_word_times(self):
        c=caption_words([{'start':.3,'end':.8,'word':'Hola'},{'start':1.2,'end':1.6,'word':'mundo'}])
        self.assertEqual(c,[{'start':.3,'end':1.6,'text':'Hola mundo'}])
    def test_changed_reference_blocks_synthesis_before_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'ref.wav').write_bytes(b'audio')
            p={'schema':'qaf_voice_profile_v1','reference_audio':'ref.wav','reference_sha256':'wrong'}
            (root/'profile.json').write_text(json.dumps(p))
            with self.assertRaisesRegex(ValidationError,'reference changed'):
                synthesize_local(root/'profile.json','Hola',root/'out.wav')
    def test_interpreter_keeps_virtual_environment_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'bin').mkdir();exe=root/'bin/python';exe.symlink_to(sys.executable)
            (root/'model.safetensors').write_bytes(b'fixture');(root/'model.bin').write_bytes(b'fixture')
            actual,_,_=runtime_settings(exe,root,root);self.assertEqual(actual,exe.absolute())


class MultilingualVoiceTests(unittest.TestCase):
    def test_mixed_plan_retains_language_and_rejects_ambiguous_input(self):
        parts=speech_plan('',segments=[{'text':'Hoy hablamos de','language':'es'},
                                      {'text':'machine learning','language':'en'}])
        self.assertEqual([p['language'] for p in parts],['Spanish','English'])
        for invalid in [[],[{'text':''}],[{'text':'Hello','language':'unknown'}]]:
            with self.assertRaises(ValidationError):speech_plan('',segments=invalid)
        with self.assertRaises(ValidationError):speech_plan('Duplicated',segments=parts)
        with self.assertRaises(ValidationError):speech_plan('',segments=[{'text':'a'*2500}]*3)
        self.assertEqual(normalize_language('ENGLISH'),'English')
    def test_cjk_budget_and_character_comparison_do_not_require_spaces(self):
        self.assertGreater(codec_token_budget('科学技术让生活更加清晰而自然'*4),96)
        comparison=script_comparison('科学技术','科学','Chinese')
        self.assertEqual(comparison['unit'],'character');self.assertEqual(comparison['rate'],.5)
        self.assertEqual(script_comparison('machine learning','machine','English')['rate'],.5)
    def test_span_offsets_include_actual_pause_insertions(self):
        mapped=retime_spans([{'start':2.,'end':4.,'language':'English'}],
                            {'tempo_factor':.8,'lead_seconds':.15,'pause_insertions':[{'at_seconds':3.,'seconds':.5}]})
        self.assertAlmostEqual(mapped[0]['start'],2.65);self.assertAlmostEqual(mapped[0]['end'],5.65)
    def test_target_language_does_not_replace_reference_language(self):
        from qaf_video.core import sha256
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'ref.wav').write_bytes(b'fixture')
            p={'schema':'qaf_voice_profile_v1','reference_audio':'ref.wav','reference_sha256':sha256(root/'ref.wav'),
               'language':'Spanish'}
            (root/'profile.json').write_text(json.dumps(p))
            with patch('qaf_video.voice_local.runtime_settings',return_value=(Path(sys.executable),root,root)),\
                 patch('qaf_video.voice_local._worker',return_value={}) as worker:
                synthesize_local(root/'profile.json','Clear technology.',root/'out.wav',language='en')
            request=worker.call_args.args[0]
            self.assertEqual(request['language'],'English')
            self.assertEqual(json.loads((root/'profile.json').read_text())['language'],'Spanish')
    def test_asr_uses_each_phrase_language_and_offsets_without_claiming_detection(self):
        from qaf_video.local_voice_worker import transcribe_recording
        calls=[]
        class Recognizer:
            def __init__(self,*args,**kwargs):pass
            def transcribe(self,audio,**options):
                calls.append(options)
                word=SimpleNamespace(start=.1,end=.6,word='voice',probability=.9)
                segment=SimpleNamespace(start=.1,end=.6,text='voice',avg_logprob=-.1,no_speech_prob=.01,words=[word])
                return [segment],SimpleNamespace(language=options['language'] or 'en',language_probability=.9)
        modules={'onnxruntime':SimpleNamespace(disable_telemetry_events=lambda:None),
                 'faster_whisper':SimpleNamespace(WhisperModel=Recognizer)}
        spans=[{'start':0,'end':1,'language':'Spanish'},{'start':2,'end':3,'language':'English'},
               {'start':4,'end':5,'language':'Auto'}]
        with patch.dict(sys.modules,modules),patch('qaf_video.voice_lab.decode',return_value=np.zeros(5*16000)):
            result=transcribe_recording('fixture.wav','model',spans=spans)
        self.assertEqual([c['language'] for c in calls],['es','en',None])
        self.assertTrue(all(c['task']=='transcribe' for c in calls))
        self.assertAlmostEqual(result['segments'][1]['words'][0]['start'],2.1)
        self.assertIsNone(result['languages'][1]['detected_probability'])
        self.assertEqual(result['languages'][2]['detected_probability'],.9)


@unittest.skipUnless(sys.platform.startswith('linux'),'Linux network isolation')
class VoicePrivacyTests(unittest.TestCase):
    def test_offline_worker_cannot_create_network_socket(self):
        code='''from qaf_video.private_runtime import harden_local_runtime
import os,socket
p=harden_local_runtime()
assert os.environ["ORT_DISABLE_TELEMETRY"]=="1"
assert os.environ["HF_HUB_OFFLINE"]=="1"
assert p["network_guard"]=="linux_seccomp_denies_network_syscalls"
try:
 socket.socket()
 raise AssertionError("network available")
except PermissionError:
 print("blocked")
'''
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('blocked',r.stdout)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class VoiceMasteringTests(unittest.TestCase):
    def test_short_high_crest_recording_reaches_loudness_without_peak_overflow(self):
        from qaf_video.voice_lab import write_wav,normalize_voice,decode
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sr=48000;t=np.arange(round(sr*2.8))/sr
            x=.03*np.sin(2*np.pi*210*t);x[round(sr*.7):round(sr*.7)+20]=.8
            write_wav(root/'input.wav',x,sr)
            r=normalize_voice(root/'input.wav',root/'out.wav')
            self.assertAlmostEqual(float(r['input_i']),-18,delta=.8)
            self.assertLessEqual(float(r['input_tp']),-1.8)
            self.assertEqual(len(decode(root/'out.wav',48000)),len(x))
    def test_timing_fits_samples_exactly_and_rejects_large_stretch(self):
        from qaf_video.voice_lab import write_wav,decode
        from qaf_video.voice_timing import fit_voice
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sr=48000;t=np.arange(sr*3)/sr
            write_wav(root/'input.wav',.1*np.sin(2*np.pi*200*t),sr)
            r=fit_voice(root/'input.wav',root/'out.wav',5,[])
            self.assertTrue(.8<=r['tempo_factor']<=1.08)
            self.assertEqual(len(decode(root/'out.wav',48000)),sr*5)
            with self.assertRaisesRegex(ValidationError,'too short'):
                fit_voice(root/'input.wav',root/'too-long.wav',60,[])
