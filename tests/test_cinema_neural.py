"""Tests skip when optional torch dependency is absent from production CI."""
import importlib.util, tempfile, unittest
HAS_TORCH=importlib.util.find_spec("torch") is not None
if HAS_TORCH:
 import torch
 from qaf_video.generative_research.cinema_neural import (
    CinemaVAE,VideoDiT,moving_shapes,flow_loss,vae_loss,generate,train_smoke)
@unittest.skipUnless(HAS_TORCH,"PyTorch optional, neural model not installed in production")
class TestTrainableCinema(unittest.TestCase):
 @classmethod
 def setUpClass(cls):torch.set_num_threads(1)
 def test_shapes_and_gradients(self):
  data=moving_shapes()
  vae,dit=CinemaVAE(),VideoDiT()
  loss,_=vae_loss(vae,data);loss.backward()
  self.assertTrue(torch.isfinite(loss))
  z,_,_=vae.encode(data,sample=False)
  self.assertEqual(tuple(z.shape),(2,4,5,4,4))
  v=flow_loss(vae,dit,data);v.backward()
  self.assertTrue(torch.isfinite(v))
  self.assertTrue(any(p.grad is not None for p in dit.parameters()))
 def test_control_ablation_and_first_frame(self):
  data=moving_shapes(batch=1)
  vae,dit=CinemaVAE(),VideoDiT()
  z,_,_=vae.encode(data,sample=False)
  a=dit(z,torch.zeros(1),z[:,:,:1])
  b=dit(z,torch.zeros(1),z[:,:,:1],qaf=torch.ones(1,8))
  self.assertFalse(torch.allclose(a,b))
  frames=generate(vae,dit,data[:,:,:1],steps=2)
  self.assertEqual(tuple(frames.shape),tuple(data.shape))
  self.assertTrue(torch.equal(frames[:,:,0],data[:,:,0]))
 def test_trained_checkpoint_is_marked_synthetic(self):
  with tempfile.TemporaryDirectory() as p:
   result=train_smoke(p,steps=2)
   self.assertFalse(result["foundation_cinema_trained"])
   self.assertFalse(result["real_video_training"])
   self.assertEqual(result["status"],"synthetic_train_smoke")
