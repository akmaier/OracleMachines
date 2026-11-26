from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,unittest
from experiments import cnf_b7_probe_cursor as c
from experiments.compare_cnf_b7_probe_cursor import FIELDS,compose
from solver.test_cnf_b6_probe_cursor import tiny as previous_tiny


def record(changed):
    rows=json.loads(Path('experiments/results/cnf-checked-b6-restore/remaining.json').read_text())['rows']
    r=next(r for r in rows if (r['target'],r['event'])==((37,40) if changed else (1,0)))
    args=tuple(r[k] for k in FIELDS)
    return (*args,compose(args,Counter()))


def tiny(source):
    args=previous_tiny(source)
    if args is None:return None
    result=c.feedback.cursor.discover(*args,Counter(),work_limit=1)
    if result['program']['status']=='refuted':return None
    args=(*args,result)
    p=c.feedback.prepare(*args,Counter());fixed,trace,conflict=c.native.propagate(p[15],Counter())
    if conflict is not None:return None
    return (*args,dict(units=trace,assignment=sorted([list(x) for x in fixed.items()])))


class B7ProbeCursorTests(unittest.TestCase):
    def test_exact_import_matches_extended_fresh_without_duplicate_preparation(self):
        args=record(False);saved=deepcopy(args);cc=Counter();mc=Counter()
        reused=c.discover(*args,cc);matched=c.discover(*args,mc,policy='matched')
        self.assertEqual(reused,matched);self.assertEqual(saved,args)
        self.assertEqual(cc['b7_imported_completed'],254);self.assertEqual(cc['probe_roots'],0)
        self.assertEqual(mc['probe_roots'],254);self.assertEqual(mc['b7_imported_completed'],0)
        self.assertEqual(cc['cursor_binding_bytes'],mc['cursor_binding_bytes']);c.validate(*args,reused,Counter())

    def test_changed_bank_resets_and_stale_binding_is_rejected(self):
        args=record(True);cc=Counter();reused=c.discover(*args,cc)
        self.assertEqual(cc['b7_imported_completed'],0);self.assertEqual(cc['probe_roots'],64)
        self.assertEqual(reused,c.discover(*args,Counter(),policy='restart'))
        self.assertEqual(reused,c.discover(*args,Counter(),policy='matched'))
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=args[-2]['cursor'])

    def test_closure_trace_and_trace_bound_bind_the_history(self):
        args=record(False);cc=Counter();p=c.discover(*args,cc,trace_limit=257)
        self.assertEqual(cc['b7_imported_completed'],0)
        self.assertEqual(p,c.discover(*args,Counter(),trace_limit=257,policy='restart'))
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=p['cursor'])
        a=deepcopy(args);a[-1]['assignment'].append([999,True])
        with self.assertRaises(ValueError):c.discover(*a,Counter())

    def test_cold_continuation_and_input_mutation_isolation(self):
        args=record(True);saved=deepcopy(args);p=c.discover(*args,Counter(),probe_limit=8)
        q=c.discover(*args,Counter(),cursor=json.loads(json.dumps(p['cursor'])),probe_limit=8)
        self.assertEqual(q,c.discover(*args,Counter(),probe_limit=16));self.assertEqual(args,saved)
        c.validate(*args,q,Counter());q['cursor']['probes'].clear();self.assertEqual(args,saved)

    def test_invalid_prior_and_current_proofs_and_schedule_rejected(self):
        args=record(True);p=c.discover(*args,Counter());prepared=c.validate(*args,p,Counter())
        for kind in ('old_binding','prior_binding','old_proof','prior_forward','closure','binding','proof','forward','duplicate','program'):
            a=deepcopy(args);q=deepcopy(p)
            if kind=='old_binding':a[12]['cursor']['binding']='changed'
            elif kind=='prior_binding':a[14]['cursor']['binding']='changed'
            elif kind=='old_proof':a[14]['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='prior_forward':a[14]['cursor']['probes'][0]['proof']['conflict']=len(prepared[13])
            elif kind=='closure':a[15]['assignment'].append([999,True])
            elif kind=='binding':q['cursor']['binding']='changed'
            elif kind=='proof':q['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='forward':q['cursor']['probes'][0]['proof']['conflict']=len(prepared[15])
            elif kind=='duplicate':q['cursor']['completed']*=2
            else:q['program']['probes']=[]
            with self.assertRaises(ValueError):c.validate(*a,q,Counter())

    def test_interrupted_probes_retry_and_terminal_is_checked(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)));cc=Counter()
        p=c.discover(*args,cc,work_limit=1);self.assertEqual(p['program']['reason'],'work_limit')
        self.assertEqual(p['cursor']['completed'],[]);self.assertLessEqual(cc['probe_occurrence_visits'],1)
        q=c.discover(*args,Counter(),cursor=p['cursor']);self.assertEqual(q,c.discover(*args,Counter()))
        self.assertEqual(q['program']['status'],'refuted');c.validate(*args,q,Counter())
        self.assertEqual(q,c.discover(*args,Counter(),cursor=q['cursor']))
        bad=deepcopy(q);bad['program']['terminal']['low']=bad['program']['terminal']['high']
        with self.assertRaises(ValueError):c.validate(*args,bad,Counter())

    def test_open_history_never_proves_sat(self):
        args=tiny(((1,2),));p=c.discover(*args,Counter())
        self.assertEqual((p['program']['status'],p['program']['reason']),('unresolved','complete'))
        bad=deepcopy(p);bad['program']['status']='sat'
        with self.assertRaises(ValueError):c.validate(*args,bad,Counter())
        for options in (dict(policy='trusted'),dict(probe_limit=0),dict(trace_limit=True),dict(work_limit=0)):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**options)

    def test_composition_checks_joint_implication_and_budget_stops(self):
        args=previous_tiny(((1,2),(1,-2),(3,4),(3,-4),(5,6),(5,-6),(-1,-3,-5)))
        history=c.feedback.cursor.discover(*args,Counter());self.assertEqual(history['program']['status'],'unresolved')
        args=(*args,history)
        p=c.feedback.discover(*args,Counter());c.feedback.validate(*args,p,Counter())
        self.assertEqual(p['status'],'refuted');self.assertEqual(c.feedback.discover(*args,Counter(),mode='base')['status'],'unresolved')
        for opts in (dict(work_limit=1),dict(trace_limit=1)):
            q=c.feedback.discover(*args,Counter(),**opts);c.feedback.validate(*args,q,Counter());self.assertEqual(q['status'],'unresolved')
        prepared=c.feedback.prepare(*args,Counter())
        with self.assertRaises(ValueError):c.frozen.check_trace(prepared[0],prepared[13],None,p['proof'],Counter(),256)

    def test_exhaustive_and_random_formulas_against_truth_tables(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260157);checked=0
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        for n,source in cases:
            args=tiny(source)
            if args is None:continue
            p=c.discover(*args,Counter());c.validate(*args,p,Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if p['program']['status']=='refuted':self.assertFalse(models)
            for row in p['program']['probes']:self.assertTrue(all(m[abs(row['assumption'])]!=(row['assumption']>0) for m in models))
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
