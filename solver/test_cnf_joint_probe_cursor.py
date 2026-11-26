from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_joint_probe_cursor as c,cnf_joint_probe_feedback as feedback,compare_cnf_joint_cursor_feedback as old
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_b7_probe_cursor import tiny


def fixtures():return json.loads(Path('experiments/results/cnf-joint-cursor-feedback/remaining-closures.json').read_text())['rows']
def args(row):return tuple(row[k] for k in old.FIELDS)
def closure(row):return row['joint_cursor_feedback_closure']
def gain():return next(r for r in fixtures() if (r['target'],r['event'])==(28,19))


class JointProbeCursorTests(unittest.TestCase):
    def test_exact_reuse_matches_fresh_and_skips_thirteen_histories(self):
        imported=0
        for row in fixtures():
            cc=Counter();a=c.discover(*args(row),closure=closure(row),counts=cc)
            b=c.discover(*args(row),closure=closure(row),counts=Counter(),policy='matched')
            self.assertEqual(a,b);imported+=cc['joint_probe_imported_cursors']
            c.validate(*args(row),closure=closure(row),result=a,counts=Counter())
        self.assertEqual(imported,13)

    def test_changed_bank_closure_trace_bound_and_format_invalidate_history(self):
        row=gain();a=args(row);cc=Counter();result=c.discover(*a,closure=closure(row),counts=cc)
        self.assertEqual(cc['joint_probe_imported_completed'],0)
        for kind in ('old','binding','format','trace','closure'):
            bad=deepcopy(result);cl=deepcopy(closure(row))
            if kind=='old':bad['cursor']=deepcopy(a[16]['cursor'])
            elif kind=='binding':bad['cursor']['binding']+='changed'
            elif kind=='format':bad['cursor']['format']=c.c.FORMAT
            elif kind=='trace':bad['program']['trace_limit']=255
            else:cl['assignment'].append([9999,True])
            with self.assertRaises(ValueError):c.validate(*a,closure=cl,result=bad,counts=Counter())

    def test_continuation_and_interrupted_probe_are_exact(self):
        row=gain();a=args(row);cl=closure(row)
        first=c.discover(*a,closure=cl,counts=Counter(),probe_limit=1)
        continued=c.discover(*a,closure=cl,counts=Counter(),cursor=first['cursor'],probe_limit=63)
        self.assertEqual(continued,c.discover(*a,closure=cl,counts=Counter()))
        stopped=c.discover(*a,closure=cl,counts=Counter(),work_limit=1)
        self.assertEqual(stopped['program']['reason'],'work_limit');self.assertEqual(stopped['cursor']['completed'],[])
        self.assertEqual(c.discover(*a,closure=cl,counts=Counter(),cursor=stopped['cursor']),continued)

    def test_failure_proofs_and_completed_schedule_are_checked(self):
        row=gain();a=args(row);cl=closure(row);result=c.discover(*a,closure=cl,counts=Counter());saved=deepcopy(a)
        for kind in ('forward','assumption','schedule','lower'):
            bad=deepcopy(result);inputs=deepcopy(a)
            if kind=='forward':bad['cursor']['probes'][0]['proof']['conflict']=1000000
            elif kind=='assumption':bad['cursor']['probes'][0]['assumption']*=-1
            elif kind=='schedule':bad['cursor']['completed'].reverse()
            else:inputs[17]['cursor']['binding']='bad'
            with self.assertRaises(ValueError):c.validate(*inputs,closure=cl,result=bad,counts=Counter())
        self.assertEqual(a,saved)

    def test_feedback_refutes_new_case_and_checks_origin_bank(self):
        row=gain();a=args(row);cl=closure(row);r=c.discover(*a,closure=cl,counts=Counter())
        p=feedback.discover(*a,r,closure=cl,counts=Counter());self.assertEqual(p['status'],'refuted')
        prepared=feedback.validate(*a,r,closure=cl,program=p,counts=Counter())
        for clause,e in zip(prepared[19],prepared[20]):
            if e['kind']=='joint_probe':self.assertEqual(clause,(-r['program']['probes'][e['index']]['assumption'],))
        with self.assertRaises(ValueError):c.c.frozen.check_trace(prepared[0],prepared[17],None,p['proof'],Counter(),256)

    def test_native_off_and_direct_both_cold_readers(self):
        row=gain();a=args(row);cl=closure(row);r=c.discover(*a,closure=cl,counts=Counter());p=feedback.discover(*a,r,closure=cl,counts=Counter())
        for shortcut in ('off','all'):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=feedback.native.ResidualSolver(path);cc=Counter()
                try:
                    key=feedback.compile_program(s,*a,r,closure=cl,program=p,counts=cc,shortcut=shortcut)
                    self.assertFalse(s._read(key)['answer'])
                    if shortcut=='off':self.assertGreater(cc['joint_probe_feedback_expanded_joint_probe'],0)
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    s=cls(path)
                    try:self.assertFalse(s._read(key)['answer'])
                    finally:s.close()

    def test_warm_rejects_bad_proofs_before_lookup_and_retains_tables(self):
        row=gain();a=args(row);cl=closure(row);r=c.discover(*a,closure=cl,counts=Counter());p=feedback.discover(*a,r,closure=cl,counts=Counter());s=feedback.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            key=feedback.compile_extension(s,a[0],a[1],prefix,*a[2:],r,closure=cl,program=p,counts=Counter())
            before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            self.assertEqual(key,feedback.compile_program(s,*a,r,closure=cl,program=p,counts=Counter()))
            bad=deepcopy(r);bad['cursor']['probes'][0]['proof']['conflict']=1000000
            with self.assertRaises(ValueError):feedback.compile_program(s,*a,bad,closure=cl,program=p,counts=Counter())
            self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_budget_and_unresolved_are_never_sat_or_native_authority(self):
        row=gain();a=args(row);cl=closure(row);r=c.discover(*a,closure=cl,counts=Counter())
        for options in (dict(work_limit=1),dict(trace_limit=1)):
            p=feedback.discover(*a,r,closure=cl,counts=Counter(),**options);feedback.validate(*a,r,closure=cl,program=p,counts=Counter())
            self.assertEqual(p['status'],'unresolved');s=feedback.native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):feedback.compile_program(s,*a,r,closure=cl,program=p,counts=Counter())
                self.assertEqual(list(s.db.execute('SELECT id FROM cnf_residual_v1')),[])
            finally:s.close()
        for options in (dict(probe_limit=True),dict(trace_limit=0),dict(policy='unchecked')):
            with self.assertRaises(ValueError):c.discover(*a,closure=cl,counts=Counter(),**options)

    def test_small_truth_tables_check_every_new_exclusion(self):
        signed=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260505);checked=0
        cases=[(2,[signed[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        for n,source in cases:
            full=tiny(source)
            if full is None:continue
            hist=c.c.discover(*full,Counter(),probe_limit=1);cmp=c.c.feedback.cursor.discover(*full[:14],Counter(),probe_limit=1)
            if any(x['program']['status']=='refuted' for x in (hist,cmp)):continue
            a=(*full,hist,cmp);prepared=c.joint.prepare(*a,counts=Counter());fixed,trace,conflict=c.c.native.propagate(prepared[17],Counter())
            if conflict is not None:continue
            cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));r=c.discover(*a,closure=cl,counts=Counter());c.validate(*a,closure=cl,result=r,counts=Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.c.native.holds(a[0],dict(enumerate(bits,1)))]
            for probe in r['program']['probes']:
                lit=probe['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if r['program']['status']=='refuted':self.assertFalse(models)
            else:
                p=feedback.discover(*a,r,closure=cl,counts=Counter());feedback.validate(*a,r,closure=cl,program=p,counts=Counter())
                if p['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
