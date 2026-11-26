from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_checked_b6_restore as m,cnf_b6_probe_native as compiler
from experiments.compare_cnf_b6_probe_cursor import FIELDS
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_b6_probe_cursor import tiny
c=m.candidate


def sample():
    rows=json.loads(Path('experiments/results/cnf-prepared-b6-search/remaining.json').read_text())['rows']
    row=next(r for r in rows if (r['target'],r['event'])==(37,40))
    return tuple(row[k] for k in FIELDS),row['b6_prepared_cursor']


class CheckedB6RestoreTests(unittest.TestCase):
    def test_restore_matches_full_check_then_construction(self):
        args,result=sample();saved=deepcopy((args,result));c.validate(*args,result,Counter())
        reference=m.PreparedB6Search(*args,counts=Counter(),cursor=result['cursor'])
        actual=m.restore(*args,result=result,counts=Counter())
        for _ in range(4):self.assertEqual(actual.advance(Counter(),probe_limit=8),reference.advance(Counter(),probe_limit=8))
        self.assertEqual((args,result),saved)

    def test_complete_result_shape_and_verdict_are_checked(self):
        args,result=sample()
        for kind in ('extra','action','cursor','program','bool_limit','sat','reason','terminal','probes'):
            bad=deepcopy(result)
            if kind=='extra':bad['checked']=True
            elif kind=='action':bad['action']='trusted'
            elif kind=='cursor':bad['cursor']=None
            elif kind=='program':bad['program']=[]
            elif kind=='bool_limit':bad['program']['trace_limit']=True
            elif kind=='sat':bad['program']['status']='sat'
            elif kind=='reason':bad['program']['reason']='unchecked'
            elif kind=='terminal':bad['program']['terminal']=dict(low=0,high=0)
            else:bad['program']['probes']=[]
            with self.assertRaises(ValueError):c.validate(*args,bad,Counter())
            with self.assertRaises(ValueError):m.restore(*args,result=bad,counts=Counter())

    def test_source_closure_bindings_and_forward_reasons_are_checked(self):
        args,result=sample()
        for kind in ('source','closure','old','binding','duplicate','proof','forward'):
            a=deepcopy(args);bad=deepcopy(result)
            if kind=='source':a[0][0].append(9999)
            elif kind=='closure':a[-1]['assignment'].append([9999,True])
            elif kind=='old':a[12]['cursor']['binding']='changed'
            elif kind=='binding':bad['cursor']['binding']='changed'
            elif kind=='duplicate':bad['cursor']['completed']*=2
            elif kind=='proof':bad['cursor']['probes'][0]['proof']['conflict']=999999
            else:bad['cursor']['probes'][0]['proof']['conflict']=len(c.validate(*args,result,Counter())[13])
            with self.assertRaises(ValueError):c.validate(*a,bad,Counter())
            with self.assertRaises(ValueError):m.restore(*a,result=bad,counts=Counter())

    def test_input_and_result_mutations_do_not_alias_the_session(self):
        args,result=sample();saved=deepcopy((args,result));session=m.restore(*args,result=result,counts=Counter())
        args[0][0].append(9999);args[-1]['units'].clear();result['cursor']['completed'].clear();result['program']['probes'].clear()
        first=session.advance(Counter(),probe_limit=8);expected=c.discover(*saved[0],Counter(),cursor=saved[1]['cursor'],probe_limit=8)
        self.assertEqual(first,expected);first['cursor']['probes'].clear()
        self.assertEqual(session.advance(Counter(),probe_limit=8),c.discover(*saved[0],Counter(),cursor=expected['cursor'],probe_limit=8))

    def test_nondefault_trace_limit_and_serialized_recovery(self):
        args=tiny(((1,2,3),(-1,-2,3)));result=c.discover(*args,Counter(),trace_limit=257,probe_limit=1)
        restored=m.restore(*args,result=json.loads(json.dumps(result)),counts=Counter())
        actual=restored.advance(Counter(),probe_limit=1)
        self.assertEqual(actual,c.discover(*args,Counter(),cursor=result['cursor'],trace_limit=257,probe_limit=1))
        bad=deepcopy(result);bad['program']['trace_limit']=256
        with self.assertRaises(ValueError):m.restore(*args,result=bad,counts=Counter())

    def test_interrupted_and_exhausted_states_preserve_the_schedule(self):
        for source in (((-2,-1),(-2,1),(-1,2),(1,2)),((1,2),)):
            args=tiny(source)
            for limit in (1,2,3,262144):
                result=c.discover(*args,Counter(),probe_limit=1,work_limit=limit)
                session=m.restore(*args,result=result,counts=Counter());actual=session.advance(Counter())
                self.assertEqual(actual,c.discover(*args,Counter(),cursor=result['cursor']))
                self.assertNotEqual(actual['program']['status'],'sat')

    def test_terminal_refutation_uses_existing_native_cold_readers(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)));result=c.discover(*args,Counter());session=m.restore(*args,result=result,counts=Counter())
        self.assertEqual(result,session.advance(Counter()))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';solver=c.native.ResidualSolver(path)
            try:key=compiler.compile_program(solver,*args,result,Counter())
            finally:solver.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:self.assertFalse(reader._read(key)['answer'])
                finally:reader.close()

    def test_exhaustive_and_generated_small_truth(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260101)
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        checked=0
        for n,source in cases:
            args=tiny(source)
            if args is None:continue
            initial=c.discover(*args,Counter(),probe_limit=1);actual=m.restore(*args,result=initial,counts=Counter()).advance(Counter())
            self.assertEqual(actual,c.discover(*args,Counter(),cursor=initial['cursor']));c.validate(*args,actual,Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if actual['program']['status']=='refuted':self.assertFalse(models)
            for row in actual['program']['probes']:self.assertTrue(all(m[abs(row['assumption'])]!=(row['assumption']>0) for m in models))
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
