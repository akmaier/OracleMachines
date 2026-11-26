from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,unittest
from experiments import cnf_shared_joint_preparation as c,compare_cnf_joint_probe_cursor as study
from solver.test_cnf_b7_probe_cursor import tiny


def fixtures():return json.loads(Path('experiments/results/cnf-joint-probe-cursor/remaining-closures.json').read_text())['rows']
def args(row):return tuple(row[k] for k in study.FIELDS)
def closure(row):return row['joint_cursor_feedback_closure']
def changed():return next(r for r in fixtures() if (r['target'],r['event'])==(28,18))


class SharedJointPreparationTests(unittest.TestCase):
    def test_all_frontiers_and_prepared_banks_equal_with_one_common_preparation(self):
        for row in fixtures():
            a=args(row);cl=closure(row);saved=deepcopy((a,cl));cc=Counter();oldc=Counter()
            result=c.discover(*a,closure=cl,counts=cc)
            self.assertEqual(result,c.prior.discover(*a,closure=cl,counts=oldc));self.assertEqual(result,row['joint_probe_cursor'])
            self.assertEqual(c.validate(*a,closure=cl,result=result,counts=Counter()),c.prior.validate(*a,closure=cl,result=result,counts=Counter()))
            self.assertEqual(cc['shared_joint_prefix_preparations'],1);self.assertEqual(cc['shared_joint_histories_checked'],3)
            self.assertEqual(oldc['context_preparations'],2*cc['context_preparations']);self.assertEqual((a,cl),saved)

    def test_all_three_original_histories_and_closures_are_checked(self):
        row=changed();a=args(row);cl=closure(row)
        for kind in ('original','upper','comparison','earlier','lower_closure','upper_closure','current_closure','comparison_program','source'):
            bad=deepcopy(a);bc=deepcopy(cl)
            if kind in ('original','upper','comparison','earlier'):bad[{'original':14,'upper':16,'comparison':17,'earlier':12}[kind]]['cursor']['binding']='changed'
            elif kind in ('lower_closure','upper_closure'):bad[13 if kind=='lower_closure' else 15]['assignment'].append([9999,True])
            elif kind=='current_closure':bc['assignment'].append([9999,True])
            elif kind=='comparison_program':bad[17]['program']['probes']=[]
            else:bad[0][0].append(9999)
            for module in (c,c.prior):
                with self.assertRaises(ValueError):module.discover(*bad,closure=bc,counts=Counter())

    def test_histories_with_distinct_trace_bounds_keep_distinct_bindings(self):
        full=tiny(((1,2),));upper=c.b7.discover(*full,Counter(),trace_limit=31)
        comparison=c.b6.discover(*full[:14],Counter(),trace_limit=17);a=(*full,upper,comparison)
        prepared=c.prior.joint.prepare(*a,counts=Counter());fixed,trace,conflict=c.b7.native.propagate(prepared[17],Counter());self.assertIsNone(conflict)
        cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));cc=Counter()
        result=c.discover(*a,closure=cl,counts=cc);self.assertEqual(result,c.prior.discover(*a,closure=cl,counts=Counter()))
        self.assertEqual(cc['shared_joint_bindings_reused'],0)
        bad=deepcopy(a);bad[17]['program']['trace_limit']=256
        with self.assertRaises(ValueError):c.discover(*bad,closure=cl,counts=Counter())

    def test_alternate_valid_closure_trace_is_preserved(self):
        for row in fixtures():
            a=args(row);cl=closure(row);prepared=c.prior.joint.prepare(*a,counts=Counter())
            for i in range(len(cl['units'])-1):
                alternate=deepcopy(cl);alternate['units'][i:i+2]=reversed(alternate['units'][i:i+2])
                try:c.b7.prior.check_closure(prepared[17],alternate,Counter())
                except ValueError:continue
                got=c.discover(*a,closure=alternate,counts=Counter())
                self.assertEqual(got,c.prior.discover(*a,closure=alternate,counts=Counter()));c.prior.validate(*a,closure=alternate,result=got,counts=Counter());return
        self.fail('Fixture needs an alternate valid unit ordering')

    def test_cold_continuation_and_frozen_validator_agree(self):
        row=changed();a=args(row);cl=closure(row);first=c.discover(*a,closure=cl,counts=Counter(),probe_limit=4)
        saved=json.loads(json.dumps(first));c.validate(*a,closure=cl,result=saved,counts=Counter())
        resumed=c.discover(*a,closure=cl,cursor=saved['cursor'],counts=Counter(),probe_limit=60)
        self.assertEqual(resumed,c.prior.discover(*a,closure=cl,counts=Counter()));c.prior.validate(*a,closure=cl,result=resumed,counts=Counter())

    def test_interruption_trace_and_policy_controls_match(self):
        row=changed();a=args(row);cl=closure(row)
        for options in (dict(work_limit=1),dict(trace_limit=1),dict(policy='restart'),dict(policy='matched')):
            got=c.discover(*a,closure=cl,counts=Counter(),**options);self.assertEqual(got,c.prior.discover(*a,closure=cl,counts=Counter(),**options));c.validate(*a,closure=cl,result=got,counts=Counter())
        for options in (dict(trace_limit=True),dict(probe_limit=0),dict(policy='trusted')):
            with self.assertRaises(ValueError):c.discover(*a,closure=cl,counts=Counter(),**options)

    def test_private_copy_survives_caller_mutation_after_ownership(self):
        row=changed();a=deepcopy(args(row));cl=deepcopy(closure(row));expected=c.prior.discover(*a,closure=cl,counts=Counter())
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='shared_joint_owned_copies':a[17]['cursor']['binding']='mutated by caller';cl['assignment'].append([9999,True])
        self.assertEqual(c.discover(*a,closure=cl,counts=MutatingCounter()),expected)
        with self.assertRaises(ValueError):c.discover(*a,closure=cl,counts=Counter())

    def test_complete_result_rejects_bad_program_cursor_and_forward_reason(self):
        row=changed();a=args(row);cl=closure(row);result=c.discover(*a,closure=cl,counts=Counter())
        for kind in ('sat','program','binding','forward','schedule','format'):
            bad=deepcopy(result)
            if kind=='sat':bad['program']['status']='sat'
            elif kind=='program':bad['program']['probes']=[]
            elif kind=='binding':bad['cursor']['binding']='changed'
            elif kind=='forward':bad['cursor']['probes'][0]['proof']['conflict']=999999
            elif kind=='schedule':bad['cursor']['completed'].reverse()
            else:bad['cursor']['format']='unchecked'
            with self.assertRaises(ValueError):c.validate(*a,closure=cl,result=bad,counts=Counter())

    def test_small_formulas_match_frozen_search_and_truth_tables(self):
        signed=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260606);checked=0
        cases=[(2,[signed[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        for n,source in cases:
            full=tiny(source)
            if full is None:continue
            upper=c.b7.discover(*full,Counter(),work_limit=1);cmp=c.b6.discover(*full[:14],Counter(),work_limit=1)
            if any(r['program']['status']=='refuted' for r in (upper,cmp)):continue
            a=(*full,upper,cmp);prepared=c.prior.joint.prepare(*a,counts=Counter());fixed,trace,conflict=c.b7.native.propagate(prepared[17],Counter())
            if conflict is not None:continue
            cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));r=c.discover(*a,closure=cl,counts=Counter());self.assertEqual(r,c.prior.discover(*a,closure=cl,counts=Counter()));c.validate(*a,closure=cl,result=r,counts=Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.b7.native.holds(a[0],dict(enumerate(bits,1)))]
            for failed in r['program']['probes']:
                lit=failed['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))
            if r['program']['status']=='refuted':self.assertFalse(models)
        self.assertGreater(checked,60)


if __name__=='__main__':unittest.main()
