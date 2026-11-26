from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_b12_progress_order as c, compare_cnf_b12_progress_order as study
from experiments import cnf_b10_probe_feedback as feedback
from solver.test_cnf_shared_b10_preparation import history, close


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.prior.load_frontier(cp['b11_probe_cursor']['remaining'])


class B12ProgressOrderTests(unittest.TestCase):
    def test_all_current_banks_match_frozen_preparation_and_fresh_search(self):
        imported=0;failures=0
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row);cc=Counter()
            result=c.discover(*args,**kw,counts=cc)
            self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='matched'))
            p=c.validate(*args,**kw,result=result,counts=Counter())
            lower=feedback.prepare(*args[:22],**study.prior.prior.prior.options(row),counts=Counter())
            bank=dict(zip(lower[23],lower[24]))
            for kind,book in (('b10_comparison_probe',args[23]['program']),('b11_probe',args[22]['program'])):
                for i,probe in enumerate(book['probes']): bank.setdefault((-probe['assumption'],),dict(kind=kind,index=i))
            clauses=tuple(sorted(bank));self.assertEqual(p,(*lower,clauses,[bank[cl] for cl in clauses]))
            imported+=cc['b12_imported_cursors'];failures+=len(result['program']['probes'])
        self.assertEqual((imported,failures),(12,1))

    def test_changed_bank_and_trace_bound_forbid_history_import(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63))
        args=study.arguments(row);kw=study.options(row);cc=Counter()
        result=c.discover(*args,**kw,counts=cc)
        self.assertEqual(cc['b12_imported_cursors'],0)
        self.assertEqual(result,c.discover(*args,**kw,counts=Counter(),policy='restart'))
        with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),cursor=args[-1]['cursor'])
        row=fixtures()[0];cc=Counter()
        c.discover(*study.arguments(row),**study.options(row),counts=cc,trace_limit=257)
        self.assertEqual(cc['b12_imported_cursors'],0)

    def test_continuation_cold_reload_and_interruption_are_exact(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63))
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
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63))
        args=study.arguments(row);kw=study.options(row);result=c.discover(*args,**kw,counts=Counter())
        for kind in ('prior_binding','prior_proof','closure','format','binding','proof','schedule','program','source'):
            a,k,r=deepcopy((args,kw,result))
            if kind=='prior_binding': a[-1]['cursor']['binding']='changed'
            elif kind=='prior_proof': a[-1]['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='closure': k['latest_closure']['assignment'].append([9999,True])
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
            normalized=c.engine.native.normalize(source)[0]
            fixed,_,conflict=c.engine.native.propagate(normalized,Counter())
            if conflict is not None:
                self.assertFalse(any(c.engine.native.holds(normalized,dict(enumerate(bits,1))) for bits in product((False,True),repeat=n)))
                continue
            residual=c.engine.native.normalize(c.engine.native.restrict_scan(normalized,fixed,Counter()))[0]
            h=history(residual)
            if h is None: continue
            original,previous_kw=h
            b10=c.prior.shared.discover(*original,**previous_kw,counts=Counter(),probe_limit=1)
            if b10['program']['status']=='refuted': continue
            full=(*original,b10);prepared=feedback.prepare(*full,**previous_kw,counts=Counter())
            cl=close(prepared[23])
            if cl is None: continue
            b11_kw=dict(**previous_kw,next_closure=cl)
            b11=c.prior.discover(*full,**b11_kw,counts=Counter(),probe_limit=1)
            cmp=c.prior.shared.discover(*original,**previous_kw,cursor=b10['cursor'],counts=Counter(),probe_limit=1)
            if any(r['program']['status']=='refuted' for r in (b11,cmp)): continue
            combined=close(tuple(sorted(set(prepared[23])|{(-p['assumption'],) for r in (b11,cmp) for p in r['program']['probes']})))
            if combined is None: continue
            args=(*full,b11,cmp);kw=dict(**b11_kw,latest_closure=combined)
            result=c.discover(*args,**kw,counts=Counter());c.validate(*args,**kw,result=result,counts=Counter());checked+=1
            alternative=c.discover(*args,**kw,ordering='source',counts=Counter());c.validate(*args,**kw,ordering='source',result=alternative,counts=Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for row in result['program']['probes']+alternative['program']['probes']:
                lit=row['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if any(r['program']['status']=='refuted' for r in (result,alternative)): self.assertFalse(models)
        self.assertGreater(checked,60)

    def test_overlay_rejects_missing_duplicate_and_parent_edits(self):
        rows=fixtures()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);parent=path/'parent.json'
            cp=study.base.load(study.PARENT/'checkpoint.json');study.compact(parent,study.old.bound(cp['b11_probe_cursor']['remaining']))
            payload=dict(parent=study.old.binding(parent),rows=[dict(target=r['target'],event=r['event'],b12_note='test') for r in rows])
            overlay=path/'overlay.json';study.compact(overlay,payload)
            self.assertEqual(len(study.load_frontier(study.old.binding(overlay))),14)
            for kind in ('duplicate','missing','overwrite','parent'):
                bad=deepcopy(payload)
                if kind=='duplicate': bad['rows'].append(bad['rows'][0])
                elif kind=='missing': bad['rows'].pop()
                elif kind=='overwrite': bad['rows'][0]['root']='bad'
                else: parent.write_text('{}')
                study.compact(overlay,bad)
                with self.assertRaises((AssertionError,ValueError)): study.load_frontier(study.old.binding(overlay))


    def test_owned_inputs_survive_mutation_after_the_copy(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63))
        args=study.arguments(row);kw=study.options(row);expected=c.discover(*args,**kw,counts=Counter())
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='shared_b10_owned_copies':
                    args[-1]['cursor']['binding']='caller mutated'
                    kw['latest_closure']['assignment'].append([9999,True])
        self.assertEqual(c.discover(*args,**kw,counts=MutatingCounter()),expected)
        with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter())

    def test_ordering_only_defers_old_literals_and_policy_is_bound(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row)
        prepared,view,bank,ids,order,binding,same,_,_=c.prepare(*args,**kw,counts=Counter())
        source_order=c.prepare(*args,**kw,ordering='source',counts=Counter())[4]
        seen=set(args[22]['cursor']['completed'])|set(args[23]['cursor']['completed'])
        self.assertFalse(same);self.assertEqual(set(order),set(source_order));self.assertEqual(len(order),len(source_order))
        self.assertEqual(order,tuple(x for x in source_order if x not in seen)+tuple(x for x in source_order if x in seen))
        cc=Counter();r=c.discover(*args,**kw,counts=cc)
        self.assertEqual(cc['b12_imported_cursors'],0)
        self.assertEqual(len(r['cursor']['completed']),cc['cursor_completed_probes'])
        self.assertEqual([x['assumption'] for x in r['program']['probes']],[83])
        other=c.discover(*args,**kw,ordering='source',counts=Counter())
        self.assertEqual([x['assumption'] for x in other['program']['probes']],[-68])
        for forged in (r,other):
            wrong='source' if forged is r else 'unseen'
            with self.assertRaises(ValueError): c.validate(*args,**kw,ordering=wrong,result=forged,counts=Counter())
        with self.assertRaises(ValueError): c.discover(*args,**kw,ordering='trust_old',counts=Counter())

if __name__=='__main__': unittest.main()
