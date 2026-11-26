from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_b13_strengthened_histories as s
from experiments.validate_cnf_b12_continuation_batch import compose
from solver.test_cnf_b13_probe_cursor import independent,history
from solver.test_cnf_shared_b12_preparation import close


def fixtures():
    cp=s.base.load(s.PARENT/'checkpoint.json')
    return s.prior.prior.load_frontier(cp['b12_cold_batch']['remaining'])


class B13StrengthenedHistoryTests(unittest.TestCase):
    def test_changed_contexts_and_independent_original_bank_checks(self):
        changed=[]
        for row in fixtures():
            before=independent(s.arguments(row,'continue'),s.options(row,'continue'),s.old.bound(row['b13_result']))
            if (row['target'],row['event']) in s.CASES:
                result=s.c.discover(*s.arguments(row,'strengthen'),**s.options(row,'strengthen'),counts=Counter(),probe_limit=1)
            else:result=s.old.bound(row['b13_result'])
            after=independent(s.arguments(row,'strengthen'),s.options(row,'strengthen'),result)
            self.assertEqual(after,s.check(s.arguments(row,'strengthen'),row,'strengthen',result,Counter()))
            self.assertEqual(after[:27],before[:27]);self.assertLessEqual(set(before[27]),set(after[27]))
            if before[27]!=after[27]:changed.append((row['target'],row['event']))
        self.assertEqual(changed,list(s.CASES))

    def test_frozen_complete_comparisons_and_new_failures(self):
        expected={(37,39):[-61,37],(67,63):[-130,-123,-112,-88,-9,45,50,79,100,107,110,133]}
        for row in fixtures():
            key=row['target'],row['event']
            if key not in s.CASES:continue
            results={}
            for mode in s.MODES:
                args=s.arguments(row,mode);kw=s.options(row,mode)
                result=s.search(args,row,mode,Counter(),dict(probe_limit=320,work_limit=1310720,trace_limit=256));results[mode]=result
                self.assertEqual(s.check(args,row,mode,result,Counter()),independent(args,kw,result))
                self.assertEqual((result['program']['status'],result['program']['reason']),('unresolved','complete'))
            self.assertEqual(results['continue'],results['fresh'])
            self.assertEqual(sorted(p['assumption'] for p in results['strengthen']['program']['probes']),expected[key])

    def test_old_cursor_invalid_on_changed_bank_and_export_corruption(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=s.arguments(row,'strengthen');kw=s.options(row,'strengthen')
        with self.assertRaises(ValueError):s.c.discover(*args,**kw,cursor=s.old.bound(row['b13_result'])['cursor'],counts=Counter())
        result=s.c.discover(*args,**kw,counts=Counter())
        for kind in ('binding','proof','schedule','program','bound'):
            bad=deepcopy(result)
            if kind=='binding':bad['cursor']['binding']='changed'
            elif kind=='proof':bad['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='schedule':bad['cursor']['completed'].reverse()
            elif kind=='program':bad['program']['probes']=[]
            else:bad['program']['trace_limit']=257
            with self.assertRaises(ValueError):s.c.validate(*args,**kw,result=bad,counts=Counter())
        for slot in (24,25):
            bad=deepcopy(args);bad[slot]['cursor']['probes'][0]['proof']['conflict']=999999
            with self.assertRaises(ValueError):s.c.discover(*bad,**kw,counts=Counter())
        bad=deepcopy(kw);bad['combined_closure']['assignment'].append([9999,True])
        with self.assertRaises(ValueError):s.c.discover(*args,**bad,counts=Counter())

    def test_complete_search_equals_bounded_cold_continuation(self):
        for row in fixtures():
            if (row['target'],row['event']) not in s.CASES:continue
            for mode in ('continue','strengthen'):
                args=s.arguments(row,mode);kw=s.options(row,mode)
                first=s.search(args,row,mode,Counter(),dict(probe_limit=64,work_limit=262144,trace_limit=256))
                continued=s.c.discover(*args,**kw,cursor=deepcopy(first['cursor']),counts=Counter(),probe_limit=256,work_limit=1048576)
                all_at_once=s.search(args,row,mode,Counter(),dict(probe_limit=320,work_limit=1310720,trace_limit=256))
                self.assertEqual(continued,all_at_once)

    def test_combined_feedback_preserves_closure_and_rejects_bad_trace(self):
        for row in fixtures():
            if (row['target'],row['event']) not in s.CASES:continue
            books={mode:s.search(s.arguments(row,mode),row,mode,Counter(),dict(probe_limit=320,work_limit=1310720,trace_limit=256)) for mode in ('continue','strengthen')}
            banks={mode:independent(s.arguments(row,mode),s.options(row,mode),books[mode]) for mode in books}
            joint,clauses=compose(banks['strengthen'][27],[p for b in books.values() for p in b['program']['probes']],Counter())
            self.assertLessEqual(dict(row['b12_batch_joint_closure']['assignment']).items(),dict(joint['assignment']).items())
            self.assertGreater(len(joint['assignment']),len(row['b12_batch_joint_closure']['assignment']))
            bad=deepcopy(joint);bad['assignment'].append([9999,True])
            with self.assertRaises(ValueError):s.c.engine.prior.check_closure(clauses,bad,Counter())

    def test_overlay_retains_all_rows_and_rejects_overwrites(self):
        rows=fixtures();cp=s.base.load(s.PARENT/'checkpoint.json')
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'overlay.json';payload=dict(parent=cp['b12_cold_batch']['remaining'],rows=[dict(target=r['target'],event=r['event'],b13_strength_note='test') for r in rows]);s.compact(dest,payload)
            self.assertEqual(len(s.load_frontier(s.old.binding(dest))),14)
            for kind in ('missing','duplicate','overwrite','parent'):
                bad=deepcopy(payload)
                if kind=='missing':bad['rows'].pop()
                elif kind=='duplicate':bad['rows'].append(bad['rows'][0])
                elif kind=='overwrite':bad['rows'][0]['root']='bad'
                else:bad['parent']['sha256']='bad'
                s.compact(dest,bad)
                with self.assertRaises((AssertionError,ValueError)):s.load_frontier(s.old.binding(dest))

    def test_generated_history_extensions_against_exhaustive_models(self):
        rng=random.Random(26112616);signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2))
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            norm=s.c.engine.native.normalize(source)[0];cl=close(norm)
            if cl is None:continue
            residual=s.c.engine.native.normalize(s.c.engine.native.restrict_scan(norm,dict(cl['assignment']),Counter()))[0];h=history(residual)
            if h is None:continue
            args,kw=h;previous={k:v for k,v in kw.items() if k!='combined_closure'}
            books=[s.c.shared.discover(*args[:24],**previous,cursor=args[i]['cursor'],ordering=ordering,trace_limit=args[i]['program']['trace_limit'],counts=Counter()) for i,ordering in ((24,'source'),(25,'unseen'))]
            if any(b['program']['status']=='refuted' for b in books):continue
            prepared=s.c.shared.validate(*args[:24],**previous,result=books[0],ordering='source',counts=Counter())
            clauses=tuple(sorted(set(prepared[25])|{(-p['assumption'],) for b in (*books,args[26]) for p in b['program']['probes']}));combined=close(clauses)
            if combined is None:continue
            new=(*args[:24],*books,args[26]);opts=dict(previous,combined_closure=combined)
            result=s.c.discover(*new,**opts,counts=Counter());checked+=1
            self.assertEqual(s.c.validate(*new,**opts,result=result,counts=Counter()),independent(new,opts,result))
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if s.c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for probe in result['program']['probes']:
                lit=probe['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if result['program']['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
