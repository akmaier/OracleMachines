from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_conditioned_saturation as s
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
k=s.k;c=s.condition


def cube(n):return [list(lits) for lits in product(*[(v,-v) for v in range(1,n+1)])]


class ConditionedSaturationTests(unittest.TestCase):
    def test_conditioning_strictly_extends_flat_saturation(self):
        source=cube(3);flat=k.discover(source,Counter());self.assertEqual(flat['reason'],'fixed_point')
        result=c.discover(source,1,Counter());self.assertEqual(result['status'],'refuted');c.validate(source,result,Counter())
        self.assertTrue(all(result[name]['status']=='refuted' for name in ('low','high')))

    def test_single_failed_branch_does_not_refute_satisfiable_source(self):
        source=[[1,*cl] for cl in ((2,3),(2,-3),(-2,3),(-2,-3))];result=c.discover(source,1,Counter())
        self.assertEqual(result['low']['status'],'refuted');self.assertEqual(result['status'],'unresolved')
        self.assertEqual(result['high']['reason'],'fixed_point');c.validate(source,result,Counter())
        self.assertTrue(k.native.holds(source,{1:True,2:False,3:False}))

    def test_interrupted_and_terminal_branch_reuse(self):
        source=cube(3);full=c.discover(source,1,Counter())
        for bounds in (dict(probe_limit=1),dict(work_limit=1)):
            first=c.discover(source,1,Counter(),**bounds);self.assertEqual(first['status'],'unresolved')
            self.assertEqual(c.discover(source,1,Counter(),previous=first),full)
        cc=Counter();saved=deepcopy(full);self.assertEqual(c.discover(source,1,cc,previous=full),full)
        self.assertEqual(full,saved);self.assertEqual(cc['probe_roots'],0);self.assertEqual(cc['saturation_terminal_reuses'],2)

    def test_corrupt_branch_binding_status_and_pivot_rejected(self):
        source=cube(3);result=c.discover(source,1,Counter())
        for kind in ('swap','seed','pivot','proof','bound','status'):
            bad=deepcopy(result)
            if kind=='swap':bad['low'],bad['high']=bad['high'],bad['low']
            elif kind=='seed':bad['seed'][0].append(99)
            elif kind=='pivot':bad['pivot']=True
            elif kind=='proof':bad['low']['rounds'][0]['search']['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='bound':bad['low']['trace_limit']=257
            else:bad['status']='unresolved'
            with self.assertRaises(ValueError,msg=kind):c.validate(source,bad,Counter())
        with self.assertRaises(ValueError):c.discover(source,2,Counter(),previous=result)
        for pivot in (0,99,True):
            with self.assertRaises(ValueError):c.discover(source,pivot,Counter())

    def test_exhaustive_small_and_generated_truth_and_sparse_coordinates(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112621)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(1,256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(rng.randrange(1,25))]) for _ in range(100)]
        for n,source in cases:
            variables=sorted({abs(l) for cl in source for l in cl});pivot=variables[0];result=c.discover(source,pivot,Counter());c.validate(source,result,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if k.native.holds(source,dict(enumerate(bits,1)))]
            if result['status']=='refuted':self.assertFalse(models)
            for name,value in (('low',False),('high',True)):
                if result[name]['status']=='refuted':self.assertTrue(all(m[pivot]!=value for m in models))
        sparse=[[l*10 for l in cl] for cl in cube(3)];r=c.discover(sparse,10,Counter());c.validate(sparse,r,Counter());self.assertEqual(r['status'],'refuted')
        self.assertEqual(r,c.discover(list(reversed(sparse))+[sparse[0],(99,-99)],10,Counter()))

    def test_real_native_recomposition_both_cold_readers_and_warm_invalidation(self):
        case=s.base.load('experiments/results/cnf-conditioned-saturation/pilot-case.json');partition=case['partition']
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';solver=s.compiler.native.ResidualSolver(path);cc=Counter()
            try:
                root=s.compile_case(solver,case,partition,cc);self.assertEqual(root,case['root']);self.assertEqual(cc['conditioned_native_root_splits'],1)
                before=s.old.tables(solver.db);warm=Counter();self.assertEqual(s.compile_case(solver,case,partition,warm),root);self.assertEqual(warm['conditioned_native_extension_hits'],1)
                for kind in ('pivot','branch','status','source','prefix'):
                    badcase=deepcopy(case);bad=deepcopy(partition)
                    if kind=='pivot':bad['pivot']+=1
                    elif kind=='branch':bad['low'],bad['high']=bad['high'],bad['low']
                    elif kind=='status':bad['status']='unresolved'
                    elif kind=='source':badcase['source'][0].append(9999)
                    else:badcase['prefix']['status']='refuted'
                    with self.assertRaises(ValueError,msg=kind):s.compile_case(solver,badcase,bad,Counter())
                self.assertEqual(before,s.old.tables(solver.db))
            finally:solver.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:self.assertFalse(reader._read(root)['answer'])
                finally:reader.close()

    def test_search_reuses_first_pivot_and_checks_schedule(self):
        case=s.base.load('experiments/results/cnf-conditioned-saturation/pilot-case.json');p=s.seed(case,Counter());pivot=s.order(p,Counter())[0]
        first=c.discover(p[29],pivot,Counter(),order_source=p[0],round_limit=1,probe_limit=32)
        full=s.search(p,'conditioned',Counter());resumed=s.search(p,'resume',Counter(),first)
        self.assertEqual(full,resumed);s.check(p,full,Counter());self.assertEqual(full['status'],'refuted')
        bad=deepcopy(full);bad['trials'].append(deepcopy(bad['trials'][0]))
        with self.assertRaises(ValueError):s.check(p,bad,Counter())

    def test_overlay_preserves_remaining_fields_and_rejects_invalid_exclusions(self):
        binding=s.base.load(s.PARENT/'checkpoint.json')['sliced_saturation']['remaining'];rows=s.rows()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay.json';s.compact(path,dict(parent=binding,excluded=[[28,17]]))
            self.assertEqual(s.load_frontier(s.old.binding(path)),[r for r in rows if (r['target'],r['event'])!=(28,17)])
            for excluded in ([[28,17],[28,17]],[[999,0]]):
                s.compact(path,dict(parent=binding,excluded=excluded))
                with self.assertRaises(ValueError):s.load_frontier(s.old.binding(path))


if __name__=='__main__':unittest.main()
