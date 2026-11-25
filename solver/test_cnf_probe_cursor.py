from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_probe_cursor as c,cnf_probe_cursor_native as compiler,cnf_complement_probes as first
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit
from solver.test_cnf_closure_probes import closure
from solver.test_cnf_changed_closure_probes import closed


def fixture(guards=False):
    source=c.native.normalize([(1,2),(1,-2),(-1,3,4),(-1,3,-4),(-3,5,6),(-3,5,-6),
        (-5,7,8),(-5,7,-8),(-5,-7,8),(-5,-7,-8),(9,10)])[0]
    ts=[conditional_unit(((-2,1),(1,2)),[[1,False]],Counter())] if guards else []
    _,_,bank,_=c.frozen.prepare(source,ts,'all',Counter())
    def failed(bank,lit):return dict(assumption=lit,proof=c.frozen.UnitIndex(bank,Counter()).probe(lit,Counter(),lambda:99999,256))
    seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[failed(bank,-1)])
    cl=closure(source,ts,seed);b1=c.feedback.feedback.prepare(source,ts,seed,Counter())[3]
    new=dict(seed,mode='conditioned',probes=[failed(b1,-3)])
    b2=c.feedback.layered.prepare(source,ts,seed,cl,new,Counter())[5];ncl=closed(b2)
    third=dict(action='searched',program=dict(new,probes=[failed(b2,-5)]))
    args=(source,ts,seed,cl,new,ncl,third);b3=c.feedback.prepare(*args,Counter())[7]
    return (*args,closed(b3))


def empty_args(source):
    seed=dict(status='unresolved',reason='complete',mode='all',trace_limit=256,terminal=None,probes=[])
    empty=dict(units=[],assignment=[])
    return source,[],seed,empty,dict(seed,mode='conditioned'),empty,dict(action='unchanged',program=None),empty


class ProbeCursorTests(unittest.TestCase):
    def test_split_budget_keeps_promoted_complement_and_exact_proof(self):
        args=fixture();one=c.discover(*args,Counter(),probe_limit=1)
        self.assertEqual(one['program']['status'],'unresolved');self.assertEqual(len(one['cursor']['completed']),1)
        counts=Counter();two=c.discover(*args,counts,cursor=one['cursor'],probe_limit=1)
        full=c.discover(*args,Counter(),probe_limit=2)
        self.assertEqual(two,full);self.assertEqual(two['program']['status'],'refuted')
        self.assertEqual(counts['probe_roots'],1);self.assertEqual(counts['cursor_reused_completed'],1)
        self.assertEqual(two['cursor']['completed'][1],-two['cursor']['completed'][0]);c.validate(*args,two,Counter())

    def test_json_roundtrip_and_input_state_not_mutated(self):
        args=fixture();one=c.discover(*args,Counter(),probe_limit=1);saved=deepcopy(one)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'cursor.json';path.write_text(json.dumps(one));cold=json.loads(path.read_text())
            two=c.discover(*args,Counter(),cursor=cold['cursor'],probe_limit=1)
        self.assertEqual(one,saved);self.assertEqual(cold,saved)
        two['cursor']['completed'].append(999);self.assertEqual(one,saved)

    def test_interrupted_probe_is_retried_not_marked_completed(self):
        args=fixture();counts=Counter();stopped=c.discover(*args,counts,work_limit=1)
        self.assertEqual(stopped['program']['reason'],'work_limit');self.assertEqual(stopped['cursor']['completed'],[])
        self.assertLessEqual(counts['probe_occurrence_visits'],1)
        resumed=c.discover(*args,Counter(),cursor=stopped['cursor']);self.assertEqual(resumed,c.discover(*args,Counter()))
        c.validate(*args,stopped,Counter())

    def test_exact_binding_and_policy_invalidation(self):
        args=empty_args(((1,2,3),));p=c.discover(*args,Counter(),probe_limit=1)
        with self.assertRaises(ValueError):c.discover(*empty_args(((-3,-2,-1),(1,2,3))),Counter(),cursor=p['cursor'])
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=p['cursor'],trace_limit=257)
        bad=deepcopy(p['cursor']);bad['binding']=bad['binding'].replace(c.POLICY,'changed-policy')
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=bad)

    def test_schedule_mutation_and_failed_proof_rejected(self):
        args=fixture();p=c.discover(*args,Counter(),probe_limit=1)
        for kind in ('duplicate','wrong','proof','order','missing'):
            bad=deepcopy(p)
            if kind=='duplicate':bad['cursor']['completed']*=2
            elif kind=='wrong':bad['cursor']['completed'][0]=True
            elif kind=='proof':bad['cursor']['probes'][0]['proof']['conflict']=99999
            elif kind=='order':bad['cursor']['completed'][0]*=-1
            else:bad['cursor']=None
            with self.assertRaises(ValueError):c.validate(*args,bad,Counter())

    def test_open_history_is_not_a_sat_certificate(self):
        args=empty_args(((-2,-1),(-2,1),(-1,2),(1,2)))
        p=c.discover(*args,Counter(),probe_limit=1)
        forged=deepcopy(p['cursor']);forged.update(completed=c.frozen.roots(args[0]),probes=[])
        skipped=c.discover(*args,Counter(),cursor=forged);c.validate(*args,skipped,Counter())
        self.assertEqual((skipped['program']['status'],skipped['program']['reason']),('unresolved','complete'))
        self.assertEqual(c.discover(*args,Counter())['program']['status'],'refuted')
        s=c.native.ResidualSolver()
        try:
            with self.assertRaises(ValueError):compiler.compile_program(s,*args,skipped,Counter())
        finally:s.close()

    def test_native_support_full_warm_and_cold(self):
        args=fixture();p=c.discover(*args,Counter())
        for selected in (False,True):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    counts=Counter();key=compiler.compile_program(s,*args,p,counts,select_support=selected)
                    self.assertFalse(s._read(key)['answer']);self.assertGreater(counts['layer_expanded_third'],0)
                    before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                    self.assertEqual(key,compiler.compile_program(s,*args,p,Counter()))
                    bad=deepcopy(p);bad['cursor']['probes'][0]['proof']['conflict']=99999
                    with self.assertRaises(ValueError):compiler.compile_program(s,*args,bad,Counter())
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(key)['answer'])
                    finally:reader.close()

    def test_guards_prefix_and_completed_terminal_reuse(self):
        args=fixture(True);p=c.discover(*args,Counter());counts=Counter()
        self.assertEqual(p,c.discover(*args,counts,cursor=p['cursor']));self.assertEqual(counts['probe_roots'],0)
        s=c.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            self.assertFalse(s._read(compiler.compile_extension(s,args[0],args[1],prefix,*args[2:],p,Counter()))['answer'])
        finally:s.close()

    def test_bounds_and_satisfiable_exhaustion(self):
        args=empty_args(((1,2),));p=c.discover(*args,Counter(),probe_limit=2);q=c.discover(*args,Counter(),cursor=p['cursor'],probe_limit=2)
        self.assertEqual(q['program']['reason'],'complete');self.assertEqual(q['program']['status'],'unresolved');self.assertEqual(len(q['cursor']['completed']),4)
        for kw in ({'probe_limit':True},{'work_limit':0},{'trace_limit':-1}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**kw)
        p=c.discover(*fixture(),Counter(),trace_limit=1);self.assertEqual(p['program']['reason'],'trace_limit');self.assertEqual(p['cursor']['completed'],[])

    def test_generated_small_inputs_split_equal_single_and_truth(self):
        rng=random.Random(251341);checked=0
        for _ in range(180):
            source=c.native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))])[0]
            seed=first.discover(source,[],Counter(),probe_limit=1)
            if seed['status']=='refuted':continue
            cl=closure(source,[],seed)
            if cl is None:continue
            new=c.prior.discover(source,[],seed,cl,Counter(),probe_limit=1)
            if new['status']=='refuted':continue
            ncl=closed(c.feedback.layered.prepare(source,[],seed,cl,new,Counter())[5])
            if ncl is None:continue
            args=(source,[],seed,cl,new,ncl);third=c.feedback.changed.discover(*args,Counter(),policy='all',probe_limit=1)
            if third['program']['status']=='refuted':continue
            args=(*args,third);fcl=closed(c.feedback.prepare(*args,Counter())[7])
            if fcl is None:continue
            args=(*args,fcl);a=c.discover(*args,Counter(),probe_limit=1);b=c.discover(*args,Counter(),cursor=json.loads(json.dumps(a['cursor'])),probe_limit=2);d=c.discover(*args,Counter(),probe_limit=3)
            self.assertEqual(b,d);c.validate(*args,b,Counter());checked+=1
            if b['program']['status']=='refuted':self.assertFalse(any(c.native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=5)))
        self.assertGreater(checked,70)


if __name__=='__main__':unittest.main()
