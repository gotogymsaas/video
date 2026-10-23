import unittest
from qaf_video.generative_research.relational_planner import choose_shots
class TestRelationalPlanner(unittest.TestCase):
 def test_dp_beats_myopic_greedy_by_identity_continuity(self):
  def cand(id,actor,error):
   return {"id":id,"actor_ref":actor,"action_error":error,"identity_error":0,
    "occlusion_error":0,"compute_cost":0,"privacy_cleared":True,"rights_cleared":True}
  data={"schema":"qaf_cinema_scene_decisions_v1","identity_switch_penalty":10,
   "scenes":[{"candidates":[cand("a","A",0),cand("b","B",2)]},
             {"candidates":[cand("c","B",0),cand("d","A",2)]}]}
  result=choose_shots(data)
  self.assertEqual(result["chosen_shots"],["a","d"])
  self.assertEqual(result["objective_cost"],2)
  self.assertEqual(result["greedy_baseline_cost"],10)
  self.assertFalse(result["qaf_quantum_advantage_proven"])
 def test_privacy_rejects_candidate(self):
  data={"schema":"qaf_cinema_scene_decisions_v1","scenes":[{"candidates":[{
   "id":"a","privacy_cleared":False,"rights_cleared":True,
   "action_error":0,"identity_error":0,"occlusion_error":0,"compute_cost":0}]}]}
  with self.assertRaises(ValueError):choose_shots(data)
