from collections import Counter, defaultdict
import copy
import itertools
import random
import unittest
from unittest.mock import patch

from experiments.cnf_affine_clause import discover, check_certificate, attach
from experiments.cnf_affine_patterns import AffinePatternInventory, extract_affine
from experiments.cnf_residual_dag import holds, normalize
from experiments.cnf_route_composition import compose, verify_plan
from solver.test_cnf_pattern_inventory import assignments, parity


def canonical(source):
    return [list(c) for c in normalize(source, Counter())[0]]


class AffineClauseTests(unittest.TestCase):
    def checked(self, source):
        cnf = canonical(source); proof = discover(cnf)
        if proof is not None:
            result = check_certificate(proof, expected_cnf=cnf)
            self.assertEqual(result['sat'], any(holds(cnf, a) for a in assignments(cnf)))
            if result['sat']: self.assertTrue(holds(cnf, result['model']))
        return proof

    def test_exhaustive_small_formulas(self):
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        accepted = 0
        for mask in range(1 << len(clauses)):
            accepted += self.checked([c for i,c in enumerate(clauses) if mask >> i & 1]) is not None
        self.assertGreater(accepted, 0)
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=3)]
        for k in range(4):
            for formula in itertools.combinations(clauses, k): self.checked(formula)

    def test_seeded_affine_mixtures_and_unlabelled_variants(self):
        rng = random.Random(2026111315)
        for _ in range(160):
            n = rng.randrange(2, 8); raw = []
            for _ in range(rng.randrange(1, 6)):
                raw += parity(rng.sample(range(1, n+1), rng.randrange(1, min(n, 4)+1)), rng.randrange(2))
            raw += [tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,n+1), rng.randrange(2,n+1)))]
            p = self.checked(raw); self.assertIsNotNone(p)
            labels = rng.sample(range(11, 1000), n); signs = [rng.choice((-1,1)) for _ in labels]
            renamed = [[labels[abs(l)-1]*signs[abs(l)-1]*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(raw)]
            q = self.checked(renamed); self.assertIsNotNone(q)
            self.assertEqual(check_certificate(p)['sat'], check_certificate(q)['sat'])

    def test_empty_and_linear_conflict(self):
        self.assertTrue(check_certificate(self.checked([]))['sat'])
        for cnf in ([[]], [[1],[-1]], parity((1,2),0)+parity((2,3),0)+parity((1,3),1)):
            p = self.checked(cnf); self.assertEqual(p['decision']['kind'], 'linear_conflict')
            self.assertFalse(check_certificate(p)['sat'])

    def test_particular_repair_and_free_clause_variables(self):
        base = parity((1,2,3),0)
        p = self.checked(base+[(-1,-2,-3,-4)]); self.assertIsNone(p['decision']['repair'])
        p = self.checked(base+[(1,2,3,4)]); self.assertIsNotNone(p['decision']['repair'])
        self.assertTrue(check_certificate(p)['sat'])

    def test_unsat_with_nonempty_kernel(self):
        p = self.checked([[-1],[-2], [1,2]]+parity((3,4,5),0))
        self.assertFalse(p['decision']['sat']); self.assertEqual(len(p['decision']['space']['directions']),2)
        bad = copy.deepcopy(p); bad['decision']['sat'] = True; bad['decision']['model'] = 0
        with self.assertRaises(ValueError): check_certificate(bad)

    def test_multiple_clauses_are_unknown_not_unsat(self):
        cnf = canonical(parity((1,2,3),0)+[(1,4,5),(-1,4,5)])
        self.assertIsNone(discover(cnf))
        proof = discover(canonical(parity((1,2,3),0)+[(1,4,5)]))
        proof['cnf'] = cnf; proof['affine'] = extract_affine(cnf, Counter())
        with self.assertRaisesRegex(ValueError, 'More than one'): check_certificate(proof)

    def test_missing_kernel_direction_cannot_prove_unsat(self):
        p = discover(canonical(parity((1,2,3),0)+[(1,2,3,4)]))
        p['decision'].update(sat=False, repair=None, model=None)
        p['decision']['space']['directions'] = []
        with self.assertRaises(ValueError): check_certificate(p)

    def test_certificate_tampering(self):
        p = discover(canonical(parity((1,2,3),0)+[(1,2,3,4)]))
        mutations = [lambda b: b['decision']['space']['directions'].pop(),
            lambda b: b['decision']['space']['directions'].__setitem__(0, b['decision']['space']['directions'][1]),
            lambda b: b['decision']['space'].__setitem__('particular', 1 << 4),
            lambda b: b['decision']['space'].__setitem__('particular', True),
            lambda b: b['decision']['space']['directions'].__setitem__(0, 2),
            lambda b: b['decision'].__setitem__('repair', 99),
            lambda b: b['decision'].__setitem__('repair', True),
            lambda b: b['decision'].__setitem__('model', 0),
            lambda b: b['affine'].__setitem__('leftovers', []),
            lambda b: b['affine']['reductions'][0].__setitem__('rhs', 1)]
        for mutate in mutations:
            b = copy.deepcopy(p); mutate(b)
            with self.assertRaises(ValueError): check_certificate(b)
        with self.assertRaises(ValueError): check_certificate(p, expected_cnf=[[1]])
        p['decision'] = dict(kind='linear_conflict', row=0)
        with self.assertRaises(ValueError): check_certificate(p)

    def test_malformed_source_and_sparse_mask_guard(self):
        for cnf in ([[1,1]], [[1,-1]], [[1],[1]], [[0]], [[True]], [[10**12]], [(1,)], None):
            with self.assertRaises(ValueError): discover(cnf)

    def test_reuse_checks_equations_and_cold_replay_needs_no_discovery(self):
        cnf = canonical(parity((1,2,3),0)+[(1,2,3,4)]); p = discover(cnf)
        counts = Counter()
        with patch('experiments.cnf_affine_clause.extract_affine', side_effect=AssertionError('discovery')):
            q = discover(cnf, counts, affine=p['affine'], space=p['decision']['space'])
            self.assertEqual(p, q); check_certificate(q)
        self.assertEqual(counts['affine_clause_reused_extractions'],1)
        self.assertEqual(counts['affine_space_vectors_constructed'],0)
        # Same kernel survives a clause edit; changing rhs must invalidate the particular.
        edited = canonical(parity((1,2,3),0)+[(-1,-2,-3,-4)])
        self.assertIsNotNone(discover(edited, space=p['decision']['space']))
        changed = canonical(parity((1,2,3),1)+[(1,2,3,4)])
        with self.assertRaises(ValueError): discover(changed, space=p['decision']['space'])

    def test_external_route_exact_binding_and_no_inventory_mutation(self):
        h = AffinePatternInventory(max_depth=0)
        cnf = parity((1,2,3,4),0)+parity((5,6,7,8),1)+[(1,5)]
        key = h.inspect(cnf)['root']['key']; node = h._load(key)
        class Routes:
            by_source = defaultdict(list)
        routes = Routes(); self.assertEqual(compose(h, [key], routes, Counter())[0], [False])
        before = list(h.db.execute('SELECT * FROM cnf_patterns_v1'))
        record = dict(source=key, proof=discover(node['cnf']))
        attach(h, routes, record, Counter()); attach(h, routes, record, Counter())
        self.assertEqual(len(routes.by_source[key]),1)
        closed, plan = compose(h, [key], routes, Counter()); self.assertEqual(closed,[True])
        verify_plan(h, plan, [key], routes, Counter())
        self.assertEqual(before, list(h.db.execute('SELECT * FROM cnf_patterns_v1')))
        record['proof'] = discover([[1]])
        with self.assertRaises(ValueError): attach(h, routes, record, Counter())
        h.close()


if __name__ == '__main__': unittest.main()
