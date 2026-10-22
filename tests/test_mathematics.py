import itertools
import unittest
import numpy as np
from qaf_video.core import ValidationError
from qaf_video.mathematics import MPS, minimum_jerk, camera_position, slerp, solve_choices, coherence_feature
from qaf_video.research import density, povm_read, replan_event, robust_normalize, allocate_samples, paired_sample_size
from qaf_video.planning import benchmark


class TensorTests(unittest.TestCase):
    def test_nonadjacent_reduced_state_matches_independent_dense_trace(self):
        rng=np.random.default_rng(4);psi=rng.normal(size=16)+1j*rng.normal(size=16);psi/=np.linalg.norm(psi)
        model=MPS.from_dense(psi,chi=4)
        tensor=psi.reshape(2,2,2,2).transpose(0,2,1,3).reshape(4,4)
        np.testing.assert_allclose(model.rdm([0,2]),tensor@tensor.conj().T,atol=1e-12)
        np.testing.assert_allclose(model.dense(),psi,atol=1e-12)
    def test_truncation_reports_lost_entanglement(self):
        bell=np.array([1,0,0,1])/np.sqrt(2)
        low=MPS.from_dense(bell,chi=1);full=MPS.from_dense(bell,chi=2)
        self.assertAlmostEqual(low.discarded_weight,.5)
        self.assertAlmostEqual(abs(np.vdot(bell,low.dense()))**2,.5)
        np.testing.assert_allclose(full.rdm([0]),np.eye(2)/2,atol=1e-12)
    def test_tdvp_converges_to_equal_information_exact_reference(self):
        result=benchmark()
        errors=[r['state_l2_error'] for r in result['tdvp_reference']]
        self.assertLess(errors[-1],1e-6);self.assertGreater(errors[0]/errors[-1],20)
    def test_invalid_state_and_hamiltonian_rejected(self):
        with self.assertRaises(ValidationError):MPS.from_dense([0,0])
        with self.assertRaises(ValidationError):MPS.from_dense([1,2,3])
        with self.assertRaises(ValidationError):MPS.from_dense([1,0]).tdvp([[0,1],[0,0]],.01)
    def test_coherence_abstains_for_empty_population(self):
        self.assertFalse(coherence_feature(np.diag([1,0]))['available'])


class ProbabilityTests(unittest.TestCase):
    def test_phase_requires_phase_sensitive_measurement(self):
        plus=density([.5,.5],[0,0]);minus=density([.5,.5],[0,np.pi])
        z=[np.diag([1,0]),np.diag([0,1])]
        x=[density([.5,.5]),density([.5,.5],[0,np.pi])]
        np.testing.assert_allclose(povm_read(plus,z),povm_read(minus,z))
        np.testing.assert_allclose(povm_read(plus,x),[1,0],atol=1e-12)
        np.testing.assert_allclose(povm_read(minus,x),[0,1],atol=1e-12)
    def test_invalid_readout_is_not_treated_as_probability(self):
        with self.assertRaises(ValidationError):povm_read(density([1,1]),[np.eye(2),np.eye(2)])
        with self.assertRaises(ValidationError):povm_read([[2,0],[0,-1]],[np.eye(2)])
    def test_material_evidence_change_always_replans(self):
        state=density([1,0]);self.assertFalse(replan_event(state,state)['replan'])
        self.assertTrue(replan_event(state,state,evidence_changed=True)['replan'])
        self.assertAlmostEqual(replan_event(state,density([0,1]))['trace_distance'],1)
    def test_missing_observation_retains_mask(self):
        result=robust_normalize([5,np.nan,30],[0,0,0],[10,10,10],[1,0,1])
        self.assertEqual(result,{'values':[.5,0.,1.],'present':[True,False,True]})


class PlannerTests(unittest.TestCase):
    def test_qubo_global_minimum_matches_native_constraints(self):
        choices=[[{'utility':2,'cost':2},{'utility':1,'cost':1}],
                 [{'utility':3,'cost':2},{'utility':1,'cost':0}]]
        result=solve_choices(choices,[(0,2,-.3)],budget=3)
        q=np.array(result['qubo']['matrix']);offset=result['qubo']['offset'];n=len(q)
        best=min((float(np.array(bits)@q@np.array(bits)+offset),bits)
                 for bits in itertools.product([0,1],repeat=n))
        self.assertEqual([i for i,x in enumerate(best[1][:4]) if x],result['selected_indices'])
        self.assertAlmostEqual(best[0],result['objective'])
    def test_infeasible_budget_and_partition_are_rejected(self):
        with self.assertRaises(ValidationError):solve_choices([[{'utility':1,'cost':3}]],budget=2)
        with self.assertRaises(ValidationError):solve_choices([[{'utility':np.nan}]])
    def test_adaptive_allocation_respects_budget_and_reduces_proxy(self):
        r=allocate_samples([1,9],[1,1],[1,1],100)
        self.assertLessEqual(r['spent'],100);self.assertGreater(r['samples'][1],r['samples'][0])
        self.assertLess(r['expected_variance_proxy'],1/50+9/50)
        with self.assertRaises(ValidationError):allocate_samples([1],[1],[2],1)
    def test_power_analysis_uses_independent_pairs(self):
        self.assertEqual(paired_sample_size(.4,.8)['independent_pairs'],32)


class CameraTests(unittest.TestCase):
    def test_minimum_jerk_boundary_velocity_and_acceleration(self):
        h=1e-5
        self.assertEqual(float(minimum_jerk(0)),0);self.assertEqual(float(minimum_jerk(1)),1)
        self.assertLess(abs((minimum_jerk(h)-minimum_jerk(0))/h),1e-7)
        self.assertLess(abs((minimum_jerk(2*h)-2*minimum_jerk(h)+minimum_jerk(0))/h**2),.001)
        np.testing.assert_allclose(camera_position([1,2,3],[4,5,6],2,2),[4,5,6])
    def test_quaternion_shortest_arc_and_unit_length(self):
        np.testing.assert_allclose(slerp([1,0,0,0],[-1,0,0,0],.5),[1,0,0,0])
        q=slerp([1,0,0,0],[0,0,1,0],.5);self.assertAlmostEqual(np.linalg.norm(q),1)
