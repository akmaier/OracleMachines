from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_bipolar_routing import probe_child,bipolar_expand
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,holds,restrict
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver

SOURCE=[[1,2],[1,-2],[3,4],[3,-4,5],[3,-4,-5]]
FLIPPED=[[(-l if abs(l)==3 else l) for l in c] for c in SOURCE]


class BipolarRoutingTests(unittest.TestCase):
    def solver(self,**kw):
        s=InputSafeAffineProbeSolver(**kw);self.addCleanup(s.close);return s

    def test_either_forced_polarity_lifts_the_surviving_model(self):
        for source,true_probe in ((SOURCE,0),(FLIPPED,1)):
            s=self.solver()
            with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):r=acquire(s,source,256)
            self.assertTrue(holds(source,r['result']['model']))
            self.assertEqual(r['metrics']['bipolar_default_selections'],1)
            self.assertEqual(r['metrics'].get('bipolar_true_probes',0),true_probe)

    def test_cached_true_negative_avoids_repeat_propagation(self):
        s=self.solver();cnf,_=normalize(FLIPPED);key=probe_child(s,cnf,3,True)
        self.assertIsNotNone(key)
        with patch('experiments.cnf_bipolar_routing.propagate',side_effect=AssertionError('Repeated propagation')):
            self.assertEqual(probe_child(s,cnf,3,True),key)

    def test_both_misses_are_inconclusive_and_positive_cache_is_not_negative(self):
        s=self.solver();cnf,_=normalize([[1,2,3],[-1,2,-3]])
        for value in (False,True):self.assertIsNone(probe_child(s,cnf,1,value))
        self.assertEqual(s.archive_storage()[0],0)
        acquire(s,restrict(cnf,{1:True}),256)
        with patch('experiments.cnf_bipolar_routing.propagate',side_effect=AssertionError('Cached model')):
            self.assertIsNone(probe_child(s,cnf,1,True))

    def test_invalid_polarity_and_trace_are_rejected(self):
        s=self.solver();cnf,_=normalize(FLIPPED)
        with self.assertRaises(ValueError):probe_child(s,cnf,3,1)
        with patch('experiments.cnf_bipolar_routing.propagate',return_value=({},[[999,0]],0)):
            with self.assertRaises(ValueError):probe_child(s,cnf,3,True)
        self.assertEqual(s.archive_storage()[0],0)

    def test_budget_stop_retains_true_cofactor_without_source_verdict(self):
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):r=acquire(s,FLIPPED,1,retain_stop=True)
        self.assertIsNone(r['result']);self.assertEqual(r['status'],'unresolved')
        self.assertEqual(r['metrics']['bipolar_true_probes'],1)
        self.assertGreater(r['metrics']['probe_retained_pending_records'],0)
        cnf,_,key=s._canonical(FLIPPED);self.assertIsNone(s._read(key,cnf))
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending)

    def test_small_mixtures_and_complements_match_truth(self):
        clauses=[[-1,-2],[-1,2],[1,-2],[1,2],[-2,-3],[-2,3],[2,-3],[2,3],[-1,3]]
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):
            for mask in range(512):
                source=[c for i,c in enumerate(clauses) if mask>>i&1]+[[1,2,3]]
                expected=any(holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
                for signed in (source,[[-l for l in c] for c in source]):
                    r=acquire(s,signed,256)['result'];self.assertEqual(r['answer'],expected)
                    if expected:self.assertTrue(holds(signed,r['model']))

    def test_cold_native_readers_verify_both_polarities(self):
        for source in (SOURCE,FLIPPED):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=InputSafeAffineProbeSolver(path)
                try:
                    with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):acquire(s,source,256)
                    keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    s=cls(path)
                    try:
                        for key in keys:self.assertIsNotNone(s._read(key))
                    finally:s.close()

    def test_disabled_leaves_skip_bipolar_discovery(self):
        s=self.solver(leaves=False)
        with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):r=acquire(s,FLIPPED,256)
        self.assertTrue(r['result']['answer']);self.assertNotIn('bipolar_false_probes',r['metrics'])


if __name__=='__main__':unittest.main()
