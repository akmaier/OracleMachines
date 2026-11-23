from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest

from experiments.cnf_prepared_partial import recompose as previous
from experiments.cnf_leaf_handoff import recompose
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_conditional_unit_support import extract
from experiments.cnf_learned_conditional import COVER_FORMAT
from experiments.cnf_residual_dag import propagate, holds
from experiments.cnf_probed_partition import acquire

CUBE = list(product((-1, 1), (-2, 2), (-3, 3)))


class LeafHandoffTests(unittest.TestCase):
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
                original = s._canonical
                result = method(s, target, self.cover, budget, screen, c)
                self.assertEqual(s._canonical, original)
                self.assertNotIn('_canonical', s.__dict__)
                rows = list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                answers.append((result, rows, dict(s.counts), c))
            finally: s.close()
        self.assertEqual(answers[0][0], answers[1][0])
        self.assertEqual(answers[0][1], answers[1][1])
        for field in ('visits', 'expanded_nodes', 'verified_nodes', 'inserted_bytes'):
            self.assertEqual(answers[0][2].get(field, 0), answers[1][2].get(field, 0))
        self.assertEqual(answers[1][2].get('leaf_handoff_reuses', 0),
                         answers[1][3]['partial_native_leaves'])
        return answers

    def test_all_cube_deletions_preserve_payloads(self):
        for mask in range(256):
            self.compare([cl for i, cl in enumerate(CUBE) if mask >> i & 1])

    def test_reduces_normalization_without_skipping_verification(self):
        before, after = self.compare(CUBE[1:] + [(-1, -2, -3, 4), (-1, -2, -3, -4)])
        self.assertGreater(after[2]['leaf_handoff_reuses'], 0)
        self.assertLess(after[2]['normalization_literal_visits'], before[2]['normalization_literal_visits'])
        self.assertLess(after[2]['key_serialized_bytes'], before[2]['key_serialized_bytes'])
        self.assertGreater(after[2]['verified_nodes'], 0)

    def test_shared_budget_and_committed_prefixes(self):
        target = CUBE[1:-1] + [(-1, -2, -3, 4), (-1, -2, -3, -4),
            (1, 2, 3, 5, 6), (1, 2, 3, 5, -6), (1, 2, 3, -5, 6), (1, 2, 3, -5, -6)]
        for budget in range(7):
            _, after = self.compare(target, budget)
            self.assertLessEqual(after[2].get('expanded_nodes', 0), budget)

    def test_fixed_prefix_and_absent_split(self):
        for budget in (0, 1, 256):
            self.compare(CUBE[1:] + [(-1,)], budget, prefix=True)

    def test_sparse_labels_duplicates_and_empty_clauses(self):
        for target in ([], [()], [(19,)], [(19,), (-19,)],
                       [(19, 73), (-19, -73)], [(73, 19, 19), (19, 73)]):
            self.compare(target)

    def test_source_mutation_requires_new_preparation(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            source = [list(cl) for cl in CUBE]
            first = recompose(s, source, self.cover, 256)
            self.assertFalse(s._read(first['root'])['answer'])
            source.pop(0)
            second = recompose(s, source, self.cover, 256)
            self.assertNotEqual(first['root'], second['root'])
            node = s._read(second['root'])
            self.assertTrue(node['answer'])
            self.assertTrue(holds(source, dict(enumerate(node['model'], 1))))
            again = recompose(s, source, self.cover, 0)
            self.assertEqual(again['root'], second['root'])
            self.assertEqual(s.counts['leaf_handoff_reuses'], 0)
        finally: s.close()

    def test_untrusted_cover_and_unit_prefix_still_rejected(self):
        for kind in ('cover', 'key', 'unit'):
            s = ConsequencePrioritySolver(leaves=False)
            try:
                cover = deepcopy(self.cover); screen = None
                if kind == 'cover':
                    cover['tree']['low'], cover['tree']['high'] = cover['tree']['high'], cover['tree']['low']
                else:
                    root = s._canonical(CUBE[1:])[2]
                    screen = dict(root='bad' if kind == 'key' else root,
                        trace=[] if kind == 'key' else [[1, 0]], conflict=None)
                with self.assertRaises(ValueError): recompose(s, CUBE[1:], cover, 256, screen)
                self.assertFalse(s.db.active)
                self.assertNotIn('_canonical', s.__dict__)
                self.assertEqual(s.archive_storage()[0], 0)
            finally: s.close()

    def test_invalid_external_literals_never_use_handoff(self):
        for target in ([(True,)], [(1.0,)], [(0,)], [('1',)], [(19, -19)]):
            s = ConsequencePrioritySolver(leaves=False)
            try:
                with self.assertRaises((ValueError, TypeError)):
                    recompose(s, target, self.cover, 256)
                self.assertEqual(s.counts['leaf_handoff_reuses'], 0)
                self.assertEqual(s.archive_storage()[0], 0)
            finally: s.close()

    def test_equal_but_distinct_input_does_not_consume_offer(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            original = s._visit
            def probe(source):
                same = [list(cl) for cl in source]
                before = s.counts['leaf_handoff_reuses']
                expected = s._canonical(same)
                self.assertEqual(s.counts['leaf_handoff_reuses'], before)
                result = original(source)
                self.assertEqual(result[1], expected[2])
                return result
            with patch.object(s, '_visit', probe): recompose(s, [(19,)], self.cover, 256)
            self.assertEqual(s.counts['leaf_handoff_reuses'], 1)
        finally: s.close()

    def test_handoff_consumed_before_expansion_and_native_checking(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            canonical, expand, verify = s._canonical, s._expand, s._verify
            def check_expand(cnf):
                self.assertEqual(s._canonical, canonical)
                return expand(cnf)
            def check_verify(key, node):
                self.assertEqual(s._canonical, canonical)
                return verify(key, node)
            with patch.object(s, '_expand', check_expand), patch.object(s, '_verify', check_verify):
                recompose(s, CUBE[1:], self.cover, 256)
            self.assertGreater(s.counts['verified_nodes'], 0)
        finally: s.close()

    def test_exception_before_consumption_restores_instance_method(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            original = s._canonical
            with patch.object(s, '_canonical', original), patch.object(s, '_visit', side_effect=ValueError('injected')):
                with self.assertRaisesRegex(ValueError, 'injected'):
                    recompose(s, [(19,)], self.cover, 256)
                self.assertIs(s.__dict__['_canonical'], original)
                self.assertFalse(s.db.active)
            self.assertNotIn('_canonical', s.__dict__)
        finally: s.close()

    def test_invalid_generated_certificate_is_still_rejected(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            with patch.object(s, '_expand', return_value=(None, dict(kind='empty'))):
                with self.assertRaises(ValueError): recompose(s, [(19,)], self.cover, 256)
            self.assertNotIn('_canonical', s.__dict__)
            self.assertFalse(s.db.active)
            self.assertEqual(s.archive_storage()[0], 0)
        finally: s.close()
