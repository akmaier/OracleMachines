from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_probe_saturation as s
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_b13_native_feedback import delayed_history
k=s.kernel;c=s.compiler


class ProbeSaturationTests(unittest.TestCase):
    def test_real_candidate_two_rounds_and_exact_first_round_resume(self):
        case=s.build_case();p=s.seed(case,Counter());cc=Counter()
        full=k.discover(p[29],cc,order_source=p[0]);k.validate(p[29],full,Counter(),order_source=p[0])
        self.assertEqual((full['status'],full['reason']),('refuted','units'))
        self.assertEqual([[x['assumption'] for x in r['search']['program']['probes']] for r in full['rounds']],[[44,142,-80,-60,50],[-62,5,-43,107,-74,84,132,88,108]])
        first=k.discover(p[29],Counter(),order_source=p[0],round_limit=1)
        self.assertEqual(first['reason'],'round_limit');reuse=Counter()
        self.assertEqual(full,k.discover(p[29],reuse,order_source=p[0],previous=first))
        self.assertEqual(cc['probe_roots']-reuse['probe_roots'],270)

    def test_interrupted_resume_and_terminal_reuse(self):
        source=((-2,-1),(-2,1),(-1,2),(1,2));full=k.discover(source,Counter())
        for bounds in (dict(probe_limit=1),dict(work_limit=1)):
            initial=k.discover(source,Counter(),**bounds);self.assertEqual(initial['status'],'unresolved')
            self.assertEqual(full,k.discover(source,Counter(),previous=initial))
        for source in (source,((1,2),)):
            result=k.discover(source,Counter());before=deepcopy(result);cc=Counter()
            self.assertEqual(result,k.discover(source,cc,previous=result));self.assertEqual(result,before)
            self.assertEqual(cc['probe_roots'],0);self.assertEqual(cc['saturation_terminal_reuses'],1)

    def test_corrupted_histories_closure_terminal_and_bindings_rejected(self):
        case=s.build_case();p=s.seed(case,Counter());result=k.discover(p[29],Counter(),order_source=p[0])
        for kind in ('seed','ordering','binding','closure','proof','terminal','extra'):
            bad=deepcopy(result)
            if kind=='seed':bad['seed'][0].append(9999)
            elif kind=='ordering':bad['order_source']=[]
            elif kind=='binding':bad['rounds'][0]['search']['cursor']['binding']='changed'
            elif kind=='closure':bad['rounds'][0]['closure']['assignment'].append([9999,True])
            elif kind=='proof':bad['rounds'][0]['search']['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='terminal':bad['proof']['conflict']=999999
            else:bad['rounds'].append(deepcopy(bad['rounds'][-1]))
            with self.assertRaises(ValueError,msg=kind):k.validate(p[29],bad,Counter(),order_source=p[0])
        with self.assertRaises(ValueError):k.discover(p[29],Counter(),order_source=p[0],previous=result,trace_limit=257)
        fixed=k.discover(((1,2),),Counter());bad=deepcopy(fixed)
        bad['rounds'][0]['search']['cursor']['completed'].pop()
        with self.assertRaises(ValueError):k.validate(((1,2),),bad,Counter())

    def test_exhaustive_small_and_generated_arbitrary_cnf_truth(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112619)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]+[(2,[[]])]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(rng.randrange(1,26))]) for _ in range(100)]
        for n,source in cases:
            result=k.discover(source,Counter());seed,_,bank,_,_=k.validate(source,result,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if k.native.holds(source,dict(enumerate(bits,1)))]
            if result['status']=='refuted':self.assertFalse(models)
            self.assertTrue(all(k.native.holds(bank,m) for m in models))
            self.assertLessEqual(len(result['rounds']),len({abs(l) for cl in seed for l in cl})+1)
            previous=set()
            for row in result['rounds']:
                fixed=set(map(tuple,row['closure']['assignment']));self.assertLessEqual(previous,fixed);previous=fixed

    def test_sparse_names_relabellings_duplicates_and_disjoint_mixtures(self):
        source=((-40,-10),(-40,10),(-10,40),(10,40));result=k.discover(source,Counter());k.validate(source,result,Counter())
        self.assertEqual(result['status'],'refuted');self.assertEqual({abs(l) for cl in result['seed'] for l in cl},{10,40})
        self.assertEqual(result,k.discover(list(reversed(source))+[source[0],(90,-90)],Counter()))
        mixed=(*source,(70,80));r=k.discover(mixed,Counter());k.validate(mixed,r,Counter());self.assertEqual(r['status'],'refuted')
        with self.assertRaises(ValueError):k.discover(source,Counter(),order_source=((1,2),))

    def test_native_round_origins_both_cold_readers_and_warm_invalidation(self):
        source=((-2,-1),(-2,1),(-1,2),(1,2));args,kw=delayed_history(source)
        result=c.feedback.probe.discover(*args,**kw,counts=Counter(),work_limit=1)
        p=c.feedback.prepare(*args,result,**kw,counts=Counter());sat=k.discover(p[29],Counter(),order_source=p[0])
        self.assertEqual(sat['status'],'refuted')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';solver=c.native.ResidualSolver(path);cc=Counter()
            try:
                root=c.compile_program(solver,*args,result,**kw,saturation=sat,counts=cc,shortcut='off');before=s.old.tables(solver.db)
                self.assertGreater(cc['saturation_native_expanded_saturation_probe_0'],0)
                self.assertEqual(root,c.compile_program(solver,*args,result,**kw,saturation=sat,counts=Counter()))
                bad=deepcopy(sat);bad['rounds'][0]['search']['cursor']['probes'][0]['proof']['conflict']=999999
                with self.assertRaises(ValueError):c.compile_program(solver,*args,result,**kw,saturation=bad,counts=Counter())
                self.assertEqual(before,s.old.tables(solver.db))
            finally:solver.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:self.assertFalse(reader._read(root)['answer'])
                finally:reader.close()

    def test_open_and_invalid_controls_never_certify_sat_or_refute(self):
        source=((1,2,3),(-1,-2,-3));result=k.discover(source,Counter());self.assertEqual((result['status'],result['reason']),('unresolved','fixed_point'))
        for controls in (dict(round_limit=0),dict(probe_limit=True),dict(work_limit=0),dict(trace_limit=False)):
            with self.assertRaises(ValueError):k.discover(source,Counter(),**controls)
        args,kw=delayed_history(((1,2),));r=c.feedback.probe.discover(*args,**kw,counts=Counter());p=c.feedback.prepare(*args,r,**kw,counts=Counter());sat=k.discover(p[29],Counter(),order_source=p[0]);solver=c.native.ResidualSolver()
        try:
            with self.assertRaises(ValueError):c.compile_program(solver,*args,r,**kw,saturation=sat,counts=Counter())
            self.assertFalse(any(s.old.tables(solver.db).values()))
        finally:solver.close()

    def test_frontier_overlay_only_removes_certified_case(self):
        parent=s.base.load(s.PARENT/'checkpoint.json')['b13_native_feedback']['remaining'];rows=s.rows()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay.json';s.compact(path,dict(parent=parent,excluded=[[37,39]]))
            self.assertEqual(s.load_frontier(s.old.binding(path)),[r for r in rows if (r['target'],r['event'])!=(37,39)])
            s.compact(path,dict(parent=parent,excluded=[[37,39],[1,0]]))
            with self.assertRaises(ValueError):s.load_frontier(s.old.binding(path))


if __name__=='__main__':unittest.main()
