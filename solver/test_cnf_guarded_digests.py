import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_guarded_digests import GuardedDigests
from experiments.compare_cnf_probe_continuation import TABLES, digests
from experiments.compare_cnf_clause_mask import table_digest


class GuardedDigestsTests(unittest.TestCase):
    def setup_db(self, root):
        db = sqlite3.connect(root/'history')
        self.addCleanup(db.close)
        for t in TABLES:
            db.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            db.execute(f'INSERT INTO {t}(rowid,id,payload) VALUES (3,?,?)', ('middle', 'original'))
        db.commit()
        return db

    def test_initial_full_scan_then_exact_unchanged_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=self.setup_db(root); cache=GuardedDigests(db)
            with patch('experiments.cnf_guarded_digests.table_digest', wraps=table_digest) as scan:
                first, stats=cache.snapshot()
                self.assertEqual(scan.call_count,len(TABLES))
                self.assertEqual(first,digests(root/'history'))
                first[TABLES[0]]['sha256']='caller mutation'
                again, stats=cache.snapshot()
                self.assertEqual(scan.call_count,len(TABLES))
                self.assertEqual(again,digests(root/'history'))
                self.assertEqual(stats['reused_tables'],list(TABLES))
                self.assertEqual(stats['scanned_rows'],0)

    def test_each_table_and_nonmonotone_keys_rescan_correctly(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=self.setup_db(root); cache=GuardedDigests(db); cache.snapshot()
            for t in TABLES:
                for key in ('z','a'):
                    with db: db.execute(f'INSERT INTO {t} VALUES (?,?)',(key,'value'))
                    with patch('experiments.cnf_guarded_digests.table_digest', wraps=table_digest) as scan:
                        got,stats=cache.snapshot()
                    self.assertEqual(got,digests(root/'history'))
                    self.assertEqual(scan.call_count,1)
                    self.assertEqual(stats['scanned_tables'],[t])
                    self.assertEqual(stats['added_rows'][t],1)

    def test_updates_deletes_replacements_and_low_rowids_invalidate(self):
        for sql in ('UPDATE {t} SET payload=payload','DELETE FROM {t}',
                    "INSERT OR REPLACE INTO {t} VALUES ('middle','changed')",
                    'UPDATE {t} SET rowid=10',
                    "INSERT INTO {t}(rowid,id,payload) VALUES (1,'low','value')"):
            with self.subTest(sql=sql), tempfile.TemporaryDirectory() as td:
                root=Path(td); db=self.setup_db(root); cache=GuardedDigests(db); cache.snapshot()
                with db:
                    db.execute(sql.format(t=TABLES[0]))
                    db.execute(f'INSERT INTO {TABLES[1]} VALUES (?,?)',('new','ok'))
                with self.assertRaisesRegex(ValueError,'Non-append'): cache.snapshot()
                with self.assertRaisesRegex(ValueError,'Invalidated'): cache.snapshot()
                self.assertEqual(GuardedDigests(db).snapshot()[0],digests(root/'history'))

    def test_rollback_rejected_and_open_transaction_can_be_finished(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=self.setup_db(root); cache=GuardedDigests(db); cache.snapshot()
            db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('new','ok'))
            with self.assertRaisesRegex(ValueError,'Commit'): cache.snapshot()
            db.commit(); self.assertEqual(cache.snapshot()[0],digests(root/'history'))
            db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('lost','ok')); db.rollback()
            with self.assertRaisesRegex(ValueError,'Non-append'): cache.snapshot()

    def test_external_writer_and_schema_changes_rejected(self):
        for schema in (False,True):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as td:
                root=Path(td); db=self.setup_db(root); cache=GuardedDigests(db); cache.snapshot()
                if schema:
                    db.execute('CREATE TABLE extra (x)'); db.commit()
                else:
                    other=sqlite3.connect(root/'history')
                    try:
                        with other: other.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('outside','v'))
                    finally: other.close()
                with self.assertRaisesRegex(ValueError,'external writer or schema'): cache.snapshot()

    def test_legacy_writes_rejected_and_noop_inserts_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=self.setup_db(root)
            db.execute('CREATE TABLE legacy (value TEXT)'); db.commit()
            cache=GuardedDigests(db); cache.snapshot()
            with db: db.execute(f"INSERT OR IGNORE INTO {TABLES[0]} VALUES ('middle','ignored')")
            self.assertEqual(cache.snapshot()[0],digests(root/'history'))
            with db: db.execute("INSERT INTO legacy VALUES ('changed')")
            with self.assertRaisesRegex(ValueError,'Non-append'): cache.snapshot()

    def test_empty_tables_and_unsupported_schema(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=self.setup_db(root)
            for t in TABLES: db.execute(f'DELETE FROM {t}')
            db.commit(); cache=GuardedDigests(db)
            self.assertEqual(cache.snapshot()[0],digests(root/'history'))
            with db: db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('first','ok'))
            self.assertEqual(cache.snapshot()[0],digests(root/'history'))
            db.execute(f'DROP TABLE {TABLES[0]}'); db.commit()
            with self.assertRaisesRegex(ValueError,'Missing'): GuardedDigests(db).snapshot()
            db.execute(f'CREATE TABLE {TABLES[0]} (id TEXT PRIMARY KEY,payload BLOB)'); db.commit()
            with self.assertRaisesRegex(ValueError,'Unsupported'): GuardedDigests(db).snapshot()


if __name__=='__main__': unittest.main()
