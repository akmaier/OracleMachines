from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest

from experiments.cnf_partial_cover import recompose as previous
from experiments.cnf_prepared_partial import recompose
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_conditional_unit_support import extract
from experiments.cnf_learned_conditional import COVER_FORMAT
from experiments.cnf_residual_dag import propagate, holds
from experiments.cnf_probed_partition import acquire

CUBE = list(product((-1, 1), (-2, 2), (-3, 3)))


class PreparedPartialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256)
            bundle, _ = extract(s, CUBE)
            cls.cover = dict(format=COVER_FORMAT, tree=bundle['tree'],
                templates=[e['template'] for e in bundle['entries']])
        finally: s.close()

    def compare(self, target, budget=256, prefix=False):
        answers = []
        for method in (previous, recompose):
            s = ConsequencePrioritySolver(leaves=False)
            try:
                c = Counter(); screen = None
                if prefix:
                    cnf, _, root = s._canonical(target)
                    _, trace, conflict = propagate(cnf, Counter())
                    screen = dict(root=root, trace=trace, conflict=conflict)
                with patch.object(s, '_canonical', wraps=s._canonical) as canonical:
                    result = method(s, target, self.cover, budget, screen, c)
                rows = list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                answers.append((result, rows, dict(s.counts), c, canonical.call_count))
            finally: s.close()
        self.assertEqual(answers[0][0], answers[1][0])
        self.assertEqual(answers[0][1], answers[1][1])
        self.assertEqual(answers[0][2].get('expanded_nodes', 0), answers[1][2].get('expanded_nodes', 0))
        self.assertEqual(answers[0][2].get('verified_nodes', 0), answers[1][2].get('verified_nodes', 0))
        return answers

    def test_all_cube_deletions_preserve_payloads_and_verification(self):
        for mask in range(256):
            target = [cl for i, cl in enumerate(CUBE) if mask >> i & 1]
            self.compare(target)

    def test_surviving_leaves_avoid_repeated_preparation(self):
        before, after = self.compare(CUBE[1:] + [(-1, -2, -3, 4), (-1, -2, -3, -4)])
        self.assertGreater(after[3]['prepared_partial_leaf_reuses'], 0)
        self.assertLess(after[4], before[4])
        self.assertLess(after[3]['restriction_literal_visits'], before[3]['restriction_literal_visits'])

    def test_prefix_pruning_reuses_the_same_frame(self):
        before, after = self.compare(CUBE[1:] + [(-1,)], budget=0, prefix=True)
        self.assertGreater(after[3]['prepared_partial_frame_reuses'], 0)
        self.assertLess(after[4], before[4])

    def test_absent_variables_and_sparse_labels_preserve_models(self):
        for target in ([], [(19,)], [(19,), (-19,)], [(19, 73), (-19, -73)]):
            self.compare(target)

    def test_shared_budgets_preserve_checked_prefixes(self):
        target = CUBE[1:-1] + [(-1, -2, -3, 4), (-1, -2, -3, -4),
            (1, 2, 3, 5, 6), (1, 2, 3, 5, -6), (1, 2, 3, -5, 6), (1, 2, 3, -5, -6)]
        for budget in range(7):
            before, after = self.compare(target, budget)
            self.assertLessEqual(after[2].get('expanded_nodes', 0), budget)

    def test_changed_source_is_rechecked_on_each_call(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            target = [list(cl) for cl in CUBE]
            first = recompose(s, target, self.cover, 256)
            self.assertFalse(s._read(first['root'])['answer'])
            target.pop(0)
            second = recompose(s, target, self.cover, 256)
            self.assertNotEqual(first['root'], second['root'])
            self.assertTrue(s._read(second['root'])['answer'])
            node = s._read(second['root'])
            self.assertTrue(holds(target, dict(enumerate(node['model'], 1))))
        finally: s.close()

    def test_bad_cover_path_or_unit_prefix_cannot_publish(self):
        for kind in ('cover', 'key', 'unit'):
            s = ConsequencePrioritySolver(leaves=False)
            try:
                target = CUBE[1:]; cover = deepcopy(self.cover); screen = None
                if kind == 'cover':
                    cover['tree']['low'], cover['tree']['high'] = cover['tree']['high'], cover['tree']['low']
                else:
                    root = s._canonical(target)[2]
                    screen = dict(root='bad' if kind == 'key' else root,
                        trace=[] if kind == 'key' else [[1, 0]], conflict=None)
                with self.assertRaises(ValueError): recompose(s, target, cover, 256, screen)
                self.assertFalse(s.db.active)
                self.assertEqual(s.archive_storage()[0], 0)
            finally: s.close()

    def test_root_preparation_work_is_counted(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            # An empty target uses no SAT search when already checked; the new
            # root binding still charges normalization and key construction.
            recompose(s, [], self.cover, 256)
            recompose(s, [], self.cover, 0)
            self.assertGreater(s.counts['key_serialized_bytes'], 0)
        finally: s.close()
