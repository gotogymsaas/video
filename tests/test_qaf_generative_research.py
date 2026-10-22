"""Smoke tests for the ten numerical reference models (not I2V quality tests)."""
import unittest
import numpy as np
from qaf_video.generative_research.models import (m01_pose_motion,m02_cloth_step,m03_scene_graph,
 m04_grounding,m05_latent_dynamics,m06_keyframe_bridge,m07_identity_update,
 m08_continuity_plan,m09_temporal_quality,m10_release_gate)
class TestGenerativeResearch(unittest.TestCase):
 def test_pose(self):
  a=np.array([[[0.,0],[1.,0]],[[0.,0],[1.,1]]])
  self.assertEqual(m01_pose_motion(a,[0.,1.],12,[(0,1)])['trajectory'].shape,(12,2,2))
 def test_cloth(self):
  r=m02_cloth_step([[0,1,0],[1,1,0]],np.zeros((2,3)),[(0,1)],[1],anchors=(0,))
  self.assertTrue(np.isfinite(r['mean_strain']))
 def test_graph(self):
  self.assertEqual(len(m03_scene_graph([[0,0,.2,.2],[.4,.4,.5,.5]],['a','b'])['relations']),2)
 def test_ground(self):
  self.assertEqual(len(m04_grounding(['a'],[[.7,.8]],[.9,.8])['support']),1)
 def test_i2v_fixture(self):
  self.assertEqual(m05_latent_dynamics(np.zeros((8,8,3)),steps=6).shape,(6,8,8,3))
 def test_bridge(self):
  self.assertEqual(m06_keyframe_bridge(np.zeros((2,2,3)),np.ones((2,2,3)),8)['frames'].shape[0],8)
 def test_identity(self):
  self.assertTrue(m07_identity_update([1,0],[1,0])['matched'])
 def test_continuity(self):
  self.assertEqual(len(m08_continuity_plan([[0,1],[1,0]],np.zeros((1,2,2)))['path']),2)
 def test_video_qa(self):
  self.assertIn('global_flicker',m09_temporal_quality(np.ones((5,4,4,3))))
 def test_gate(self):
  self.assertTrue(m10_release_gate([[.8,.7]],[1],2,[True],[.5,.5])['requires_human_review'])
if __name__=='__main__': unittest.main()
