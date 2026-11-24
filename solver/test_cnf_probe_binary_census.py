from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import json,random,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_census import closure,BinaryCensusSolver
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_fresh_mixtures import attempt


class BinaryCensusTests(unittest.TestCase):
    def discover(self,source):
        child,names=native.normalize(source);key=native.token(child,Counter())
        fixed,trace,conflict=native.propagate(child,Counter())
        return closure((child,names,key),(fixed,trace,conflict,0),Counter())

    def check(self,result,cls=native.ResidualSolver,path=None):
        s=cls(path) if path is not None else cls()
        try:
            for item in result['nodes']:s._store(item['key'],item['node'])
        finally:s.close()

    def test_binary_only_and_mixed_refutations(self):
        core=[[1,2],[1,-2],[-1,2],[-1,-2]]
        for src in (core,core+[[1,2,3]]):
            r=self.discover(src);self.assertEqual(r['status'],'binary-unsat')
            self.assertEqual(len(r['nodes']),1);self.check(r)

    def test_existing_units_transport_to_cold_checked_source(self):
        source=[[91]]+[[-91,17*a,29*b] for a,b in product((-1,1),repeat=2)]+[[17,29,43]]
        r=self.discover(source);self.assertEqual(r['status'],'binary-unsat');self.assertEqual(len(r['nodes']),2)
        with TemporaryDirectory() as td:
            path=Path(td)/'db';self.check(r,path=path)
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for item in r['nodes']:self.assertEqual(s._read(item['key']),item['node'])
                finally:s.close()

    def test_binary_sat_is_not_a_full_verdict(self):
        clauses=[[a,b*2,c*3] for a,b,c in product((-1,1),repeat=3)]
        for extra in ([],[[1,2]],[[1,2],[-1,-2]]):
            r=self.discover(clauses+extra);self.assertFalse(r['nodes']);self.assertNotEqual(r['status'],'binary-unsat')
            self.assertFalse(any(native.holds(clauses+extra,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3)))

    def test_small_exhaustive_truth(self):
        clauses=[[1],[-1],[2],[-2],[1,2],[1,-2],[-1,2],[-1,-2],[1,2,3],[-1,-2,-3]]
        hits=0
        for mask in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            cnf,names=native.normalize(source);fixed,trace,conflict=native.propagate(cnf,Counter())
            if conflict is not None:continue
            r=closure((cnf,names,native.token(cnf,Counter())),(fixed,trace,conflict,0),Counter())
            if r['nodes']:
                hits+=1;self.check(r)
                self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3)))
        self.assertGreater(hits,0)

    def test_corrupted_paths_and_unit_lifts_rejected(self):
        r=self.discover([[4]]+[[-4,a,b*2] for a,b in product((-1,1),repeat=2)])
        for component in ('path','units','key'):
            bad=deepcopy(r)
            if component=='path':bad['nodes'][0]['node']['proof']['forward'][0][1]=9999
            elif component=='units':bad['nodes'][-1]['node']['proof']['trace'][0][1]=9999
            else:bad['nodes'][-1]['key']='wrong'
            with self.assertRaises(ValueError):self.check(bad)
        with self.assertRaises(ValueError):closure((((),),(),''),({},[],0,0),Counter())

    def test_observation_does_not_change_search_or_counters(self):
        a=ProbeLifetimeSolver(node_limit=64,handoff_bytes=2*1024*1024,affine_variables=1)
        b=BinaryCensusSolver(node_limit=64,handoff_bytes=2*1024*1024,affine_variables=1);b.observe=True
        self.addCleanup(a.close);self.addCleanup(b.close)
        for seed in range(24):
            rng=random.Random(seed);source=[[v if rng.randrange(2) else -v for v in rng.sample(range(1,9),3)] for _ in range(34)]
            x,y=attempt(a,source),attempt(b,source)
            self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
            self.assertEqual(dict(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),dict(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))
        self.assertTrue(b.events)
        for e in b.events:
            if e['discovery']['nodes']:self.check(e['discovery'])


if __name__=='__main__':unittest.main()
