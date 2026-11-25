from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_third_feedback as c,cnf_complement_probes as first
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit
from solver.test_cnf_closure_probes import closure
from solver.test_cnf_changed_closure_probes import closed


def fixture(guards=False):
    source=c.native.normalize([(1,2),(1,-2),(-1,3,4),(-1,3,-4),
        (-3,5,6),(-3,5,-6),(-3,7,8),(-3,7,-8),(-3,9,10),(-3,9,-10),(-5,-7,-9),(11,12)])[0]
    ts=[conditional_unit(((-2,1),(1,2)),[[1,False]],Counter())] if guards else []
    _,_,bank,_=c.frozen.prepare(source,ts,'all',Counter())
    def failed(bank,lit):
        return dict(assumption=lit,proof=c.frozen.UnitIndex(bank,Counter()).probe(lit,Counter(),lambda:99999,256))
    seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[failed(bank,-1)])
    cl=closure(source,ts,seed);b1=c.feedback.prepare(source,ts,seed,Counter())[3]
    new=dict(seed,mode='conditioned',probes=[failed(b1,-3)])
    b2=c.layered.prepare(source,ts,seed,cl,new,Counter())[5];ncl=closed(b2)
    third=dict(action='searched',program=dict(new,probes=[failed(b2,v) for v in (-5,-7,-9)]))
    return source,ts,seed,cl,new,ncl,third


class ThirdFeedbackTests(unittest.TestCase):
    def test_composition_refutes_without_new_assumptions(self):
        args=fixture()
        for mode,status in (('base','unresolved'),('feedback','refuted')):
            counts=Counter();p=c.discover(*args,counts,mode=mode);c.validate(*args,p,Counter())
            self.assertEqual(p['status'],status);self.assertEqual(counts['unit_probes'],1);self.assertEqual(counts['probe_roots'],0)
        self.assertFalse(any(c.native.holds(args[0],dict(enumerate(bits,1))) for bits in product((False,True),repeat=12)))

    def test_native_full_support_warm_and_both_readers(self):
        args=fixture();p=c.discover(*args,Counter())
        for selected in (False,True):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    counts=Counter();key=c.compile_program(s,*args,p,counts,select_support=selected)
                    self.assertFalse(s._read(key)['answer'])
                    for k in ('layer_expanded_old','layer_expanded_new','layer_expanded_third'):self.assertGreater(counts[k],0)
                    before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                    self.assertEqual(key,c.compile_program(s,*args,p,Counter(),select_support=selected))
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    r=cls(path)
                    try:self.assertFalse(r._read(key)['answer'])
                    finally:r.close()

    def test_guard_and_binary_extension(self):
        args=fixture(True);p=c.discover(*args,Counter());s=c.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            self.assertFalse(s._read(c.compile_extension(s,args[0],args[1],prefix,*args[2:],p,Counter()))['answer'])
        finally:s.close()

    def test_invalid_provenance_and_closures_rejected_when_warm(self):
        args=fixture();p=c.discover(*args,Counter());s=c.native.ResidualSolver()
        try:
            c.compile_program(s,*args,p,Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            prepared=c.prepare(*args,Counter())
            for kind in ('old','new','third','forward','closure','next','top','open'):
                a=deepcopy(args);q=deepcopy(p)
                if kind=='old':a[2]['probes'][0]['proof']['conflict']=99999
                elif kind=='new':a[4]['probes'][0]['proof']['conflict']=99999
                elif kind=='third':a[6]['program']['probes'][0]['assumption']=99999
                elif kind=='forward':a[6]['program']['probes'][0]['proof']['conflict']=len(prepared[5])
                elif kind=='closure':a[3]['assignment'][0][1]=False
                elif kind=='next':a[5]['assignment'][0][1]=False
                elif kind=='top':q['proof']['conflict']=99999
                else:q.update(status='unresolved',reason='open',proof=None)
                with self.assertRaises(ValueError):c.compile_program(s,*a,q,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_no_exclusions_and_satisfiable_banks_remain_unresolved(self):
        source=((1,2),);empty=dict(units=[],assignment=[])
        seed=dict(status='unresolved',reason='complete',mode='all',trace_limit=256,terminal=None,probes=[])
        new=dict(seed,mode='conditioned');args=(source,[],seed,empty,new,empty,dict(action='unchanged',program=None))
        for mode in ('base','feedback'):
            p=c.discover(*args,Counter(),mode=mode);c.validate(*args,p,Counter())
            self.assertEqual((p['status'],p['reason']),('unresolved','open'))
        prepared=c.prepare(*args,Counter());self.assertEqual(prepared[5],prepared[7])

    def test_budget_stops_charge_occurrences(self):
        args=fixture()
        for kw in ({'work_limit':1},{'trace_limit':1}):
            counts=Counter();p=c.discover(*args,counts,**kw);c.validate(*args,p,Counter())
            self.assertEqual(p['status'],'unresolved');self.assertLessEqual(counts['probe_occurrence_visits'],kw.get('work_limit',262144))
        for kw in ({'mode':'sat'},{'work_limit':True},{'trace_limit':0}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**kw)

    def test_third_stage_cannot_be_flattened(self):
        args=fixture();prepared=c.prepare(*args,Counter())
        for bank in (prepared[1],prepared[3]):
            with self.assertRaises(ValueError):c.changed.prior.check_program(prepared[0],bank,args[6]['program'],Counter())

    def test_generated_small_formulas_against_exhaustive_truth(self):
        rng=random.Random(251212);checked=0
        for _ in range(180):
            source=c.native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))])[0]
            seed=first.discover(source,[],Counter(),probe_limit=2)
            if seed['status']=='refuted':continue
            cl=closure(source,[],seed)
            if cl is None:continue
            new=c.changed.prior.discover(source,[],seed,cl,Counter(),probe_limit=2)
            if new['status']=='refuted':continue
            ncl=closed(c.layered.prepare(source,[],seed,cl,new,Counter())[5])
            if ncl is None:continue
            args=(source,[],seed,cl,new,ncl);third=c.changed.discover(*args,Counter(),policy='all',probe_limit=2)
            if third['program']['status']=='refuted':continue
            args=(*args,third);p=c.discover(*args,Counter());c.validate(*args,p,Counter());checked+=1
            if p['status']=='refuted':
                self.assertFalse(any(c.native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=5)))
        self.assertGreater(checked,70)


if __name__=='__main__':unittest.main()
