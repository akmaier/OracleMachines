from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_sliced_saturation as s
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_b13_native_feedback import delayed_history
from solver.test_cnf_shared_b10_preparation import close
c=s.sliced;k=s.parent.kernel


class SlicedSaturationTests(unittest.TestCase):
    def test_real_cases_both_cold_readers_and_exact_root(self):
        for name,case in s.build_cases().items():
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';solver=c.native.ResidualSolver(path);cc=Counter()
                try:
                    self.assertEqual(s.compile_case(solver,case,cc,'sliced'),case['root'])
                    self.assertGreater(cc['support_trace_steps'],cc['support_trace_kept'])
                finally:solver.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(case['root'])['answer'])
                    finally:reader.close()

    def test_backward_slice_removes_irrelevant_chain_and_keeps_assumption(self):
        bank=((-1,2),(-2,3),(-3,),(-1,4),(-4,5))
        proof=dict(units=[[4,3],[5,4],[2,0],[3,1]],conflict=2);cc=Counter()
        compact,dependent=c.slice_trace(bank,proof,1,cc)
        self.assertEqual(compact,dict(units=[[2,0],[3,1]],conflict=2));self.assertTrue(dependent)
        c.frozen.check_trace(bank,bank,1,compact,Counter(),256)
        self.assertEqual((cc['support_trace_steps'],cc['support_trace_kept']),(4,2))

    def test_independent_conflict_and_missing_dependency(self):
        bank=((1,),(-1,),(2,));proof=dict(units=[[2,2],[1,0]],conflict=1)
        compact,dependent=c.slice_trace(bank,proof,3,Counter());self.assertFalse(dependent)
        c.frozen.check_trace(bank,bank,None,compact,Counter(),256)
        with self.assertRaises(ValueError):c.slice_trace(((-2,3),(-3,)),dict(units=[[3,0]],conflict=1),1,Counter())

    def test_warm_rechecks_changed_histories_and_does_not_publish(self):
        case=s.build_cases()['cascade'];solver=c.native.ResidualSolver()
        try:
            s.compile_case(solver,case,Counter(),'sliced');before=s.old.tables(solver.db);cc=Counter()
            self.assertEqual(s.compile_case(solver,case,cc,'sliced'),case['root']);self.assertEqual(cc['saturation_native_extension_hits'],1);self.assertEqual(cc['slice_unique_traces'],0)
            for kind in ('source','prefix','bank','failure','terminal','closure'):
                bad=deepcopy(case)
                if kind=='source':bad['source'][0].append(9999)
                elif kind=='prefix':bad['prefix']['status']='refuted'
                elif kind=='bank':bad['inputs'][24]['cursor']['binding']='changed'
                elif kind=='failure':bad['saturation']['rounds'][0]['search']['cursor']['probes'][0]['proof']['conflict']=999999
                elif kind=='terminal':bad['saturation']['proof']['conflict']=999999
                else:bad['saturation']['rounds'][0]['closure']['assignment'].append([9999,True])
                with self.assertRaises(ValueError,msg=kind):s.compile_case(solver,bad,Counter(),'sliced')
            self.assertEqual(before,s.old.tables(solver.db))
        finally:solver.close()

    def test_same_clause_ids_in_different_banks_do_not_share_slices(self):
        proof=dict(units=[[2,0],[3,1]],conflict=2)
        a=((-1,2),(-2,3),(-3,));b=((-1,2),(-1,3),(-3,))
        first=c.slice_trace(a,proof,1,Counter())[0];second=c.slice_trace(b,proof,1,Counter())[0]
        self.assertNotEqual(first,second)
        for bank,compact in ((a,first),(b,second)):c.frozen.check_trace(bank,bank,1,compact,Counter(),256)

    def test_small_truth_checked_histories_with_both_shortcut_settings(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112620)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,25))]) for _ in range(70)]
        checked=refuted=0
        for n,source in cases:
            norm=c.native.normalize(source)[0];closure=close(norm)
            if closure is None:continue
            residual=c.native.normalize(c.native.restrict_scan(norm,dict(closure['assignment']),Counter()))[0];history=delayed_history(residual)
            if history is None:continue
            args,kw=history;result=c.feedback.probe.discover(*args,**kw,counts=Counter(),work_limit=1)
            p=c.feedback.prepare(*args,result,**kw,counts=Counter());sat=k.discover(p[29],Counter(),order_source=p[0]);checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if sat['status']!='refuted':continue
            self.assertFalse(models);refuted+=1
            for shortcut in ('all','off'):
                solver=c.native.ResidualSolver()
                try:
                    root=c.compile_program(solver,*args,result,**kw,saturation=sat,counts=Counter(),shortcut=shortcut)
                    self.assertFalse(solver._read(root)['answer'])
                finally:solver.close()
        self.assertGreater(checked,60);self.assertGreater(refuted,0)

    def test_growing_disjoint_mixtures_and_deterministic_fresh_reconstruction(self):
        for size in (0,4,12,24):
            source=[[-2,-1],[-2,1],[-1,2],[1,2]]+[[v,v+1] for v in range(3,3+size,2)]
            args,kw=delayed_history(source);result=c.feedback.probe.discover(*args,**kw,counts=Counter(),work_limit=1)
            p=c.feedback.prepare(*args,result,**kw,counts=Counter());sat=k.discover(p[29],Counter(),order_source=p[0]);self.assertEqual(sat['status'],'refuted')
            snapshots=[]
            for shortcut in ('off','off','all'):
                solver=c.native.ResidualSolver()
                try:
                    root=c.compile_program(solver,*args,result,**kw,saturation=sat,counts=Counter(),shortcut=shortcut)
                    self.assertFalse(solver._read(root)['answer']);snapshots.append(s.old.tables(solver.db))
                finally:solver.close()
            self.assertEqual(snapshots[0],snapshots[1])

    def test_open_inputs_and_invalid_bounds_publish_nothing(self):
        args,kw=delayed_history(((1,2),));result=c.feedback.probe.discover(*args,**kw,counts=Counter(),work_limit=1)
        p=c.feedback.prepare(*args,result,**kw,counts=Counter());sat=k.discover(p[29],Counter(),order_source=p[0]);solver=c.native.ResidualSolver()
        try:
            for controls in ({},{'shortcut':'unchecked'},{'unit_work_limit':0},{'unit_trace_limit':True}):
                with self.assertRaises(ValueError):c.compile_program(solver,*args,result,**kw,saturation=sat,counts=Counter(),**controls)
            self.assertFalse(any(s.old.tables(solver.db).values()))
        finally:solver.close()


if __name__=='__main__':unittest.main()
