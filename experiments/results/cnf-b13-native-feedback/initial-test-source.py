from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random, tempfile, unittest
from experiments import compare_cnf_b13_native_feedback as s
from experiments import cnf_shared_b10_preparation as lower
from experiments import cnf_b10_probe_feedback as lower_feedback
from experiments import cnf_joint_probe_feedback as joint_feedback
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_b7_probe_cursor import tiny
from solver.test_cnf_shared_b10_preparation import close
from solver.test_cnf_b13_probe_cursor import independent
c=s.feedback; probe=c.probe


def delayed_history(source):
    """Retain checked interrupted histories so small UNSAT reaches the new layer."""
    f=lower.prior;full=tiny(source)
    if full is None:return None
    def run(module,*args,**kw):return module.discover(*args,counts=Counter(),work_limit=1,**kw)
    upper=f.engine.discover(*full,Counter(),work_limit=1)
    comparison=f.engine.feedback.cursor.discover(*full[:14],Counter(),work_limit=1)
    if any(r['program']['status']=='refuted' for r in (upper,comparison)):return None
    joint=(*full,upper,comparison);cl=close(f.prior.prior.joint.prepare(*joint,counts=Counter())[17])
    if cl is None:return None
    original=run(f.prior.prior,*joint,closure=cl);cmp=run(f.prior.prior,*joint,closure=cl)
    initial=(*joint,original);fc=close(joint_feedback.prepare(*initial,closure=cl,counts=Counter())[19])
    if fc is None:return None
    upper=run(f.prior,*initial,closure=cl,feedback_closure=fc)
    args=(*initial,upper,cmp);kw=dict(closure=cl,feedback_closure=fc,joint_closure=fc)
    b10=run(probe.shared.shared,*args,**kw);cmp10=run(probe.shared.shared,*args,**kw)
    if any(r['program']['status']=='refuted' for r in (original,cmp,upper,b10,cmp10)):return None
    args=(*args,b10);nc=close(lower_feedback.prepare(*args,**kw,counts=Counter())[23])
    if nc is None:return None
    kw=dict(kw,next_closure=nc);b11=run(probe.shared.b11,*args,**kw)
    args=(*args,b11,cmp10);kw=dict(kw,latest_closure=nc)
    b12=run(probe.shared,*args,**kw,ordering='source');unseen=run(probe.shared,*args,**kw,ordering='unseen')
    continuation=run(probe.shared.b11,*args[:22],**{k:v for k,v in kw.items() if k!='latest_closure'})
    if any(r['program']['status']=='refuted' for r in (b11,b12,unseen,continuation)):return None
    return (*args,b12,unseen,continuation),dict(kw,combined_closure=nc)


class B13NativeFeedbackTests(unittest.TestCase):
    def test_native_candidate_both_modes_and_independent_cold_readers(self):
        case=s.build_case()
        for mode in ('direct','disabled'):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';solver=c.native.ResidualSolver(path);cc=Counter()
                try:
                    root=s.compile_case(solver,case,cc,mode)
                    self.assertEqual(root,case['root']);self.assertFalse(solver._read(root)['answer'])
                    self.assertGreater(cc['b13_probe_feedback_expanded_b13_probe'],0)
                    self.assertGreater(cc['b13_probe_feedback_expanded_b12_source_probe'],0)
                    self.assertGreater(cc['b13_probe_feedback_expanded_b11_continuation_probe'],0)
                finally:solver.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(root)['answer'])
                    finally:reader.close()

    def test_original_banks_and_final_unit_origins(self):
        case=s.build_case();args=case['inputs'];result=case['search'];kw=case['options']
        lower_prepared=independent(args,kw,result)
        prepared=c.validate(*args,result,**kw,program=case['program'],counts=Counter())
        self.assertEqual(prepared[:29],lower_prepared)
        bank=dict(zip(lower_prepared[27],lower_prepared[28]))
        for i,r in enumerate(result['program']['probes']):bank.setdefault((-r['assumption'],),dict(kind='b13_probe',index=i))
        self.assertEqual(prepared[29],tuple(sorted(bank)));self.assertEqual(prepared[30],[bank[k] for k in sorted(bank)])
        self.assertEqual(c.discover(*args,result,**kw,counts=Counter()),case['program'])

    def test_warm_hits_recheck_histories_program_and_prefix_before_writing(self):
        case=s.build_case();solver=c.native.ResidualSolver()
        try:
            s.compile_case(solver,case,Counter(),'direct');before=s.old.tables(solver.db);cc=Counter()
            self.assertEqual(s.compile_case(solver,case,cc,'direct'),case['root'])
            self.assertEqual(cc['b13_probe_feedback_extension_hits'],1)
            for slot in (21,22,23,24,25,26):
                bad=deepcopy(case);bad['inputs'][slot]['cursor']['binding']='changed'
                with self.assertRaises(ValueError):s.compile_case(solver,bad,Counter(),'direct')
            for kind in ('search','proof','source','prefix','closure'):
                bad=deepcopy(case)
                if kind=='search':bad['search']['cursor']['probes'][0]['proof']['conflict']=999999
                elif kind=='proof':bad['program']['proof']['conflict']=999999
                elif kind=='source':bad['source'][0].append(9999)
                elif kind=='prefix':bad['prefix']['steps'].pop()
                else:bad['options']['combined_closure']['assignment'].append([9999,True])
                with self.assertRaises(ValueError,msg=kind):s.compile_case(solver,bad,Counter(),'direct')
            self.assertEqual(before,s.old.tables(solver.db))
        finally:solver.close()

    def test_unresolved_and_invalid_controls_never_publish(self):
        row=next(r for r in s.seeds() if (r['target'],r['event'])==(37,39))
        args=(*s.prior.arguments(row,'strengthen'),s.old.bound(row['b13_strength_result']));kw=s.prior.options(row,'strengthen')
        program=c.discover(*args,**kw,counts=Counter());self.assertEqual(program['status'],'unresolved')
        solver=c.native.ResidualSolver()
        try:
            for controls in ({},{'shortcut':'unchecked'},{'unit_trace_limit':True},{'unit_work_limit':0}):
                with self.assertRaises(ValueError):c.compile_program(solver,*args,**kw,program=program,counts=Counter(),**controls)
            self.assertFalse(any(s.old.tables(solver.db).values()))
        finally:solver.close()
        case=s.build_case();args=(*case['inputs'],case['search']);kw=case['options']
        for bound in (dict(work_limit=1),dict(trace_limit=1)):
            program=c.discover(*args,**kw,counts=Counter(),**bound)
            self.assertEqual(program['status'],'unresolved');c.validate(*args,**kw,program=program,counts=Counter())

    def test_exhaustive_small_and_generated_cold_native_truth(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112618)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0;refuted=0
        for n,source in cases:
            norm=c.native.normalize(source)[0];cl=close(norm)
            if cl is None:continue
            residual=c.native.normalize(c.native.restrict_scan(norm,dict(cl['assignment']),Counter()))[0]
            history=delayed_history(residual)
            if history is None:continue
            args,kw=history;result=probe.discover(*args,**kw,counts=Counter())
            program=c.discover(*args,result,**kw,counts=Counter());c.validate(*args,result,**kw,program=program,counts=Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if program['status']=='refuted':
                self.assertFalse(models);refuted+=1
                with tempfile.TemporaryDirectory() as td:
                    path=Path(td)/'db';solver=c.native.ResidualSolver(path)
                    try:root=c.compile_program(solver,*args,result,**kw,program=program,counts=Counter(),shortcut='off')
                    finally:solver.close()
                    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                        reader=cls(path)
                        try:self.assertFalse(reader._read(root)['answer'])
                        finally:reader.close()
        self.assertGreater(checked,60);self.assertGreater(refuted,0)

    def test_overlay_preserves_every_other_frontier_field(self):
        parent=s.base.load(s.PARENT/'checkpoint.json')['b13_strengthened_histories']['remaining'];rows=s.seeds()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay.json';payload=dict(parent=parent,excluded=[[67,63]])
            s.compact(path,payload);actual=s.load_frontier(s.old.binding(path))
            self.assertEqual(actual,[r for r in rows if (r['target'],r['event'])!=(67,63)])
            for exclusions in ([],[[67,63],[37,39]],[[67,64]]):
                s.compact(path,dict(payload,excluded=exclusions))
                with self.assertRaises(ValueError):s.load_frontier(s.old.binding(path))


if __name__=='__main__':unittest.main()
