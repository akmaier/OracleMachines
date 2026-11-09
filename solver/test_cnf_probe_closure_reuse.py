from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_closure_reuse import (
    ProbeClosureReuseInventory, batch_inactive, discover_reuse_probes,
    check_reuse_probes, expand_references)
from experiments.cnf_probe_learning import ProbeLearningInventory, discover_learning_probes, check_learning_probes
from experiments.cnf_residual_dag import normalize
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_probe_learning import learning_source, equivalence_source, check_fibers


def active_source():
    return [(-8, -7, 3), (-8, -6, 5), (-8, -2, 3), (-8, -1), (-7, 2, 8),
            (-6, -3, 2), (-6, 4, 7), (-5, 3), (-4, 5, 7), (-3, 5, 7),
            (-2, -1, 6), (-2, 1, 3), (3, 5, 7), (4, 5), (6, 8)]


def expanded_result(result):
    if result['status'] not in ('learned', 'learning_clear'):
        return result
    return dict(result, continuation=expand_references(result['continuation'], result['attempts']))


def check_matched(source, cap=4):
    cnf, _ = normalize(source)
    before, after = Counter(), Counter()
    baseline = discover_learning_probes(cnf, 4, cap, before)
    reused = discover_reuse_probes(cnf, 4, cap, after)
    a = check_learning_probes(cnf, baseline, 4, cap, Counter())
    b = check_reuse_probes(cnf, reused, 4, cap, Counter())
    assert a == b
    assert baseline['status'] == reused['status']
    assert before['probe_attempts'] == after['probe_attempts']
    if 'continuation' in baseline:
        assert baseline['attempts'] == reused['attempts']
        assert baseline['batch'] == reused['batch']
        assert baseline['continuation']['status'] == reused['continuation']['status']
        assert baseline['continuation'].get('witness') == reused['continuation'].get('witness')
    # A separate full checker verifies every expanded reference from scratch.
    check_fibers(cnf, expanded_result(reused), 4, cap)
    return reused, after


class ProbeClosureReuseTests(unittest.TestCase):
    def test_exhaustive_small_matched_fibers(self):
        for variables, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses, count):
                    for cap in (0, 1, 4):
                        check_matched(source, cap)

    def test_inactive_satisfied_unassigned_active_and_conflicting_delta(self):
        attempt = dict(variable=1, value=False,
                       certificate=dict(units=[[2, 0]], conflict=None, pure_rounds=[]))
        for clause, expected in (([1, 2], True), ([3, 4], True), ([-2, 3], False), ([1, -2], False)):
            self.assertEqual(batch_inactive(attempt, [dict(clause=clause)], Counter()), expected)
        for bad in (dict(units=[], conflict=0, pure_rounds=[]),
                    dict(units=[], conflict=None, pure_rounds=[[2]])):
            self.assertFalse(batch_inactive(dict(attempt, certificate=bad), [], Counter()))

    def test_fresh_and_active_probes_preserved(self):
        totals = Counter()
        for source in (learning_source(), equivalence_source(), active_source(), [(-4, -1), (-3, -1, 2), (1, 2)]):
            result, counts = check_matched(source)
            totals.update(counts)
            h = ProbeClosureReuseInventory(max_depth=0)
            r = h.inspect(source); check_fused_tree(h, r['root']['key']); h.close()
            self.assertIn(result['status'], ('learned', 'learning_clear'))
        for name in ('reused_continuation_probes', 'fresh_continuation_probes', 'active_continuation_probes'):
            self.assertGreater(totals[name], 0)

    def test_random_signed_mixtures_and_source_edits(self):
        rng = random.Random(20261109033545)
        sources = [learning_source(), equivalence_source()]
        for _ in range(60):
            sources.append([tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.choice((2, 3, 4))))
                            for _ in range(rng.randrange(8, 24))])
        h = ProbeClosureReuseInventory(max_depth=2)
        for source in sources:
            variables = sorted({abs(l) for c in source for l in c})
            permutation = rng.sample(variables, len(variables))
            names = {v: p*31*rng.choice((-1, 1)) for v, p in zip(variables, permutation)}
            signed = [tuple(names[abs(l)]*(1 if l > 0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source, signed, source+[(1,)], source[:-1]):
                check_matched(changed)
                result = h.inspect(changed); check_fused_tree(h, result['root']['key'])
        h.close()

    def test_reference_corruption_and_active_reuse_rejected(self):
        cnf, _ = normalize(active_source())
        result = discover_reuse_probes(cnf, 4, 4, Counter())
        refs = [i for i, a in enumerate(result['continuation']['attempts']) if 'reuse' in a['certificate']]
        self.assertTrue(refs)
        for certificate in ({'reuse': False}, {'reuse': -1}, {'reuse': 999}, {'reuse': 0, 'units': []}):
            bad = copy.deepcopy(result); bad['continuation']['attempts'][refs[0]]['certificate'] = certificate
            with self.assertRaises(ValueError): check_reuse_probes(cnf, bad, 4, 4, Counter())
        bad = copy.deepcopy(result)
        first = bad['continuation']['attempts'][refs[0]]
        first['certificate']['reuse'] = (first['certificate']['reuse'] + 1) % len(bad['attempts'])
        with self.assertRaisesRegex(ValueError, 'different assumption'): check_reuse_probes(cnf, bad, 4, 4, Counter())
        bad = copy.deepcopy(result)
        ref = bad['continuation']['attempts'][refs[0]]['certificate']['reuse']
        bad['attempts'][ref]['certificate']['units'].append([999, 999])
        with self.assertRaises(ValueError): check_reuse_probes(cnf, bad, 4, 4, Counter())
        bad = copy.deepcopy(result); bad['batch'][0]['clause'][0] *= -1
        with self.assertRaises(ValueError): check_reuse_probes(cnf, bad, 4, 4, Counter())
        with self.assertRaises(ValueError): check_reuse_probes(cnf[:-1], result, 4, 4, Counter())
        # A matching assumption is insufficient when the additions activate it.
        tested = 0
        for i, a in enumerate(result['continuation']['attempts']):
            for j, old in enumerate(result['attempts']):
                if ((a['variable'], a['value']) == (old['variable'], old['value']) and
                        not batch_inactive(old, result['batch'], Counter())):
                    bad = copy.deepcopy(result); bad['continuation']['attempts'][i]['certificate'] = dict(reuse=j)
                    with self.assertRaisesRegex(ValueError, 'invalidates'): check_reuse_probes(cnf, bad, 4, 4, Counter())
                    tested += 1
        self.assertGreater(tested, 0)

    def test_cold_coexistence_reference_corruption_and_disabled_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'
            old = ProbeLearningInventory(path, max_depth=0)
            old.inspect(equivalence_source()); prior = dict(old.db.execute('SELECT * FROM cnf_patterns_v1')); old.close()
            h = ProbeClosureReuseInventory(path, max_depth=0); result = h.inspect(equivalence_source())
            key = result['root']['key']; node = copy.deepcopy(h._load(key))
            check_fused_tree(h, key)
            for model in ({}, {1: 1}):
                with self.assertRaises(ValueError): h.lift(key, model)
            for k, v in prior.items():
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (k,)).fetchone()[0], v)
            h.close(); raw = path.read_bytes()
            h = ProbeClosureReuseInventory(path, max_depth=0)
            self.assertEqual(h.inspect(equivalence_source())['metrics'].get('inserted_nodes', 0), 0)
            h.close(); self.assertEqual(raw, path.read_bytes())
            a = next(a for a in node['profile']['probing']['continuation']['attempts'] if 'reuse' in a['certificate'])
            a['certificate']['reuse'] = 999
            h = ProbeClosureReuseInventory(path, max_depth=0)
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(node), key))
            h.close(); h = ProbeClosureReuseInventory(path, max_depth=0)
            with self.assertRaises(ValueError): h.inspect(equivalence_source())
            h.close()
        for cap in (0, 1, 4): check_matched(learning_source(), cap)
