from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_b10_probe_cursor as c,cnf_b10_probe_feedback as feedback,compare_cnf_b10_probe_cursor as study
from experiments import cnf_joint_probe_feedback as frozen_feedback
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_b7_probe_cursor import tiny


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.prior.load_frontier(cp['b9_probe_cursor']['remaining'])


def record(key): return next(r for r in fixtures() if (r['target'],r['event'])==key)


class B10ProbeCursorTests(unittest.TestCase):
    def test_exact_reuse_matches_fresh_and_original_bank_origins(self):
        imported=0;failures=0
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row);cc=Counter()
            result=c.discover(*args,**kw,counts=cc)
            self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='matched'))
            p=c.validate(*args,**kw,result=result,counts=Counter())
            frozen=frozen_feedback.prepare(*args[:19],closure=kw['closure'],counts=Counter())
            self.assertEqual(p[:21],frozen)
            c.engine.prior.check_program(p[0],p[17],args[20]['program'],Counter())
            c.engine.prior.check_program(p[0],p[19],args[19]['program'],Counter())
            for clause,entry in zip(p[21],p[22]):
                if entry['kind'] in ('b8_comparison_probe','b9_probe'):
                    book=args[20 if entry['kind']=='b8_comparison_probe' else 19]['program']
                    self.assertEqual(clause,(-book['probes'][entry['index']]['assumption'],))
            imported+=cc['b10_imported_cursors'];failures+=len(result['program']['probes'])
        self.assertEqual((imported,failures),(12,17))

    def test_changed_bank_trace_bound_and_old_format_invalidate_reuse(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row);cc=Counter()
        result=c.discover(*args,**kw,counts=cc)
        self.assertEqual(cc['b10_imported_cursors'],0)
        self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='restart'))
        with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),cursor=args[19]['cursor'])
        row=record((1,0));cc=Counter()
        c.discover(*study.arguments(row),**study.options(row),counts=cc,trace_limit=257)
        self.assertEqual(cc['b10_imported_cursors'],0)

    def test_owned_cold_continuation_and_interrupted_probe(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row);saved=deepcopy((args,kw))
        first=c.discover(*args,**kw,counts=Counter(),probe_limit=1)
        result=c.discover(*args,**kw,counts=Counter(),cursor=json.loads(json.dumps(first['cursor'])),probe_limit=63)
        self.assertEqual(result,c.discover(*args,**kw,counts=Counter()))
        stopped=c.discover(*args,**kw,counts=Counter(),work_limit=1)
        self.assertEqual(stopped['program']['reason'],'work_limit');self.assertEqual(stopped['cursor']['completed'],[])
        self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),cursor=stopped['cursor']))
        result['cursor']['completed'].clear();result['program']['probes'].clear();self.assertEqual((args,kw),saved)

    def test_prior_current_proof_schedule_source_and_closure_edits_rejected(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row);result=c.discover(*args,**kw,counts=Counter())
        for kind in ('b8_binding','b8_proof','b9_proof','closure','format','binding','proof','schedule','program','source'):
            a,k,r=deepcopy((args,kw,result))
            if kind=='b8_binding': a[20]['cursor']['binding']='bad'
            elif kind=='b8_proof': a[20]['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='b9_proof': a[19]['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='closure': k['joint_closure']['assignment'].append([9999,True])
            elif kind=='format': r['cursor']['format']=c.prior.FORMAT
            elif kind=='binding': r['cursor']['binding']+='bad'
            elif kind=='proof': r['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='schedule': r['cursor']['completed'].reverse()
            elif kind=='program': r['program']['probes']=[]
            else: a[0][0].append(9999)
            with self.assertRaises(ValueError,msg=kind): c.validate(*a,**k,result=r,counts=Counter())

    def test_two_gains_native_direct_and_disabled_both_cold_readers(self):
        for key,shortcut in (((28,18),'all'),((40,0),'all'),((40,0),'off')):
            row=record(key);args=study.arguments(row);kw=study.options(row)
            r=c.discover(*args,**kw,counts=Counter());p=feedback.discover(*args,r,**kw,counts=Counter())
            self.assertEqual(p['status'],'refuted');prepared=feedback.validate(*args,r,**kw,program=p,counts=Counter())
            with self.assertRaises(ValueError): c.engine.frozen.check_trace(prepared[0],prepared[21],None,p['proof'],Counter(),256)
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';solver=feedback.native.ResidualSolver(path);cc=Counter()
                try:
                    root=feedback.compile_program(solver,*args,r,**kw,program=p,counts=cc,shortcut=shortcut)
                    self.assertFalse(solver._read(root)['answer'])
                    if shortcut=='off': self.assertGreater(cc['b10_probe_feedback_expanded_b10_probe'],0)
                finally: solver.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try: self.assertFalse(reader._read(root)['answer'])
                    finally: reader.close()

    def test_warm_checks_before_lookup_and_extension_retains_tables(self):
        row=record((40,0));args=study.arguments(row);kw=study.options(row);r=c.discover(*args,**kw,counts=Counter());p=feedback.discover(*args,r,**kw,counts=Counter())
        solver=feedback.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            root=feedback.compile_extension(solver,args[0],args[1],prefix,*args[2:],r,**kw,program=p,counts=Counter())
            before=study.old.tables(solver.db)
            self.assertEqual(root,feedback.compile_program(solver,*args,r,**kw,program=p,counts=Counter()))
            bad=deepcopy(r);bad['cursor']['probes'][0]['proof']['conflict']=999999
            with self.assertRaises(ValueError): feedback.compile_program(solver,*args,bad,**kw,program=p,counts=Counter())
            with self.assertRaises(ValueError): feedback.compile_program(solver,*args,r,**kw,program=p,counts=Counter(),unit_work_limit=True)
            self.assertEqual(before,study.old.tables(solver.db))
        finally: solver.close()

    def test_unresolved_budgets_and_exhaustion_never_publish_sat(self):
        row=record((1,0));args=study.arguments(row);kw=study.options(row);r=c.discover(*args,**kw,counts=Counter())
        self.assertEqual((r['program']['status'],r['program']['reason']),('unresolved','complete'))
        row=record((28,18));args=study.arguments(row);kw=study.options(row);r=c.discover(*args,**kw,counts=Counter())
        for limits in (dict(work_limit=1),dict(trace_limit=1)):
            p=feedback.discover(*args,r,**kw,counts=Counter(),**limits);feedback.validate(*args,r,**kw,program=p,counts=Counter())
            self.assertEqual(p['status'],'unresolved');solver=feedback.native.ResidualSolver()
            try:
                with self.assertRaises(ValueError): feedback.compile_program(solver,*args,r,**kw,program=p,counts=Counter())
                self.assertEqual(list(solver.db.execute('SELECT id FROM cnf_residual_v1')),[])
            finally: solver.close()
        for limits in (dict(probe_limit=True),dict(work_limit=0),dict(trace_limit=False),dict(policy='unchecked')):
            with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),**limits)

    def test_truth_tables_for_exhaustive_small_and_generated_mixtures(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112608)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        def close(bank):
            fixed,trace,conflict=c.engine.native.propagate(bank,Counter())
            return None if conflict is not None else dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
        for n,source in cases:
            source=c.engine.native.normalize(source)[0];closed=close(source)
            if closed is None:
                self.assertFalse(any(c.engine.native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=n)));continue
            source=c.engine.native.normalize(c.engine.native.restrict_scan(source,dict(closed['assignment']),Counter()))[0]
            full=tiny(source)
            if full is None: continue
            hist=c.engine.discover(*full,Counter(),probe_limit=1);comp=c.engine.feedback.cursor.discover(*full[:14],Counter(),probe_limit=1)
            if any(r['program']['status']=='refuted' for r in (hist,comp)): continue
            joint=(*full,hist,comp);prepared=c.prior.prior.joint.prepare(*joint,counts=Counter());cl=close(prepared[17])
            if cl is None: continue
            b8=c.prior.prior.discover(*joint,closure=cl,counts=Counter(),probe_limit=1)
            if b8['program']['status']=='refuted': continue
            initial=(*joint,b8);prepared=frozen_feedback.prepare(*initial,closure=cl,counts=Counter());fc=close(prepared[19])
            if fc is None: continue
            b9=c.prior.discover(*initial,closure=cl,feedback_closure=fc,counts=Counter(),probe_limit=1)
            b8more=c.prior.prior.discover(*joint,closure=cl,cursor=b8['cursor'],counts=Counter(),probe_limit=1)
            if any(r['program']['status']=='refuted' for r in (b9,b8more)): continue
            bank=tuple(sorted(set(prepared[19])|{(-r['assumption'],) for p in (b9,b8more) for r in p['program']['probes']}));jc=close(bank)
            if jc is None: continue
            args=(*initial,b9,b8more);kw=dict(closure=cl,feedback_closure=fc,joint_closure=jc)
            result=c.discover(*args,**kw,counts=Counter());c.validate(*args,**kw,result=result,counts=Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for row in result['program']['probes']:
                lit=row['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            p=feedback.discover(*args,result,**kw,counts=Counter());feedback.validate(*args,result,**kw,program=p,counts=Counter())
            if result['program']['status']=='refuted' or p['status']=='refuted': self.assertFalse(models)
        self.assertGreater(checked,60)

    def test_overlay_rejects_missing_duplicate_overwrite_and_unknown_exclusions(self):
        cp=study.base.load(study.PARENT/'checkpoint.json');rows=fixtures()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay.json';payload=dict(parent=cp['b9_probe_cursor']['remaining'],excluded=[[28,18],[40,0]],
                rows=[dict(target=r['target'],event=r['event'],b10_note='test') for r in rows if (r['target'],r['event']) not in ((28,18),(40,0))])
            study.compact(path,payload);self.assertEqual(len(study.load_frontier(study.old.binding(path))),14)
            for kind in ('duplicate','missing','overwrite','exclude'):
                bad=deepcopy(payload)
                if kind=='duplicate': bad['rows'].append(bad['rows'][0])
                elif kind=='missing': bad['rows'].pop()
                elif kind=='overwrite': bad['rows'][0]['root']='bad'
                else: bad['excluded'].append([9999,9999])
                study.compact(path,bad)
                with self.assertRaises(ValueError): study.load_frontier(study.old.binding(path))


if __name__=='__main__': unittest.main()
