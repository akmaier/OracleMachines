from collections import Counter
import copy
import gzip
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_anchored_subsets import (anchored_certificate,check_anchored_subsumption,
    AnchoredImpliedInventory,AnchoredAdditiveInventory)
from experiments.cnf_implied_subsumption import indexed_certificate,check_indexed_subsumption,ImpliedSubsumptionInventory
from experiments.cnf_additive_elimination import AdditiveEliminationInventory
from experiments.cnf_pattern_inventory import encode


class AnchoredSubsetTests(unittest.TestCase):
    def agree(self,cnf):
        old=indexed_certificate(cnf,Counter()); new=anchored_certificate(cnf,Counter())
        self.assertEqual(new,old,cnf)
        self.assertEqual(check_anchored_subsumption(cnf,new,Counter()),check_indexed_subsumption(cnf,old,Counter()))

    def test_exhaustive_ordered_sources_and_duplicates(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(512):self.agree([c for i,c in enumerate(clauses) if mask>>i&1])
        for n in range(4):
            for cnf in itertools.product(clauses,repeat=n):self.agree(cnf)
        for cnf in ([(1,1),(1,2),(1,)],[(1,-1),(1,)], [(),(),(1,)],[(1,2),(2,1)],[]):self.agree(cnf)

        counts=Counter(); anchored_certificate(list(itertools.combinations(range(1,12),3)),counts)
        self.assertEqual(counts['anchor_uniform_width_fallbacks'],1)
        self.assertEqual(counts['anchor_posting_entries'],0)

    def test_random_edits_large_identifiers_and_shared_anchor_adversaries(self):
        rng=random.Random(202611121950)
        for _ in range(250):
            cnf=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,17),rng.randrange(0,7))) for _ in range(rng.randrange(60))]
            self.agree(cnf);rng.shuffle(cnf);self.agree(cnf)
            shifted=[tuple((1 if l>0 else -1)*((1<<130)+abs(l)*123) for l in c) for c in cnf];self.agree(shifted)
        for width in (2,4,8):
            cnf=[tuple(range(1,width))+ (n,) for n in range(20,90)]
            self.agree(cnf+[(1,2,3,20,21,22),(20,),(21,)])

    def test_all_saved_trace_inputs_and_certificates(self):
        with gzip.open('experiments/results/cnf-subset-reuse-trace/calls.json.gz','rt') as f:data=json.load(f)
        self.assertEqual(len(data['sources']),851)
        for cnf in data['sources']:self.agree(cnf)
        for row in data['calls']:
            self.assertEqual(anchored_certificate(data['sources'][row['source']],Counter()),row['certificate'])

    def test_forged_policy_indices_and_mutation_do_not_poison_checking(self):
        cnf=[(2,),(1,),(1,2),(1,2,3)];good=anchored_certificate(cnf,Counter())
        bads=[{},dict(kept=[True],removed=[]),dict(kept=[0,1,2,3],removed=[]),dict(kept=[0,1],removed=[[2,1],[3,1]])]
        for bad in bads:
            with self.assertRaises(ValueError):check_anchored_subsumption(cnf,bad,Counter())
        mutated=copy.deepcopy(good);mutated['kept'].append(3)
        with self.assertRaises(ValueError):check_anchored_subsumption(cnf,mutated,Counter())
        self.assertEqual(anchored_certificate(cnf,Counter()),good)
        # The optimized independent checker does not consult the old search.
        with patch('experiments.cnf_anchored_subsets.indexed_certificate',side_effect=AssertionError('old search')):
            check_anchored_subsumption(cnf,good,Counter())

    def test_inventory_byte_identity_restart_and_forged_origins(self):
        sources=[[(-4,-1),(-3,-1,2),(1,2)],[(1,2,3),(-1,2),(-2,3),(-3,1)]]
        for old_cls,new_cls,options in ((ImpliedSubsumptionInventory,AnchoredImpliedInventory,dict(max_depth=0)),
            (AdditiveEliminationInventory,AnchoredAdditiveInventory,dict(max_depth=0,clause_growth_limit=2))):
            with tempfile.TemporaryDirectory() as tmp:
                a,b=Path(tmp)/'a.db',Path(tmp)/'b.db';old=old_cls(a,**options);new=new_cls(b,**options)
                for source in sources:
                    x,y=old.inspect(source),new.inspect(source)
                    for field in ('root','profile','summary'):self.assertEqual(encode(x[field]),encode(y[field]))
                old.close();new.close();self.assertEqual(a.read_bytes(),b.read_bytes());snapshot=b.read_bytes()
                new=new_cls(b,**options)
                for source in sources:self.assertFalse(new.inspect(source)['metrics'].get('inserted_nodes',0))
                key=next(k for k,p in new.db.execute('SELECT id,payload FROM cnf_patterns_v1') if '"implied"' in p)
                node=copy.deepcopy(new._load(key))
                if node['subsumption'].get('implied',{}).get('implications'):
                    node['subsumption']['implied']['implications'][0]['attempt']=99999
                    with self.assertRaises(ValueError):new._check(key,node)
                new.close();self.assertEqual(snapshot,b.read_bytes())


if __name__=='__main__':unittest.main()
