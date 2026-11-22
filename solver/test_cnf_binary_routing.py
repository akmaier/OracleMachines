from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_binary_routing import default_false_child,priority_expand
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,holds,restrict
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver

SOURCE=[[1,2],[1,-2],[3,4],[3,-4,5],[3,-4,-5]]


class BinaryRoutingTests(unittest.TestCase):
    def solver(self,**kw):
        s=InputSafeAffineProbeSolver(**kw);self.addCleanup(s.close);return s

    def test_default_failed_literal_has_priority_and_lifts_sat(self):
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',priority_expand):r=acquire(s,SOURCE,256)
        self.assertTrue(holds(SOURCE,r['result']['model']))
        self.assertEqual(r['metrics']['routing_default_selections'],1)
        self.assertEqual(r['metrics']['routing_compiled_children'],1)

    def test_cached_negative_child_is_reused_without_propagation(self):
        s=self.solver();cnf,_=normalize(SOURCE);key=default_false_child(s,cnf,3)
        with patch('experiments.cnf_binary_routing.propagate',side_effect=AssertionError('Repeated discovery')):
            self.assertEqual(default_false_child(s,cnf,3),key)
        self.assertEqual(s.counts['routing_cached_negative'],1)

    def test_no_conflict_and_cached_positive_are_inconclusive(self):
        s=self.solver();cnf,_=normalize([[1,2,3],[-1,2,-3]])
        self.assertIsNone(default_false_child(s,cnf,1));self.assertEqual(s.archive_storage()[0],0)
        acquire(s,restrict(cnf,{1:False}),256)
        with patch('experiments.cnf_binary_routing.propagate',side_effect=AssertionError('Cached model')):
            self.assertIsNone(default_false_child(s,cnf,1))
        self.assertEqual(s.counts['routing_cached_positive'],1)

    def test_native_checker_rejects_invalid_retained_trace(self):
        s=self.solver();cnf,_=normalize(SOURCE)
        with patch('experiments.cnf_binary_routing.propagate',return_value=({},[[999,0]],0)):
            with self.assertRaises(ValueError):default_false_child(s,cnf,3)
        self.assertEqual(s.archive_storage()[0],0)

    def test_budget_stop_retains_completed_cofactor_not_source_verdict(self):
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',priority_expand):r=acquire(s,SOURCE,1,retain_stop=True)
        self.assertIsNone(r['result']);self.assertEqual(r['status'],'unresolved')
        self.assertGreater(r['metrics']['probe_retained_pending_records'],0)
        cnf,_,key=s._canonical(SOURCE);self.assertIsNone(s._read(key,cnf))
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending)

    def test_small_mixtures_match_truth_tables(self):
        clauses=[[-1,-2],[-1,2],[1,-2],[1,2],[-2,-3],[-2,3],[2,-3],[2,3],[-1,3]]
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',priority_expand):
            for mask in range(512):
                source=[c for i,c in enumerate(clauses) if mask>>i&1]+[[1,2,3]]
                expected=any(holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
                r=acquire(s,source,256)['result'];self.assertEqual(r['answer'],expected)
                if expected:self.assertTrue(holds(source,r['model']))

    def test_cold_native_readers_and_disabled_leaves(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=InputSafeAffineProbeSolver(path)
            try:
                with patch.object(TargetedBackboneMixin,'_expand',priority_expand):r=acquire(s,SOURCE,256)
                keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(s._read(key))
                finally:s.close()
        s=self.solver(leaves=False)
        with patch.object(TargetedBackboneMixin,'_expand',priority_expand):r=acquire(s,SOURCE,256)
        self.assertTrue(r['result']['answer']);self.assertNotIn('routing_false_probes',r['metrics'])

    def test_signed_renaming_keeps_semantics(self):
        source=[[(-1 if abs(l)%2 else 1)*(1 if l>0 else -1)*(10*abs(l)+7) for l in c] for c in SOURCE]
        s=self.solver()
        with patch.object(TargetedBackboneMixin,'_expand',priority_expand):r=acquire(s,source,256)
        self.assertTrue(holds(source,r['result']['model']))


if __name__=='__main__':unittest.main()
