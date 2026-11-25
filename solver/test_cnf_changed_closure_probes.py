from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random
import tempfile
import unittest
from experiments import cnf_changed_closure_probes as c
from experiments import cnf_changed_closure_native as compiler
from experiments import cnf_complement_probes as first
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit
from solver.test_cnf_closure_probes import closure


def closed(bank):
    fixed, trace, conflict = c.layered.native.propagate(bank, Counter())
    if conflict is not None:
        return None
    return dict(units=trace, assignment=sorted([list(p) for p in fixed.items()]))


def fixture(guards=False):
    source=c.layered.native.normalize([(1,2),(1,-2),(-1,3,4),(-1,3,-4),
        (-3,5,6),(-3,5,-6),(-3,-5,6),(-3,-5,-6),(7,8)])[0]
    ts=[conditional_unit(((-2,1),(1,2)),[[1,False]],Counter())] if guards else []
    _,_,bank,_=c.frozen.prepare(source,ts,'all',Counter())
    def failed(bank,lit):
        return dict(assumption=lit,proof=c.frozen.UnitIndex(bank,Counter()).probe(lit,Counter(),lambda:99999,256))
    seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[failed(bank,-1)])
    cl=closure(source,ts,seed)
    b1=c.layered.feedback.prepare(source,ts,seed,Counter())[3]
    new=dict(status='unresolved',reason='probe_limit',mode='conditioned',trace_limit=256,terminal=None,probes=[failed(b1,-3)])
    b2=c.layered.prepare(source,ts,seed,cl,new,Counter())[5]
    return source,ts,seed,cl,new,closed(b2)


class ChangedClosureProbeTests(unittest.TestCase):
    def test_third_probe_layer_refutes_and_matches_truth(self):
        args=fixture();results=[]
        for policy in ('all','changed'):
            counts=Counter();p=c.discover(*args,counts,policy=policy);c.validate(*args,p,Counter())
            self.assertEqual(p['program']['status'],'refuted');self.assertEqual(counts['probe_roots'],2);results.append(p)
        self.assertEqual(*results)
        self.assertFalse(any(c.layered.native.holds(args[0],dict(enumerate(b,1))) for b in product((False,True),repeat=8)))

    def test_native_full_support_warm_and_cold(self):
        args=fixture();p=c.discover(*args,Counter())
        for selected in (False,True):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=compiler.native.ResidualSolver(path)
                try:
                    counts=Counter();key=compiler.compile_program(s,*args,p,counts,select_support=selected)
                    self.assertFalse(s._read(key)['answer']);self.assertGreater(counts['layer_expanded_old'],0);self.assertGreater(counts['layer_expanded_new'],0)
                    before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                    self.assertEqual(key,compiler.compile_program(s,*args,p,Counter(),select_support=selected))
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    r=cls(path)
                    try:self.assertFalse(r._read(key)['answer'])
                    finally:r.close()

    def test_guard_and_prefix_path(self):
        args=fixture(True);p=c.discover(*args,Counter());s=compiler.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            key=compiler.compile_extension(s,args[0],args[1],prefix,*args[2:],p,Counter())
            self.assertFalse(s._read(key)['answer'])
        finally:s.close()

    def test_unchanged_policy_is_not_a_completeness_claim(self):
        # An unresolved program certifies its failures, not the search it omitted.
        # A caller can deliberately skip useful search. It must remain unresolved.
        source=((-2,-1),(-2,1),(-1,2),(1,2));empty=dict(units=[],assignment=[])
        seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[])
        new=dict(seed,mode='conditioned');args=(source,[],seed,empty,new,empty)
        counts=Counter();p=c.discover(*args,counts);c.validate(*args,p,Counter())
        self.assertEqual(p,dict(action='unchanged',program=None));self.assertEqual(counts['probe_roots'],0)
        self.assertEqual(c.discover(*args,Counter(),policy='all')['program']['status'],'refuted')
        solver=compiler.native.ResidualSolver()
        try:
            with self.assertRaises(ValueError):compiler.compile_program(solver,*args,p,Counter())
        finally:solver.close()

    def test_malformed_layers_and_closures_rejected_even_when_warm(self):
        args=fixture();p=c.discover(*args,Counter());s=compiler.native.ResidualSolver()
        try:
            compiler.compile_program(s,*args,p,Counter())
            before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('old','new','closure','next','top','terminal','skip'):
                a=deepcopy(args);q=deepcopy(p)
                if kind=='old':a[2]['probes'][0]['proof']['conflict']=99999
                elif kind=='new':a[4]['probes'][0]['proof']['conflict']=99999
                elif kind=='closure':a[3]['assignment'][0][1]=False
                elif kind=='next':a[5]['assignment'][0][1]=False
                elif kind=='top':q['program']['probes'][0]['proof']['conflict']=99999
                elif kind=='terminal':q['program']['terminal']['high']=q['program']['terminal']['low']
                else:q=dict(action='unchanged',program=None)
                with self.assertRaises(ValueError):compiler.compile_program(s,*a,q,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_budget_stops_and_accounting(self):
        args=fixture()
        for kw in ({'probe_limit':1},{'work_limit':1},{'trace_limit':1}):
            counts=Counter();p=c.discover(*args,counts,**kw);c.validate(*args,p,Counter())
            self.assertEqual(p['program']['status'],'unresolved')
            self.assertLessEqual(counts['probe_roots'],kw.get('probe_limit',64))
            self.assertLessEqual(counts['probe_occurrence_visits'],kw.get('work_limit',262144))
        for kw in ({'probe_limit':True},{'work_limit':0},{'trace_limit':-1},{'policy':'sat'}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**kw)

    def test_generated_small_formulas_exhaustive_truth(self):
        rng=random.Random(251125);checked=0
        for _ in range(180):
            source=compiler.native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))])[0]
            seed=first.discover(source,[],Counter(),probe_limit=2)
            if seed['status']=='refuted':continue
            cl=closure(source,[],seed)
            if cl is None:continue
            new=c.prior.discover(source,[],seed,cl,Counter(),probe_limit=2)
            if new['status']=='refuted':continue
            b2=c.layered.prepare(source,[],seed,cl,new,Counter())[5];ncl=closed(b2)
            if ncl is None:continue
            args=(source,[],seed,cl,new,ncl);p=c.discover(*args,Counter(),policy='all');c.validate(*args,p,Counter());checked+=1
            truth=any(compiler.native.holds(source,dict(enumerate(b,1))) for b in product((False,True),repeat=5))
            for row in p['program']['probes']:
                a=row['assumption']
                self.assertFalse(any(compiler.native.holds(source,dict(enumerate(b,1))) and b[abs(a)-1]==(a>0) for b in product((False,True),repeat=5)))
            if p['program']['status']=='refuted':self.assertFalse(truth)
        self.assertGreater(checked,70)

    def test_saved_outcomes_cannot_be_flattened_into_old_bank(self):
        args=fixture();p=c.discover(*args,Counter());prepared=c.prepare(*args,Counter())[0]
        with self.assertRaises(ValueError):c.prior.check_program(prepared[0],prepared[1],p['program'],Counter())


if __name__=='__main__':unittest.main()
