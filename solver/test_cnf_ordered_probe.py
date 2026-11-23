from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import json, random, unittest
from experiments.cnf_residual_dag import normalize, restrict, token, holds
from experiments.cnf_whole_lookahead import WholeLookaheadSolver
from experiments.cnf_ordered_probe import OrderedProbeSolver, _prepare, _probe
from experiments.cnf_bipolar_routing import probe_child
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class OrderedProbeTests(unittest.TestCase):
    def solver(self, cls=OrderedProbeSolver, **kwargs):
        s=cls(**kwargs);self.addCleanup(s.close);return s

    def compare_preparation(self, source):
        parent, _=normalize(source)
        for v in sorted({abs(l) for c in parent for l in c}) or [1]:
            for value in (False, True):
                raw=restrict(parent, {v:value}); expected,names=normalize(raw)
                self.assertEqual(_prepare(parent,v,value,Counter()),(expected,names,token(expected,Counter())))

    def test_exhaustive_two_variable_preparation(self):
        clauses=[tuple(s*v for v,s in enumerate(signs,1) if s) for signs in product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            self.compare_preparation([c for i,c in enumerate(clauses) if mask&(1<<i)])

    def test_reordering_duplicates_support_gaps_and_empty_collapse(self):
        for source in ([(-1,2),(2,3),(2,),(1,3)],[(1,),(-1,3)],[],[()],
                [(-900,15,400),(900,15),(15,400),(15,15),(2,-2,400)]):
            self.compare_preparation(source)

    def test_random_wide_preparation(self):
        rng=random.Random(202611232056)
        for _ in range(128):
            self.compare_preparation([[rng.choice((-1,1))*v for v in rng.sample(range(1,12),rng.randrange(1,7))]
                for _ in range(rng.randrange(1,35))])

    def test_argument_types(self):
        for v,b in ((True,False),(1,0),(0,False),(-1,True),(1.0,True)):
            with self.assertRaises(ValueError):_prepare(((1,2),),v,b,Counter())

    def test_queries_and_proof_payloads_match(self):
        rng=random.Random(571)
        a,b=self.solver(WholeLookaheadSolver),self.solver()
        prepared=0
        for _ in range(128):
            src=[[rng.choice((-1,1))*v for v in rng.sample(range(1,6),rng.choice((2,3,4)))]
                for _ in range(rng.randrange(5,27))]
            x,y=a.solve(src),b.solve(src)
            prepared+=b.counts['ordered_probe_preparations']
            truth=any(holds(src,dict(zip(range(1,6),bits))) for bits in product((False,True),repeat=5))
            self.assertEqual((x['answer'],x['model'],x['root']),(y['answer'],y['model'],y['root']))
            self.assertEqual(y['answer'],truth)
            if truth:self.assertTrue(holds(src,y['model']))
        self.assertEqual(dict(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),
                         dict(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))
        self.assertGreater(prepared,0)

    def test_cached_negative_not_discarded_by_nonunit_syntax(self):
        hard=[tuple(v if bit else -v for v,bit in enumerate(bits,1)) for bits in product((False,True),repeat=3)]
        parent,_=normalize([(1,)+tuple((abs(l)+1)*(1 if l>0 else -1) for l in c) for c in hard])
        for cls,probe in ((WholeLookaheadSolver,probe_child),(OrderedProbeSolver,_probe)):
            s=self.solver(cls);child=restrict(parent,{1:False})
            self.assertIsNone(s._visit(child)[0])
            self.assertIsNotNone(probe(s,parent,1,False))
            self.assertEqual(s.counts['bipolar_cached_negative'],1)

    def test_public_input_validation_and_single_pass(self):
        s=self.solver()
        for bad in (True,1.5,0):
            with self.assertRaises((ValueError,TypeError)):s.solve([[bad]])
        source=[(1,2),(-1,3),(1,-2,-3)]
        self.assertTrue(s.solve((iter(c) for c in source))['answer'])

    def test_budget_stop_and_cold_native_readers(self):
        src=[(1,2),(1,3),(1,-2,-3),(1,4,5),(-1,6,7)]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=OrderedProbeSolver(path,node_limit=0)
            try:
                with self.assertRaisesRegex(RuntimeError,'Residual expansion budget exhausted'):s.solve(src)
                s.node_limit=256;self.assertTrue(s.solve(src)['answer'])
                hard=[tuple(v if b else -v for v,b in enumerate(bits,1)) for bits in product((False,True),repeat=3)]
                self.assertFalse(s.solve(hard)['answer'])
                rows=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for k,v in rows.items():self.assertEqual(s._read(k),json.loads(v))
                finally:s.close()


if __name__=='__main__':unittest.main()
