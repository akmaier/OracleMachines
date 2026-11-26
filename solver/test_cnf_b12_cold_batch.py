from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import random,unittest
from experiments import cnf_b12_cold_batch as c,compare_cnf_b12_cold_batch as study
from experiments.validate_cnf_b12_progress_order import independent
from solver.test_cnf_shared_b12_preparation import upper_history,close


def fixtures():
    cp=study.base.load(study.PARENT/'checkpoint.json')
    return study.prior.load_frontier(cp['b12_continuation_batch']['remaining'])


def snapshots(row,ordering='source'):
    return [study.old.bound(b) for b in row['b12_batch_'+ordering+'_rounds']]


def productive():
    return next(r for r in fixtures() if (r['target'],r['event'])==(67,63))


class B12ColdBatchTests(unittest.TestCase):
    def test_all_saved_snapshots_equal_independent_checks(self):
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row)
            for ordering in ('source','unseen'):
                results=snapshots(row,ordering);cc=Counter();bc=Counter()
                with patch.object(c.prior.prior,'_load',wraps=c.prior.prior._load) as replay:
                    prepared=c.validate_many(*args,**kw,results=results,counts=cc,ordering=ordering)
                    self.assertEqual(replay.call_count,len(results))
                self.assertEqual(cc['context_preparations'],1)
                self.assertEqual(cc['cold_batch_snapshots_checked'],len(results))
                for result in results:
                    self.assertEqual(prepared,c.prior.validate(*args,**kw,result=result,counts=bc,ordering=ordering))
                    self.assertEqual(prepared,independent(args,kw,result,ordering)[0])
                self.assertEqual(bc['context_preparations'],len(results))

    def test_corruption_at_every_snapshot_position_is_rejected(self):
        row=productive();args=study.arguments(row);kw=study.options(row)
        for ordering in ('source','unseen'):
            results=snapshots(row,ordering)
            for i in range(len(results)):
                for kind in ('binding','format','proof','program','schedule'):
                    bad=deepcopy(results);r=bad[i]
                    if kind=='binding':r['cursor']['binding']='changed'
                    elif kind=='format':r['cursor']['format']='changed'
                    elif kind=='proof':r['cursor']['probes'][0]['proof']['conflict']=999999
                    elif kind=='program':r['program']['probes']=[]
                    else:r['cursor']['completed'].reverse()
                    with self.subTest(ordering=ordering,position=i,kind=kind):
                        with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=bad,counts=Counter(),ordering=ordering)
                        with self.assertRaises(ValueError):c.prior.validate(*args,**kw,result=r,counts=Counter(),ordering=ordering)

    def test_history_closure_source_and_policy_changes_are_rejected(self):
        row=productive();args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        for slot in (12,14,16,17,18,19,20,21,22,23):
            bad=deepcopy(args);bad[slot]['cursor']['binding']='changed'
            with self.assertRaises(ValueError):c.validate_many(*bad,**kw,results=results,counts=Counter())
        for key in kw:
            bad=deepcopy(kw);bad[key]['assignment'].append([9999,True])
            with self.assertRaises(ValueError):c.validate_many(*args,**bad,results=results,counts=Counter())
        bad=list(deepcopy(args));bad[0]=list(bad[0])+[[9999]]
        with self.assertRaises(ValueError):c.validate_many(*bad,**kw,results=results,counts=Counter())
        with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=results,ordering='unseen',counts=Counter())
        with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=results,ordering='invalid',counts=Counter())

    def test_different_valid_trace_bounds_require_separate_batches(self):
        row=productive();args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        other=c.prior.discover(*args,**kw,trace_limit=257,ordering='source',counts=Counter())
        prepared=c.prior.validate(*args,**kw,result=other,ordering='source',counts=Counter())
        self.assertEqual(c.validate_many(*args,**kw,results=(other,),counts=Counter()),prepared)
        with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=[results[0],other],counts=Counter())

    def test_ownership_precedes_counter_callbacks_and_returns_are_isolated(self):
        row=productive();args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        expected=c.validate_many(*args,**kw,results=results,counts=Counter());a,k,books=deepcopy((args,kw,results))
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='cold_batch_owned_copies':
                    a[23]['cursor']['binding']='changed';k['latest_closure']['assignment'].append([9999,True]);books[-1]['cursor']['binding']='changed'
        prepared=c.validate_many(*a,**k,results=books,counts=MutatingCounter());self.assertEqual(prepared,expected)
        prepared[26].clear()
        self.assertEqual(c.validate_many(*args,**kw,results=results,counts=Counter()),expected)
        with self.assertRaises(ValueError):c.validate_many(*a,**k,results=books,counts=Counter())

    def test_duplicates_and_reversed_snapshots_are_each_checked(self):
        row=productive();args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        books=list(reversed(results))+[deepcopy(results[0])];cc=Counter()
        with patch.object(c.prior.prior,'_load',wraps=c.prior.prior._load) as replay:
            prepared=c.validate_many(*args,**kw,results=books,counts=cc)
            self.assertEqual(replay.call_count,4)
        self.assertEqual(cc['cold_batch_snapshots_checked'],4)
        self.assertEqual(prepared,c.prior.validate(*args,**kw,result=results[0],ordering='source',counts=Counter()))

    def test_no_discovery_or_cross_call_validation_authority(self):
        row=productive();args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        with patch.object(c.prior,'discover',side_effect=AssertionError('No discovery during checking')):
            c.validate_many(*args,**kw,results=results,counts=Counter())
            bad=deepcopy(results);bad[-1]['cursor']['binding']='changed'
            with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=bad,counts=Counter())
            history=deepcopy(args);history[23]['cursor']['binding']='changed'
            with self.assertRaises(ValueError):c.validate_many(*history,**kw,results=results,counts=Counter())

    def test_malformed_batch_and_snapshot_headers(self):
        row=fixtures()[0];args=study.arguments(row);kw=study.options(row);results=snapshots(row)
        for malformed in (None,[],(),{},'bad',iter(results)):
            with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=malformed,counts=Counter())
        for kind in ('empty','action','extra','trace_zero','trace_bool','trace_string'):
            bad=deepcopy(results)
            if kind=='empty':bad[-1]={}
            elif kind=='action':bad[-1]['action']='invalid'
            elif kind=='extra':bad[-1]['extra']=True
            else:bad[-1]['program']['trace_limit']={'trace_zero':0,'trace_bool':True,'trace_string':'256'}[kind]
            with self.assertRaises(ValueError):c.validate_many(*args,**kw,results=bad,counts=Counter())

    def test_small_and_generated_formulas_against_models(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112615)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            normalized=c.prior.engine.native.normalize(source)[0];cl=close(normalized)
            if cl is None:continue
            residual=c.prior.engine.native.normalize(c.prior.engine.native.restrict_scan(normalized,dict(cl['assignment']),Counter()))[0];history=upper_history(residual)
            if history is None:continue
            args,kw=history;checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.prior.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for ordering in ('source','unseen'):
                initial=c.prior.discover(*args,**kw,ordering=ordering,probe_limit=1,counts=Counter())
                results=study.prior.candidate.continue_rounds(*args,**kw,cursor=initial['cursor'],ordering=ordering,probe_limit=1,counts=Counter())
                prepared=c.validate_many(*args,**kw,results=results,ordering=ordering,counts=Counter())
                for result in results:
                    self.assertEqual(prepared,c.prior.validate(*args,**kw,result=result,ordering=ordering,counts=Counter()))
                    for probe in result['program']['probes']:
                        lit=probe['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
                    if result['program']['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
