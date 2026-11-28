from collections import Counter
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_answer_certificate as e
from experiments import cnf_watched_learning as watched
from solver.test_cnf_selective_learning import SQUARE


def certificate(kind, records, conclusion=None, witness=None):
    return dict(format=e.resolution.FORMAT, kind=kind, witness=witness,
                derivations=records, conclusion=conclusion)


class AnswerCertificateTests(TestCase):
    def test_unsat_remaps_a_shared_dag_and_omits_unused_records(self):
        source = [[-1], [1]]
        archive = certificate('unsat', [[1, [], [1]], [1, [], [1]],
                                       [3, [[1, 0]], []], [2, [], [1]]], 4)
        saved = deepcopy(archive)
        proof, diag = e.project(source, archive)
        self.assertEqual(proof, certificate('unsat', [[1, [], [1]], [2, [[1, 0]], []]], 3))
        self.assertEqual(diag['retained_derivations'], 2)
        self.assertEqual(diag['reached_original_clauses'], 2)
        self.assertEqual(archive, saved)
        proof['derivations'][0][2].append(19)
        self.assertEqual(archive, saved)

    def test_sat_keeps_only_an_independent_witness(self):
        archive, _ = e.resolution.solve([[1]])
        archive['derivations'] = [[0, [], [1]]]
        saved = deepcopy(archive)
        proof, _ = e.project([[1]], archive)
        self.assertEqual(proof['derivations'], [])
        self.assertTrue(e.resolution.check_result([[1]], proof)['answer'])
        proof['witness']['values'][0] = False
        self.assertEqual(archive, saved)

    def test_unknown_remains_unknown_and_does_not_discard_archive(self):
        archive = certificate('unknown', [[0, [], [1]]])
        proof, _ = e.project([[1]], archive)
        self.assertEqual(proof, certificate('unknown', []))
        self.assertEqual(len(archive['derivations']), 1)
        self.assertIsNone(e.resolution.check_result([[1]], proof)['answer'])

    def test_original_empty_clause_needs_no_derivations(self):
        proof, _ = e.project([[], [1]], certificate('unsat', [[1, [], [1]]], 0))
        self.assertEqual(proof, certificate('unsat', [], 0))

    def test_unused_corruption_is_rejected_for_every_verdict(self):
        for source in ([[1]], SQUARE):
            archive, _ = e.resolution.solve(source)
            for kind in (archive['kind'], 'unknown'):
                bad = deepcopy(archive)
                if kind == 'unknown': bad.update(kind=kind, witness=None, conclusion=None)
                bad['derivations'].append([0, [], [999]])
                with self.assertRaisesRegex(ValueError, 'Changed learned clause'):
                    e.project(source, bad)

    def test_corrupt_references_and_conclusions_are_rejected(self):
        for record in ([2, [], [1]], [-1, [], [1]], [True, [], [1]], [0, [[0, 0]], []]):
            with self.assertRaises(ValueError): e.project([[1]], certificate('unknown', [record]))
        for root in (-1, True, 1, None):
            with self.assertRaises(ValueError): e.project([[]], certificate('unsat', [], root))

    def test_changed_source_and_tampered_output_are_rejected(self):
        source = [[-1], [1]]
        archive = certificate('unsat', [[0, [[1, 1]], []]], 2)
        proof, _ = e.project(source, archive)
        with self.assertRaises(ValueError): e.resolution.check_result([[1]], proof)
        proof['derivations'][0][1][0][0] = 2
        with self.assertRaises(ValueError): e.resolution.check_result(source, proof)

    def test_duplicates_tautologies_sparse_labels_and_order(self):
        source = [[-17], [17], [17], [211, -211]]
        archive = certificate('unsat', [[0, [[17, 1]], []]], 2)
        proof, _ = e.project(list(reversed(source)), archive)
        self.assertFalse(e.resolution.check_result(source, proof)['answer'])

    def test_iterative_deep_chain(self):
        size = 1500
        records = [[0, [], [-1]]]
        records += [[i + 1, [], [-1]] for i in range(1, size)]
        records.append([size + 1, [[1, 1]], []])
        proof, _ = e.project([[-1], [1]], certificate('unsat', records, size + 2))
        self.assertEqual(len(proof['derivations']), size + 1)

    def test_idempotence_and_search_free_projection(self):
        archive, _ = e.resolution.solve(SQUARE)
        with patch.object(e.resolution, 'search', side_effect=AssertionError), \
             patch.object(watched, 'search', side_effect=AssertionError):
            proof, _ = e.project(SQUARE, archive)
            again, _ = e.project(SQUARE, proof)
            self.assertEqual(proof, again)

    def test_all_validation_and_projection_work_is_counted(self):
        archive = certificate('unsat', [[0, [[1, 1]], []]], 2)
        counts = Counter()
        e.project([[-1], [1]], archive, counts)
        self.assertEqual(counts['resolution_steps_checked'], 2)
        self.assertEqual(counts['answer_projection_copied_steps'], 1)
        self.assertEqual(counts['answer_projection_reference_visits'], 3)
