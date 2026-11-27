from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_relation_buckets as k
from experiments.cnf_relation_bucket_panel import panel
from experiments.cnf_fresh_seed_panel import truth


SIGNED=[[-1,2],[1,-2],[-1,-3],[1,3],[1,2,-3]]
CONFLICT=[[-1,2],[1,-2],[-2,3],[2,-3],[3,1],[-3,-1],[1,4,5]]


class RelationBucketTests(unittest.TestCase):
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
            for mode in k.MODES:
                p,_=self.checked(source,mode=mode,bag_limit=1);self.assertNotEqual(p['status'],'unresolved')

    def test_seeded_random_cnf_and_sparse_lifting(self):
        rng=random.Random(2711270642)
        for _ in range(65):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.choice((2,3)))] for _ in range(4*n)]
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=2)
            self.checked([[(-1 if l<0 else 1)*(101+19*abs(l)) for l in c] for c in source],bag_limit=2)

    def test_signed_substitution_then_units(self):
        p,_=self.checked(SIGNED,depth_limit=0,bag_limit=1)
        self.assertTrue(any(e['relation'] and e['relation']['kind']=='equivalence' and e['after_units'] for e in p['edges']))
        model=k.check_certificate(SIGNED,p)['model'];self.assertEqual(model,{1:True,2:True,3:False})
        for values in product((False,True),repeat=3):
            self.assertEqual(k.native.holds(SIGNED,dict(enumerate(values,1))),values==(True,True,False))

    def test_disappearing_representative_is_free(self):
        source=[[-1,-2],[1,2],[3,4,5]];p,_=self.checked(source,depth_limit=0)
        self.assertTrue(p['edges'][0]['relation']);m=k.check_certificate(source,p)['model'];self.assertNotEqual(m[1],m[2])
        sparse=[[l//abs(l)*(37*abs(l)+7) for l in c] for c in source];self.checked(sparse)

    def test_binary_conflict_paths_are_source_bound(self):
        cnf,_=k.native.normalize(CONFLICT);binary=tuple(c for c in cnf if len(c)==2);_,ev=k.native.two_cnf(binary,Counter())
        k.check_binary_conflict(cnf,ev,Counter());p,_=self.checked(CONFLICT,mode='conflict',depth_limit=0,bag_limit=1);self.assertEqual(p['status'],'unsat')
        for mutate in (lambda e:e['forward'].pop(),lambda e:e.__setitem__('variable',True),lambda e:e['backward'][0].__setitem__(1,999),lambda e:e['forward'][0].__setitem__(0,True)):
            bad=deepcopy(ev);mutate(bad)
            with self.assertRaises(ValueError):k.check_binary_conflict(cnf,bad,Counter())
        with self.assertRaises(ValueError):k.check_binary_conflict(tuple(c for c in cnf if c!=binary[ev['forward'][0][1]]),ev,Counter())

    def test_one_way_implication_is_not_equivalence(self):
        cnf,_=k.native.normalize([[-1,2],[1,3,4]]);steps,rel,after,closed,data,_=k.prepare_edge(cnf,'relations',k.DEFAULTS,Counter());self.assertIsNone(rel)
        fake=dict(kind='equivalence',evidence=dict(representative=1,forward=[[1,2,0]],backward=[[2,1,0]]))
        with self.assertRaises(ValueError):k.replay_edge(cnf,[],fake,[],'relations',k.DEFAULTS,Counter())

    def test_unknown_budgets_and_single_block(self):
        source=[[-1,2],[1,-2],[-3,4],[3,-4],[1,3,5],[2,4,-5]]
        p,_=self.checked(source,depth_limit=0,bag_limit=1,index_work_limit=1)
        self.assertEqual(len(p['edges']),1);self.assertIn(p['status'],('sat','unresolved'))
        wide=[[1,2,3,4,5],[-1,-2,-3,-4,-5]]
        p,_=self.checked(wide,depth_limit=0,bag_limit=1);self.assertEqual(p['status'],'unresolved')
        q=deepcopy(p);q['status']='unsat';q['nodes'][-1]['status']='unsat'
        with self.assertRaises(ValueError):k.check_certificate(wide,q)

    def test_corrupt_relation_graph_and_transport(self):
        p,_=self.checked(SIGNED,depth_limit=0,bag_limit=1)
        changes=[lambda q:q.__setitem__('mode','units'),lambda q:q['edges'][0]['relation']['evidence']['backward'][0].__setitem__(2,999),lambda q:q['edges'][0]['after_units'][0].__setitem__('literal',-1),lambda q:q['edges'][0].__setitem__('residual',[[]]),lambda q:q['edges'][0].__setitem__('target',1),lambda q:q.__setitem__('model',[False]*3)]
        for change in changes:
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(SIGNED,q)

    def test_cold_replay_without_recognition(self):
        programs=[(s,self.checked(s,depth_limit=0,bag_limit=1)[0]) for s in (SIGNED,CONFLICT)]
        with patch.object(k.symbolic,'preprocess',side_effect=AssertionError('units')),patch.object(k.equivalence,'discover',side_effect=AssertionError('SCC')),patch.object(k.native,'two_cnf',side_effect=AssertionError('binary search')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')),patch.object(k.bucket,'project',side_effect=AssertionError('project')):
            for source,p in programs:self.assertIsNotNone(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-relation-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
