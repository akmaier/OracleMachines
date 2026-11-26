from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_joint_cursor_feedback as c,compare_cnf_b7_probe_cursor as prior
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_b7_probe_cursor import tiny
FIELDS=(*prior.FIELDS,'b6_cursor_feedback_closure','b7_probe_cursor','b6_comparison_cursor')


def fixture():
    rows=json.loads(Path('experiments/results/cnf-b7-probe-cursor/remaining.json').read_text())['rows']
    row=next(r for r in rows if (r['target'],r['event'])==(37,40))
    return tuple(row[k] for k in FIELDS)


class JointCursorFeedbackTests(unittest.TestCase):
    def test_joint_and_single_bank_ablations_are_checked_without_new_probes(self):
        args=fixture();saved=deepcopy(args)
        for mode,status in (('base','unresolved'),('b6_only','unresolved'),('b7_only','refuted'),('joint','refuted')):
            cc=Counter();p=c.discover(*args,counts=cc,mode=mode);c.validate(*args,program=p,counts=Counter())
            self.assertEqual(p['status'],status);self.assertEqual(cc['probe_roots'],0);self.assertEqual(cc['unit_probes'],1)
        self.assertEqual(args,saved)

    def test_joint_origins_keep_their_original_banks(self):
        args=fixture();p=c.prepare(*args,counts=Counter())
        kinds={e['kind'] for e in p[18]};self.assertIn('b6_comparison_probe',kinds);self.assertIn('b7_probe',kinds)
        for cl,e in zip(p[17],p[18]):
            if e['kind'] in ('b6_comparison_probe','b7_probe'):
                index=17 if e['kind']=='b6_comparison_probe' else 16
                self.assertEqual(cl,(-args[index]['program']['probes'][e['index']]['assumption'],))
        program=c.discover(*args,counts=Counter())
        with self.assertRaises(ValueError):c.frozen.check_trace(p[0],p[15],None,program['proof'],Counter(),256)

    def test_native_direct_and_disabled_through_both_readers(self):
        args=fixture()
        for mode,shortcut in product(('b7_only','joint'),('all','off')):
            program=c.discover(*args,counts=Counter(),mode=mode)
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    cc=Counter();key=c.compile_program(s,*args,program=program,counts=cc,shortcut=shortcut)
                    self.assertFalse(s._read(key)['answer'])
                    self.assertLessEqual(sum(cc[k] for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                    if mode=='joint' and shortcut=='off':
                        self.assertGreater(cc['joint_expanded_b6_comparison_probe'],0);self.assertGreater(cc['joint_expanded_b7_probe'],0)
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(key)['answer'])
                    finally:reader.close()

    def test_malformed_inputs_are_rejected_before_warm_lookup(self):
        args=fixture();program=c.discover(*args,counts=Counter());prepared=c.prepare(*args,counts=Counter());s=c.native.ResidualSolver()
        try:
            c.compile_program(s,*args,program=program,counts=Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('old','b7','comparison','b7_forward','comparison_forward','closure','source','program','mode'):
                a=deepcopy(args);p=deepcopy(program)
                if kind=='old':a[14]['cursor']['binding']='changed'
                elif kind=='b7':a[16]['cursor']['binding']='changed'
                elif kind=='comparison':a[17]['cursor']['binding']='changed'
                elif kind=='b7_forward':a[16]['cursor']['probes'][0]['proof']['conflict']=len(prepared[15])
                elif kind=='comparison_forward':a[17]['cursor']['probes'][0]['proof']['conflict']=len(prepared[13])
                elif kind=='closure':a[15]['assignment'].append([9999,True])
                elif kind=='source':a[0][0].append(9999)
                elif kind=='program':p['proof']['conflict']=len(prepared[17])
                else:p['mode']='trusted'
                with self.assertRaises(ValueError):c.compile_program(s,*a,program=p,counts=Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_cold_program_and_unchanged_warm_native_tables(self):
        args=fixture();p=c.discover(*args,counts=Counter());cold=json.loads(json.dumps(p));c.validate(*args,program=cold,counts=Counter());s=c.native.ResidualSolver()
        try:
            key=c.compile_program(s,*args,program=cold,counts=Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            self.assertEqual(key,c.compile_program(s,*args,program=p,counts=Counter()))
            self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_empty_prefix_and_direct_budget_fallback(self):
        args=fixture();p=c.discover(*args,counts=Counter());payloads=[]
        for options in (dict(shortcut='off'),dict(unit_work_limit=1)):
            s=c.native.ResidualSolver()
            try:
                key=c.compile_extension(s,args[0],args[1],dict(status='unresolved',steps=[],path_limit=256),*args[2:],program=p,counts=Counter(),**options)
                self.assertFalse(s._read(key)['answer']);payloads.append(list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
            finally:s.close()
        self.assertEqual(*payloads)

    def test_budget_stops_and_unresolved_programs_never_publish(self):
        args=fixture()
        for options in (dict(work_limit=1),dict(trace_limit=1),dict(mode='base')):
            cc=Counter();p=c.discover(*args,counts=cc,**options);c.validate(*args,program=p,counts=Counter());self.assertEqual(p['status'],'unresolved')
            self.assertLessEqual(cc['probe_occurrence_visits'],options.get('work_limit',262144));s=c.native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):c.compile_program(s,*args,program=p,counts=Counter())
                self.assertEqual(list(s.db.execute('SELECT id FROM cnf_residual_v1')),[])
            finally:s.close()
        for options in (dict(mode='trusted'),dict(trace_limit=True),dict(work_limit=0)):
            with self.assertRaises(ValueError):c.discover(*args,counts=Counter(),**options)

    def test_open_history_and_duplicate_consequences_supply_no_new_axioms(self):
        full=tiny(((1,2),));history=c.cursor.discover(*full,Counter());comparison=c.cursor.feedback.cursor.discover(*full[:14],Counter())
        args=(*full,history,comparison);p=c.prepare(*args,counts=Counter())
        self.assertEqual(p[15],p[17]);out=c.discover(*args,counts=Counter());self.assertEqual(out['status'],'unresolved')
        bad=deepcopy(out);bad['status']='sat'
        with self.assertRaises(ValueError):c.validate(*args,program=bad,counts=Counter())

    def test_exhaustive_and_generated_small_truth_tables(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260406);checked=0
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        for n,source in cases:
            full=tiny(source)
            if full is None:continue
            history=c.cursor.discover(*full,Counter(),probe_limit=1);comparison=c.cursor.feedback.cursor.discover(*full[:14],Counter(),probe_limit=1)
            if history['program']['status']=='refuted' or comparison['program']['status']=='refuted':continue
            args=(*full,history,comparison);p=c.discover(*args,counts=Counter());c.validate(*args,program=p,counts=Counter());checked+=1
            if p['status']=='refuted':
                self.assertFalse(any(c.native.holds(args[0],dict(enumerate(bits,1))) for bits in product((False,True),repeat=n)))
                s=c.native.ResidualSolver()
                try:self.assertFalse(s._read(c.compile_program(s,*args,program=p,counts=Counter()))['answer'])
                finally:s.close()
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
