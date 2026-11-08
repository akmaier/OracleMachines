from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_affine_patterns import AffinePatternInventory, check_affine, complete_half, extract_affine
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise


class AffinePatternTests(unittest.TestCase):
    def inspect_checked(self, h, source):
        r = h.inspect(source)
        check_pointwise(h, r['root']['key'])
        node = h._load(r['root']['key'])
        cert = r['profile']['evidence']['explicit_affine']
        summary = check_affine(node['cnf'], cert, Counter())
        if summary['pure']:
            self.assertEqual(any(holds(node['cnf'], a) for a in assignments(node['cnf'])), not summary['inconsistent'])
        if summary['inconsistent']:
            self.assertFalse(any(holds(node['cnf'], a) for a in assignments(node['cnf'])))
        return r, cert, summary

    def test_exhaustive_two_variable_and_full_three_variable_support(self):
        h = AffinePatternInventory(max_depth=0)
        for clauses in ([tuple(s*(i+1) for i, s in enumerate(signs) if s)
                         for signs in itertools.product((-1, 0, 1), repeat=2)],
                        parity((1, 2, 3), 0)+parity((1, 2, 3), 1)):
            for mask in range(1 << len(clauses)):
                self.inspect_checked(h, [c for i, c in enumerate(clauses) if mask >> i & 1])
        h.close()

    def test_equations_overlapping_supports_and_conflicting_dependencies(self):
        h = AffinePatternInventory(max_depth=0)
        for source in (parity((1, 2, 3, 4), 1)+parity((3, 4, 5, 6), 1),
                       parity((1, 2), 0)+parity((2, 3), 0)+parity((1, 3), 1),
                       parity(range(1, 7), 0)+parity(range(1, 7), 1)):
            r, _, summary = self.inspect_checked(h, source)
            self.assertTrue(summary['pure'])
            self.assertTrue(r['summary']['closed'])
        self.assertTrue(summary['inconsistent'])
        h.close()

    def test_couplings_are_preserved_and_not_declared_easy(self):
        h = AffinePatternInventory(max_depth=0)
        source = parity((1, 2, 3, 4), 1)+parity((5, 6, 7, 8), 1)+[(1, 5)]
        r, cert, summary = self.inspect_checked(h, source)
        self.assertEqual(len(cert['equations']), 2)
        self.assertEqual(summary['leftover_clauses'], 1)
        self.assertEqual(summary['interface_variables'], [1, 5])
        self.assertFalse(r['summary']['closed'])
        self.assertEqual(r['profile']['outcomes']['explicit_affine'], 'excluded')
        # Contradiction in a checked subsystem suffices even with arbitrary leftovers.
        source += parity((1, 2, 3, 4), 0)
        r, _, summary = self.inspect_checked(h, source)
        self.assertTrue(summary['inconsistent'])
        self.assertTrue(r['summary']['closed'])
        h.close()

    def test_missing_and_added_sign_patterns_retain_exact_meaning(self):
        h = AffinePatternInventory(max_depth=1)
        source = parity((1, 2, 3, 4), 1)
        for edited in (source[:-1], source+[parity((1, 2, 3, 4), 0)[0]],
                       [tuple(c)+(5,) for c in source]+[(-5,)]):
            _, _, summary = self.inspect_checked(h, edited)
            self.assertFalse(summary['pure'])
        h.close()

    def test_random_mixtures_conditioning_and_arbitrary_renaming(self):
        rng = random.Random(2026110821)
        h = AffinePatternInventory(max_depth=2)
        for _ in range(60):
            source = parity(rng.sample(range(1, 7), 3), rng.randrange(2))
            source += [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(1, 5)))
                       for _ in range(rng.randrange(1, 12))]
            r, _, _ = self.inspect_checked(h, source)
            variables = list(range(1, 7));rng.shuffle(variables)
            rename = dict(zip(range(1, 7), (v*101+13 for v in variables)))
            variant = [tuple(rename[abs(lit)]*(1 if lit > 0 else -1) for lit in reversed(c)) for c in reversed(source)]
            r2, _, _ = self.inspect_checked(h, variant+variant[:2]+[(999, -999)])
            self.assertEqual(r['profile']['cell'], r2['profile']['cell'])
        h.close()

    def test_large_width_and_no_assignment_enumeration_cap(self):
        self.assertTrue(complete_half(512, 10))
        self.assertFalse(complete_half(3, 10**12))
        cnf, _ = normalize([tuple(range(1, 20001))], Counter())
        counts = Counter();cert = extract_affine(cnf, counts)
        self.assertEqual(cert['leftovers'], [0])
        self.assertEqual(counts['affine_grouping_literals'], 20000)
        h = AffinePatternInventory(max_depth=0, parity_width=3)
        r = h.inspect(parity(range(1, 11), 1))
        self.assertEqual(r['profile']['outcomes']['single_parity'], 'unresolved')
        self.assertEqual(r['profile']['outcomes']['explicit_affine'], 'recognized')
        h.close()

    def test_forged_extraction_and_reduction_fail(self):
        source = parity((1, 2), 0)+parity((2, 3), 0)+parity((1, 3), 1)+[(1, 2, 3)]
        cnf, _ = normalize(source, Counter())
        cert = extract_affine(cnf, Counter())
        check_affine(cnf, cert, Counter())
        mutations = []
        bad = copy.deepcopy(cert);bad['equations'][0]['rhs'] ^= 1;mutations.append(bad)
        bad = copy.deepcopy(cert);bad['equations'][0]['clauses'].pop();mutations.append(bad)
        bad = copy.deepcopy(cert);bad['equations'][0]['clauses'].append(bad['equations'][0]['clauses'][0]);mutations.append(bad)
        bad = copy.deepcopy(cert);bad['leftovers'] = [];mutations.append(bad)
        bad = copy.deepcopy(cert);bad['reductions'][-1]['using'] = [];mutations.append(bad)
        bad = copy.deepcopy(cert);bad['reductions'][-1]['rhs'] ^= 1;mutations.append(bad)
        bad = copy.deepcopy(cert);bad['reductions'][0]['using'] = [0];mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):
                check_affine(cnf, bad, Counter())
        h = AffinePatternInventory(max_depth=0)
        bad = copy.deepcopy(cert);bad['leftovers'] = []
        with patch('experiments.cnf_affine_patterns.extract_affine', return_value=bad):
            with self.assertRaisesRegex(ValueError, 'coupling clause'):
                h.inspect(source)
        h.close()

    def test_cold_replay_versions_and_source_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'patterns.sqlite3'
            source = parity((1, 2, 3, 4), 0)+parity((1, 2, 3, 4), 1)
            old = PatternInventory(path, max_depth=0)
            before = old.inspect(source)
            saved = list(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h = AffinePatternInventory(path, max_depth=0)
            after = h.inspect(source)
            self.assertNotEqual(before['root']['key'], after['root']['key'])
            self.assertFalse(before['summary']['closed']);self.assertTrue(after['summary']['closed'])
            for key, payload in saved:
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()[0], payload)
            h.close();raw = path.read_bytes()
            for cls, expected in ((PatternInventory, before), (AffinePatternInventory, after)):
                h = cls(path, max_depth=0)
                actual = h.inspect(source)
                self.assertEqual(actual['root'], expected['root'])
                self.assertEqual(actual['metrics'].get('inserted_nodes', 0), 0)
                self.assertEqual(actual['metrics']['inserted_sources'], 0)
                h.close()
            self.assertEqual(raw, path.read_bytes())
            h = AffinePatternInventory(path, max_depth=0)
            key = after['root']['key'];bad = copy.deepcopy(h._load(key))
            bad['profile']['evidence']['explicit_affine']['reductions'][0]['rhs'] ^= 1
            h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (json.dumps(bad), key))
            h.db.commit();h.close()
            h = AffinePatternInventory(path, max_depth=0)
            with self.assertRaisesRegex(ValueError, 'pattern certificate'):
                h.inspect(source)
            h.close()


if __name__ == '__main__':
    unittest.main()
