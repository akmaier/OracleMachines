from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_prepared_b6_search as module,cnf_b6_probe_native as compiler
from experiments.compare_cnf_b6_probe_cursor import FIELDS
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_b6_probe_cursor import tiny
c=module.candidate


def sample():
    rows=json.loads(Path('experiments/results/cnf-b6-probe-cursor/remaining.json').read_text())['rows']
    r=next(r for r in rows if (r['target'],r['event'])==(37,40))
    return tuple(r[k] for k in FIELDS),r['b6_probe_cursor']['cursor']


class PreparedB6SearchTests(unittest.TestCase):
    def test_chunk_boundaries_match_reference_and_single_pass(self):
        args,cursor=sample();counts=Counter();session=module.PreparedB6Search(*args,counts=counts,cursor=cursor)
        for _ in range(8):
            actual=session.advance(counts,probe_limit=8);expected=c.discover(*args,Counter(),cursor=cursor,probe_limit=8)
            self.assertEqual(actual,expected);cursor=expected['cursor'];c.validate(*args,actual,Counter())
        self.assertEqual(actual,c.discover(*args,Counter(),cursor=sample()[1]))
        self.assertEqual(counts['probe_index_builds'],1);self.assertEqual(counts['prepared_sessions'],1)

    def test_caller_and_returned_payloads_cannot_mutate_owned_search(self):
        args,cursor=sample();saved=deepcopy((args,cursor));session=module.PreparedB6Search(*args,counts=Counter(),cursor=cursor)
        first=session.advance(Counter(),probe_limit=8);clean=deepcopy(first)
        args[0][0].append(9999);args[-1]['assignment'].append([9999,True]);cursor['completed'].clear()
        first['cursor']['completed'].clear();first['cursor']['probes'].clear();first['program']['trace_limit']=1
        actual=session.advance(Counter(),probe_limit=8)
        self.assertEqual(actual,c.discover(*saved[0],Counter(),cursor=clean['cursor'],probe_limit=8))

    def test_interruption_and_promoted_candidates_retry_exactly(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)))
        for limit in range(1,13):
            counts=Counter();session=module.PreparedB6Search(*args,counts=counts,policy='restart')
            first=session.advance(counts,probe_limit=1,work_limit=limit)
            ref=c.discover(*args,Counter(),policy='restart',probe_limit=1,work_limit=limit)
            self.assertEqual(first,ref);self.assertLessEqual(counts['probe_occurrence_visits'],limit)
            second=session.advance(Counter(),probe_limit=1)
            self.assertEqual(second,c.discover(*args,Counter(),cursor=ref['cursor'],probe_limit=1))
            self.assertEqual(session.advance(Counter()),c.discover(*args,Counter(),cursor=second['cursor']))

    def test_cold_recovery_rechecks_every_binding_and_failure(self):
        args,cursor=sample();session=module.PreparedB6Search(*args,counts=Counter(),cursor=cursor)
        first=session.advance(Counter(),probe_limit=8)
        restored=module.PreparedB6Search(*args,counts=Counter(),cursor=json.loads(json.dumps(first['cursor'])))
        self.assertEqual(restored.advance(Counter()),session.advance(Counter()))
        for kind in ('binding','duplicate','failure','closure','old'):
            a=deepcopy(args);history=deepcopy(first['cursor'])
            if kind=='binding':history['binding']='changed'
            elif kind=='duplicate':history['completed']*=2
            elif kind=='failure':history['probes'][0]['proof']['conflict']=999999
            elif kind=='closure':a[-1]['assignment'].append([999,True])
            else:a[12]['cursor']['binding']='changed'
            with self.assertRaises(ValueError):module.PreparedB6Search(*a,counts=Counter(),cursor=history)

    def test_sessions_are_independent_and_options_cannot_silently_change(self):
        args,cursor=sample();a=module.PreparedB6Search(*args,counts=Counter(),cursor=cursor);b=module.PreparedB6Search(*args,counts=Counter(),cursor=cursor)
        a.advance(Counter(),probe_limit=8)
        self.assertEqual(b.advance(Counter(),probe_limit=8),c.discover(*args,Counter(),cursor=cursor,probe_limit=8))
        for options in ({'probe_limit':True},{'work_limit':0}):
            with self.assertRaises(ValueError):a.advance(Counter(),**options)
        with self.assertRaises(TypeError):a.advance(Counter(),trace_limit=257)
        with self.assertRaises(ValueError):module.PreparedB6Search(*args,counts=Counter(),cursor=cursor,trace_limit=257)
        with self.assertRaises(ValueError):module.PreparedB6Search(*args,counts=Counter(),policy='unsafe')

    def test_terminal_proof_and_open_exhaustion_preserve_verdicts(self):
        for source in (((-2,-1),(-2,1),(-1,2),(1,2)),((1,2),)):
            args=tiny(source);session=module.PreparedB6Search(*args,counts=Counter());result=session.advance(Counter())
            self.assertEqual(result,session.advance(Counter()));c.validate(*args,result,Counter())
            self.assertNotEqual(result['program']['status'],'sat')
            if result['program']['status']=='refuted':
                with tempfile.TemporaryDirectory() as td:
                    path=Path(td)/'db';solver=c.native.ResidualSolver(path)
                    try:key=compiler.compile_program(solver,*args,result,Counter())
                    finally:solver.close()
                    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                        reader=cls(path)
                        try:self.assertFalse(reader._read(key)['answer'])
                        finally:reader.close()

    def test_representative_changed_and_unchanged_inputs_match(self):
        rows=json.loads(Path('experiments/results/cnf-b5-cursor-feedback/remaining-closures.json').read_text())['rows']
        for changed in (False,True):
            row=next(r for r in rows if bool(r['b5_cursor_feedback_additional_variables'])==changed)
            args=tuple(row[k] for k in FIELDS);counts=Counter();session=module.PreparedB6Search(*args,counts=counts)
            self.assertEqual(session.advance(counts),c.discover(*args,Counter()))
            self.assertEqual(counts['b6_imported_cursors'],int(not changed))

    def test_exhaustive_and_generated_small_truth_tables(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260038)
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        checked=0
        for n,source in cases:
            args=tiny(source)
            if args is None:continue
            session=module.PreparedB6Search(*args,counts=Counter());cursor=None
            for _ in range(4):
                result=session.advance(Counter(),probe_limit=3);reference=c.discover(*args,Counter(),cursor=cursor,probe_limit=3)
                self.assertEqual(result,reference);cursor=reference['cursor']
                if result['program']['reason']!='probe_limit':break
            c.validate(*args,result,Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if result['program']['status']=='refuted':self.assertFalse(models)
            for proof in result['program']['probes']:self.assertTrue(all(m[abs(proof['assumption'])]!=(proof['assumption']>0) for m in models))
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
