from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,tempfile,unittest
from experiments import cnf_b12_continuation_batch as c,compare_cnf_b12_continuation_batch as study
from experiments.validate_cnf_b12_progress_order import independent
from solver.test_cnf_shared_b12_preparation import upper_history,close


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.prior.load_frontier(cp['b13_probe_cursor']['remaining'])


def separate(args,kw,cursor,ordering,counts,rounds=3,**limits):
    results=[]
    for _ in range(rounds):
        before=len(cursor['completed']);r=c.prior.discover(*args,**kw,cursor=cursor,ordering=ordering,counts=counts,**limits);results.append(deepcopy(r))
        if r['program']['status']=='refuted' or r['program']['reason']=='complete' or len(r['cursor']['completed'])==before:break
        cursor=r['cursor']
    return results


class B12ContinuationBatchTests(unittest.TestCase):
    def test_all_snapshots_banks_and_search_counters_equal(self):
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row)
            for ordering in ('source','unseen'):
                cursor=study.saved_cursor(row,ordering);cc=Counter();bc=Counter()
                results=c.continue_rounds(*args,**kw,cursor=cursor,ordering=ordering,counts=cc)
                self.assertEqual(results,separate(args,kw,cursor,ordering,bc))
                self.assertEqual(cc['context_preparations'],1);self.assertEqual(bc['context_preparations'],len(results))
                for name in ('probe_roots','probe_occurrence_visits','cursor_completed_probes','cursor_promoted_probes','probe_index_builds'):
                    self.assertEqual(cc[name],bc[name])
                for r in results:self.assertEqual(c.prior.validate(*args,**kw,result=r,ordering=ordering,counts=Counter()),independent(args,kw,r,ordering)[0])

    def test_popped_uncompleted_root_and_promotions_are_reloaded(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row)
        for ordering in ('source','unseen'):
            cursor=study.saved_cursor(row,ordering)
            with patch.object(c.prior.prior,'_load',wraps=c.prior.prior._load) as reload_cursor:
                batch=c.continue_rounds(*args,**kw,cursor=cursor,ordering=ordering,counts=Counter(),probe_limit=1,rounds=5)
                self.assertEqual(reload_cursor.call_count,5)
            self.assertEqual(batch,separate(args,kw,cursor,ordering,Counter(),probe_limit=1,rounds=5))
            self.assertEqual(len(batch),5)
            self.assertEqual([len(r['cursor']['completed']) for r in batch],list(range(len(cursor['completed'])+1,len(cursor['completed'])+6)))

    def test_zero_progress_stops_and_cold_resume_is_exact(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row);cursor=study.saved_cursor(row,'source')
        stopped=c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter(),work_limit=1)
        self.assertEqual(len(stopped),1);self.assertEqual(stopped[0]['program']['reason'],'work_limit')
        self.assertEqual(stopped,separate(args,kw,cursor,'source',Counter(),work_limit=1))
        resumed=c.continue_rounds(*args,**kw,cursor=json.loads(json.dumps(stopped[0]['cursor'])),counts=Counter())
        self.assertEqual(resumed,c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter()))
        a=c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter(),rounds=1)
        b=c.continue_rounds(*args,**kw,cursor=json.loads(json.dumps(a[-1]['cursor'])),counts=Counter(),rounds=2)
        self.assertEqual(a+b,resumed)

    def test_caller_mutations_and_snapshots_do_not_alias(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row);cursor=study.saved_cursor(row,'source')
        expected=c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter())
        a,k,saved=deepcopy((args,kw,cursor))
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='batch_owned_copies':a[23]['cursor']['binding']='changed';k['latest_closure']['assignment'].append([9999,True]);saved['binding']='changed'
        result=c.continue_rounds(*a,**k,cursor=saved,counts=MutatingCounter());self.assertEqual(result,expected)
        other=deepcopy(result[1:]);result[0]['cursor']['completed'].clear();result[0]['program']['probes'].clear()
        self.assertEqual(result[1:],other)
        with self.assertRaises(ValueError):c.continue_rounds(*a,**k,cursor=saved,counts=Counter())

    def test_history_closure_cursor_and_policy_edits_are_rejected(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(67,63));args=study.arguments(row);kw=study.options(row);cursor=study.saved_cursor(row,'source')
        for slot in (12,14,16,17,18,19,20,21,22,23):
            bad=deepcopy(args);bad[slot]['cursor']['binding']='changed'
            with self.assertRaises(ValueError):c.continue_rounds(*bad,**kw,cursor=cursor,counts=Counter())
        for key in kw:
            bad=deepcopy(kw);bad[key]['assignment'].append([9999,True])
            with self.assertRaises(ValueError):c.continue_rounds(*args,**bad,cursor=cursor,counts=Counter())
        for kind in ('binding','format','proof','schedule'):
            bad=deepcopy(cursor)
            if kind=='binding':bad['binding']='bad'
            elif kind=='format':bad['format']='bad'
            elif kind=='proof':bad['probes'][0]['proof']['conflict']=999999
            else:bad['completed'].reverse()
            with self.assertRaises(ValueError):c.continue_rounds(*args,**kw,cursor=bad,counts=Counter())
        with self.assertRaises(ValueError):c.continue_rounds(*args,**kw,cursor=cursor,ordering='unseen',counts=Counter())

    def test_controls_changed_trace_and_exhaustion(self):
        row=fixtures()[0];args=study.arguments(row);kw=study.options(row);cursor=study.saved_cursor(row,'source')
        result=c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter())
        self.assertEqual(len(result),1);self.assertEqual((result[0]['program']['status'],result[0]['program']['reason']),('unresolved','complete'))
        for opts in (dict(rounds=0),dict(rounds=True),dict(work_limit=0),dict(probe_limit=False),dict(trace_limit=257),dict(ordering='bad')):
            with self.assertRaises(ValueError):c.continue_rounds(*args,**kw,cursor=cursor,counts=Counter(),**opts)
        with self.assertRaises(ValueError):c.continue_rounds(*args,**kw,cursor=None,counts=Counter())

    def test_ordinary_checker_rejects_corrupted_export(self):
        row=next(r for r in fixtures() if (r['target'],r['event'])==(37,39));args=study.arguments(row);kw=study.options(row)
        results=c.continue_rounds(*args,**kw,cursor=study.saved_cursor(row,'source'),counts=Counter());r=results[-1]
        self.assertEqual([p['assumption'] for p in r['program']['probes']],[32])
        for kind in ('proof','program','binding'):
            bad=deepcopy(r)
            if kind=='proof':bad['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='program':bad['program']['probes']=[]
            else:bad['cursor']['binding']='bad'
            with self.assertRaises(ValueError):c.prior.validate(*args,**kw,result=bad,ordering='source',counts=Counter())

    def test_overlay_integrity(self):
        rows=fixtures();cp=study.base.load(study.PARENT/'checkpoint.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);parent=path/'parent.json';study.compact(parent,study.old.bound(cp['b13_probe_cursor']['remaining']))
            payload=dict(parent=study.old.binding(parent),rows=[dict(target=r['target'],event=r['event'],b12_batch_note='test') for r in rows]);dest=path/'overlay.json';study.compact(dest,payload)
            self.assertEqual(len(study.load_frontier(study.old.binding(dest))),14)
            for kind in ('duplicate','missing','overwrite','parent'):
                bad=deepcopy(payload)
                if kind=='duplicate':bad['rows'].append(bad['rows'][0])
                elif kind=='missing':bad['rows'].pop()
                elif kind=='overwrite':bad['rows'][0]['root']='bad'
                else:parent.write_text('{}')
                study.compact(dest,bad)
                with self.assertRaises((AssertionError,ValueError)):study.load_frontier(study.old.binding(dest))

    def test_small_and_generated_formulas_against_models(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112614)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            normalized=c.prior.engine.native.normalize(source)[0];cl=close(normalized)
            if cl is None:continue
            residual=c.prior.engine.native.normalize(c.prior.engine.native.restrict_scan(normalized,dict(cl['assignment']),Counter()))[0];h=upper_history(residual)
            if h is None:continue
            args,kw=h;checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.prior.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for ordering in ('source','unseen'):
                initial=c.prior.discover(*args,**kw,ordering=ordering,probe_limit=1,counts=Counter())
                results=c.continue_rounds(*args,**kw,cursor=initial['cursor'],ordering=ordering,probe_limit=1,counts=Counter())
                self.assertEqual(results,separate(args,kw,initial['cursor'],ordering,Counter(),probe_limit=1))
                for result in results:
                    c.prior.validate(*args,**kw,result=result,ordering=ordering,counts=Counter())
                    for probe in result['program']['probes']:
                        lit=probe['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
                    if result['program']['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
