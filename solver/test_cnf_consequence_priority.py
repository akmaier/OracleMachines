from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random,unittest
from experiments import cnf_consequence_priority as priority
from experiments.cnf_joint_backbone import discover
from experiments.cnf_residual_dag import normalize,restrict,holds
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

SOURCE=[(1,4),(-1,5),(1,-6),(-1,16),(2,3),(2,-3),(7,9),(7,10),(-9,-10,7),(7,12,13),(7,-12,14),(7,-14,15)]


class ConsequencePriorityTests(unittest.TestCase):
    def solver(self,**kwargs):
        s=priority.ConsequencePrioritySolver(**kwargs);self.addCleanup(s.close);return s

    def test_late_single_consequence_prefers_checked_full_cnf_refutation(self):
        cnf,_=normalize(SOURCE);parts=discover(cnf,Counter())[2];self.assertEqual(len(parts),1)
        s=self.solver();r=acquire(s,cnf,256)
        self.assertTrue(r['result']['answer']);self.assertTrue(holds(cnf,r['result']['model']))
        self.assertEqual(s.counts['priority_selections'],1);self.assertEqual(s.counts['bipolar_compiled_children'],1)

    def test_both_polarities_and_sparse_signed_source(self):
        for flip in (False,True):
            src=[[(100*abs(l)+11)*(1 if l>0 else -1)*(-1 if flip else 1) for l in c] for c in SOURCE]
            s=self.solver();r=acquire(s,src,256);self.assertTrue(r['result']['answer']);self.assertTrue(holds(src,r['result']['model']))
            self.assertEqual(s.counts['priority_selections'],1)
            self.assertEqual(s.counts['bipolar_true_probes'],int(flip))

    def test_first_ranked_consequence_skips_probes(self):
        cnf,_=normalize([(1,2),(1,-2),(3,4,5)]);s=self.solver()
        with patch.object(priority,'probe_child',side_effect=AssertionError('Unneeded probe')):
            self.assertTrue(acquire(s,cnf,256)['result']['answer'])
        self.assertEqual(s.counts['priority_first_target_skips'],1)

    def test_two_consequences_keep_joint_policy(self):
        cnf,_=normalize([(1,3),(1,-3),(2,4),(2,-4),(5,6,7)]);s=self.solver()
        with patch.object(priority,'probe_child',side_effect=AssertionError('Joint selection should survive')):
            self.assertTrue(acquire(s,cnf,256)['result']['answer'])
        self.assertEqual(s.counts['priority_joint_skips'],1)

    def test_inconclusive_probes_do_not_publish_answers(self):
        src=[(-9,10,7) if c==(-9,-10,7) else c for c in SOURCE];cnf,_=normalize(src);s=self.solver()
        got=priority.prefer_ordinary(s,cnf,discover(cnf,Counter())[2])
        self.assertIsNone(got);self.assertEqual(s.counts['priority_misses'],1);self.assertEqual(s.archive_storage()[0],0)

    def test_size_guard_does_not_probe(self):
        cnf,_=normalize(SOURCE+[(i,i+1,i+2) for i in range(30,300,3)]);s=self.solver()
        with patch.object(priority,'probe_child',side_effect=AssertionError('Size guard failed')):
            self.assertIsNone(priority.prefer_ordinary(s,cnf,discover(cnf,Counter())[2]))
        self.assertEqual(s.counts['priority_size_skips'],1)

    def test_cached_negative_cofactor_retains_authority(self):
        cnf,_=normalize(SOURCE);s=self.solver();acquire(s,restrict(cnf,{7:False}),256)
        before=s.counts['bipolar_compiled_children'];got=priority.prefer_ordinary(s,cnf,discover(cnf,Counter())[2])
        self.assertIsNotNone(got);self.assertTrue(holds(cnf,got[0]));self.assertEqual(s.counts['bipolar_cached_negative'],1)
        self.assertEqual(s.counts['bipolar_compiled_children'],before)

    def test_small_unlabelled_mixtures_match_exhaustive_truth(self):
        rng=random.Random(533);s=self.solver()
        for _ in range(192):
            src=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,6),rng.choice((2,3)))] for _ in range(rng.randrange(3,23))]
            truth=any(holds(src,dict(zip(range(1,6),bits))) for bits in product((False,True),repeat=5))
            r=acquire(s,src,256);self.assertEqual(r['result']['answer'],truth)
            if truth:self.assertTrue(holds(src,r['result']['model']))

    def test_native_cold_readers_check_retained_compiled_children(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=priority.ConsequencePrioritySolver(path)
            try:
                for sign in (1,-1):acquire(s,[[sign*l for l in c] for c in SOURCE],256)
                keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(s._read(key))
                finally:s.close()

    def test_budget_stop_keeps_only_completed_evidence(self):
        s=self.solver();cnf,_=normalize(SOURCE);r=acquire(s,cnf,1,retain_stop=True)
        self.assertIsNone(r['result']);self.assertIsNone(s._read(s._canonical(cnf)[2]))
        self.assertGreater(s.archive_storage()[0],0);self.assertTrue(acquire(s,cnf,256)['result']['answer'])


if __name__=='__main__':unittest.main()
