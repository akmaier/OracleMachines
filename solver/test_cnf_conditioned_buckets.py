from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_conditioned_buckets as k
from experiments.cnf_conditioned_bucket_panel import panel
from experiments.cnf_fresh_seed_panel import truth


def twins():
    core=[[s*(i+2) for i,s in enumerate(signs)] for signs in product((-1,1),repeat=3)]
    return [c+[sign] for c in core for sign in (-1,1)]


class ConditionedBucketTests(unittest.TestCase):
    def checked(self,source,**options):
        p,d=k.discover(source,**options);r=k.check_certificate(source,p)
        if r['answer'] is not None:
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return p,d

    def test_exhaustive_two_variable_formulas(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            for reuse in (False,True):
                p,_=self.checked(source,bag_limit=1,reuse=reuse)
                self.assertNotEqual(p['status'],'unresolved')

    def test_random_signed_sparse_names(self):
        rng=random.Random(2711270334)
        for _ in range(60):
            n=rng.randrange(3,8);raw=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            for reuse in (False,True):self.checked(raw,bag_limit=3,reuse=reuse)
            names=rng.sample(range(101,300),n)
            self.checked([[(1 if l>0 else -1)*names[abs(l)-1] for l in c] for c in raw],bag_limit=3)

    def test_identical_cofactors_share_exact_depth(self):
        c=Counter();tree,_=k.discover(twins(),bag_limit=2,reuse=False);memo,_=k.discover(twins(),c,bag_limit=2)
        self.assertEqual((tree['status'],memo['status']),('unsat','unsat'))
        self.assertEqual((len(tree['nodes']),len(memo['nodes'])),(7,3));self.assertEqual(c['condition_memo_hits'],2)
        q=deepcopy(memo);q['nodes'][0]['depth']=1
        with self.assertRaises(ValueError):k.check_certificate(twins(),q)

    def test_edited_guard_and_lifted_sparse_witness(self):
        source=twins()[:-1];p,_=self.checked(source,bag_limit=2)
        self.assertEqual(p['status'],'sat')
        renamed=[[(1 if l>0 else -1)*(29*abs(l)+3) for l in c] for c in source]
        self.checked(renamed,bag_limit=2)
        with self.assertRaises(ValueError):k.check_certificate(twins(),p)

    def test_unknown_branches_are_not_refutations(self):
        p,_=self.checked(twins(),bag_limit=1);self.assertEqual(p['status'],'unresolved')
        for status in ('sat','unsat'):
            q=deepcopy(p);q['status']=status;q['nodes'][-1]['status']=status
            with self.assertRaises(ValueError):k.check_certificate(twins(),q)
        for depth in (-1,9,True):
            with self.assertRaises(ValueError):k.discover([[1]],depth_limit=depth)

    def test_graph_and_leaf_corruption_rejected(self):
        source=twins();p,_=k.discover(source,bag_limit=2)
        changes=[lambda q:q['nodes'][-1].__setitem__('low',q['root']),lambda q:q['nodes'][-1].__setitem__('pivot',99),
                 lambda q:q['nodes'][-1].pop('high'),lambda q:q['nodes'][0]['cnf'].pop(),
                 lambda q:q['nodes'][0]['bucket'].__setitem__('status','sat'),lambda q:q.__setitem__('model',[]),
                 lambda q:q.__setitem__('root',0),lambda q:q['limits'].__setitem__('bag_limit',3)]
        for change in changes:
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)

    def test_cold_check_without_acquisition(self):
        source=twins();p,_=k.discover(source,bag_limit=2);p=json.loads(json.dumps(p))
        with patch.object(k,'discover',side_effect=AssertionError('search')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket search')),patch.object(k.bucket,'project',side_effect=AssertionError('projection')),patch.object(k.bucket,'reduce_support',side_effect=AssertionError('support')):
            self.assertFalse(k.check_certificate(source,p)['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-conditioned-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
