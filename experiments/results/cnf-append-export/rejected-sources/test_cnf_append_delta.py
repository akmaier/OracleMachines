import sqlite3
from pathlib import Path
import shutil
import tempfile
import unittest

from experiments.cnf_append_delta import AppendDelta
from experiments.compare_cnf_probe_continuation import TABLES, digests
from experiments.compare_cnf_split_batch import save_delta


class AppendDeltaTests(unittest.TestCase):
    def setup_db(self, root):
        path = root/'history'; db = sqlite3.connect(path)
        self.addCleanup(db.close)
        for t in TABLES:
            db.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            db.execute(f'INSERT INTO {t}(rowid,id,payload) VALUES (3,?,?)', ('old', 'original'))
        db.commit(); shutil.copyfile(path, root/'seed')
        return db

    def test_all_tables_and_order_equal_full_comparison(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
            for t in TABLES:
                with db:
                    db.execute(f'INSERT INTO {t} VALUES (?,?)', ('z', 'first'))
                    db.execute(f'INSERT INTO {t} VALUES (?,?)', ('a', 'second'))
            got = boundary.save(root/'fast', root/'fast.gz')
            expected = save_delta(root/'seed', root/'history', root/'full', root/'full.gz')
            self.assertEqual(digests(root/'fast'), digests(root/'full'))
            self.assertEqual(got['database_sha256'], expected['database_sha256'])
            self.assertEqual(got['preserved_rows'], expected['preserved_rows'])
            self.assertEqual(got['added_rows'], expected['added_rows'])
            again = boundary.save(root/'again', root/'again.gz')
            self.assertEqual(got['database_sha256'], again['database_sha256'])

    def test_empty_export_and_committed_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
            empty = boundary.save(root/'empty', root/'empty.gz'); self.assertEqual(empty['rows_exported'], 0)
            with db: db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)', ('new', 'value'))
            self.assertEqual(boundary.save(root/'new', root/'new.gz')['rows_exported'], 1)

    def test_updates_deletes_and_replacements_rejected(self):
        for sql in ('UPDATE {t} SET payload=payload', 'DELETE FROM {t}',
                    "INSERT OR REPLACE INTO {t} VALUES ('old','changed')",
                    "UPDATE {t} SET rowid=10"):
            with self.subTest(sql=sql), tempfile.TemporaryDirectory() as td:
                root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
                with db:
                    db.execute(sql.format(t=TABLES[0]))
                    db.execute(f'INSERT INTO {TABLES[1]} VALUES (?,?)', ('new', 'ok'))
                with self.assertRaisesRegex(ValueError, 'Non-append'):
                    boundary.save(root/'delta', root/'delta.gz')
                self.assertFalse((root/'delta').exists())

    def test_low_rowid_and_rolled_back_writes_rejected(self):
        for rollback in (False, True):
            with self.subTest(rollback=rollback), tempfile.TemporaryDirectory() as td:
                root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
                db.execute(f'INSERT INTO {TABLES[0]}(rowid,id,payload) VALUES (1,?,?)', ('new', 'value'))
                db.rollback() if rollback else db.commit()
                with self.assertRaisesRegex(ValueError, 'Non-append'):
                    boundary.save(root/'delta', root/'delta.gz')

    def test_external_writer_and_schema_changes_rejected(self):
        for schema in (False, True):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as td:
                root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
                if schema:
                    db.execute('CREATE TABLE extra (x)'); db.commit()
                else:
                    other = sqlite3.connect(root/'history')
                    try:
                        with other: other.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)', ('external', 'v'))
                    finally: other.close()
                with self.assertRaisesRegex(ValueError, 'external writer or schema'):
                    boundary.save(root/'delta', root/'delta.gz')

    def test_open_transaction_outputs_and_schema_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); db = self.setup_db(root); boundary = AppendDelta(db)
            db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)', ('new', 'value'))
            with self.assertRaisesRegex(ValueError, 'Commit'): AppendDelta(db)
            with self.assertRaisesRegex(ValueError, 'Commit'): boundary.save(root/'delta', root/'delta.gz')
            db.commit(); (root/'delta').write_text('keep')
            with self.assertRaisesRegex(ValueError, 'already exists'): boundary.save(root/'delta', root/'delta.gz')
            self.assertEqual((root/'delta').read_text(), 'keep')
            db.execute('CREATE TABLE extra (x)'); db.commit()
            with self.assertRaisesRegex(ValueError, 'Unsupported'): AppendDelta(db)


if __name__ == '__main__': unittest.main()
