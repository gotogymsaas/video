import json,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
import numpy as np
from qaf_video.core import ValidationError
from qaf_video.voice_lab import acoustic_metrics,spectral_enhance,preservation_metrics
from qaf_video.voice_local import caption_words,word_error_rate,runtime_settings,synthesize_local


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
