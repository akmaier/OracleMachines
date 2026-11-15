import ast
from collections import Counter
import contextlib
import gzip
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import types
import unittest
from unittest.mock import patch

from solver import test_cnf_expansion_session as fixtures
from experiments.cnf_copyless_worker import worker
from experiments.cnf_failed_append import preserve_failure
from experiments.cnf_append_delta import AppendDelta
from experiments.compare_cnf_probe_continuation import TABLES, digests
from experiments.compare_cnf_projection_bridge import read_archive
from solver.test_cnf_source_local import OPTIONS


class CopylessWorkerTests(unittest.TestCase):
    prepare = fixtures.ExpansionSessionTests.prepare

    def test_copy_and_append_modes_have_identical_successful_expansion(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);results=[]
            for mode in ('copy','append'):
                base=root/mode;base.mkdir();h,key,ev,s,_=self.prepare(base)
                with contextlib.redirect_stdout(io.StringIO()):
                    r,s=worker(base/'out',base/'tmp',base/'history',dict(options=OPTIONS),ev,[],key,s,'live',mode)
                results.append((r,digests(base/'history')))
                self.assertEqual((base/'tmp'/'batch-seed').exists(),mode=='copy')
                self.assertEqual(r['seed_copy_bytes']>0,mode=='copy')
            a,b=[x[0] for x in results]
            self.assertEqual(results[0][1],results[1][1])
            for field in ('target_flags','without_growth_flags','admitted_state_sha256','completed_new_state_sha256',
                          'entered_but_unstored_sha256','seed_table_digests','admission_counts'):
                self.assertEqual(a[field],b[field])
            self.assertEqual([read_archive(x['operation']) for x in a['steps']],
                             [read_archive(x['operation']) for x in b['steps']])
            self.assertEqual(a['delta']['database_sha256'],b['delta']['database_sha256'])

    def small_db(self, root):
        path=root/'history';db=sqlite3.connect(path);self.addCleanup(db.close)
        for table in TABLES:
            db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            db.execute(f'INSERT INTO {table} VALUES (?,?)',('old','old'))
        db.commit();(root/'out').mkdir();(root/'tmp').mkdir()
        return types.SimpleNamespace(db=db),path

    def test_failure_preserves_append_without_seed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);h,path=self.small_db(root);boundary=AppendDelta(h.db)
            with h.db:h.db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('new','evidence'))
            r=preserve_failure(root/'out',root/'tmp',h,path,root/'missing',boundary)
            self.assertEqual(r['kind'],'unchecked_delta');self.assertFalse(r['verified_checkpoint'])
            with sqlite3.connect(root/'tmp'/'failed-delta') as db:
                self.assertEqual(db.execute(f'SELECT * FROM {TABLES[0]}').fetchall(),[('new','evidence')])

    def test_failure_with_copied_seed_uses_full_comparison(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);h,path=self.small_db(root);shutil.copyfile(path,root/'seed')
            boundary=AppendDelta(h.db)
            with h.db:h.db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('new','evidence'))
            r=preserve_failure(root/'out',root/'tmp',h,path,root/'seed',boundary)
            self.assertEqual(r['kind'],'unchecked_delta');self.assertFalse(r['verified_checkpoint'])
            self.assertEqual(r['delta']['added_rows'][TABLES[0]],1)

    def test_rejected_boundary_keeps_untrusted_snapshot_and_committed_rows(self):
        for kind in ('update','rollback','no_boundary'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);h,path=self.small_db(root);boundary=AppendDelta(h.db)
                with h.db:h.db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('committed','keep'))
                if kind=='update':
                    with h.db:h.db.execute(f'UPDATE {TABLES[0]} SET payload=? WHERE id=?',('changed','old'))
                elif kind=='rollback':h.db.execute(f'INSERT INTO {TABLES[0]} VALUES (?,?)',('uncommitted','discard'))
                else:boundary=None
                r=preserve_failure(root/'out',root/'tmp',h,path,root/'missing',boundary)
                self.assertEqual(r['kind'],'unchecked_snapshot');self.assertFalse(r['verified_checkpoint'])
                self.assertEqual(r['rolled_back_uncommitted'],kind=='rollback')
                with sqlite3.connect(root/'tmp'/'failed-history') as db:
                    rows=dict(db.execute(f'SELECT * FROM {TABLES[0]}'))
                    self.assertEqual(rows['committed'],'keep');self.assertNotIn('uncommitted',rows)

    def test_worker_failure_archives_results_and_reraises(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);h,key,ev,s,_=self.prepare(root)
            # Fail after acquisition has committed; the suffix must survive.
            with patch.object(s.maintenance,'refresh',side_effect=RuntimeError('injected failure')):
                with self.assertRaisesRegex(RuntimeError,'injected failure'):
                    worker(root/'out',root/'tmp',root/'history',dict(options=OPTIONS),ev,[],key,s,'live','append')
            r=json.loads((root/'out'/'failed-report.json').read_text())
            self.assertEqual(r['failure_evidence']['kind'],'unchecked_delta')
            self.assertFalse(r['failure_evidence']['verified_checkpoint'])
            self.assertGreater(r['failure_evidence']['delta']['rows_exported'],0)
            self.assertFalse((root/'out'/'report.json').exists())

    def test_acquisition_loop_is_exact_frozen_baseline_ast(self):
        def loop(path):
            tree=ast.parse(Path(path).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
            # The complete successful acquisition/check/export block must match.
            block=[n for n in fn.body if isinstance(n,ast.Try)][-1]
            return ast.dump(ast.Module(body=block.body,type_ignores=[]),include_attributes=False)
        self.assertEqual(loop('experiments/cnf_digest_worker.py'),loop('experiments/cnf_copyless_worker.py'))

    def test_unsupported_modes_rejected_before_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for digest,seed in [('copy','append'),('guarded','append'),('live','unknown')]:
                with self.assertRaises(ValueError):worker(root/'out',root/'tmp',root/'absent',{},[],[],None,None,digest,seed)
                self.assertFalse((root/'out').exists())


if __name__=='__main__':unittest.main()
