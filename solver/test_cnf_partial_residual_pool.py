from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,random,sqlite3,unittest
from experiments.cnf_partial_residual_pool import PartialResidualSolver,charge
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_cross_family import truth_table
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_snapshot_replay import SnapshotResidualSolver


class PartialResidualTests(unittest.TestCase):
    def make(self,*args,**kw):
        s=PartialResidualSolver(*args,**kw);self.addCleanup(s.close);return s

    def seed(self,path,source):
        s=ResidualSolver(path,leaves=False,decompose=False)
        try:return s.solve(source)
        finally:s.close()

    def test_partial_refutation_does_not_refute_its_sat_source(self):
        s=self.make(affine_variables=1,leaves=False,decompose=False,batch_rows=1,node_limit=3)
        source=[[1,2,3],[1,2,-3],[1,-2,3],[1,-2,-3],[-1,4],[-1,5]]
        with self.assertRaisesRegex(RuntimeError,'no verdict'):s.solve(iter(source))
        self.assertTrue(s.partial_pool);self.assertFalse(s.db.in_transaction)
        self.assertFalse(s.negative_pool)
        s.node_limit=100;r=s.solve(iter(source));self.assertTrue(r['answer']);self.assertTrue(holds(source,r['model']))

    def test_cold_partial_support_hit_without_native_fallback(self):
        with TemporaryDirectory() as td:
            source=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
            path=Path(td)/'db';self.seed(path,source+[[1,4,5]])
            s=PartialResidualSolver(path,affine_variables=1)
            try:
                with patch.object(ResidualSolver,'_expand',side_effect=AssertionError('Fresh fallback')):
                    r=s.solve((iter(c) for c in source+[[1,4,-5]]))
                self.assertFalse(r['answer']);self.assertEqual(r['metrics']['partial_hits'],1)
                self.assertEqual(r['metrics']['partial_support_attempts'],1)
                self.assertEqual(r['metrics'].get('negative_hits',0),0)
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:
                for key, in s.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(s._read(key))
            finally:s.close()

    def test_deleted_required_premise_is_only_a_miss(self):
        with TemporaryDirectory() as td:
            source=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
            path=Path(td)/'db';self.seed(path,source+[[1,4,5]])
            s=PartialResidualSolver(path,affine_variables=1)
            try:
                target=source[:-1]+[[1,4,5]]
                r=s.solve(target);self.assertTrue(r['answer']);self.assertTrue(holds(target,r['model']))
                self.assertEqual(r['metrics']['partial_support_misses'],1)
            finally:s.close()

    def test_failed_batch_does_not_admit_pending_nodes(self):
        s=self.make(affine_variables=1,leaves=False,batch_rows=32)
        def fail(event,table,key):
            if event=='after_insert':raise RuntimeError('Injected')
        s.publication_hook=fail
        with self.assertRaisesRegex(RuntimeError,'Injected'):s.solve([[1,2],[1,-2],[-1,3],[-1,4]])
        self.assertFalse(s.partial_pool);self.assertFalse(s.db.pending);self.assertFalse(s.db.in_transaction)
        s.publication_hook=None;self.assertTrue(s.solve([[1,2],[1,-2],[-1,3],[-1,4]])['answer'])

    def test_budgets_and_conservative_retained_charge(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';self.seed(path,[list(c) for c in product((-1,1),(-2,2),(-3,3))]+[[1,4,5]])
            for limits in (dict(partial_bytes=1),dict(partial_row_bytes=1),dict(partial_literals=1)):
                s=PartialResidualSolver(path,**limits)
                try:self.assertFalse(s.partial_pool)
                finally:s.close()
        s=self.make(partial_capacity=3,partial_bytes=10000,partial_probes=2,partial_candidates=1)
        for i in range(2,20):
            s._hint(str(i),json.dumps(dict(format='cnf-residual-v1',answer=False,cnf=[[1],[-1],[i,i+1]],proof=dict(kind='split'))))
            self.assertLessEqual(len(s.partial_pool),3)
            self.assertLessEqual(s._partial_size(),10000)
            self.assertGreaterEqual(s._partial_size(),charge((s.partial_pool,s.partial_index)))
        r=s.solve([[1,2,3],[-1,2],[-2,3]])
        self.assertLessEqual(r['metrics'].get('partial_probes',0),2)
        self.assertLessEqual(r['metrics'].get('partial_candidates',0),2)
        for kw in (dict(partial_rows=False),dict(partial_bytes=0),dict(partial_support_nodes=-1)):
            with self.assertRaises(ValueError):PartialResidualSolver(**kw)

    def test_untrusted_hint_requires_checked_authority(self):
        s=self.make(affine_variables=1)
        s._hint('missing',json.dumps(dict(format='cnf-residual-v1',answer=False,cnf=[[1],[-1],[2,3]],proof=dict(kind='split'))))
        r=s.solve([[1],[-1],[2,3]])
        self.assertFalse(r['answer']);self.assertGreater(r['metrics'].get('partial_stale_hints',0),0)
        self.assertEqual(r['metrics'].get('partial_hits',0),0)

    def test_corrupt_persisted_origin_is_not_a_proof(self):
        with TemporaryDirectory() as td:
            source=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
            path=Path(td)/'db';root=self.seed(path,source+[[1,4,5]])['root']
            con=sqlite3.connect(path)
            try:
                node=json.loads(con.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(root,)).fetchone()[0]);node['proof']={'kind':'split','variable':0,'low':'invalid','high':'invalid'}
                with con:con.execute('UPDATE cnf_residual_v1 SET payload=? WHERE id=?',(json.dumps(node),root))
            finally:con.close()
            s=PartialResidualSolver(path,affine_variables=1)
            try:
                with self.assertRaises(ValueError):s.solve(source+[[1,4,-5]])
            finally:s.close()

    def test_exhaustive_small_and_random_mixed_streams(self):
        s=self.make(affine_variables=1)
        clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        sources=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(41)
        sources += [[[v if rng.randrange(2) else -v for v in rng.sample(range(1,6),rng.randint(1,3))] for _ in range(18)] for _ in range(100)]
        for source in sources:
            r=s.solve(source);self.assertEqual(r['answer'],truth_table(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))


if __name__=='__main__':unittest.main()
