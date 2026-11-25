from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_layered_feedback as c,cnf_complement_probes as first
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit
from solver.test_cnf_closure_probes import closure


def fixture():
    return c.native.normalize([(1,2),(1,-2),(-1,3,6),(-1,3,-6),(-1,4,7),(-1,4,-7),(-1,5,8),(-1,5,-8),(-3,-4,-5),(9,10)])[0]


def layers(source,ts=(),limit=64):
    _,_,bank,_=c.frozen.prepare(source,list(ts),'all',Counter());idx=c.frozen.UnitIndex(bank,Counter())
    seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[dict(assumption=-1,proof=idx.probe(-1,Counter(),lambda:99999,256))])
    cl=closure(source,list(ts),seed);new=c.prior.discover(source,list(ts),seed,cl,Counter(),probe_limit=limit)
    return seed,cl,new


class LayeredFeedbackTests(unittest.TestCase):
    def test_new_exclusions_compose_without_new_assumptions(self):
        source=fixture();seed,cl,new=layers(source);self.assertEqual(new['status'],'unresolved')
        for mode,status in (('base','unresolved'),('feedback','refuted')):
            counts=Counter();p=c.discover(source,[],seed,cl,new,counts,mode=mode);c.validate(source,[],seed,cl,new,p,Counter())
            self.assertEqual(p['status'],status);self.assertEqual(counts['unit_probes'],1);self.assertEqual(counts['probe_roots'],0)
        self.assertFalse(any(c.native.holds(source,dict(enumerate(b,1))) for b in product((False,True),repeat=10)))

    def test_full_and_support_native_proofs_warm_and_cold(self):
        source=fixture();seed,cl,new=layers(source);p=c.discover(source,[],seed,cl,new,Counter())
        for selected in (False,True):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    counts=Counter();key=c.compile_program(s,source,[],seed,cl,new,p,counts,select_support=selected)
                    self.assertFalse(s._read(key)['answer']);self.assertGreater(counts['layer_expanded_old'],0);self.assertGreater(counts['layer_expanded_new'],0)
                    if selected:self.assertEqual(s._read(key)['proof']['kind'],'component')
                    else:self.assertGreater(counts['layer_fixed_trace_steps'],0)
                    before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                    self.assertEqual(key,c.compile_program(s,source,[],seed,cl,new,p,Counter()))
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    r=cls(path)
                    try:self.assertFalse(r._read(key)['answer'])
                    finally:r.close()

    def test_checked_guard_provenance(self):
        source=fixture();ts=[conditional_unit(((-6,-1,3),(-1,3,6)),[[1,True],[3,False]],Counter())]
        seed,cl,new=layers(source,ts,limit=1);self.assertEqual(new['status'],'unresolved');p=c.discover(source,ts,seed,cl,new,Counter());self.assertEqual(p['status'],'refuted')
        for selected in (False,True):
            s=c.native.ResidualSolver()
            try:self.assertFalse(s._read(c.compile_program(s,source,ts,seed,cl,new,p,Counter(),select_support=selected))['answer'])
            finally:s.close()

    def test_invalid_or_forward_dependency_rejected_before_warm_reuse(self):
        source=fixture();seed,cl,new=layers(source);p=c.discover(source,[],seed,cl,new,Counter())
        prepared=c.prepare(source,[],seed,cl,new,Counter())
        for warm in (False,True):
            s=c.native.ResidualSolver()
            try:
                if warm:c.compile_program(s,source,[],seed,cl,new,p,Counter())
                before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                for kind in ('old','closure','new','forward','top','open'):
                    a,b,d,q=map(deepcopy,(seed,cl,new,p))
                    if kind=='old':a['probes'][0]['proof']['conflict']=len(prepared[1])
                    elif kind=='closure':b['assignment'][0][1]=False
                    elif kind=='new':d['probes'][0]['assumption']=99999
                    elif kind=='forward':d['probes'][0]['proof']['conflict']=len(prepared[3])
                    elif kind=='top':q['proof']['conflict']=len(prepared[5])
                    else:q.update(status='unresolved',reason='open',proof=None)
                    with self.assertRaises(ValueError):c.compile_program(s,source,[],a,b,d,q,Counter())
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
            finally:s.close()

    def test_new_layer_is_not_an_original_bank_seed(self):
        source=fixture();seed,cl,new=layers(source)
        flattened=dict(new,mode='all')
        with self.assertRaises(ValueError):c.feedback.prepare(source,[],flattened,Counter())

    def test_random_small_layers_against_exhaustive_truth(self):
        rng=random.Random(252506);checked=0
        for _ in range(160):
            source=c.native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))])[0]
            seed=first.discover(source,[],Counter(),probe_limit=2)
            if seed['status']=='refuted':continue
            cl=closure(source,[],seed)
            if cl is None:continue
            new=c.prior.discover(source,[],seed,cl,Counter(),probe_limit=2)
            if new['status']=='refuted':continue
            p=c.discover(source,[],seed,cl,new,Counter());c.validate(source,[],seed,cl,new,p,Counter());checked+=1
            if p['status']=='refuted':
                self.assertFalse(any(c.native.holds(source,dict(enumerate(b,1))) for b in product((False,True),repeat=5)))
                s=c.native.ResidualSolver()
                try:self.assertFalse(s._read(c.compile_program(s,source,[],seed,cl,new,p,Counter()))['answer'])
                finally:s.close()
        self.assertGreater(checked,60)

    def test_budget_stops_and_satisfiable_closures_are_not_sat(self):
        source=fixture();seed,cl,new=layers(source)
        for kw in ({'work_limit':1},{'trace_limit':1}):
            counts=Counter();p=c.discover(source,[],seed,cl,new,counts,**kw);self.assertEqual(p['status'],'unresolved');c.validate(source,[],seed,cl,new,p,Counter())
            self.assertLessEqual(counts['probe_occurrence_visits'],kw.get('work_limit',262144))
        source=c.native.normalize([(1,2),(1,-2)])[0];seed,cl,new=layers(source)
        p=c.discover(source,[],seed,cl,new,Counter());self.assertEqual((p['status'],p['reason']),('unresolved','open'))

    def test_extension_validates_layers_before_cached_root(self):
        source=fixture();seed,cl,new=layers(source);p=c.discover(source,[],seed,cl,new,Counter());prefix=dict(status='unresolved',steps=[],path_limit=256)
        s=c.native.ResidualSolver()
        try:
            root=c.compile_extension(s,source,[],prefix,seed,cl,new,p,Counter());self.assertFalse(s._read(root)['answer'])
            bad=deepcopy(new);bad['probes'][0]['proof']['conflict']=99999
            with self.assertRaises(ValueError):c.compile_extension(s,source,[],prefix,seed,cl,bad,p,Counter())
        finally:s.close()


if __name__=='__main__':unittest.main()
