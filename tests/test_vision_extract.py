import shutil,subprocess,tempfile,unittest
from pathlib import Path
from qaf_video.generative_research.vision_extract import decode_frames
class TestVisionExtractor(unittest.TestCase):
 def test_decode_actual_mp4(self):
  if not shutil.which("ffmpeg"):self.skipTest("FFmpeg missing")
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);video=root/"source.mp4"
   subprocess.run(["ffmpeg","-nostdin","-y","-v","error","-f","lavfi","-i",
      "testsrc=size=128x128:rate=8:duration=2","-pix_fmt","yuv420p",str(video)],check=True)
   images=decode_frames(video,128,128,8,8)
   self.assertEqual(len(images),8)
   self.assertEqual(images[0].size,(128,128))
   with self.assertRaises(ValueError):decode_frames(video,128,128,8,80)
