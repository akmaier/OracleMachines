from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_b5_probe_cursor as c,cnf_b5_probe_native as compiler
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.compare_cnf_b4_probe_cursor import FIELDS as OLD_FIELDS
from solver.test_cnf_b4_probe_cursor import small
from solver.test_cnf_changed_closure_probes import closed
FIELDS=(*OLD_FIELDS,'b4_probe_cursor','b4_cursor_feedback_closure')


def record(changed):
    rows=json.loads(Path('experiments/results/cnf-b4-cursor-feedback/remaining-closures.json').read_text())['rows']
    return next(tuple(r[k] for k in FIELDS) for r in rows if bool(r['b4_cursor_feedback_additional_variables'])==changed)


def tiny(source):
    args=small(source)
    if args is None:return None
    history=c.feedback.cursor.discover(*args,Counter(),policy='all',work_limit=1)
    if history['program']['status']=='refuted':return None
    args=(*args,history);closure=closed(c.feedback.prepare(*args,Counter())[11])
    return (*args,closure) if closure is not None else None


class B5ProbeCursorTests(unittest.TestCase):
    def test_exact_bank_import_matches_fresh_extended_frontier(self):
        args=record(False);saved=deepcopy(args);counts=Counter()
        reused=c.discover(*args,counts);fresh=c.discover(*args,Counter(),policy='restart',probe_limit=128,work_limit=524288)
        self.assertEqual(reused,fresh);self.assertEqual(args,saved)
        self.assertEqual(counts['b5_imported_completed'],64);self.assertEqual(counts['b5_imported_cursors'],1)
        c.validate(*args,reused,Counter())

    def test_changed_bank_starts_fresh_and_rejects_old_cursor(self):
        args=record(True);counts=Counter();a=c.discover(*args,counts)
        self.assertEqual(a,c.discover(*args,Counter(),policy='restart'));self.assertEqual(counts['b5_imported_completed'],0)
        self.assertEqual(counts['b5_fresh_cursors'],1)
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=args[10]['cursor'])

    def test_trace_bound_change_disables_import(self):
        args=record(False);counts=Counter();p=c.discover(*args,counts,trace_limit=257)
        self.assertEqual(counts['b5_imported_cursors'],0)
        self.assertEqual(p,c.discover(*args,Counter(),policy='restart',trace_limit=257))
        with self.assertRaises(ValueError):c.discover(*args,Counter(),cursor=p['cursor'])

    def test_cold_split_continuation_and_parent_immutability(self):
        args=record(False);p=c.discover(*args,Counter(),probe_limit=32);saved=deepcopy(p);counts=Counter()
        q=c.discover(*args,counts,cursor=json.loads(json.dumps(p['cursor'])),probe_limit=32)
        self.assertEqual(q,c.discover(*args,Counter()));self.assertEqual(p,saved)
        self.assertEqual(counts['b5_continued_cursors'],1);self.assertEqual(counts['b5_imported_cursors'],0)

    def test_interruption_retries_unfinished_assumption(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)));counts=Counter()
        p=c.discover(*args,counts,work_limit=1);self.assertEqual(p['program']['reason'],'work_limit')
        self.assertEqual(p['cursor']['completed'],[]);self.assertLessEqual(counts['probe_occurrence_visits'],1)
        q=c.discover(*args,Counter(),cursor=p['cursor']);self.assertEqual(q,c.discover(*args,Counter()))

    def test_malformed_history_or_proof_rejected_before_warm_lookup(self):
        args=record(True);p=c.discover(*args,Counter());self.assertEqual(p['program']['status'],'refuted');s=c.native.ResidualSolver()
        try:
            compiler.compile_program(s,*args,p,Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('old','b4','binding','proof','closure','duplicate'):
                a=deepcopy(args);q=deepcopy(p)
                if kind=='old':a[8]['cursor']['binding']='bad'
                elif kind=='b4':a[10]['cursor']['binding']='bad'
                elif kind=='binding':q['cursor']['binding']='bad'
                elif kind=='proof':q['cursor']['probes'][0]['proof']['conflict']=999999
                elif kind=='closure':a[11]['assignment'].append([999,True])
                else:q['cursor']['completed']*=2
                with self.assertRaises(ValueError):compiler.compile_program(s,*a,q,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_native_full_selected_and_independent_cold_readers(self):
        args=record(True);p=c.discover(*args,Counter())
        for selected in (False,True):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    counts=Counter();key=compiler.compile_program(s,*args,p,counts,select_support=selected)
                    self.assertFalse(s._read(key)['answer']);self.assertGreater(counts['cursor_pair_splits'],0)
                    self.assertLessEqual(sum(counts[k] for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(key)['answer'])
                    finally:reader.close()

    def test_open_history_cannot_establish_sat_or_native_refutation(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)));p=c.discover(*args,Counter(),work_limit=1)
        forged=deepcopy(p['cursor']);forged.update(completed=c.frozen.roots(args[0]),probes=[])
        q=c.discover(*args,Counter(),cursor=forged);c.validate(*args,q,Counter())
        self.assertEqual((q['program']['status'],q['program']['reason']),('unresolved','complete'))
        s=c.native.ResidualSolver()
        try:
            with self.assertRaises(ValueError):compiler.compile_program(s,*args,q,Counter())
        finally:s.close()

    def test_prefix_extension_and_invalid_limits(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)));p=c.discover(*args,Counter());s=c.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            key=compiler.compile_extension(s,args[0],args[1],prefix,*args[2:],p,Counter());self.assertFalse(s._read(key)['answer'])
        finally:s.close()
        for kw in ({'policy':'unsafe'},{'probe_limit':True},{'work_limit':0},{'trace_limit':0}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**kw)

    def test_exhaustive_binary_and_generated_small_truth(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(252049)
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        checked=0
        for n,source in cases:
            args=tiny(source)
            if args is None:continue
            p=c.discover(*args,Counter());c.validate(*args,p,Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if p['program']['status']=='refuted':self.assertFalse(models)
            for proof in p['program']['probes']:
                self.assertTrue(all(m[abs(proof['assumption'])]!=(proof['assumption']>0) for m in models))
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
