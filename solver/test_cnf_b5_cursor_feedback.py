from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_b5_cursor_feedback as c
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_b5_probe_cursor import tiny


def fixture():
    args=tiny(((1,2),(1,-2),(3,4),(3,-4),(5,6),(5,-6),(-1,-3,-5)))
    history=c.cursor.discover(*args,Counter())
    assert history['program']['status']=='unresolved' and len(history['program']['probes'])==3
    return (*args,history)


class B5CursorFeedbackTests(unittest.TestCase):
    def test_joint_failures_refute_without_new_assumptions(self):
        args=fixture()
        for mode,status in (('base','unresolved'),('feedback','refuted')):
            counts=Counter();p=c.discover(*args,counts,mode=mode);c.validate(*args,p,Counter())
            self.assertEqual(p['status'],status);self.assertEqual(counts['probe_roots'],0);self.assertEqual(counts['unit_probes'],1)
        self.assertFalse(any(c.native.holds(args[0],dict(enumerate(bits,1))) for bits in product((False,True),repeat=6)))

    def test_support_full_shortcut_off_and_both_cold_readers(self):
        args=fixture();p=c.discover(*args,Counter())
        for mode,selected in product(('off','all'),(False,True)):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';s=c.native.ResidualSolver(path)
                try:
                    counts=Counter();key=c.compile_program(s,*args,p,counts,select_support=selected,shortcut=mode)
                    self.assertFalse(s._read(key)['answer'])
                    self.assertLessEqual(sum(counts[k] for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                    before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                    self.assertEqual(key,c.compile_program(s,*args,p,Counter()))
                    self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
                finally:s.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(key)['answer'])
                    finally:reader.close()

    def test_prefix_extension_and_shortcut_budget_fallback(self):
        args=fixture();p=c.discover(*args,Counter());payloads=[]
        for options in (dict(shortcut='off'),dict(unit_work_limit=1)):
            s=c.native.ResidualSolver()
            try:
                prefix=dict(status='unresolved',steps=[],path_limit=256)
                key=c.compile_extension(s,args[0],args[1],prefix,*args[2:],p,Counter(),**options)
                self.assertFalse(s._read(key)['answer']);payloads.append(list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
            finally:s.close()
        self.assertEqual(*payloads)

    def test_invalid_history_proofs_closure_and_forward_reason_rejected_when_warm(self):
        args=fixture();p=c.discover(*args,Counter());s=c.native.ResidualSolver();prepared=c.prepare(*args,Counter())
        try:
            c.compile_program(s,*args,p,Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('old_binding','binding','proof','forward','closure','top','open'):
                a=deepcopy(args);q=deepcopy(p)
                if kind=='old_binding':a[8]['cursor']['binding']='different'
                elif kind=='binding':a[-1]['cursor']['binding']='different'
                elif kind=='proof':a[-1]['cursor']['probes'][0]['proof']['conflict']=999999
                elif kind=='forward':a[-1]['cursor']['probes'][0]['proof']['conflict']=len(prepared[11])
                elif kind=='closure':a[11]['assignment'].append([99,True])
                elif kind=='top':q['proof']['conflict']=999999
                else:q.update(status='unresolved',reason='open',proof=None)
                with self.assertRaises(ValueError):c.compile_program(s,*a,q,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_open_history_never_supplies_exclusions_or_a_sat_verdict(self):
        args=tiny(((1,2),));history=c.cursor.discover(*args,Counter());args=(*args,history)
        prepared=c.prepare(*args,Counter());self.assertEqual(prepared[11],prepared[13])
        p=c.discover(*args,Counter());c.validate(*args,p,Counter());self.assertEqual((p['status'],p['reason']),('unresolved','open'))
        bad=deepcopy(args);bad[-1].update(action='unchanged',program=None,cursor=None)
        with self.assertRaises(ValueError):c.prepare(*bad,Counter())

    def test_budget_and_trace_stops_are_not_refutations(self):
        args=fixture()
        for options in ({'work_limit':1},{'trace_limit':1}):
            counts=Counter();p=c.discover(*args,counts,**options);c.validate(*args,p,Counter())
            self.assertEqual(p['status'],'unresolved');self.assertLessEqual(counts['probe_occurrence_visits'],options.get('work_limit',262144))
        for options in ({'mode':'sat'},{'trace_limit':True},{'work_limit':0}):
            with self.assertRaises(ValueError):c.discover(*args,Counter(),**options)

    def test_support_reasons_stay_on_their_own_bank(self):
        args=fixture();p=c.discover(*args,Counter());prepared=c.prepare(*args,Counter())
        with self.assertRaises(ValueError):c.frozen.check_trace(prepared[0],prepared[11],None,p['proof'],Counter(),256)
        plan=c._plan(args[0],args[1],args[2],args[4],args[6],args[8]['program'],args[10]['program'],args[12]['program'],p,prepared,Counter())
        self.assertIsNotNone(plan);c.check_program(plan['prepared'],plan['program'],Counter())
        self.assertEqual(len(plan['sixth']['probes']),3)

    def test_generated_small_inputs_against_complete_truth_tables(self):
        rng=random.Random(251954);checked=0
        for _ in range(130):
            source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]
            args=tiny(source)
            if args is None:continue
            history=c.cursor.discover(*args,Counter(),probe_limit=1)
            if history['program']['status']=='refuted':continue
            args=(*args,history);p=c.discover(*args,Counter());c.validate(*args,p,Counter());checked+=1
            if p['status']=='refuted':
                self.assertFalse(any(c.native.holds(args[0],dict(enumerate(bits,1))) for bits in product((False,True),repeat=5)))
                s=c.native.ResidualSolver()
                try:self.assertFalse(s._read(c.compile_program(s,*args,p,Counter()))['answer'])
                finally:s.close()
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
