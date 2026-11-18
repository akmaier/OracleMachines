from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random
import unittest
from experiments.cnf_affine_completion import complete,select
from experiments.cnf_affine_patterns import extract_affine
from experiments.cnf_affine_clause import make_space
from experiments.cnf_cover_probe import select as previous
from experiments.cnf_cross_family import generate
from experiments.cnf_positive_child import publish_model
from experiments.cnf_residual_dag import ResidualSolver,holds


def parity(variables,rhs):
    return [[-v if bit else v for v,bit in zip(variables,bits)]
            for bits in product((False,True),repeat=len(variables)) if sum(bits)%2!=rhs]


def truth(source):
    variables=sorted({abs(l) for c in source for l in c})
    return any(holds(source,dict(zip(variables,bits))) for bits in product((False,True),repeat=len(variables)))


class AffineCompletionTests(unittest.TestCase):
    def solver(self,**kw):
        s=ResidualSolver(**kw);self.addCleanup(s.close);return s

    def test_gray_walk_reuses_basis_and_packed_leftovers(self):
        source=parity((1,2),0)+[[1,3],[-1,3]];s=self.solver(node_limit=0);counts=Counter()
        with patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Publication')):
            choice,e=complete(s,source,counts)
        self.assertEqual(e['status'],'model');self.assertEqual(e['accepted']['index'],2)
        self.assertEqual(counts['affine_bridge_candidates'],3);self.assertEqual(counts['affine_bridge_basis_xors'],2)
        self.assertEqual(counts['affine_bridge_packed_literals'],4)
        self.assertTrue(holds(source,dict(choice['model'])))
        with patch.object(s,'_visit',side_effect=AssertionError('Native search')):
            self.assertTrue(publish_model(s,source,choice)['answer'])

    def test_negative_evidence_is_retained_without_native_publication(self):
        s=self.solver()
        exhausted=parity((1,2),0)+[[1,3],[1,-3],[-2,4],[-2,-4]]
        for source,status in ((exhausted,'space-exhausted'),(parity((1,2,3),0)+parity((1,2,3),1),'linear-conflict')):
            choice,e=complete(s,source)
            self.assertIsNone(choice);self.assertEqual(e['status'],status);self.assertFalse(truth(source))
            self.assertEqual(s.archive_storage()[0],0)
        raw=generate('coupled-parity',20,1,7);choice,t=select(s,raw)
        if 'affine_bridge' in t and t['affine_bridge']['status']!='model':self.assertEqual(choice,previous(s,raw)[0])

    def test_cap_precedes_basis_and_no_equations_is_a_miss(self):
        s=self.solver();source=parity((1,2,3),0)
        with patch('experiments.cnf_affine_completion.make_space',side_effect=AssertionError('Basis beyond cap')):
            choice,e=complete(s,source,free_limit=1)
        self.assertIsNone(choice);self.assertEqual(e['status'],'free-cap');self.assertIsNone(e['space'])
        choice,e=complete(s,source[:-1]);self.assertIsNone(choice);self.assertEqual(e['status'],'no-equations')
        for bad in (-1,17,True):
            with self.assertRaises(ValueError):complete(s,source,free_limit=bad)

    def test_forged_extraction_or_incomplete_basis_is_rejected(self):
        source=parity((1,2),0)+[[1,3],[-1,3]];s=self.solver();cnf,_,_=s._canonical(source)
        a=extract_affine(cnf,Counter());bad=deepcopy(a);bad['leftovers']=[]
        with patch('experiments.cnf_affine_completion.extract_affine',return_value=bad):
            with self.assertRaises(ValueError):complete(s,source)
        space=make_space(3,a,Counter());space['directions'].pop()
        with patch('experiments.cnf_affine_completion.make_space',return_value=space):
            with self.assertRaises(ValueError):complete(s,source)
        self.assertEqual(s.archive_storage()[0],0)

    def test_forced_prefix_and_signed_coordinates(self):
        source=generate('coupled-parity',16,0,7)
        for raw in (source,[[10000]]+source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
            s=self.solver();counts=Counter();choice,t=select(s,raw,counts=counts)
            self.assertEqual(t['reason'],'affine-positive-model');self.assertTrue(holds(raw,dict(choice['model'])))
            self.assertEqual(counts['fallback_trace_reuses'],0)
            self.assertTrue(publish_model(s,raw,choice)['answer'])

    def test_known_disabled_routes_and_cold_native_replay(self):
        source=generate('coupled-parity',16,0,7)
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:
                self.assertEqual(select(s,source,0),previous(s,source,0))
                choice,t=select(s,source);publish_model(s,source,choice)
                before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                self.assertEqual(select(s,source)[1]['reason'],'known-target')
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')):self.assertTrue(s.solve(source)['answer'])
            finally:s.close()

    def test_exhaustive_full_three_variable_support_and_coordinates(self):
        pool=parity((1,2,3),0)+parity((1,2,3),1)
        for mask in range(256):
            source=[c for i,c in enumerate(pool) if mask>>i&1];answer=truth(source)
            for raw in (source,[[-13*l for l in c[::-1]] for c in source[::-1]]):
                s=ResidualSolver()
                try:
                    choice,e=complete(s,raw)
                    if choice:self.assertTrue(answer);self.assertTrue(holds(raw,dict(choice['model'])))
                    elif e['status'] in ('linear-conflict','space-exhausted'):self.assertFalse(answer)
                    else:self.assertIn(e['status'],('no-equations','free-cap'))
                finally:s.close()

    def test_random_affine_mixtures_against_all_assignments(self):
        rng=random.Random(2026111804)
        for _ in range(64):
            source=parity(tuple(rng.sample(range(1,7),3)),rng.randrange(2))
            source += [[rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(1,5))] for _ in range(rng.randrange(0,13))]
            s=ResidualSolver()
            try:
                choice,e=complete(s,source)
                self.assertEqual(choice is not None,truth(source))
                if choice:self.assertTrue(holds(source,dict(choice['model'])))
            finally:s.close()


if __name__=='__main__':unittest.main()
