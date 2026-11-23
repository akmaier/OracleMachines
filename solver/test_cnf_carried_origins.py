from collections import Counter
from copy import deepcopy
from itertools import product
import random
import unittest
from unittest.mock import patch

from experiments import cnf_learned_conditional as learned
from experiments.cnf_carried_origins import OriginIndex, extract, carried_origins
from experiments.cnf_conditional_unit_support import extract as previous, ExtractionBudget
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_residual_dag import FORMAT, normalize, restrict
from experiments.cnf_probed_partition import acquire

CUBE = list(product((-1, 1), (-2, 2), (-3, 3)))


def scanned(root, fixed):
    origins = {}
    for cid, clause in enumerate(root):
        reduced = restrict((clause,), fixed)
        if reduced: origins.setdefault(reduced[0], cid)
    return origins


class CarriedOriginTests(unittest.TestCase):
    def compare(self, source, **kwargs):
        s = ConsequencePrioritySolver(leaves=False, **kwargs)
        self.addCleanup(s.close)
        acquire(s, source, 256)
        before = list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
        old, a = previous(s, source)
        new, b = extract(s, source)
        self.assertEqual(old, new)
        self.assertEqual(before, list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        for field in ('conditional_node_visits', 'conditional_node_literals', 'conditional_slice_steps'):
            self.assertEqual(a.get(field, 0), b.get(field, 0))
        return s, new, a, b

    def test_all_small_sources_and_partial_assignments(self):
        clauses = [(-2,), (-1,), (), (1,), (2,), (-2, -1), (-2, 1), (-1, 2), (1, 2)]
        checks = 0
        for mask in range(512):
            root, _ = normalize([cl for i, cl in enumerate(clauses) if mask >> i & 1])
            for values in product((None, False, True), repeat=2):
                c = Counter(); index = OriginIndex(root, c); state = index.initial; fixed = {}
                for v, bit in enumerate(values, 1):
                    if bit is None: continue
                    parent = deepcopy(state.by_clause)
                    child = index.advance(state, {v: bit})
                    self.assertEqual(parent, state.by_clause)
                    fixed[v] = bit; state = child
                    self.assertEqual(state.by_clause, scanned(root, fixed))
                    self.assertEqual(state.by_id, {cid: cl for cl, cid in state.by_clause.items()})
                checks += 1
        self.assertEqual(checks, 4608)

    def test_smallest_original_id_survives_duplicates_and_future_updates(self):
        root = ((-3, 2), (-1, 2), (2,), (4, 5))
        index = OriginIndex(root, Counter())
        first = index.advance(index.initial, {3: True})
        self.assertEqual(first.by_clause[(2,)], 0)
        second = index.advance(first, {1: True})
        self.assertEqual(second.by_clause[(2,)], 0)
        third = index.advance(second, {2: False})
        self.assertEqual(third.by_clause[()], 0)
        self.assertEqual(third.by_clause, scanned(root, {3: True, 1: True, 2: False}))
        self.assertIn((2,), first.by_clause)

    def test_identity_and_unrelated_assignments_share_state(self):
        root = ((1, 2), (3, 4)); c = Counter(); index = OriginIndex(root, c)
        self.assertIs(index.advance(index.initial, {}), index.initial)
        self.assertIs(index.advance(index.initial, {100: True}), index.initial)
        self.assertEqual(c['origin_copied_map_slots'], 0)

    def test_only_posted_live_representatives_are_scanned(self):
        root = tuple((3*i+1, 3*i+2, 3*i+3) for i in range(100))
        c = Counter(); index = OriginIndex(root, c)
        child = index.advance(index.initial, {1: False})
        self.assertEqual(child.by_clause, scanned(root, {1: False}))
        self.assertEqual(c['origin_scanned_literals'], 3)
        self.assertEqual(c['origin_untouched_representatives'], 99)
        self.assertEqual(c['origin_copied_map_slots'], 200)
        index.release(index.initial, child)
        self.assertEqual(index.live_slots, 200)

    def test_random_branch_orders_and_dense_assignments(self):
        rng = random.Random(202611231648)
        for _ in range(128):
            raw = [tuple((1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1, 10), rng.randrange(1, 5))) for _ in range(20)]
            root, _ = normalize(raw); index = OriginIndex(root, Counter()); fixed = {}; state = index.initial
            variables = rng.sample(range(1, 10), 9)
            for start in (0, 3, 6):
                delta = {v: bool(rng.randrange(2)) for v in variables[start:start+3]}
                child = index.advance(state, delta); fixed.update(delta)
                self.assertEqual(child.by_clause, scanned(root, fixed)); state = child
            for bit in (False, True):
                child = index.advance(index.initial, {variables[0]: bit})
                self.assertEqual(child.by_clause, scanned(root, {variables[0]: bit}))

    def test_extracted_covers_and_unit_ancestors_are_identical(self):
        for source in (CUBE, [(5,)] + CUBE, CUBE + [(7, 8)],
                       [[(1 if l > 0 else -1)*[71, 903, 1047][abs(l)-1] for l in cl] for cl in CUBE]):
            _, _, old, new = self.compare(source)
            self.assertLess(new.get('restriction_literal_visits', 0), old['restriction_literal_visits'])

    def test_component_subset_retains_global_original_representatives(self):
        source = CUBE + [(-1, -2), (7, 8)]
        s = ConsequencePrioritySolver(leaves=False); self.addCleanup(s.close)
        cnf, names, key = s._canonical(source)
        rename = {v: i+1 for i, v in enumerate(names)}
        subset = [tuple(sorted((1 if l > 0 else -1)*rename[abs(l)] for l in cl)) for cl in CUBE]
        child = acquire(s, subset, 256)['result']['root']
        s._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in cnf], answer=False,
            proof=dict(kind='component', clauses=sorted(cnf.index(cl) for cl in subset), child=child)))
        a, _ = previous(s, source); b, counts = extract(s, source)
        self.assertEqual(a, b)
        self.assertGreater(counts['origin_identity_reuses'], 0)

    def test_supported_unsat_small_formulas_match_exactly(self):
        clauses = [(-2,), (-1,), (), (1,), (2,), (-2, -1), (-2, 1), (-1, 2), (1, 2)]
        s = ConsequencePrioritySolver(leaves=False); self.addCleanup(s.close)
        checked = 0
        for mask in range(512):
            source = [cl for i, cl in enumerate(clauses) if mask >> i & 1]
            r = acquire(s, source, 256)
            if r['status'] == 'unsat':
                self.assertEqual(previous(s, source)[0], extract(s, source)[0]); checked += 1
        self.assertGreater(checked, 256)

    def test_limits_positive_origins_and_missing_children_fail_closed(self):
        s, bundle, _, _ = self.compare([(5,)] + CUBE)
        for kwargs in (dict(node_limit=1), dict(literal_limit=1)):
            with self.assertRaises(ExtractionBudget): extract(s, [(5,)] + CUBE, **kwargs)
        for kwargs in (dict(node_limit=0), dict(literal_limit=True)):
            with self.assertRaises(ValueError): extract(s, CUBE, **kwargs)
        acquire(s, [(9,)], 256)
        with self.assertRaises(ValueError): extract(s, [(9,)])
        child = s._read(bundle['origin'])['proof']['child']; original = s._read
        with patch.object(s, '_read', side_effect=lambda key,*a,**kw: None if key == child else original(key,*a,**kw)):
            with self.assertRaises(ValueError): extract(s, [(5,)] + CUBE)

    def test_unsupported_endpoints_stay_unresolved(self):
        s = ConsequencePrioritySolver(); self.addCleanup(s.close)
        source = [(1, 2), (1, -2), (-1, 2), (-1, -2)]
        acquire(s, source, 256)
        a, _ = previous(s, source); b, _ = extract(s, source)
        self.assertEqual(a, b)
        self.assertIn('unresolved', b['tree'])

    def test_scoped_policy_restores_after_exception(self):
        original = learned.extract
        with self.assertRaisesRegex(RuntimeError, 'test'):
            with carried_origins():
                self.assertIs(learned.extract, extract)
                raise RuntimeError('test')
        self.assertIs(learned.extract, original)
