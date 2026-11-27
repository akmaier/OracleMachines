from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_semantic_buckets as k
from experiments.cnf_semantic_bucket_panel import panel
from experiments.cnf_fresh_seed_panel import truth


class SemanticBucketTests(unittest.TestCase):
    def checked(self,source,**options):
        p,d=k.discover(source,**options);r=k.check_certificate(source,p)
        if r['answer'] is not None:
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return p,d

    def test_exhaustive_two_variable_formulas(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i & 1]
            for reduce in (False,True):self.checked(source,reduce=reduce)

    def test_random_cnf_signed_sparse_names(self):
        rng=random.Random(2711270236);cache={}
        for _ in range(80):
            n=rng.randrange(3,8);raw=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(1,4))] for _ in range(3*n)]
            self.checked(raw,cache=cache)
            perm=rng.sample(range(101,300),n)
            self.checked([[(1 if l>0 else -1)*perm[abs(l)-1] for l in c] for c in raw],cache=cache)

    def test_dropped_scope_keeps_dependent_lifting_choice(self):
        source=[[-1,2],[1,-2],[2]];p,_=self.checked(source)
        first=p['steps'][0];self.assertEqual(first['variable'],1);self.assertEqual(first['scope'],[])
        self.assertEqual(first['choices'],2);self.assertEqual(p['model'],[True,True])
        bad=deepcopy(p);bad['steps'][0]['choices']=0
        with self.assertRaisesRegex(ValueError,'choice'):k.check_certificate(source,bad)

    def test_semantic_support_is_exact_for_all_three_variable_tables(self):
        for bits in range(1<<8):
            scope,out=k.reduce_support([1,2,3],bits,Counter())
            for row in range(8):
                assignment={i+1:bool(row>>i&1) for i in range(3)}
                self.assertEqual(k.evaluate(dict(scope=scope,bits=out),assignment),bool(bits>>row&1))
            for v in scope:
                self.assertTrue(any(((bits>>row)^(bits>>(row^(1<<(v-1)))))&1 for row in range(8)))

    def test_corrupt_bucket_or_cache_cannot_issue_verdict(self):
        source=[[-1,2],[1,-2],[2]];p,_=k.discover(source)
        changes=[lambda q:q['steps'][0]['inputs'].pop(),lambda q:q['steps'][0].__setitem__('bits',0),
                 lambda q:q['steps'][0].__setitem__('scope',[99]),lambda q:q['steps'][0].__setitem__('variable',3),
                 lambda q:q['steps'][0].__setitem__('choices',0),lambda q:q.__setitem__('model',[False,False]),
                 lambda q:q.__setitem__('status','unsat'),lambda q:q['cnf'].pop()]
        for mutate in changes:
            q=deepcopy(p);mutate(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)
        cache={};k.discover(source,cache=cache);key=next(iter(cache));slots,bits,choices=cache[key];cache[key]=(slots,0,choices)
        with self.assertRaises(ValueError):k.discover(source,cache=cache)

    def test_budgets_leave_unknown_and_no_partial_truth(self):
        for source,opts,reason in (([[1,2,3]],dict(bag_limit=2),'leaf-width'),([[-1,2],[1,-2]],dict(work_limit=1),'row-work')):
            p,d=k.discover(source,**opts);self.assertEqual(d['reason'],reason);self.assertIsNone(k.check_certificate(source,p)['answer'])
            for status in ('sat','unsat'):
                q=deepcopy(p);q['status']=status
                with self.assertRaises(ValueError):k.check_certificate(source,q)
        for bad in (0,13,True):
            with self.assertRaises(ValueError):k.discover([[1]],bag_limit=bad)

    def test_operator_reuse_and_cold_check_without_discovery(self):
        source=[[-1,2],[1,-2],[2]];cache={};p,_=k.discover(source,cache=cache)
        c=Counter();q,_=k.discover(source,c,cache=cache);self.assertEqual(p,q);self.assertGreater(c['bucket_operator_hits'],0)
        q=json.loads(json.dumps(q))
        with patch.object(k,'project',side_effect=AssertionError('discovery')),patch.object(k,'reduce_support',side_effect=AssertionError('discovery')):
            self.assertTrue(k.check_certificate(source,q)['answer'])
        with self.assertRaises(ValueError):k.check_certificate([[-1,2],[1,-2],[-2]],q)

    def test_frozen_panel(self):
        r,d=panel();out=Path('experiments/results/cnf-semantic-buckets')
        self.assertEqual(r,json.loads((out/'heldout.json').read_text()))
        self.assertEqual(d,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
