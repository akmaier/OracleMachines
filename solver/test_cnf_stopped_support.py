from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import json, random, unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_observer import StoppedObserver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_stopped_support import conditional_unit, extract, make_open_plan
from experiments.cnf_partial_proof_plan import check_plan, survival, recompose
from experiments.cnf_conditional_unit_support import check_template, materialize
from experiments.cnf_fresh_mixtures import attempt, generate
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class StoppedSupportTests(unittest.TestCase):
    def template(self, source, guards):
        source = native.normalize(source)[0]
        return conditional_unit(source, guards, Counter())

    def test_unit_reason_slice_preserves_branch_assumptions(self):
        source = ((-3,),(-2,3),(-1,2),(4,5))
        t = self.template(source,[[1,True],[4,True]])
        self.assertEqual(t['assumptions'],[[1,True]])
        self.assertEqual(check_template(t),{(-3,),(-2,3),(-1,2)})

    def test_exhaustive_conditional_truth(self):
        clauses=[[-1],[-2],[1,2],[-1,2],[1,-2]]
        hits=0
        for mask in range(1<<len(clauses)):
            source=native.normalize([c for i,c in enumerate(clauses) if mask>>i&1])[0]
            for values in product((None,False,True),repeat=2):
                guards=[[i+1,b] for i,b in enumerate(values) if b is not None]
                t=conditional_unit(source,guards,Counter())
                if t is None:continue
                hits+=1;check_template(t)
                for bits in product((False,True),repeat=2):
                    assignment=dict(enumerate(bits,1))
                    if all(assignment[v]==b for v,b in t['assumptions']):
                        self.assertFalse(native.holds(t['clauses'],assignment))
        self.assertGreater(hits,0)

    def test_open_plan_never_claims_uncovered_assignments(self):
        ts=[self.template([[1,2],[-1,2]],[[2,False]]), self.template([[1,2],[1,-2]],[[1,False]])]
        for cap in (1,2,3,7,129):
            counts=Counter();plan=make_open_plan(ts,node_limit=cap,counts=counts)
            check_plan(plan,node_limit=cap);self.assertLessEqual(counts['stopped_plan_nodes'],cap)
            for bits in product((False,True),repeat=2):
                assignment=dict(enumerate(bits,1));node=plan['tree']
                while 'variable' in node:node=node['high' if assignment[node['variable']] else 'low']
                t=plan['templates'][node['leaf']]
                if not t.get('open'):
                    self.assertTrue(all(assignment[v]==b for v,b in t['assumptions']))
                    self.assertFalse(native.holds(t['clauses'],assignment))

    def test_zero_budget_open_plan_stays_unknown(self):
        s=LazyBinaryClosureSolver();self.addCleanup(s.close)
        result=recompose(s,[[1,2]],make_open_plan([]),0)
        self.assertTrue(result['stopped']);self.assertIsNone(s._read(result['root']))

    def test_complete_conditional_cover_and_cold_readers(self):
        source=[[-1,-2],[-1,2],[1,-2],[1,2]]
        ts=[self.template(source,[[1,b]]) for b in (False,True)]
        plan=make_open_plan(ts)
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=LazyBinaryClosureSolver(path)
            try:
                r=recompose(s,source,plan,0)
                self.assertFalse(r['stopped']);self.assertFalse(s._read(r['root'])['answer'])
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:self.assertFalse(s._read(r['root'])['answer'])
                finally:s.close()

    def test_deleted_support_is_open_and_cannot_refute_sat_target(self):
        source=[[-1,-2],[-1,2],[1,-2],[1,2]]
        plan=make_open_plan([self.template(source,[[1,b]]) for b in (False,True)])
        target=source[1:];self.assertFalse(all(survival(target,plan,Counter())))
        s=LazyBinaryClosureSolver();self.addCleanup(s.close)
        r=recompose(s,target,plan,256)
        self.assertFalse(r['stopped']);self.assertTrue(s._read(r['root'])['answer'])

    def test_capture_is_passive_for_unlabelled_random_inputs(self):
        a=LazyBinaryClosureSolver(node_limit=16,batch_rows=1,affine_variables=1)
        b=StoppedObserver(node_limit=16,batch_rows=1,affine_variables=1);b.observe=True
        self.addCleanup(a.close);self.addCleanup(b.close)
        captured=0
        for seed in range(20):
            rng=random.Random(seed)
            source=[[v if rng.randrange(2) else -v for v in rng.sample(range(1,9),3)] for _ in range(34)]
            x,y=attempt(a,source),attempt(b,source)
            self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
            self.assertEqual(dict(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),dict(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            c=Counter();r=extract(b.capture['source'],b.capture['candidates'],b,c)
            captured+=len(r['templates'])
            for t in r['templates']:check_template(t)
            self.assertFalse(b._pending);self.assertFalse(b._visit_frames)
        self.assertGreater(captured,0)

    def test_budget_rollback_is_explicitly_unretained(self):
        s=StoppedObserver(node_limit=8);s.observe=True;self.addCleanup(s.close)
        r=attempt(s,generate('random-three',18,0,seed=202611240501)[0])
        self.assertEqual(r['status'],'unresolved');self.assertTrue(s.capture['candidates'])
        c=Counter();out=extract(s.capture['source'],s.capture['candidates'],s,c)
        self.assertGreater(c['stopped_unretained_endpoints'],0)
        self.assertFalse(out['templates'])

    def test_capture_limits_only_reduce_observations(self):
        source=generate('random-three',36,0,seed=202611240501)[0]
        a=LazyBinaryClosureSolver(node_limit=64)
        b=StoppedObserver(node_limit=64,capture_slots=1,capture_candidates=1,capture_key_bytes=1);b.observe=True
        self.addCleanup(a.close);self.addCleanup(b.close)
        x,y=attempt(a,source),attempt(b,source)
        self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
        self.assertFalse(b.capture['candidates'])
        self.assertGreater(b.capture['counts'].get('pending_limit_skips',0),0)

    def test_corrupt_capture_and_conditional_certificate_rejected(self):
        s=StoppedObserver(node_limit=64,batch_rows=1);s.observe=True;self.addCleanup(s.close)
        attempt(s,generate('random-three',18,0,seed=202611240501)[0])
        self.assertTrue(s.capture['candidates'])
        record=deepcopy(s.capture['candidates'][0]);record['mapping']=[[1,99999]]
        with self.assertRaises(ValueError):extract(s.capture['source'],[record],s)
        t=self.template([[-1,2],[-2]],[[1,True]])
        t['trace'][0][1]=9999
        with self.assertRaises(ValueError):check_template(t)

    def test_json_roundtrip_keeps_plan_and_support(self):
        source=[[-1,-2],[-1,2],[1,-2],[1,2]]
        plan=make_open_plan([self.template(source,[[1,b]]) for b in (False,True)])
        restored=json.loads(json.dumps(plan));check_plan(restored)
        self.assertEqual(plan,restored)


if __name__=='__main__':unittest.main()
