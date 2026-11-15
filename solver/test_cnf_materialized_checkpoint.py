from collections import Counter
import copy
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from experiments import cnf_materialized_checkpoint as snap
from experiments.continue_cnf_retained_discovery import (
    BudgetedInventory, archive_json, digests, expand, full, routes_for)
from experiments.compare_cnf_probe_continuation import TABLES
from solver.test_cnf_source_local import OPTIONS


class MaterializedCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.history = self.root/'history'
        self.evidence = [[], [], [], [], []]; self.cache = self.root/'cache'
        h = BudgetedInventory(self.history, **OPTIONS)
        try:
            for t in TABLES: h.db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            h.db.commit(); h.set_admission_budget(32)
            cnf = [[1]]; key = h._edge(cnf, h.config['max_depth'])['key']
            routes = routes_for(h, self.evidence, [])
            flags, plans, _ = full(h, [key], routes)
            proof = expand(h, plans[0], [key], routes, Counter())
        finally: h.close()
        self.code = self.root/'implementation'; self.code.write_text('checked implementation\n')
        self.parent = dict(options=OPTIONS, fingerprints={str(self.code):snap.sha(self.code)},
            cases=[dict(source=cnf)], final_closed=flags[0], logical_table_digests=digests(self.history),
            evidence_counts_after=[0]*5, bridges=archive_json(self.root/'bridges.gz', []),
            expanded_certificate=archive_json(self.root/'positive.gz', proof))
        self.parent_path = self.root/'parent.json'; self.parent_path.write_text(json.dumps(self.parent))
        self.parent_sha = snap.sha(self.parent_path)
        self.descriptor, _ = snap.materialize(self.history, self.evidence, [], self.parent_path, self.parent_sha, self.cache)
        self.descriptor_path = self.root/'descriptor.json'; self.write_descriptor()
        self.fallback = Mock(side_effect=AssertionError('unexpected fallback'))

    def write_descriptor(self):
        self.descriptor_path.write_text(json.dumps(self.descriptor))
        self.descriptor_sha = snap.sha(self.descriptor_path)

    def restore(self, **kwargs):
        return snap.restore_cached(self.descriptor_path, self.descriptor_sha,
            self.parent_path, self.parent_sha, self.cache, self.root/'restored',
            self.root, self.fallback, **kwargs)

    def test_roundtrip_rechecks_proof_without_discovery_or_historical_replay(self):
        metrics = {}
        with patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('fresh solving')):
            parent, *evidence = self.restore(metrics=metrics)
        self.assertEqual(parent, self.parent); self.assertEqual(evidence, self.evidence)
        self.assertEqual(snap.sha(self.history), snap.sha(self.root/'restored'))
        self.assertEqual(digests(self.history), digests(self.root/'restored'))
        self.assertEqual(metrics['mode'], 'materialized'); self.assertTrue(metrics['positive_checks'])
        self.fallback.assert_not_called()

    def test_absent_object_uses_authoritative_fallback(self):
        (self.cache/self.descriptor['database']['name']).unlink()
        def replay(parent, dest, tmp):
            shutil.copyfile(self.history, dest)
            return self.parent, *copy.deepcopy(self.evidence)
        self.fallback.side_effect = replay; metrics = {}
        self.restore(metrics=metrics)
        self.fallback.assert_called_once(); self.assertEqual(metrics['mode'], 'authoritative-fallback')
        self.assertEqual(snap.sha(self.history), snap.sha(self.root/'restored'))

    def test_corrupt_cache_rejects_without_fallback_or_published_destination(self):
        p = self.cache/self.descriptor['database']['name']; p.write_bytes(p.read_bytes()+b'x')
        with self.assertRaisesRegex(ValueError, 'Corrupt'): self.restore()
        self.fallback.assert_not_called(); self.assertFalse((self.root/'restored').exists())

    def test_sidecar_corruption_rejects(self):
        p = self.cache/self.descriptor['evidence']['name']; p.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'Corrupt'): self.restore()
        self.assertFalse((self.root/'restored').exists())

    def test_descriptor_requires_independent_hash_binding(self):
        self.descriptor_path.write_text(self.descriptor_path.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'trusted snapshot descriptor'): self.restore()

    def test_parent_and_implementation_changes_reject(self):
        self.parent_path.write_text(self.parent_path.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'checkpoint parent'): self.restore()
        self.parent_path.write_text(json.dumps(self.parent)); self.code.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'implementation'): self.restore()

    def test_policy_or_parent_rebinding_rejects(self):
        for field in ('parent', 'options', 'table_digests'):
            original = copy.deepcopy(self.descriptor[field]); self.descriptor[field] = {}
            self.write_descriptor()
            with self.assertRaisesRegex(ValueError, 'binding mismatch'): self.restore()
            self.descriptor[field] = original

    def test_full_byte_identity_rejects_schema_change_even_with_equal_rows(self):
        altered = self.root/'altered'; shutil.copyfile(self.history, altered)
        db = sqlite3.connect(altered)
        try:
            db.execute('CREATE TABLE extra (x)'); db.commit()
        finally: db.close()
        self.assertEqual(digests(altered), digests(self.history))
        obj = snap._publish(altered, self.cache)
        obj['raw_sha256'] = self.descriptor['database']['raw_sha256']
        self.descriptor['database'] = obj; self.write_descriptor()
        with patch.object(snap, 'verify_checkpoint', side_effect=AssertionError('must not open SQLite')):
            with self.assertRaisesRegex(ValueError, 'full materialized byte identity'): self.restore()
        self.assertFalse((self.root/'restored').exists())

    def test_failure_during_positive_check_does_not_publish(self):
        with patch.object(snap, 'verify_checkpoint', side_effect=ValueError('bad proof')):
            with self.assertRaisesRegex(ValueError, 'bad proof'): self.restore()
        self.assertFalse((self.root/'restored').exists())

    def test_destination_and_uncheckpointed_source_are_not_overwritten(self):
        dest = self.root/'restored'; dest.write_text('prior work')
        with self.assertRaisesRegex(ValueError, 'already exists'): self.restore()
        self.assertEqual(dest.read_text(), 'prior work')
        Path(str(self.history)+'-wal').write_text('live transaction')
        with self.assertRaisesRegex(ValueError, 'Close and checkpoint'):
            snap.materialize(self.history, self.evidence, [], self.parent_path, self.parent_sha, self.cache)

    def test_materialization_is_idempotent_and_preserves_input(self):
        before = snap.sha(self.history)
        descriptor, _ = snap.materialize(self.history, self.evidence, [], self.parent_path, self.parent_sha, self.cache)
        self.assertEqual(descriptor, self.descriptor); self.assertEqual(snap.sha(self.history), before)
        self.assertEqual(len(list(self.cache.glob('*.gz'))), 2)

    def test_incomplete_evidence_and_changed_history_reject_publication(self):
        with self.assertRaisesRegex(ValueError, 'evidence groups'):
            snap.materialize(self.history, self.evidence[:-1], [], self.parent_path, self.parent_sha, self.cache)
        db = sqlite3.connect(self.history)
        try:
            db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' '"); db.commit()
        finally: db.close()
        with self.assertRaisesRegex(ValueError, 'Incorrect materialized history'):
            snap.materialize(self.history, self.evidence, [], self.parent_path, self.parent_sha, self.cache)


if __name__ == '__main__': unittest.main()
