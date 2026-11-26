from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_b9_probe_cursor as c, compare_cnf_b9_probe_cursor as study
from experiments import cnf_joint_probe_feedback as feedback
from solver.test_cnf_b7_probe_cursor import tiny


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.old.bound(cp['prepared_prefix_replay']['remaining'])['rows']


class B9ProbeCursorTests(unittest.TestCase):
    def test_all_current_banks_match_frozen_preparation_and_fresh_search(self):
        imported=0;failures=0
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row);cc=Counter()
            result=c.discover(*args,**kw,counts=cc)
            self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='matched'))
            p=c.validate(*args,**kw,result=result,counts=Counter())
            self.assertEqual(p,feedback.prepare(*args,closure=kw['closure'],counts=Counter()))
            imported+=cc['b9_imported_cursors'];failures+=len(result['program']['probes'])
        self.assertEqual((imported,failures),(15,8))

    def test_changed_bank_and_trace_bound_forbid_history_import(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(28,18))
        args=study.arguments(row);kw=study.options(row);cc=Counter()
        result=c.discover(*args,**kw,counts=cc)
        self.assertEqual(cc['b9_imported_cursors'],0)
        self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='restart'))
        with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),cursor=args[-1]['cursor'])
        row=fixtures()[0];cc=Counter()
        c.discover(*study.arguments(row),**study.options(row),counts=cc,trace_limit=257)
        self.assertEqual(cc['b9_imported_cursors'],0)

    def test_continuation_cold_reload_and_interruption_are_exact(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(28,18))
        args=study.arguments(row);kw=study.options(row);saved=deepcopy((args,kw))
        first=c.discover(*args,**kw,counts=Counter(),probe_limit=1)
        continued=c.discover(*args,**kw,counts=Counter(),cursor=json.loads(json.dumps(first['cursor'])),probe_limit=63)
        self.assertEqual(continued,c.discover(*args,**kw,counts=Counter()))
        stopped=c.discover(*args,**kw,counts=Counter(),work_limit=1)
        self.assertEqual(stopped['program']['reason'],'work_limit');self.assertEqual(stopped['cursor']['completed'],[])
        self.assertEqual(continued,c.discover(*args,**kw,counts=Counter(),cursor=stopped['cursor']))
        continued['cursor']['completed'].clear();continued['program']['probes'].clear()
        self.assertEqual((args,kw),saved)

    def test_rejects_prior_and_current_proof_schedule_binding_and_closure_edits(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(28,18))
        args=study.arguments(row);kw=study.options(row);result=c.discover(*args,**kw,counts=Counter())
        for kind in ('prior_binding','prior_proof','closure','format','binding','proof','schedule','program','source'):
            a,k,r=deepcopy((args,kw,result))
            if kind=='prior_binding': a[-1]['cursor']['binding']='changed'
            elif kind=='prior_proof': a[-1]['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='closure': k['feedback_closure']['assignment'].append([9999,True])
            elif kind=='format': r['cursor']['format']=c.prior.FORMAT
            elif kind=='binding': r['cursor']['binding']+='changed'
            elif kind=='proof': r['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='schedule': r['cursor']['completed'].reverse()
            elif kind=='program': r['program']['probes']=[]
            else: a[0][0].append(9999)
            with self.assertRaises(ValueError,msg=kind): c.validate(*a,**k,result=r,counts=Counter())

    def test_invalid_options_and_exhaustion_never_claim_sat(self):
        row=fixtures()[0];args=study.arguments(row);kw=study.options(row)
        result=c.discover(*args,**kw,counts=Counter())
        self.assertEqual((result['program']['status'],result['program']['reason']),('unresolved','complete'))
        for opt in (dict(probe_limit=True),dict(work_limit=0),dict(trace_limit=False),dict(policy='unchecked')):
            with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),**opt)

    def test_small_truth_tables_conditioned_failures(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(261126)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            full=tiny(source)
            if full is None: continue
            hist=c.engine.discover(*full,Counter(),probe_limit=1)
            comp=c.engine.feedback.cursor.discover(*full[:14],Counter(),probe_limit=1)
            if any(r['program']['status']=='refuted' for r in (hist,comp)): continue
            joint=(*full,hist,comp);p=c.prior.joint.prepare(*joint,counts=Counter())
            fixed,trace,conflict=c.engine.native.propagate(p[17],Counter())
            if conflict is not None: continue
            cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
            b8=c.prior.discover(*joint,closure=cl,counts=Counter(),probe_limit=1)
            if b8['program']['status']=='refuted': continue
            args=(*joint,b8);p=feedback.prepare(*args,closure=cl,counts=Counter())
            fixed,trace,conflict=c.engine.native.propagate(p[19],Counter())
            if conflict is not None: continue
            kw=dict(closure=cl,feedback_closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()])))
            result=c.discover(*args,**kw,counts=Counter());c.validate(*args,**kw,result=result,counts=Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for row in result['program']['probes']:
                lit=row['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if result['program']['status']=='refuted': self.assertFalse(models)
        self.assertGreater(checked,60)

    def test_overlay_rejects_missing_duplicate_and_parent_edits(self):
        rows=fixtures()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);parent=path/'parent.json';study.compact(parent,dict(rows=rows))
            payload=dict(parent=study.old.binding(parent),rows=[dict(target=r['target'],event=r['event'],b9_note='test') for r in rows])
            overlay=path/'overlay.json';study.compact(overlay,payload)
            self.assertEqual(len(study.load_frontier(study.old.binding(overlay))),16)
            for kind in ('duplicate','missing','overwrite','parent'):
                bad=deepcopy(payload)
                if kind=='duplicate': bad['rows'].append(bad['rows'][0])
                elif kind=='missing': bad['rows'].pop()
                elif kind=='overwrite': bad['rows'][0]['root']='bad'
                else: parent.write_text('{}')
                study.compact(overlay,bad)
                with self.assertRaises((AssertionError,ValueError)): study.load_frontier(study.old.binding(overlay))


if __name__=='__main__': unittest.main()
