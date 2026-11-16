from collections import Counter
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from experiments import compare_cnf_bootstrap as study
from experiments.cnf_incremental_coverage import catalog
from experiments.cnf_split_registry import SplitRegistry, PATTERNS


class SplitRegistryTests(unittest.TestCase):
    def history(self, path=':memory:'):
        h = study.CompleteAdmissionInventory(path, **study.OPTIONS)
        study.split.initialize(h);h.set_admission_budget(64)
        return h

    def source(self, h):
        return h._edge(json.loads(Path('solver/fixtures/trace-split.json').read_text()), 0)['key']

    def test_pending_children_without_new_pair_activate_and_replay(self):
        h = self.history()
        try:
            source = self.source(h);registry = SplitRegistry(h)
            record = study.split.acquire_record(h, source, 5, Counter())
            registry.refresh()
            self.assertEqual(registry.statistics()['records'], 1)
            self.assertGreater(registry.statistics()['pending_dependencies'], 0)
            self.assertEqual(catalog(registry), catalog(study.routes_for(h, [record])))
            targets, _ = study.split.verify(h, record, Counter())
            for target in targets:
                h._edge(target, 0);registry.refresh()
                self.assertEqual(catalog(registry), catalog(study.routes_for(h, [record])))
            self.assertEqual(registry.counts['registry_verified_records'], 1)
            self.assertGreater(registry.counts['registry_pending_notifications'], 0)
            closed, plan = study.compose(h, [source], registry, Counter())
            self.assertEqual(closed, [True])
            proof = study.expand(h, plan, [source], registry, Counter())
            study.split.verify_positive(h, proof, [source], [record], Counter())
            with patch.object(study.split, 'verify', side_effect=AssertionError('rechecked old record')):
                for _ in range(8):registry.refresh()
            self.assertEqual(registry.counts['registry_verified_records'], 1)
        finally:h.close()

    def test_partial_budget_and_later_completion_match_full_builder(self):
        h = self.history()
        try:
            source = self.source(h);registry = SplitRegistry(h)
            records = [study.split.acquire_record(h, source, v, Counter()) for v in (1, 5)]
            registry.refresh();h.set_admission_budget(0)
            self.assertTrue(any(study.acquire(h, records[0])))
            registry.refresh();self.assertEqual(catalog(registry), catalog(study.routes_for(h, records)))
            h.set_admission_budget(256)
            for record in reversed(records):
                study.acquire(h, record);registry.refresh()
                self.assertEqual(catalog(registry), catalog(study.routes_for(h, records)))
            self.assertEqual(registry.counts['registry_verified_records'], 2)
        finally:h.close()

    def test_duplicate_child_and_detached_record(self):
        h = self.history()
        try:
            source = h._edge(((1, 2), (-1, 2)), 0)['key'];registry = SplitRegistry(h)
            record = study.split.acquire_record(h, source, 1, Counter());saved = copy.deepcopy(record)
            self.assertEqual(record['branches'][0]['edge']['key'], record['branches'][1]['edge']['key'])
            registry.refresh();record['branches'].clear()  # caller mutation cannot change SQL evidence
            study.acquire(h, saved);registry.refresh()
            self.assertEqual(catalog(registry), catalog(study.routes_for(h, [saved])))
            rows = registry.by_source[source];self.assertEqual(len(rows), 1)
            self.assertEqual(len(rows[0][1]), 2)  # preserve AND-premise multiplicity
        finally:h.close()

    def test_nonappend_and_unrelated_writes_invalidate(self):
        for operation in ('update', 'delete', 'replace', 'rollback', 'unrelated'):
            with self.subTest(operation=operation):
                h = self.history()
                try:
                    source = self.source(h);study.split.acquire_record(h, source, 5, Counter());registry = SplitRegistry(h)
                    identity, payload = h.db.execute(f'SELECT id,payload FROM {study.split.TABLE}').fetchone()
                    if operation == 'replace':
                        h.db.execute(f'INSERT OR REPLACE INTO {study.split.TABLE} VALUES (?,?)', (identity, payload))
                    elif operation == 'delete':h.db.execute(f'DELETE FROM {study.split.TABLE}')
                    elif operation == 'unrelated':
                        h.db.execute('INSERT INTO cnf_pattern_sources_v1 VALUES (?,?)', ('unrelated', '{}'))
                    else:h.db.execute(f'UPDATE {study.split.TABLE} SET payload=payload WHERE id=?', (identity,))
                    if operation == 'rollback':h.db.rollback()
                    else:h.db.commit()
                    with self.assertRaises(ValueError):registry.refresh()
                    with self.assertRaises(ValueError):registry.refresh()
                finally:h.close()

    def test_external_writer_policy_schema_and_uncommitted_changes(self):
        for operation in ('external', 'policy', 'schema', 'transaction'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as td:
                path = Path(td)/'h';h = self.history(path)
                try:
                    source = self.source(h);registry = SplitRegistry(h)
                    if operation == 'external':
                        other = sqlite3.connect(path)
                        try:
                            other.execute(f"UPDATE {PATTERNS} SET payload=payload || ' ' WHERE id=?", (source,));other.commit()
                        finally:other.close()
                    elif operation == 'policy':h.config['candidate_limit'] += 1
                    elif operation == 'schema':h.db.execute('CREATE TABLE foreign_table (id INTEGER)');h.db.commit()
                    else:h.db.execute('BEGIN')
                    with self.assertRaises(ValueError):registry.refresh()
                finally:h.close()

    def test_cold_rebuild_checks_each_pair_and_rejects_forgery(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h';h = self.history(path)
            try:
                source = self.source(h);record = study.split.acquire_record(h, source, 5, Counter())
                study.acquire(h, record);registry = SplitRegistry(h);expected = catalog(registry)
            finally:h.close()
            h = self.history(path);h.set_admission_budget(0)
            try:
                with study.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('acquisition')):
                    registry = SplitRegistry(h)
                    self.assertEqual(catalog(registry), expected)
                    self.assertEqual(registry.counts['registry_verified_records'], 1)
                bad = copy.deepcopy(record);bad['branches'].pop()
                h.db.execute(f'UPDATE {study.split.TABLE} SET payload=?', (study.encode(bad),));h.db.commit()
            finally:h.close()
            h = self.history(path)
            try:
                with self.assertRaises(ValueError):SplitRegistry(h)
            finally:h.close()


if __name__ == '__main__':unittest.main()
