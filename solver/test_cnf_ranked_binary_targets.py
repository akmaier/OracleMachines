from collections import Counter
from functools import partial
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json, unittest

from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_backbone import check_path
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver


class RankedBinaryTargetTests(unittest.TestCase):
    def test_saved_branch_exposes_two_missed_targets(self):
        source=json.loads(Path('experiments/results/cnf-probed-partition/next-branch.json').read_text())['source']
        cnf,_=normalize(source)
        self.assertEqual(targeted.inspect_targeted_backbone(cnf,Counter()),(None,None,None))
        for policy,literal in (('total4',-117),('binary1',50)):
            counts=Counter();proof,cover,found=discover(cnf,counts,policy=policy)
            self.assertIsNone(proof);self.assertIsNone(cover)
            self.assertEqual(found[0]['literal'],literal);check_path(cnf,found[0],Counter())
            self.assertLessEqual(counts['binary_target_reach_roots'],4 if policy=='total4' else 1)

    def test_shape_gates_and_budget_validation(self):
        for source in ([],[[]],[[1]],[[1,2]],[[1,2,3]]):
            cnf,_=normalize(source)
            for policy in ('total4','binary1'):
                self.assertEqual(discover(cnf,Counter(),policy=policy),(None,None,None))
        for kw in ({'policy':'bad'},{'policy':'binary1','root_limit':True},{'policy':'total4','root_limit':-1}):
            with self.assertRaises(ValueError):discover((),Counter(),**kw)

    def test_target_budget_is_independent_of_cover_budget(self):
        cnf,_=normalize([[-1,2],[-1,-2],[1,3,4]])
        for policy in ('total4','binary1'):
            counts=Counter();_,_,found=discover(cnf,counts,policy=policy,root_limit=0)
            self.assertEqual(found[0]['literal'],1);check_path(cnf,found[0],Counter())
            self.assertEqual(counts['binary_cover_reach_roots'],0)

    def test_small_mixtures_against_truth_tables(self):
        clauses=[[-1,-2],[-1,2],[1,-2],[1,2],[-2,-3],[-2,3],[2,-3],[2,3],[-1,3]]
        for mask in range(512):
            cnf,_=normalize([c for i,c in enumerate(clauses) if mask>>i&1]+[[1,2,3]])
            models=[dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)]
            binary=[c for c in cnf if len(c)==2]
            for policy in ('total4','binary1'):
                counts=Counter();proof,cover,found=discover(cnf,counts,policy=policy)
                self.assertLessEqual(counts['binary_target_reach_roots'],4 if policy=='total4' else 1)
                if proof or cover:self.assertFalse(any(holds(cnf,m) for m in models))
                for evidence in found or []:
                    check_path(cnf,evidence,Counter());l=evidence['literal']
                    self.assertFalse(any(holds(binary,m) and m[abs(l)]==(l>0) for m in models))

    def test_native_sat_unsat_lifts_and_independent_cold_readers(self):
        sources=[[[1,2,3],[-1,2],[-1,-2]],
                 [[1,2,3],[-1,4],[-1,-4],[-2,5],[-2,-5],[-3,6],[-3,-6]]]
        for policy in ('total4','binary1'):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=InputSafeAffineProbeSolver(path);answers=[]
                try:
                    with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy=policy)):
                        for source in sources:
                            result=acquire(s,source,256)['result'];answers.append(result)
                            expected=any(holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=6))
                            self.assertEqual(result['answer'],expected)
                            if expected:self.assertTrue(holds(source,result['model']))
                finally:s.close()
                for reader in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    s=reader(path)
                    try:
                        for result in answers:self.assertEqual(s._read(result['root'])['answer'],result['answer'])
                    finally:s.close()

    def test_checked_paths_reject_tampered_reason(self):
        cnf,_=normalize([[-1,2],[-1,-2],[1,3,4]])
        _,_,found=discover(cnf,Counter(),policy='binary1');found[0]['path'][0][1]=len(cnf)
        with self.assertRaises(ValueError):check_path(cnf,found[0],Counter())


if __name__=='__main__':unittest.main()
