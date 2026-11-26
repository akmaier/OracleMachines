from collections import Counter
from copy import deepcopy
from itertools import product
import json, random, unittest
from experiments import cnf_shared_b10_preparation as c
from solver.test_cnf_b10_probe_cursor import fixtures, record, study, tiny, frozen_feedback


def close(bank):
    fixed, trace, conflict = c.engine.native.propagate(bank, Counter())
    return None if conflict is not None else dict(units=trace, assignment=sorted([list(x) for x in fixed.items()]))


def history(source, bounds=(31, 17, 23)):
    f = c.prior
    full = tiny(source)
    if full is None: return None
    upper = f.engine.discover(*full, Counter(), probe_limit=1)
    comparison = f.engine.feedback.cursor.discover(*full[:14], Counter(), probe_limit=1)
    if any(r['program']['status']=='refuted' for r in (upper, comparison)): return None
    joint = (*full, upper, comparison)
    cl = close(f.prior.prior.joint.prepare(*joint, counts=Counter())[17])
    if cl is None: return None
    original = f.prior.prior.discover(*joint, closure=cl, counts=Counter(), probe_limit=1, trace_limit=bounds[0])
    cmp = f.prior.prior.discover(*joint, closure=cl, counts=Counter(), probe_limit=2, trace_limit=bounds[1])
    if any(r['program']['status']=='refuted' for r in (original, cmp)): return None
    initial = (*joint, original)
    prepared = frozen_feedback.prepare(*initial, closure=cl, counts=Counter())
    fc = close(prepared[19])
    if fc is None: return None
    upper = f.prior.discover(*initial, closure=cl, feedback_closure=fc, counts=Counter(), probe_limit=1, trace_limit=bounds[2])
    if upper['program']['status']=='refuted': return None
    jc = close(tuple(sorted(set(prepared[19]) | {(-r['assumption'],) for p in (upper, cmp) for r in p['program']['probes']})))
    return None if jc is None else ((*initial, upper, cmp), dict(closure=cl, feedback_closure=fc, joint_closure=jc))


class SharedB10PreparationTests(unittest.TestCase):
    def test_all_results_and_banks_equal_with_one_prefix_preparation(self):
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row);cc=Counter();old=Counter()
            result=c.discover(*args,**kw,counts=cc)
            self.assertEqual(result,c.prior.discover(*args,**kw,counts=old))
            self.assertEqual(c.validate(*args,**kw,result=result,counts=Counter()),c.prior.validate(*args,**kw,result=result,counts=Counter()))
            self.assertEqual(cc['shared_b10_prefix_preparations'],1)
            self.assertEqual(cc['shared_b10_histories_checked'],3)
            self.assertEqual(old['context_preparations'],2*cc['context_preparations'])
            for key in ('probe_roots','probe_occurrence_visits','cursor_completed_probes','b10_imported_completed'):
                self.assertEqual(cc[key],old[key])

    def test_every_history_source_and_closure_is_checked(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row)
        for slot in (12,14,16,17,18,19,20):
            bad=deepcopy(args);bad[slot]['cursor']['binding']='changed'
            for module in (c,c.prior):
                with self.assertRaises(ValueError): module.discover(*bad,**kw,counts=Counter())
        for key in kw:
            bad=deepcopy(kw);bad[key]['assignment'].append([9999,True])
            with self.assertRaises(ValueError): c.discover(*args,**bad,counts=Counter())
        bad=deepcopy(args);bad[0][0].append(9999)
        with self.assertRaises(ValueError): c.discover(*bad,**kw,counts=Counter())

    def test_distinct_history_trace_bounds_get_distinct_bindings(self):
        args,kw=history(((1,2),));cc=Counter()
        result=c.discover(*args,**kw,counts=cc)
        self.assertEqual(result,c.prior.discover(*args,**kw,counts=Counter()))
        self.assertEqual(cc['shared_b10_bindings_reused'],0)
        bad=deepcopy(args);bad[20]['program']['trace_limit']=31
        with self.assertRaises(ValueError): c.discover(*bad,**kw,counts=Counter())

    def test_cold_and_interrupted_continuations_match(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row)
        first=c.discover(*args,**kw,counts=Counter(),probe_limit=1)
        result=c.discover(*args,**kw,cursor=json.loads(json.dumps(first['cursor'])),counts=Counter(),probe_limit=63)
        self.assertEqual(result,c.prior.discover(*args,**kw,counts=Counter()))
        stopped=c.discover(*args,**kw,counts=Counter(),work_limit=1)
        self.assertEqual(stopped['program']['reason'],'work_limit')
        self.assertEqual(c.discover(*args,**kw,cursor=stopped['cursor'],counts=Counter()),result)

    def test_policies_bounds_and_invalid_controls(self):
        row=record((40,0));args=study.arguments(row);kw=study.options(row)
        for options in (dict(policy='restart'),dict(policy='matched'),dict(trace_limit=1),dict(work_limit=1)):
            result=c.discover(*args,**kw,counts=Counter(),**options)
            self.assertEqual(result,c.prior.discover(*args,**kw,counts=Counter(),**options))
            c.validate(*args,**kw,result=result,counts=Counter())
        for options in (dict(policy='trusted'),dict(trace_limit=True),dict(work_limit=0)):
            with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter(),**options)

    def test_private_copy_before_caller_mutation_for_search_and_check(self):
        row=record((28,18));original=study.arguments(row);original_kw=study.options(row)
        expected=c.prior.discover(*original,**original_kw,counts=Counter())
        for validate in (False,True):
            args,kw,result=deepcopy((original,original_kw,expected))
            class MutatingCounter(Counter):
                def __setitem__(self,key,value):
                    super().__setitem__(key,value)
                    if key=='shared_b10_owned_copies':
                        args[20]['cursor']['binding']='caller changed'
                        kw['joint_closure']['assignment'].append([9999,True])
                        result['cursor']['binding']='caller changed'
            if validate:
                self.assertEqual(c.validate(*args,**kw,result=result,counts=MutatingCounter()),c.prior.validate(*original,**original_kw,result=expected,counts=Counter()))
            else: self.assertEqual(c.discover(*args,**kw,counts=MutatingCounter()),expected)
            with self.assertRaises(ValueError): c.discover(*args,**kw,counts=Counter())

    def test_result_and_original_bank_proof_corruption_rejected(self):
        row=record((28,18));args=study.arguments(row);kw=study.options(row)
        result=c.discover(*args,**kw,counts=Counter())
        for kind in ('program','binding','proof','schedule','format','b8_proof','b9_proof'):
            a,r=deepcopy((args,result))
            if kind=='program': r['program']['probes']=[]
            elif kind=='binding': r['cursor']['binding']='bad'
            elif kind=='proof': r['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='schedule': r['cursor']['completed'].reverse()
            elif kind=='format': r['cursor']['format']='unchecked'
            else: a[20 if kind=='b8_proof' else 19]['cursor']['probes'][0]['proof']['conflict']=999999
            with self.assertRaises(ValueError): c.validate(*a,**kw,result=r,counts=Counter())

    def test_alternate_valid_closure_order_is_not_canonicalized_away(self):
        for row in fixtures():
            args=study.arguments(row);kw=study.options(row)
            prepared=c.prior.prepare(*args,**kw,counts=Counter())[0]
            for i in range(len(kw['joint_closure']['units'])-1):
                alt=deepcopy(kw);units=alt['joint_closure']['units'];units[i:i+2]=reversed(units[i:i+2])
                try: c.engine.prior.check_closure(prepared[21],alt['joint_closure'],Counter())
                except ValueError: continue
                result=c.discover(*args,**alt,counts=Counter())
                self.assertEqual(result,c.prior.discover(*args,**alt,counts=Counter()))
                c.prior.validate(*args,**alt,result=result,counts=Counter());return
        self.fail('Fixture needs a valid alternate closure ordering')

    def test_exhaustive_small_and_generated_formulas_against_models(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112609)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked=0
        for n,source in cases:
            source=c.engine.native.normalize(source)[0];cl=close(source)
            if cl is None: continue
            source=c.engine.native.normalize(c.engine.native.restrict_scan(source,dict(cl['assignment']),Counter()))[0]
            h=history(source)
            if h is None: continue
            args,kw=h;result=c.discover(*args,**kw,counts=Counter());checked+=1
            self.assertEqual(result,c.prior.discover(*args,**kw,counts=Counter()))
            self.assertEqual(c.validate(*args,**kw,result=result,counts=Counter()),c.prior.validate(*args,**kw,result=result,counts=Counter()))
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.engine.native.holds(args[0],dict(enumerate(bits,1)))]
            for row in result['program']['probes']:
                lit=row['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if result['program']['status']=='refuted': self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__': unittest.main()
