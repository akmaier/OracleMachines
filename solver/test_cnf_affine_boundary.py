from collections import Counter
from copy import deepcopy
from itertools import product
import json,random,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import cnf_affine_boundary as k
from experiments.cnf_affine_boundary_panel import hidden_pairs,panel,parity
from experiments.cnf_fresh_seed_panel import truth,parity_prism


class AffineBoundaryTests(unittest.TestCase):
    def check(self,source):
        c=Counter();p,d=k.discover(source,c)
        if p is not None:
            r=k.check_certificate(source,p)
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return p,d,c

    def test_exhaustive_two_variable_cnfs(self):
        clauses=[list(c) for signs in product((-1,0,1),repeat=2) if (c:=tuple((i+1)*s for i,s in enumerate(signs) if s))]
        for bits in range(1<<len(clauses)):self.check([c for i,c in enumerate(clauses) if bits>>i & 1])
        self.check([[]])

    def test_seeded_affine_mixtures_and_signed_sparse_names(self):
        rng=random.Random(2711270137)
        for _ in range(80):
            n=rng.randrange(3,8);source=[]
            for _ in range(rng.randrange(1,5)):source+=parity(rng.sample(range(1,n+1),rng.randrange(1,4)),rng.randrange(2))
            source += [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(1,4))] for _ in range(rng.randrange(1,8))]
            self.check(source)
            ren={i:(101+7*i)*rng.choice((-1,1)) for i in range(1,n+1)}
            self.check([[(1 if l>0 else -1)*ren[abs(l)] for l in c] for c in reversed(source)])

    def test_hidden_directions_and_connected_crossing_edit(self):
        for pairs in (0,1,3):
            for sat in (False,True):
                p,d,c=self.check(hidden_pairs(pairs,sat));self.assertEqual(d['free'],5+pairs)
                self.assertEqual(d['boundary_rank'],5)
                if not sat:self.assertEqual(c['boundary_candidates'],32)
        source=hidden_pairs(6,False);p,d=k.discover(source)
        self.assertFalse(k.check_certificate(source,p)['answer']);self.assertEqual((d['free'],d['boundary_rank']),(11,5))
        p,d=k.discover(hidden_pairs(6,True)+[[8,-9,2]])
        self.assertTrue(k.check_certificate(hidden_pairs(6,True)+[[8,-9,2]],p)['answer']);self.assertEqual(d['boundary_rank'],6)

    def test_zero_boundary_and_cap_are_distinct(self):
        p,d=k.discover(parity_prism(10,False));self.assertEqual((d['free'],d['boundary_rank']),(11,0))
        self.assertTrue(k.check_certificate(parity_prism(10,False),p)['answer'])
        p,d=k.discover(hidden_pairs(3,False),boundary_limit=4);self.assertIsNone(p);self.assertEqual(d['status'],'boundary-cap')
        p,d=k.discover(hidden_pairs(3,False),variables=1);self.assertIsNone(p);self.assertEqual(d['status'],'size-cap')
        for bad in (-1,9,True):
            with self.assertRaises(ValueError):k.discover([[1]],boundary_limit=bad)

    def test_tampered_space_image_and_exhaustion_fail(self):
        source=hidden_pairs(1,False);proof,_=k.discover(source)
        mutations=[lambda p:p['image'].pop(),lambda p:p['image'].append(p['image'][0]),
                   lambda p:p['space']['directions'].pop(),lambda p:p['space'].__setitem__('particular',1),
                   lambda p:p['decision']['rejected'].pop(),lambda p:p['decision']['rejected'].__setitem__(0,0),
                   lambda p:p['affine']['leftovers'].pop(),lambda p:p['cnf'].pop()]
        for mutate in mutations:
            p=deepcopy(proof);mutate(p)
            with self.assertRaises(ValueError):k.check_certificate(source,p)
        with self.assertRaises(ValueError):k.check_certificate(source[:-1],proof)

    def test_nonzero_projected_vectors_can_still_be_dependent(self):
        source=hidden_pairs(1,False);p,_=k.discover(source);keep=k.boundary_mask(p['cnf'],p['affine'])
        self.assertTrue(all(v & keep for v in p['space']['directions']))
        self.assertGreater(len(p['space']['directions']),len(p['image']))
        p['image']=list(range(len(p['space']['directions'])))
        with self.assertRaisesRegex(ValueError,'Dependent'):k.check_certificate(source,p)

    def test_serialized_cold_check_needs_no_discovery(self):
        for source in (hidden_pairs(6,False),hidden_pairs(6,True),parity_prism(4,True)):
            p,_=k.discover(source);p=json.loads(json.dumps(p))
            with patch.object(k,'bounded_extract',side_effect=AssertionError('acquisition')),patch.object(k,'image_basis',side_effect=AssertionError('acquisition')):
                k.check_certificate(source,p)

    def test_frozen_panel_and_exact_repeat_sources(self):
        rows,desc=panel();out=Path('experiments/results/cnf-affine-boundary')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()))
        self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))
        byid={r['id']:r for r in rows}
        for row in rows:
            if 'repeat_of' in desc[row['id']]:
                self.assertEqual(k.native.normalize(row['source'])[0],k.native.normalize(byid[desc[row['id']]['repeat_of']]['source'])[0])


if __name__=='__main__':unittest.main()
