from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_closure import BinaryClosureSolver
from experiments.cnf_probe_binary_census import closure
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver,_UP
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_fresh_mixtures import attempt


class BinaryClosureTests(unittest.TestCase):
    def solver(self,**kw):
        s=BinaryClosureSolver(affine_variables=1,**kw);self.addCleanup(s.close);return s

    def test_guarded_binary_conflict_uses_native_authority(self):
        # Neither the parent nor its false branch has a unit; its binary core
        # is refutable, while the other polarity satisfies all guarded clauses.
        source=[[1,a*2,b*3] for a,b in product((-1,1),repeat=2)]
        s=self.solver();r=s.solve(source)
        self.assertTrue(r['answer']);self.assertTrue(native.holds(source,r['model']))
        self.assertGreater(r['metrics'].get('closure_compiled_children',0),0)

    def test_unit_then_binary_certificate_composition(self):
        # A private probe is enough to exercise the two-level certificate.
        s=self.solver();cnf,_=native.normalize([[4]]+[[3,-4,a,b*2] for a,b in product((-1,1),repeat=2)])
        key,offer=s._probe(cnf,3,False)
        self.assertIsNone(offer);self.assertIsNotNone(key)
        self.assertFalse(s._read(key)['answer']);self.assertEqual(s._read(key)['proof']['kind'],'units')

    def test_small_random_truth_and_budgets(self):
        stopped=0;closed=0
        for limit in (0,1,8,256):
            s=self.solver(node_limit=limit,handoff_bytes=128*1024)
            for seed in range(36):
                rng=random.Random(seed);source=[[v if rng.randrange(2) else -v for v in rng.sample(range(1,7),3)] for _ in range(24)]
                r=attempt(s,source);self.assertLessEqual(r['metrics'].get('expanded_nodes',0),limit)
                self.assertEqual((s._handoff_held,s._transferred_held),(0,0));self.assertIsNone(_UP.get())
                if r['result'] is None:stopped+=1;continue
                closed+=1;truth=any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=6))
                self.assertEqual(r['result']['answer'],truth)
                if truth:self.assertTrue(native.holds(source,r['result']['model']))
        self.assertGreater(stopped,0);self.assertGreater(closed,0)

    def test_satisfiable_subset_is_not_published_as_result(self):
        s=self.solver();cnf,_=native.normalize([[3,1,2],[3,-1,-2],[1,2,4]])
        # Initialize the standard transient session through solve rather than
        # calling _offer outside its lifetime management.
        r=s.solve(cnf);self.assertTrue(r['answer']);self.assertTrue(native.holds(cnf,r['model']))
        self.assertEqual(r['metrics'].get('closure_compiled_children',0),0)

    def test_both_readers_and_zero_budget_reopen(self):
        source=[[3,a,b*2] for a,b in product((-1,1),repeat=2)]+[[-3,a,b*2] for a,b in product((-1,1),repeat=2)]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BinaryClosureSolver(path,affine_variables=1)
            try:
                r=s.solve(source);self.assertFalse(r['answer']);keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(reader._read(key))
                finally:reader.close()
            reader=BinaryClosureSolver(path,node_limit=0)
            try:
                with patch.object(reader,'_expand',side_effect=AssertionError('Fresh expansion')):
                    self.assertFalse(reader.solve(source)['answer'])
            finally:reader.close()

    def test_disabled_leaves_keeps_original_search(self):
        s=self.solver(leaves=False);old=ProbeLifetimeSolver(leaves=False,affine_variables=1);self.addCleanup(old.close)
        source=[[3,a,b*2] for a,b in product((-1,1),repeat=2)]
        a,b=s.solve(source),old.solve(source)
        self.assertEqual(a['answer'],b['answer']);self.assertNotIn('closure_calls',a['metrics'])
        self.assertEqual(dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')),dict(old.db.execute('SELECT id,payload FROM cnf_residual_v1')))


if __name__=='__main__':unittest.main()
