from collections import Counter
from copy import deepcopy
from itertools import combinations, product
from unittest.mock import patch
import json
import unittest
from experiments import cnf_choice_forest as e


def coloring(n, edges, width=3):
    demands = [[1 + width*i + j for j in range(width)] for i in range(n)]
    return demands + [[-demands[a][j], -demands[b][j]] for a, b in edges for j in range(width)]


def certificate(source, demands, cut):
    demands = [sorted(c) for c in demands]
    d, g, c = e.layout(source, demands, Counter())
    tree = e.forest(g, cut, Counter())
    return dict(format=e.FORMAT, empty=False, demands=demands, cutset=cut,
                branches=[e.tables(d, cut, values, c, tree, Counter(), [1000000])
                          for values in product(*(d[i] for i in cut))])


class ChoiceForestTests(unittest.TestCase):
    def test_nonclique_path_previously_missed(self):
        source = [[1,2,3],[4,5,6]] + [[-i,-i-1] for i in range(1,6)]
        self.assertIsNone(e.prior.discover(source)[0])
        proof, _ = e.discover(source)
        self.assertEqual(proof['cutset'], [])
        self.assertTrue(e.check(source, proof)['answer'])

    def test_full_cross_conflict_unsat(self):
        source = [[1,2,3],[4,5,6]] + [[-a,-b] for a in (1,2,3) for b in (4,5,6)]
        proof, _ = e.discover(source)
        self.assertIs(e.check(source, proof)['answer'], False)

    def test_cyclic_coloring_and_two_cutset(self):
        for n, answer, cuts in ((3,True,1), (4,False,2)):
            source = coloring(n, combinations(range(n), 2))
            self.assertIsNone(e.discover(source, cutset_limit=0)[0])
            proof, _ = e.discover(source)
            self.assertEqual(len(proof['cutset']), cuts)
            self.assertIs(e.check(source, proof)['answer'], answer)

    def test_two_color_odd_cycle_given_description(self):
        source = coloring(3, [(0,1),(1,2),(0,2)], 2)
        proof = certificate(source, source[:3], [0])
        self.assertIs(e.check(source, proof)['answer'], False)
        proof['branches'].pop()
        self.assertIsNone(e.check(source, proof)['answer'])

    def test_positive_prefix_remains_authoritative(self):
        source = coloring(3, combinations(range(3), 2))
        proof, _ = e.discover(source)
        proof['branches'] = proof['branches'][:1]
        self.assertIs(e.check(source, proof)['answer'], True)

    def test_empty_and_tautological_support(self):
        for source, answer in (([],True), ([[71,-71]],True), ([[]],False)):
            proof, _ = e.discover(source)
            self.assertIs(e.check(source, proof)['answer'], answer)
        proof, _ = e.discover([[71,-71]])
        self.assertEqual(set(e.check([[71,-71]], proof)['model']), {71})

    def test_sparse_signed_and_duplicate_replay(self):
        source = coloring(4, [(0,1),(1,2),(2,3)])
        mapping = {i: (-1 if i%2 else 1)*(101+17*i) for i in range(1,13)}
        source = [[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source]
        proof, _ = e.discover(source)
        self.assertTrue(e.check(source[::-1] + source[:2], proof)['answer'])

    def test_dense_residual_remains_unrecognized(self):
        source = coloring(5, combinations(range(5), 2))
        proof, diag = e.discover(source)
        self.assertIsNone(proof)
        self.assertEqual(diag['attempts'][0]['reason'], 'no-cutset-at-allowed-size')

    def test_extra_clause_not_discarded(self):
        source = coloring(4, [(0,1),(1,2),(2,3)])
        proof, _ = e.discover(source)
        edited = source + [[-1,-4,-7]]
        with self.assertRaises(ValueError): e.check(edited, proof)
        self.assertIsNone(e.discover(edited)[0])

    def test_inexact_live_or_dead_entry_rejected(self):
        source = coloring(3, [(0,1),(1,2)])
        proof, _ = e.discover(source)
        for replacement in ([], [True], [10000], [1,1,2,3]):
            bad = deepcopy(proof); bad['branches'][0][0] = replacement
            with self.assertRaises(ValueError): e.check(source, bad)

    def test_changed_conflicts_cannot_reuse_false_verdict(self):
        source = [[1,2,3],[4,5,6]] + [[-a,-b] for a in (1,2,3) for b in (4,5,6)]
        proof, _ = e.discover(source)
        with self.assertRaises(ValueError): e.check(source[:-1], proof)

    def test_budget_stops_never_authorize_negative(self):
        source = coloring(4, combinations(range(4), 2))
        proof, diag = e.discover(source, pair_limit=0)
        self.assertIsNone(e.check(source, proof)['answer'])
        self.assertEqual(diag['reason'], 'incomplete')
        self.assertIsNone(e.discover(source, recognition_limit=0)[0])

    def test_cutset_conflict_rows_checked(self):
        source = coloring(4, combinations(range(4), 2))
        proof, _ = e.discover(source)
        self.assertIsNone(proof['branches'][0])
        proof['branches'][0] = [[] for _ in proof['demands']]
        with self.assertRaises(ValueError): e.check(source, proof)

    def test_malformed_schema(self):
        source = coloring(3, [(0,1),(1,2)])
        proof, _ = e.discover(source)
        for key, value in (('cutset',[True]), ('cutset',[0,0]), ('cutset',[0,1,2]),
                           ('empty',1), ('format','bad'), ('demands',[[1,2,3],[1,5,6]])):
            bad = deepcopy(proof); bad[key] = value
            with self.assertRaises(ValueError): e.check(source, bad)
        for source in ([[0]], [[True]], [[1.0]], 'cnf'):
            with self.assertRaises(ValueError): e.discover(source)
        for kwargs in ({'cutset_limit':3}, {'pair_limit':True}, {'recognition_limit':-1}):
            with self.assertRaises(ValueError): e.discover([], **kwargs)

    def test_cold_check_without_construction(self):
        source = coloring(4, combinations(range(4), 2)); proof, _ = e.discover(source)
        with patch.object(e,'discover',side_effect=AssertionError), \
             patch.object(e,'choose_cutset',side_effect=AssertionError), \
             patch.object(e,'tables',side_effect=AssertionError), \
             patch.object(e.prior.native,'solve_matching',side_effect=AssertionError):
            self.assertIs(e.check(source, json.loads(json.dumps(proof)))['answer'], False)


if __name__ == '__main__': unittest.main()
