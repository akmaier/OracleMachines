from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_symbolic_buckets as k
from experiments.cnf_symbolic_bucket_panel import panel
from experiments.cnf_fresh_seed_panel import truth


class SymbolicBucketTests(unittest.TestCase):
    def equivalence(self,source,mode='fold',**values):
        cnf,names=k.native.normalize(source);steps,active,diag=k.preprocess(cnf,mode,k.options(values),Counter())
        fixed={abs(s['literal']):s['literal']>0 for s in steps if s['kind']=='unit'}
        for bits in product((False,True),repeat=len(names)):
            assignment=dict(enumerate(bits,1))
            self.assertEqual(k.native.holds(cnf,assignment),all(assignment[v]==b for v,b in fixed.items()) and k.native.holds(active,assignment))
        return steps,active,diag

    def checked(self,source,**options):
        p,d=k.discover(source,**options);r=k.check_certificate(source,p)
        if r['answer'] is not None:
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return p,d

    def test_exhaustive_two_variable_equivalence(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            for mode in ('units','fold'):self.equivalence(source,mode);self.checked(source,mode=mode)

    def test_random_full_truth_sets_and_sparse_lifting(self):
        rng=random.Random(2711270441)
        for _ in range(50):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(1,4))] for _ in range(3*n)]
            self.equivalence(source);self.equivalence(source,step_limit=1);self.checked(source)
            renamed=[[(1 if l>0 else -1)*(31*abs(l)+7) for l in c] for c in source]
            self.checked(renamed)

    def test_multilevel_folds_and_stale_index_entries(self):
        source=[[a,b,3] for a in (-1,1) for b in (-2,2)]+[[-3,4],[-4,5]]
        p,_=self.checked(source);self.assertEqual(p['status'],'sat');self.assertGreaterEqual(sum(s['kind']=='fold' for s in p['steps']),2)
        self.assertEqual(p['model'][2:],[True,True,True]);self.equivalence(source)
        self.checked(source+[[-5]])

    def test_general_resolvent_cannot_replace_parents(self):
        source=[[1,2],[-1,3]];p,_=k.discover(source)
        p['steps']=[dict(kind='fold',left=[1,2],right=[-1,3])]
        with self.assertRaisesRegex(ValueError,'remainders'):k.check_certificate(source,p)
        # The resolvent alone allows an assignment forbidden by the first parent.
        assignment={1:False,2:False,3:True}
        self.assertTrue(k.native.holds([[2,3]],assignment));self.assertFalse(k.native.holds(source,assignment))

    def test_missing_parent_and_changed_unit_rejected(self):
        source=[[1,2],[-1,2],[-2,3]];p,_=self.checked(source)
        for change in (lambda q:q['steps'][0]['left'].append(9),lambda q:q['steps'][0].__setitem__('right',[2]),lambda q:q.__setitem__('model',[False]*3),lambda q:q.__setitem__('residual',[[1]]),lambda q:q.__setitem__('mode','units')):
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)
        with self.assertRaises(ValueError):k.check_certificate(source[:-1],p)

    def test_partial_preprocessing_budgets_preserve_exactness(self):
        source=[[1,2],[-1,2],[-2,3]]
        for limits in (dict(index_work_limit=1),dict(index_work_limit=30),dict(step_limit=1)):
            self.equivalence(source,**limits);self.checked(source,**limits)
        for value in (0,True):
            with self.assertRaises(ValueError):k.discover(source,step_limit=value)
        with self.assertRaises(ValueError):k.discover(source,mode='other')

    def test_cold_check_without_index_or_discovery(self):
        source=[[1,2],[-1,2],[-2,3],[-3]];p,_=self.checked(source);p=json.loads(json.dumps(p))
        with patch.object(k,'preprocess',side_effect=AssertionError('index')),patch.object(k.conditioned,'discover',side_effect=AssertionError('conditioning')),patch.object(k.conditioned.bucket,'project',side_effect=AssertionError('projection')):
            self.assertFalse(k.check_certificate(source,p)['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-symbolic-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
