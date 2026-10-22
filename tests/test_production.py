import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from qaf_video.core import ValidationError, validate, local_asset, atomic_json, sha256
from qaf_video.color import srgb_to_linear,linear_to_srgb,composite
from qaf_video.render.pathtrace import render,intersect
from qaf_video.render.compositor import Movie
from qaf_video.voice import captions_from_boundaries


def fixture():
    return {'schema':'qaf_video_project_v1','duration':2,'fps':12,'mode':'conceptual',
            'shots':[{'start':0,'end':2,'title':'Una prueba','body':'Un resultado verificable.'}]}


class ProjectTests(unittest.TestCase):
    def test_gap_overlap_fractional_frame_and_wrong_type_rejected(self):
        m=fixture();self.assertTrue(validate(m,Path('.'))['valid'])
        for update in [{'start':.1},{'end':1.99},{'title':12},{'zoom':None},{'focus':[]},{'nodes':'abc'}]:
            bad=copy.deepcopy(m);bad['shots'][0].update(update)
            with self.subTest(update=update),self.assertRaises(ValidationError):validate(bad,Path('.'))
    def test_claims_gate_cannot_be_bypassed_by_demonstration_mode(self):
        m=fixture();m['mode']='demonstration';m['shots'][0].update(claim_ids=['c'],evidence_required=True)
        m['claims']={'c':{'status':'conceptual','source':'a paper'}}
        with self.assertRaises(ValidationError):validate(m,Path('.'))
        m['claims']['c'].update(status='verified',scope='fixture only',verified_at='2026-10-22',reviewer='test fixture')
        self.assertTrue(validate(m,Path('.'))['valid'])
    def test_missing_binding_and_final_reviews_are_rejected(self):
        m=fixture();m['shots'][0]['evidence_required']=True
        with self.assertRaises(ValidationError):validate(m,Path('.'))
        with self.assertRaises(ValidationError):validate(fixture(),Path('.'),final=True)
    def test_traversal_and_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'inside').mkdir();(root/'secret').write_text('private')
            with self.assertRaises(ValidationError):local_asset(root/'inside','../secret')
            (root/'inside/link').symlink_to(root/'secret')
            with self.assertRaises(ValidationError):local_asset(root/'inside','link')
    def test_invalid_subtitles_are_rejected(self):
        m=fixture();m['subtitles']=[{'start':0,'end':1,'text':'Hola'},{'start':.5,'end':2,'text':'Mundo'}]
        with self.assertRaises(ValidationError):validate(m,Path('.'))
    def test_final_asset_hash_and_caption_binding_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'voice.wav').write_bytes(b'fixture');(root/'logo.png').write_bytes(b'fixture')
            m=fixture();m.update(voice='voice.wav',logo='logo.png',subtitles=[{'start':0,'end':1,'text':'Hola'}],
                caption_audio_sha256=sha256(root/'voice.wav'),reviews={k:{'approved':True,'reviewer':'fixture','at':'2026-10-22'}
                for k in ['brand','voice','claims','rights','picture','accessibility']},assets={})
            m['shots'][0]['claim_ids']=['fixture'];m['claims']={'fixture':{'status':'verified','scope':'unit test fixture',
                'source':'test fixture','reviewer':'fixture','verified_at':'2026-10-22'}}
            for name in ['voice.wav','logo.png']:m['assets'][name]={'origin':'fixture','rights':'fixture','sha256':sha256(root/name)}
            self.assertTrue(validate(m,root,final=True,verify_assets=False)['valid'])
            (root/'logo.png').write_bytes(b'changed')
            with self.assertRaises(ValidationError):validate(m,root,final=True,verify_assets=False)


class ImageTests(unittest.TestCase):
    def test_srgb_round_trip_and_linear_alpha_against_known_value(self):
        x=np.linspace(0,1,256);np.testing.assert_allclose(linear_to_srgb(srgb_to_linear(x)),x,atol=1e-6)
        im=composite(Image.new('RGBA',(1,1),(255,255,255,128)),Image.new('RGBA',(1,1),(0,0,0,255)))
        self.assertTrue(187<=im.getpixel((0,0))[0]<=189)  # Linear half-white is about sRGB 188, not 128.
    def test_native_transport_is_repeatable_finite_and_nontrivial(self):
        a,report=render(32,20,2,seed=42,bounces=3);b,_=render(32,20,2,seed=42,bounces=3)
        np.testing.assert_array_equal(a,b);self.assertTrue(np.isfinite(a).all());self.assertGreater(a.max()-a.min(),.1)
        self.assertEqual(report['color'],'scene_linear')
    def test_sphere_intersection_uses_nearest_positive_root(self):
        objects=[{'center':[0,0,0],'radius':1}]
        dist,index=intersect(np.array([[0.,0.,3.],[0,0,0.],[0,0,3.]]),np.array([[0,0,-1.],[0,0,1.],[0,1,0.]]),objects)
        np.testing.assert_allclose(dist[:2],[2,1]);self.assertTrue(np.isinf(dist[2]));self.assertEqual(index.tolist(),[0,0,-1])
    def test_composition_accepts_both_orientations_and_linear_pipeline(self):
        m=fixture();m['color_pipeline']='srgb_linear_composite'
        for profile,size in [('proxy',(540,960)),('landscape-proxy',(960,540))]:
            movie=Movie(m,Path('.'),profile)
            try:self.assertEqual(movie.frame(m['shots'][0],1).size,size)
            finally:movie.close_decoder()


class TimingTests(unittest.TestCase):
    def test_captions_preserve_actual_offsets_and_do_not_invent_segments(self):
        raw=[{'text':'Hola','offset':10000000,'duration':4000000},
             {'text':'Barranquilla','offset':18000000,'duration':9000000}]
        cues=captions_from_boundaries(raw);self.assertEqual(cues,[{'start':1.,'end':2.7,'text':'Hola Barranquilla'}])
        self.assertEqual(captions_from_boundaries([]),[])


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class MediaIntegrationTests(unittest.TestCase):
    def test_incomplete_container_is_remuxed_once_before_publication(self):
        from unittest.mock import patch
        from qaf_video import pipeline
        from qaf_video.audio import procedural_score
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);procedural_score(root/'music.wav',2)
            m=fixture();m['music']='music.wav';atomic_json(root/'project.json',m)
            original=pipeline.run;writes=[]
            def interrupted_first_mux(args,**kw):
                value=original(args,**kw)
                if str(args[-1]).endswith('/delivery.mp4'):
                    writes.append(1)
                    if len(writes)==1:Path(args[-1]).write_bytes(b'incomplete container')
                return value
            with patch.object(pipeline,'run',side_effect=interrupted_first_mux):
                report=pipeline.render_project(root/'project.json',root/'video.mp4')
            self.assertEqual(report['delivery_attempts'],2)
            self.assertEqual(len(report['recovered_errors']),1)
            self.assertTrue(report['technical']['technical_passed'])
    def test_end_to_end_video_audio_cache_and_tamper_detection(self):
        from qaf_video.audio import procedural_score
        from qaf_video.pipeline import render_project
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);procedural_score(root/'music.wav',2)
            m=fixture();m['music']='music.wav';atomic_json(root/'project.json',m)
            first=render_project(root/'project.json',root/'video.mp4')
            self.assertTrue(first['technical']['technical_passed']);self.assertEqual(first['frames'],24)
            self.assertTrue(first['audio']['two_pass'])
            self.assertTrue(render_project(root/'project.json',root/'video.mp4')['cache_hit'])
            (root/'video.mp4').write_bytes(b'tampered')
            self.assertFalse(render_project(root/'project.json',root/'video.mp4')['cache_hit'])
    def test_four_stem_ducking_and_silent_mix_failure(self):
        from qaf_video.audio import procedural_score,mix_audio
        import wave
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);procedural_score(root/'voice.wav',2);procedural_score(root/'bed.wav',2)
            report=mix_audio(root/'mix.wav',2,voice=root/'voice.wav',music=root/'bed.wav',ambience=root/'bed.wav',effects=root/'bed.wav')
            self.assertTrue(report['ducking']);self.assertLessEqual(float(report['output_measurement']['input_tp']),-1)
            with wave.open(str(root/'silence.wav'),'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(bytes(48000*2*2))
            with self.assertRaises(ValidationError):mix_audio(root/'bad.wav',2,voice=root/'silence.wav')
