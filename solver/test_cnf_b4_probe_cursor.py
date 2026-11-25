from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,unittest
from experiments import cnf_b4_probe_cursor as c
from solver.test_cnf_probe_cursor import empty_args
from solver.test_cnf_changed_closure_probes import closed

FIELDS=('final_source','templates','seed','closure','new','next_closure','third','feedback_closure','probe_cursor','cursor_feedback_closure')


def small(source):
    args=empty_args(c.native.normalize(source)[0])
    history=c.feedback.cursor.discover(*args,Counter(),work_limit=1)
    if history['program']['status']=='refuted':return None
    args=(*args,history);cl=closed(c.feedback.prepare(*args,Counter())[9])
    return (*args,cl) if cl is not None else None


def fixture():
    rows=json.loads(Path('experiments/results/cnf-cursor-feedback/remaining-closures.json').read_text())['rows']
    for r in rows:
        args=tuple(r[k] for k in FIELDS)
        result=c.discover(*args,Counter())
        if result['action']=='searched' and result['program']['probes']:return args,result
    raise AssertionError('Missing preserved B4 failure fixture')


class B4ProbeCursorTests(unittest.TestCase):
    def test_cold_split_equals_single_and_keeps_prior_input(self):
        args,result=fixture();saved=deepcopy(args)
        initial_counts=Counter();a=c.discover(*args,initial_counts,probe_limit=32);counts=Counter()
        b=c.discover(*args,counts,cursor=json.loads(json.dumps(a['cursor'])),probe_limit=32)
        self.assertEqual(b,result);self.assertEqual(args,saved)
        self.assertEqual(counts['cursor_reused_completed']-initial_counts['cursor_reused_completed'],32)
        c.validate(*args,b,Counter())

    def test_unchanged_skip_is_not_exhaustion_counterexample(self):
        args=small(((-2,-1),(-2,1),(-1,2),(1,2)));self.assertIsNotNone(args)
        skipped=c.discover(*args,Counter());c.validate(*args,skipped,Counter())
        self.assertEqual(skipped,dict(action='unchanged',program=None,cursor=None))
        full=c.discover(*args,Counter(),policy='all');c.validate(*args,full,Counter())
        self.assertEqual(full['program']['status'],'refuted')
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=full['cursor'])

    def test_interrupted_root_retried_and_promoted_complement_preserved(self):
        args=small(((-2,-1),(-2,1),(-1,2),(1,2)));counts=Counter()
        p=c.discover(*args,counts,policy='all',work_limit=1)
        self.assertEqual(p['program']['reason'],'work_limit');self.assertEqual(p['cursor']['completed'],[])
        self.assertLessEqual(counts['probe_occurrence_visits'],1)
        one=c.discover(*args,Counter(),policy='all',cursor=p['cursor'],probe_limit=1)
        two=c.discover(*args,Counter(),policy='all',cursor=one['cursor'],probe_limit=1)
        self.assertEqual(two,c.discover(*args,Counter(),policy='all',probe_limit=2))
        self.assertEqual(two['cursor']['completed'][0],-two['cursor']['completed'][1])

    def test_b3_cursor_and_changed_binding_rejected(self):
        args,p=fixture()
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=args[8]['cursor'])
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=p['cursor'],trace_limit=257)
        bad=deepcopy(p);bad['cursor']['binding']='different'
        with self.assertRaises(ValueError):c.validate(*args,bad,Counter())
        with self.assertRaises(ValueError):c.validate(*args,dict(action='unchanged',program=None,cursor=None),Counter())

    def test_failed_proofs_schedule_and_old_provenance_rechecked(self):
        args,p=fixture()
        for kind in ('proof','duplicate','bool','old','closure'):
            a=deepcopy(args);q=deepcopy(p)
            if kind=='proof':q['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='duplicate':q['cursor']['completed']*=2
            elif kind=='bool':q['cursor']['completed'][0]=True
            elif kind=='old':a[8]['cursor']['binding']='different'
            else:a[9]['assignment'].append([999999,True])
            with self.assertRaises(ValueError):c.validate(*a,q,Counter())

    def test_open_history_is_trusted_scheduling_not_sat(self):
        args=small(((-2,-1),(-2,1),(-1,2),(1,2)))
        p=c.discover(*args,Counter(),policy='all',work_limit=1)
        forged=deepcopy(p['cursor']);forged.update(completed=c.frozen.roots(args[0]),probes=[])
        q=c.discover(*args,Counter(),policy='all',cursor=forged);c.validate(*args,q,Counter())
        self.assertEqual((q['program']['status'],q['program']['reason']),('unresolved','complete'))

    def test_bounds_and_trace_interruptions(self):
        args,p=fixture()
        for kw in ({'policy':'sat'},{'probe_limit':True},{'work_limit':0},{'trace_limit':-1}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**kw)
        q=c.discover(*args,Counter(),trace_limit=1)
        self.assertEqual(q['program']['reason'],'trace_limit');self.assertEqual(q['cursor']['completed'],[])
        c.validate(*args,q,Counter())

    def test_exhaustive_binary_and_generated_small_formula_truth(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(251846)
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        checked=0
        for n,source in cases:
            args=small(source)
            if args is None:continue
            a=c.discover(*args,Counter(),policy='all',probe_limit=1)
            b=c.discover(*args,Counter(),policy='all',cursor=json.loads(json.dumps(a['cursor'])),probe_limit=2)
            self.assertEqual(b,c.discover(*args,Counter(),policy='all',probe_limit=3));c.validate(*args,b,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if b['program']['status']=='refuted':self.assertFalse(models)
            for p in b['program']['probes']:
                self.assertTrue(all(m[abs(p['assumption'])]!=(p['assumption']>0) for m in models))
            checked+=1
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
