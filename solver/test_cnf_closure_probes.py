from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_closure_probes as candidate
from experiments import cnf_complement_probes as first
from experiments import cnf_residual_dag as native
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit


def fixture():
    return native.normalize([(1,2),(1,-2),(-1,-3,4),(-1,-3,-4),(-1,3,5),(-1,3,-5),(6,7)])[0]


def closure(source,templates,seed):
    _,_,_,bank,_=candidate.feedback.prepare(source,templates,seed,Counter())
    fixed,trace,conflict=native.propagate(bank,Counter())
    if conflict is not None:return None
    return dict(units=trace,assignment=sorted([list(p) for p in fixed.items()]))


class ClosureProbeTests(unittest.TestCase):
    def test_conditioned_probes_close_an_open_feedback_bank(self):
        source=fixture();seed=first.discover(source,[],Counter());self.assertEqual(seed['status'],'unresolved');cl=closure(source,[],seed)
        results={}
        for mode in ('restart','conditioned'):
            c=Counter();p=candidate.discover(source,[],seed,cl,c,mode=mode);candidate.validate(source,[],seed,cl,p,Counter())
            self.assertEqual(p['status'],'refuted');self.assertEqual(c['probe_roots'],2);results[mode]=c
        self.assertLess(results['conditioned']['probe_occurrence_visits'],results['restart']['probe_occurrence_visits'])
        self.assertLess(results['conditioned']['probe_initialization_clauses'],results['restart']['probe_initialization_clauses'])

    def test_native_proofs_survive_warm_and_both_cold_readers(self):
        source=fixture();seed=first.discover(source,[],Counter());cl=closure(source,[],seed);p=candidate.discover(source,[],seed,cl,Counter())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';s=native.ResidualSolver(path)
            try:
                root=candidate.compile_program(s,source,[],seed,cl,p,Counter());self.assertFalse(s._read(root)['answer'])
                self.assertEqual(s._read(root)['proof']['kind'],'component');before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                self.assertEqual(root,candidate.compile_program(s,source,[],seed,cl,p,Counter()))
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path)
                try:self.assertFalse(r._read(root)['answer'])
                finally:r.close()

    def test_guard_and_old_probe_provenance_remain_separate(self):
        source=fixture();template=conditional_unit(((-2,1),(1,2)),[[1,False]],Counter());templates=[template]
        _,_,bank,_=candidate.frozen.prepare(source,templates,'all',Counter());idx=candidate.frozen.UnitIndex(bank,Counter())
        seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[dict(assumption=-1,proof=idx.probe(-1,Counter(),lambda:99999,256))])
        cl=closure(source,templates,seed);p=candidate.discover(source,templates,seed,cl,Counter())
        for selected in (True,False):
            s=native.ResidualSolver()
            try:self.assertFalse(s._read(candidate.compile_program(s,source,templates,seed,cl,p,Counter(),select_support=selected))['answer'])
            finally:s.close()

    def test_random_small_open_closures_match_truth_and_restart(self):
        rng=random.Random(242510);checked=0
        for _ in range(160):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,22))])[0]
            seed=first.discover(source,[],Counter(),probe_limit=2)
            if seed['status']=='refuted':continue
            cl=closure(source,[],seed)
            if cl is None:continue
            a=candidate.discover(source,[],seed,cl,Counter(),mode='restart');b=candidate.discover(source,[],seed,cl,Counter())
            self.assertEqual(a['status'],b['status']);candidate.validate(source,[],seed,cl,b,Counter());checked+=1
            if b['status']=='refuted':
                self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=5)))
                s=native.ResidualSolver()
                try:self.assertFalse(s._read(candidate.compile_program(s,source,[],seed,cl,b,Counter()))['answer'])
                finally:s.close()
        self.assertGreater(checked,60)

    def test_invalid_closure_seed_or_new_trace_rejected_before_warm_reuse(self):
        source=fixture();seed=first.discover(source,[],Counter());cl=closure(source,[],seed);p=candidate.discover(source,[],seed,cl,Counter());s=native.ResidualSolver()
        try:
            candidate.compile_program(s,source,[],seed,cl,p,Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('closure','assignment','incomplete','seed','new','opposite'):
                cc=deepcopy(cl);ss=deepcopy(seed);pp=deepcopy(p)
                if kind=='closure':cc['units'][0][1]=99999
                elif kind=='assignment':cc['assignment'][0][1]=not cc['assignment'][0][1]
                elif kind=='incomplete':cc=dict(units=[],assignment=[])
                elif kind=='seed':ss['probes'][0]['proof']['conflict']=99999
                elif kind=='new':pp['probes'][0]['proof']['conflict']=99999
                else:pp['terminal']['high']=pp['terminal']['low']
                with self.assertRaises(ValueError):candidate.compile_program(s,source,[],ss,cc,pp,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_budgets_charge_lifted_closure_and_never_call_open_sat(self):
        source=fixture();seed=first.discover(source,[],Counter());cl=closure(source,[],seed)
        for kw in ({'probe_limit':1},{'work_limit':1},{'trace_limit':1}):
            c=Counter();p=candidate.discover(source,[],seed,cl,c,**kw);self.assertEqual(p['status'],'unresolved');candidate.validate(source,[],seed,cl,p,Counter())
            self.assertLessEqual(c['probe_roots'],kw.get('probe_limit',64));self.assertLessEqual(c['probe_occurrence_visits'],kw.get('work_limit',262144))
        source=native.normalize([(1,2),(1,-2)])[0];seed=first.discover(source,[],Counter());cl=closure(source,[],seed)
        p=candidate.discover(source,[],seed,cl,Counter());self.assertEqual((p['status'],p['reason']),('unresolved','complete'))


if __name__=='__main__':unittest.main()
