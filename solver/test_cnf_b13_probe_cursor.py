from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json, random, tempfile, unittest
from experiments import cnf_b13_probe_cursor as c, compare_cnf_b13_probe_cursor as study
from experiments.validate_cnf_b12_progress_order import independent as lower_independent
from solver.test_cnf_shared_b12_preparation import upper_history, close


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.prior.load_frontier(cp['shared_b12_preparation']['remaining'])


def independent(args,kw,result):
    previous={k:v for k,v in kw.items() if k!='combined_closure'}
    prepared=lower_independent(args[:24],previous,args[24],'source')[0]
    assert prepared==lower_independent(args[:24],previous,args[25],'unseen')[0]
    c.shared.b11.validate(*args[:22],**{k:v for k,v in previous.items() if k!='latest_closure'},result=args[26],counts=Counter())
    bank=dict(zip(prepared[25],prepared[26]))
    for kind,book in (('b12_source_probe',args[24]),('b12_unseen_probe',args[25]),('b11_continuation_probe',args[26])):
        for i,probe in enumerate(book['program']['probes']):bank.setdefault((-probe['assumption'],),dict(kind=kind,index=i))
    clauses=tuple(sorted(bank));prepared=(*prepared,clauses,[bank[cl] for cl in clauses])
    fixed=c.engine.prior.check_closure(clauses,kw['combined_closure'],Counter())
    residual,_=c.engine.prior.residual_bank(clauses,fixed,Counter());active={abs(lit) for clause in residual for lit in clause}
    order=tuple(lit for lit in c.engine.frozen.roots(prepared[0]) if abs(lit) in active)
    limit=result['program']['trace_limit']
    binding=json.dumps([c.POLICY,prepared[0],clauses,kw['combined_closure'],order,limit],sort_keys=True,separators=(',',':'))
    cursor=deepcopy(result['cursor']);assert cursor['format']==c.FORMAT;cursor['format']=c.engine.FORMAT
    state=c.engine.load((*prepared[:15],clauses,prepared[28]),order,binding,cursor,Counter(),limit)
    c.engine.prior.check_program(prepared[0],clauses,result['program'],Counter())
    assert result['program']==c.engine._program(state[4],state[6],limit,result['program']['reason'])
    return prepared


def history(source, bounds=(31,17,23)):
    previous=upper_history(source)
    if previous is None:return None
    args,kw=previous;lower={k:v for k,v in kw.items() if k!='latest_closure'}
    source_result=c.shared.discover(*args,**kw,ordering='source',trace_limit=bounds[0],probe_limit=1,counts=Counter())
    unseen=c.shared.discover(*args,**kw,ordering='unseen',trace_limit=bounds[1],probe_limit=2,counts=Counter())
    continuation=c.shared.b11.discover(*args[:22],**lower,trace_limit=bounds[2],probe_limit=2,counts=Counter())
    if any(r['program']['status']=='refuted' for r in (source_result,unseen,continuation)):return None
    prepared=c.shared.validate(*args,**kw,ordering='source',result=source_result,counts=Counter())
    cl=close(tuple(sorted(set(prepared[25])|{(-r['assumption'],) for book in (source_result,unseen,continuation) for r in book['program']['probes']})))
    return None if cl is None else ((*args,source_result,unseen,continuation),dict(**kw,combined_closure=cl))


class B13ProbeCursorTests(unittest.TestCase):
    def test_all_banks_match_independent_composition_and_matched_fresh(self):
        imported=0
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row);cc=Counter()
            r=c.discover(*args,**kw,counts=cc);imported+=cc['b13_imported_cursors']
            self.assertEqual(r,c.discover(*args,**kw,policy='matched',counts=Counter()))
            self.assertEqual(c.validate(*args,**kw,result=r,counts=Counter()),independent(args,kw,r))
            self.assertEqual(cc['b13_prefix_preparations'],1)
            self.assertEqual(cc['context_preparations'],1)
            self.assertEqual(cc['b13_histories_checked'],3)
        self.assertEqual(imported,13)

    def test_changed_bank_and_trace_bound_block_import(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row);cc=Counter()
        r=c.discover(*args,**kw,counts=cc);self.assertEqual(cc['b13_imported_cursors'],0)
        self.assertEqual(r,c.discover(*args,**kw,policy='restart',counts=Counter()))
        with self.assertRaises(ValueError):c.discover(*args,**kw,cursor=args[24]['cursor'],counts=Counter())
        row=fixtures()[0];cc=Counter();c.discover(*study.arguments(row),**study.options(row),trace_limit=257,counts=cc)
        self.assertEqual(cc['b13_imported_cursors'],0)

    def test_cold_interrupted_and_owned_continuation(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row)
        r=c.discover(*args,**kw,counts=Counter());first=c.discover(*args,**kw,probe_limit=1,counts=Counter())
        self.assertEqual(r,c.discover(*args,**kw,probe_limit=63,cursor=json.loads(json.dumps(first['cursor'])),counts=Counter()))
        stopped=c.discover(*args,**kw,work_limit=1,counts=Counter());self.assertEqual(stopped['program']['reason'],'work_limit')
        self.assertEqual(r,c.discover(*args,**kw,cursor=stopped['cursor'],counts=Counter()))
        a,k,saved=deepcopy((args,kw,r))
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='b13_owned_copies':
                    a[25]['cursor']['binding']='mutated';k['combined_closure']['assignment'].append([9999,True]);saved['cursor']['binding']='mutated'
        expected=c.discover(*args,**kw,cursor=r['cursor'],probe_limit=1,counts=Counter())
        self.assertEqual(expected,c.discover(*a,**k,cursor=saved['cursor'],probe_limit=1,counts=MutatingCounter()))
        a,k,saved=deepcopy((args,kw,r));self.assertEqual(independent(args,kw,r),c.validate(*a,**k,result=saved,counts=MutatingCounter()))
        with self.assertRaises(ValueError):c.discover(*a,**k,counts=Counter())

    def test_all_histories_and_closures_are_independently_checked(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row)
        for slot in (12,14,16,17,18,19,20,21,22,23,24,25,26):
            bad=deepcopy(args);bad[slot]['cursor']['binding']='changed'
            with self.assertRaises(ValueError,msg=str(slot)):c.discover(*bad,**kw,counts=Counter())
        for slot in (24,25,26):
            bad=deepcopy(args);bad[slot]['cursor']['probes'][0]['proof']['conflict']=999999
            with self.assertRaises(ValueError,msg=str(slot)):c.discover(*bad,**kw,counts=Counter())
        for key in kw:
            bad=deepcopy(kw);bad[key]['assignment'].append([9999,True])
            with self.assertRaises(ValueError,msg=key):c.discover(*args,**bad,counts=Counter())
        bad=deepcopy(args);bad[0][0].append(9999)
        with self.assertRaises(ValueError):c.discover(*bad,**kw,counts=Counter())

    def test_policy_bound_histories_and_result_edits_rejected(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row);r=c.discover(*args,**kw,counts=Counter())
        bad=list(deepcopy(args));bad[24],bad[25]=bad[25],bad[24]
        with self.assertRaises(ValueError):c.discover(*bad,**kw,counts=Counter())
        for kind in ('format','binding','schedule','program'):
            bad=deepcopy(r)
            if kind=='format':bad['cursor']['format']=c.shared.prior.FORMAT
            elif kind=='binding':bad['cursor']['binding']='changed'
            elif kind=='schedule':bad['cursor']['completed'].reverse()
            else:bad['program']['status']='refuted'
            with self.assertRaises(ValueError,msg=kind):c.validate(*args,**kw,result=bad,counts=Counter())

    def test_different_history_bounds_and_invalid_options(self):
        args,kw=history(((1,2),))
        r=c.discover(*args,**kw,counts=Counter());self.assertEqual(c.validate(*args,**kw,result=r,counts=Counter()),independent(args,kw,r))
        for slot in (24,25,26):
            bad=deepcopy(args);bad[slot]['program']['trace_limit']=99
            with self.assertRaises(ValueError):c.discover(*bad,**kw,counts=Counter())
        for opts in (dict(policy='trusted'),dict(work_limit=0),dict(trace_limit=True),dict(probe_limit=False)):
            with self.assertRaises(ValueError):c.discover(*args,**kw,counts=Counter(),**opts)
        row=fixtures()[0];r=c.discover(*study.arguments(row),**study.options(row),counts=Counter())
        self.assertEqual((r['program']['status'],r['program']['reason']),('unresolved','complete'))

    def test_alternative_complete_closure_trace_is_retained(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row)
        r=c.discover(*args,**kw,counts=Counter());prepared=independent(args,kw,r)
        for i in range(len(kw['combined_closure']['units'])-1):
            alt=deepcopy(kw);units=alt['combined_closure']['units'];units[i:i+2]=reversed(units[i:i+2])
            try:c.engine.prior.check_closure(prepared[27],alt['combined_closure'],Counter())
            except ValueError:continue
            result=c.discover(*args,**alt,counts=Counter())
            self.assertNotEqual(result['cursor']['binding'],r['cursor']['binding'])
            self.assertEqual(c.validate(*args,**alt,result=result,counts=Counter()),independent(args,alt,result));return
        self.fail('Need an alternative valid trace')

    def test_overlay_rejects_parent_overwrite_missing_and_duplicates(self):
        rows=fixtures();cp=study.base.load(study.PARENT/'checkpoint.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);parent=path/'parent.json';study.compact(parent,study.old.bound(cp['shared_b12_preparation']['remaining']))
            payload=dict(parent=study.old.binding(parent),rows=[dict(target=r['target'],event=r['event'],b13_note='test') for r in rows]);overlay=path/'overlay.json';study.compact(overlay,payload)
            self.assertEqual(len(study.load_frontier(study.old.binding(overlay))),14)
            for kind in ('duplicate','missing','overwrite','parent'):
                bad=deepcopy(payload)
                if kind=='duplicate':bad['rows'].append(bad['rows'][0])
                elif kind=='missing':bad['rows'].pop()
                elif kind=='overwrite':bad['rows'][0]['root']='bad'
                else:parent.write_text('{}')
                study.compact(overlay,bad)
                with self.assertRaises((AssertionError,ValueError)):study.load_frontier(study.old.binding(overlay))

    def test_small_and_generated_formulas_against_models(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112613)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            normalized=c.engine.native.normalize(source)[0];cl=close(normalized)
            if cl is None:continue
            residual=c.engine.native.normalize(c.engine.native.restrict_scan(normalized,dict(cl['assignment']),Counter()))[0];h=history(residual)
            if h is None:continue
            args,kw=h;r=c.discover(*args,**kw,counts=Counter());checked+=1
            self.assertEqual(c.validate(*args,**kw,result=r,counts=Counter()),independent(args,kw,r))
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for p in r['program']['probes']:
                lit=p['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if r['program']['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
