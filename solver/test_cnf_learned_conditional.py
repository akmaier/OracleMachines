from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json, sqlite3, unittest

from experiments.cnf_learned_conditional import COVER_FORMAT, check_cover, publish_cover, LearnedCoverBank, check_bank
from experiments.cnf_conditional_unit_support import extract
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import holds
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

CUBE = list(product((-1, 1), (-2, 2), (-3, 3)))


class LearnedConditionalTests(unittest.TestCase):
    def solver(self, **kwargs):
        s = ConsequencePrioritySolver(**kwargs)
        self.addCleanup(s.close)
        return s

    def donor(self, source=CUBE):
        s = self.solver(leaves=False)
        acquire(s, source, 256)
        bundle, _ = extract(s, source)
        cover = dict(format=COVER_FORMAT, templates=[e['template'] for e in bundle['entries']], tree=bundle['tree'])
        return s, cover

    def prepared(self, solver, source):
        cnf, names, key = solver._canonical(source)
        return SimpleNamespace(cnf=cnf, names=names, key=key)

    def test_complete_cover_publishes_without_search(self):
        _, cover = self.donor()
        s = self.solver()
        target = CUBE + [(8, 9)]
        with patch.object(s, '_expand', side_effect=AssertionError('Fresh search')):
            root = publish_cover(s, target, cover)
        self.assertFalse(s._read(root)['answer'])
        self.assertEqual(root, s._canonical(target)[2])
        self.assertFalse(s.db.active)

    def test_missing_branch_assumption_or_reason_is_rejected(self):
        _, cover = self.donor()
        for field in ('low', 'high', 'variable'):
            bad = deepcopy(cover)
            del bad['tree'][field]
            with self.assertRaises(ValueError):
                check_cover(bad)
        bad = deepcopy(cover)
        bad['templates'][0]['assumptions'].append([99, True])
        with self.assertRaises(ValueError):
            check_cover(bad)
        with self.assertRaises(ValueError):
            publish_cover(self.solver(), CUBE[1:], cover)

    def test_absent_split_variable_can_use_one_branch(self):
        _, cover = self.donor()
        tree = cover['tree']
        cover['tree'] = dict(variable=99, low=deepcopy(tree), high=deepcopy(tree))
        s = self.solver()
        root = publish_cover(s, CUBE, cover)
        self.assertFalse(s._read(root)['answer'])

    def test_deletion_truth_no_partial_cover_becomes_answer(self):
        _, cover = self.donor()
        s = self.solver()
        for mask in range(256):
            target = [cl for i, cl in enumerate(CUBE) if mask >> i & 1]
            truth = any(holds(target, dict(zip((1, 2, 3), bits))) for bits in product((False, True), repeat=3))
            if mask == 255:
                self.assertFalse(truth)
                self.assertFalse(s._read(publish_cover(s, target, cover))['answer'])
            else:
                self.assertTrue(truth)
                with self.assertRaises(ValueError):
                    publish_cover(s, target, cover)

    def test_lazy_guard_filtered_registration_and_reuse(self):
        s, _ = self.donor()
        entries = []
        bank = LearnedCoverBank(s, entries)
        prepared = self.prepared(s, CUBE)
        bank.register(prepared, [[77, True]], 3)
        self.assertIsNone(entries[0]['cover'])
        self.assertIsNone(bank.reuse(CUBE + [(8, 9)], [[77, False]]))
        self.assertIsNone(entries[0]['cover'])
        result = bank.reuse(CUBE + [(8, 9)], [[77, True]])
        self.assertIsNotNone(result)
        self.assertEqual(bank.counts['learned_extractions'], 1)
        bank.reuse(CUBE + [(8, -9)], [[77, True]])
        self.assertEqual(bank.counts['learned_extractions'], 1)

    def test_positive_and_cheap_results_are_not_learned(self):
        s, _ = self.donor()
        bank = LearnedCoverBank(s, [])
        bank.register(self.prepared(s, CUBE), [], 2)
        acquire(s, [[7]], 256)
        bank.register(self.prepared(s, [[7]]), [], 9)
        self.assertEqual(bank.entries, [])

    def test_sparse_names_and_irrelevant_source_deletion(self):
        mapping = {1: 15, 2: 71, 3: 900}
        source = [[mapping[abs(l)] * (1 if l > 0 else -1) for l in cl] for cl in CUBE]
        s, _ = self.donor(source + [[1100, 1101]])
        bank = LearnedCoverBank(s, [])
        bank.register(self.prepared(s, source + [[1100, 1101]]), [], 4)
        result = bank.reuse(source + [[1200, -1201]], [])
        self.assertIsNotNone(result)
        self.assertFalse(s._read(result['root'])['answer'])

    def test_persistence_and_both_cold_readers(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'db'
            s = ConsequencePrioritySolver(path, leaves=False)
            try:
                acquire(s, CUBE, 256)
                bank = LearnedCoverBank(s, [])
                bank.register(self.prepared(s, CUBE), [], 3)
                root = bank.reuse(CUBE + [(9, 10)], [])['root']
                saved = json.loads(json.dumps(bank.entries))
            finally:
                s.close()
            for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
                reader = cls(path)
                try:
                    check_bank(reader, saved)
                    self.assertFalse(reader._read(root)['answer'])
                    bad = deepcopy(saved)
                    bad[0]['names'] = [True, 2, 3]
                    with self.assertRaises(ValueError):
                        check_bank(reader, bad)
                finally:
                    reader.close()

    def test_commit_failure_rolls_back_all_children(self):
        _, cover = self.donor()
        s = self.solver()
        with patch.object(s.db, '_commit', side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):
                publish_cover(s, CUBE + [(8, 9)], cover)
        self.assertFalse(s.db.active)
        self.assertFalse(s.db.pending)
        self.assertEqual(s.db.execute('SELECT COUNT(*) FROM cnf_residual_v1').fetchone()[0], 0)
        self.assertIsNone(s._read(s._canonical(CUBE + [(8, 9)])[2]))

    def test_caps_and_unsupported_endpoints_never_certify(self):
        s, cover = self.donor()
        with self.assertRaises(ValueError):
            check_cover(cover, node_limit=1)
        for limit in (0, 1):
            with self.assertRaises(ValueError):
                LearnedCoverBank(s, [], byte_limit=limit)
        bank = LearnedCoverBank(s, [], byte_limit=2)
        bank.register(self.prepared(s, CUBE), [], 4)
        self.assertEqual(bank.entries, [])
        binary = [[1, 2], [1, -2], [-1, 2], [-1, -2]]
        s = self.solver()
        acquire(s, binary, 256)
        bank = LearnedCoverBank(s, [])
        bank.register(self.prepared(s, binary), [], 3)
        self.assertIsNone(bank.reuse(binary + [[7, 8]], []))
        self.assertTrue(bank.entries[0]['rejected'])

    def test_stale_origin_is_rejected_before_discovery(self):
        s, _ = self.donor()
        bank = LearnedCoverBank(s, [])
        prepared = self.prepared(s, CUBE)
        bank.register(prepared, [], 3)
        s.checked.pop(prepared.key, None)
        with s.db:
            s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?', (prepared.key,))
        with self.assertRaises(ValueError):
            bank.reuse(CUBE + [[7, 8]], [])
