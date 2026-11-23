from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from functools import partial
from unittest.mock import patch
import random,unittest
from experiments.cnf_binary_target_fallback import discover
from experiments.cnf_ranked_binary_targets import discover as prior
from experiments.cnf_binary_backbone import check_path
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

SOURCE=((1,4),(-1,5),(1,6),(-1,7),(2,3),(2,-3),(8,9,10))


class BinaryTargetFallbackTests(unittest.TestCase):
    def make(self,**kw):
        s=InputSafeAffineProbeSolver(**kw);self.addCleanup(s.close);return s
    def test_second_target_finds_missed_consequence_in_shared_graph(self):
        cnf,_=normalize(SOURCE);old=Counter();new=Counter()
        self.assertIsNone(prior(cnf,old,policy='binary1')[2])
        proof,cover,parts=discover(cnf,new,policy='binary2');self.assertIsNone(proof);self.assertIsNone(cover)
        self.assertEqual(parts[0]['literal'],-2);check_path(cnf,parts[0],Counter())
        self.assertEqual(new['binary_fallback_second_candidates'],1);self.assertEqual(new['binary_fallback_second_found'],1)
        self.assertEqual(new['binary_cover_graph_edges'],12);self.assertEqual(new['binary_target_reach_roots'],2)
    def test_first_success_and_whole_refutation_keep_priority(self):
        for source in (((1,2),(1,-2),(3,4,5)),((1,2),(1,-2),(-1,2),(-1,-2),(3,4,5))):
            cnf,_=normalize(source);counts=Counter();actual=discover(cnf,counts,policy='binary2')
            self.assertEqual(actual,prior(cnf,Counter(),policy='binary1'))
            self.assertEqual(counts['binary_fallback_second_candidates'],0)
    def test_two_target_limit_leaves_later_forced_variable_unresolved(self):
        source=((1,4),(-1,5),(1,6),(2,7),(-2,8),(2,9),(3,10),(3,-10),(11,12,13))
        cnf,_=normalize(source);c=Counter();self.assertEqual(discover(cnf,c,policy='binary2'),(None,None,None))
        self.assertEqual(c['ranked_target_candidates'],2)
        c=Counter();got=discover(cnf,c,policy='total4');self.assertIsNotNone(got[2])
    def test_zero_cover_budget_and_reasons_remain_checked(self):
        cnf,_=normalize(SOURCE);c=Counter();parts=discover(cnf,c,policy='binary2',root_limit=0)[2]
        self.assertIsNotNone(parts);check_path(cnf,parts[0],Counter())
        for bad in ({'literal':parts[0]['literal'],'path':[[99,0]]},{'literal':True,'path':parts[0]['path']}):
            with self.assertRaises(ValueError):check_path(cnf,bad,Counter())
    def test_invalid_policy_and_budgets(self):
        cnf,_=normalize(SOURCE)
        for args in ({'policy':'other'},{'policy':'binary2','root_limit':True},{'policy':'binary2','root_limit':-1},{'policy':'binary2','width_limit':2}):
            with self.assertRaises(ValueError):discover(cnf,Counter(),**args)
    def test_signed_sparse_inputs_truth_and_native_proof_readers(self):
        source=[[1,2],[1,-2],[-1,3],[-1,-3],[4,5,6]]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=InputSafeAffineProbeSolver(path)
            try:
                for flip in range(8):
                    changed=[[(100*abs(l)+7)*(1 if l>0 else -1)*(-1 if flip>>(abs(l)-1)&1 else 1) for l in c] for c in source]
                    with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary2')):r=acquire(s,changed,256)
                    self.assertFalse(r['result']['answer'])
                keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                rd=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(rd._read(key))
                finally:rd.close()
    def test_small_random_mixtures_and_signs_match_truth(self):
        rng=random.Random(202611230229);a=self.make();b=self.make()
        for _ in range(96):
            source=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,6),rng.choice((2,3)))] for _ in range(rng.randrange(3,22))]
            for signed in (source,[[-l for l in c] for c in source]):
                truth=any(holds(signed,dict(zip(range(1,6),bits))) for bits in product((False,True),repeat=5))
                with patch.object(targeted,'inspect_targeted_backbone',partial(prior,policy='binary1')):x=acquire(a,signed,256)
                with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary2')):y=acquire(b,signed,256)
                self.assertEqual(x['result']['answer'],truth);self.assertEqual(y['result']['answer'],truth)
                if truth:self.assertTrue(holds(signed,y['result']['model']))
    def test_budget_stop_has_no_unfinished_root_authority(self):
        s=self.make();source=list(SOURCE)+[list(c) for c in product((-8,8),(-9,9),(-10,10))]
        with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary2')):
            r=acquire(s,source,1,retain_stop=True)
        self.assertEqual(r['status'],'unresolved');self.assertIsNone(s._read(s._canonical(source)[2]))
        with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary2')):r=acquire(s,source,256)
        self.assertFalse(r['result']['answer'])


if __name__=='__main__':unittest.main()
