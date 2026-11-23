from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import unittest

from experiments.cnf_refined_origins import register_recomposed, run_after_pool_miss
from experiments.cnf_leaf_handoff import recompose, PartialCoverBank
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_conditional_unit_support import extract
from experiments.cnf_learned_conditional import COVER_FORMAT, check_bank
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import holds

CUBE = list(product((-1, 1), (-2, 2), (-3, 3)))


class RefinedOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256)
            bundle, _ = extract(s, CUBE)
            cls.cover = dict(format=COVER_FORMAT, tree=bundle['tree'], templates=[e['template'] for e in bundle['entries']])
        finally: s.close()

    def prepared(self, s, source):
        cnf, names, key = s._canonical(source)
        return SimpleNamespace(target=source, cnf=cnf, names=names, key=key)

    def produce(self, s, target):
        p = self.prepared(s, target)
        result = recompose(s, target, self.cover, 256)
        evidence = dict(route='partial-cover', partial=result, stopped=result['stopped'])
        return p, evidence

    def test_completed_negative_origin_is_lazy_and_deduplicated(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            # Removing one original reason and adding a three-variable UNSAT
            # expansion requires multiple native dispatches in that branch.
            target = CUBE[1:] + [(-1, -2, -3, a, b, c) for a, b, c in product((-4, 4), (-5, 5), (-6, 6))]
            p, evidence = self.produce(s, target)
            self.assertGreaterEqual(s.counts['expanded_nodes'], 2)
            entries = []; c = Counter()
            first = register_recomposed(s, p, [], entries, evidence, c)
            self.assertTrue(first['admitted'])
            self.assertIsNone(entries[0]['cover'])
            self.assertIsNone(register_recomposed(s, p, [], entries, evidence, c))
            self.assertEqual(len(entries), 1)
            check_bank(s, entries)
        finally: s.close()

    def test_positive_and_missing_roots_never_enter_bank(self):
        for target in (CUBE[1:], [(19, 23), (-19, -23)]):
            s = ConsequencePrioritySolver(leaves=False)
            try:
                p, evidence = self.produce(s, target)
                self.assertTrue(s._read(p.key)['answer'])
                # Exercise the status gate independently of the cost heuristic.
                s.counts['expanded_nodes'] = 2
                entries = []
                self.assertIsNone(register_recomposed(s, p, [], entries, evidence, Counter()))
                p.key = s._canonical([(101, 103, 107)])[2]
                p.cnf = ((1, 2, 3),)
                self.assertIsNone(register_recomposed(s, p, [], entries, evidence, Counter()))
                self.assertEqual(entries, [])
            finally: s.close()

    def test_stops_and_other_routes_never_propose(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            p = self.prepared(s, CUBE[1:]); entries = []
            r = recompose(s, p.target, self.cover, 0)
            self.assertTrue(r['stopped'])
            s.counts['expanded_nodes'] = 8
            for evidence in (dict(route='partial-cover', stopped=True), dict(route='native', stopped=False)):
                self.assertIsNone(register_recomposed(s, p, [], entries, evidence, Counter()))
            self.assertEqual(entries, [])
        finally: s.close()

    def test_small_completed_acquisition_does_not_change_admission_policy(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            p, evidence = self.produce(s, CUBE[1:] + [(-1, -2, -3, 4), (-1, -2, -3, -4)])
            self.assertLess(s.counts['expanded_nodes'], 2)
            self.assertIsNone(register_recomposed(s, p, [], [], evidence, Counter()))
        finally: s.close()

    def test_capacity_eviction_never_removes_native_results(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256); p = self.prepared(s, CUBE)
            evidence = dict(route='partial-cover', stopped=False)
            s.counts['expanded_nodes'] = 2
            entries = []
            a = register_recomposed(s, p, [[9, False]], entries, evidence, Counter(), entry_limit=1)
            b = register_recomposed(s, p, [[9, True]], entries, evidence, Counter(), entry_limit=1)
            self.assertTrue(a['admitted'] and b['admitted'])
            self.assertEqual(entries[0]['guard'], [[9, True]])
            c = register_recomposed(s, p, [], entries, evidence, Counter(), byte_limit=2)
            self.assertFalse(c['admitted']); self.assertEqual(entries, [])
            self.assertFalse(s._read(p.key)['answer'])
        finally: s.close()

    def test_open_transaction_and_bad_source_map_are_rejected(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256); p = self.prepared(s, CUBE)
            s.counts['expanded_nodes'] = 2
            evidence = dict(route='partial-cover', stopped=False)
            s.db.start()
            with self.assertRaises(RuntimeError): register_recomposed(s, p, [], [], evidence, Counter())
            s.db.abort(); s.db.active = False
            p.names = [True, 2, 3]
            entries = []
            with self.assertRaises(ValueError): register_recomposed(s, p, [], entries, evidence, Counter())
            self.assertEqual(entries, [])
        finally: s.close()

    def test_guard_filters_reuse_and_inputs_are_copied(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256); p = self.prepared(s, CUBE); guard = [[9, False]]
            s.counts['expanded_nodes'] = 2; entries = []
            register_recomposed(s, p, guard, entries, dict(route='partial-cover', stopped=False), Counter())
            guard[0][1] = True
            bank = PartialCoverBank(s, entries)
            self.assertIsNone(bank.reuse(CUBE, guard))
            self.assertIsNone(entries[0]['cover'])
            self.assertIsNotNone(bank.reuse(CUBE, [[9, False]]))
            self.assertIsNotNone(entries[0]['cover'])
        finally: s.close()

    def test_persisted_proposals_and_ready_covers_replay_with_both_readers(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'proofs.sqlite'; s = ConsequencePrioritySolver(path, leaves=False)
            try:
                acquire(s, CUBE, 256); p = self.prepared(s, CUBE); s.counts['expanded_nodes'] = 2
                entries = []
                register_recomposed(s, p, [], entries, dict(route='partial-cover', stopped=False), Counter())
                lazy = json.loads(json.dumps(entries))
                PartialCoverBank(s, entries).reuse(CUBE, [])
                ready = json.loads(json.dumps(entries))
            finally: s.close()
            for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
                reader = cls(path)
                try:
                    check_bank(reader, lazy); check_bank(reader, ready)
                    changed = deepcopy(ready); changed[0]['cover']['templates'][0]['trace'] = []
                    with self.assertRaises(ValueError): check_bank(reader, changed)
                finally: reader.close()

    def test_all_cube_deletions_with_live_origin_bank_match_truth_table(self):
        s = ConsequencePrioritySolver(leaves=False)
        try:
            acquire(s, CUBE, 256); p = self.prepared(s, CUBE); s.counts['expanded_nodes'] = 2
            entries = []
            register_recomposed(s, p, [], entries, dict(route='partial-cover', stopped=False), Counter())
            for mask in range(256):
                target = [cl for i, cl in enumerate(CUBE) if mask >> i & 1]
                prepared = self.prepared(s, target); s.counts = Counter()
                result = run_after_pool_miss(s, prepared, [], entries, 256, Counter())
                self.assertFalse(result['stopped'])
                answer = s._read(prepared.key)['answer']
                expected = any(holds(target, dict(zip((1, 2, 3), bits))) for bits in product((False, True), repeat=3))
                self.assertEqual(answer, expected)
                check_bank(s, entries)
        finally: s.close()
