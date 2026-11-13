from collections import Counter
import copy
from itertools import combinations, product
import json
import unittest
from unittest.mock import patch

from experiments.cnf_lemma_transport import FORMAT, check_certificate, checked_augmentation
from experiments.cnf_residual_dag import normalize, restrict, holds
from experiments.cnf_simplification import discover_simplification, check_simplification
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_binary_paths import discover_binary_paths, check_binary_paths


def trace(cnf, variable, value):
    return dict(variable=variable, value=value, certificate=discover_simplification(
        restrict(cnf, {variable: value}, Counter()), Counter(), pure=False))


def certificate(cnf, attempt):
    x = attempt['variable'] * (1 if attempt['value'] else -1)
    lemmas = [dict(attempt=0, unit=i, clause=sorted((-x, lit)))
              for i, (lit, _) in enumerate(attempt['certificate']['units'])]
    return dict(format=FORMAT, source=[list(c) for c in cnf], attempts=[attempt] if lemmas else [],
        lemmas=lemmas, steps=[])


def step(kind, raw, **kw):
    target, names = normalize(raw)
    return dict(kind=kind, names=list(names), target=[list(c) for c in target], **kw)


class LemmaTransportTests(unittest.TestCase):
    def fixture(self):
        cnf = [[-1, 2], [-2, 3], [-3, 4], [-1, 2, 5], [4, 6, 7]]
        cert = certificate(cnf, trace(cnf, 1, True))
        proof = discover_binary_paths(cnf, Counter()); target = check_binary_paths(cnf, proof, Counter())
        cert['steps'].append(step('binary_paths', target, certificate=proof, root_limit=64))
        current = cert['steps'][-1]['target']
        target = check_additive_elimination(current, {'variable': 2}, Counter(), clause_growth_limit=2)
        cert['steps'].append(step('eliminate', target, certificate={'variable': 2},
            pair_limit=64, clause_growth_limit=2))
        return cert

    def test_replay_with_no_search_and_exact_binding(self):
        cert = self.fixture(); target = cert['steps'][-1]['target']
        with patch('experiments.cnf_simplification.discover_simplification', side_effect=AssertionError('search')):
            result = check_certificate(json.loads(json.dumps(cert)), expected_source=cert['source'], expected_target=target)
            augmented = checked_augmentation(cert, tuple(map(tuple, target)))
        self.assertIn([-1, 3], result['additions'])
        self.assertIn(0, result['transcript'][1]['lost_support'])
        self.assertEqual(list(map(list, augmented)), target + result['additions'])
        for source, leaf in [(cert['source'][::-1], target), (cert['source'], target + [[1]])]:
            with self.assertRaises(ValueError):
                check_certificate(cert, expected_source=source, expected_target=leaf)

    def test_disappearing_literal_does_not_become_a_stronger_clause(self):
        cnf = [[-1, 2], [2, 3]]; cert = certificate(cnf, trace(cnf, 1, True))
        raw = check_additive_elimination(cnf, {'variable': 1}, Counter())
        cert['steps'] = [step('eliminate', raw, certificate={'variable': 1}, pair_limit=64, clause_growth_limit=1)]
        result = check_certificate(cert)
        self.assertEqual(result['survivors'], [])
        self.assertEqual(result['transcript'][0]['lost_support'], [0])
        # The projected formula permits the surviving variable to be false.
        self.assertTrue(holds(result['target'], {1: False, 2: True}))

    def test_conditioning_uses_all_forced_values_and_discards_satisfied_lemmas(self):
        cnf = [[-1, 2], [-2, 3], [4, 5]]; cert = certificate(cnf, trace(cnf, 1, True))
        a = trace(cnf, 1, True)
        raw, _ = check_simplification(restrict(cnf, {1: True}, Counter()), a['certificate'], Counter(), pure=False)
        cert['steps'] = [step('condition', raw, attempt=a)]
        result = check_certificate(cert)
        self.assertEqual(result['survivors'], [])
        self.assertEqual(result['transcript'][0]['satisfied'], [0, 1])
        self.assertEqual(result['target'], [[1, 2]])

    def test_forged_reasons_mappings_targets_and_projection_are_rejected(self):
        cert = self.fixture(); bad = []
        x = copy.deepcopy(cert); x['lemmas'][0]['clause'] = [1, 2]; bad.append(x)
        x = copy.deepcopy(cert); x['attempts'][0]['certificate']['units'][0][1] = 999; bad.append(x)
        x = copy.deepcopy(cert); x['steps'][0]['names'][0] = 99; bad.append(x)
        x = copy.deepcopy(cert); x['steps'][0]['target'].pop(); bad.append(x)
        x = copy.deepcopy(cert); x['steps'][1]['certificate']['variable'] = None; bad.append(x)
        x = copy.deepcopy(cert); x['steps'][1]['pair_limit'] = 0; bad.append(x)
        x = copy.deepcopy(cert); x['steps'][0]['kind'] = 'arbitrary_equisatisfiable'; bad.append(x)
        x = copy.deepcopy(cert); x['steps'][0]['certificate']['proof'][-1][-1] = 999; bad.append(x)
        for x in bad:
            with self.subTest(certificate=x):
                with self.assertRaises(ValueError): check_certificate(x)

    def test_duplicate_unused_and_noninteger_premises_are_rejected(self):
        cert = self.fixture(); bad = []
        x = copy.deepcopy(cert); x['attempts'].append(x['attempts'][0]); bad.append(x)
        x = copy.deepcopy(cert); x['lemmas'].append(x['lemmas'][0]); bad.append(x)
        x = copy.deepcopy(cert); x['lemmas'][0]['attempt'] = True; bad.append(x)
        x = copy.deepcopy(cert); x['source'][0][0] = False; bad.append(x)
        x = copy.deepcopy(cert); x['attempts'].append(trace(x['source'], 7, False)); bad.append(x)
        for x in bad:
            with self.assertRaises(ValueError): check_certificate(x)

    def test_exhaustive_small_projection_semantics(self):
        # Every pair of distinct width-2/3 clauses on three variables, every
        # clear assumption with a consequence, and every variable projection.
        clauses = [tuple(v * s for v, s in zip(vs, signs))
            for width in (2, 3) for vs in combinations((1, 2, 3), width)
            for signs in product((-1, 1), repeat=width)]
        checked = 0
        for cs in combinations(clauses, 2):
            cnf = [list(c) for c in cs]; support = sorted({abs(l) for c in cnf for l in c})
            for v, b in product(support, (False, True)):
                a = trace(cnf, v, b)
                if a['certificate']['conflict'] is not None or not a['certificate']['units']: continue
                for eliminate in support:
                    cert = certificate(cnf, a)
                    raw = check_additive_elimination(cnf, {'variable': eliminate}, Counter(), clause_growth_limit=4)
                    cert['steps'] = [step('eliminate', raw, certificate={'variable': eliminate},
                        pair_limit=64, clause_growth_limit=4)]
                    result = check_certificate(cert); names = cert['steps'][0]['names']
                    for values in product((False, True), repeat=len(names)):
                        model = dict(enumerate(values, 1))
                        if holds(result['target'], model):
                            self.assertTrue(holds(result['survivors'], model))
                    checked += 1
        self.assertGreater(checked, 1000)


if __name__ == '__main__': unittest.main()
