from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_bundle import TABLES
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_source_local import local_inventory, SourceProbeRoutes, advance_one, check_delta
from experiments.compare_cnf_probe_continuation import apply_delta, digests, TABLES as DELTA_TABLES

OPTIONS = dict(max_depth=2,probe_limit=4,learn_limit=4,clause_growth_limit=2)


def seed(path,name='clear'):
    h = BudgetedInventory(path,**OPTIONS); h.set_admission_budget(32)
    for table in DELTA_TABLES:
        h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    cnf = json.loads(Path('solver/fixtures/probe-continuation.json').read_text())[name]
    key = h._edge(cnf,0)['key']; h.close()
    return key,cnf


class SourceLocalTests(unittest.TestCase):
    def test_omitted_existing_state_never_admitted(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,cnf=seed(p/'parent'); before=(p/'parent').read_bytes()
            with local_inventory(p/'parent',p/'local',OPTIONS) as (h,store):
                h.set_admission_budget(0)
                with patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('rediscovery')):
                    self.assertEqual(h._edge(cnf,0)['key'],key)
                self.assertFalse(h.admitted); self.assertGreater(store.counts['imported_rows'],0)
                self.assertFalse(any(store.export_delta(p/'delta').values()))
            self.assertEqual((p/'parent').read_bytes(),before)

    def test_matching_prefixes_cold_merge_and_exhaustion(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,_=seed(p/'parent'); shutil.copyfile(p/'parent',p/'full')
            full=BudgetedInventory(p/'full',**OPTIONS); full.set_admission_budget(32)
            eager=ContinuationRoutes(full); reference=[]
            for _ in range(6): reference.append(advance_one(full,eager,key,Counter()))
            full.close()
            before=digests(p/'parent')
            with local_inventory(p/'parent',p/'local',OPTIONS) as (h,store):
                h.set_admission_budget(32); routes=SourceProbeRoutes(h,key)
                actual=[advance_one(h,routes,key,Counter()) for _ in range(6)]
                self.assertEqual(actual,reference)
                self.assertIsNone(actual[-1]['record'])
                self.assertEqual(sum(store.export_delta(p/'delta').values()),5)
                with self.assertRaises(ValueError): list(routes.windows)
            self.assertEqual(digests(p/'parent'),before)
            shutil.copyfile(p/'parent',p/'merged'); apply_delta(p/'merged',p/'delta')
            self.assertEqual(check_delta(p/'merged',p/'delta',OPTIONS)['checked_delta_rows'],5)
            self.assertEqual(digests(p/'full'),digests(p/'merged'))
            merged_before=(p/'merged').read_bytes(); apply_delta(p/'merged',p/'delta')
            self.assertEqual((p/'merged').read_bytes(),merged_before)
            with local_inventory(p/'merged',p/'cold',OPTIONS) as (h,store):
                h.set_admission_budget(0)
                with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('rediscovery')):
                    self.assertIsNone(advance_one(h,SourceProbeRoutes(h,key),key,Counter())['record'])
                self.assertFalse(any(store.export_delta(p/'empty').values()))

    def test_forced_pending_resume_and_shared_allowance(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,_=seed(p/'parent','forced')
            with local_inventory(p/'parent',p/'local',OPTIONS) as (h,store):
                h.set_admission_budget(0); routes=SourceProbeRoutes(h,key)
                self.assertFalse(advance_one(h,routes,key,Counter())['admission_stopped'])
                forced=advance_one(h,routes,key,Counter())
                self.assertTrue(forced['admission_stopped']); store.export_delta(p/'delta')
            shutil.copyfile(p/'parent',p/'merged'); apply_delta(p/'merged',p/'delta')
            check_delta(p/'merged',p/'delta',OPTIONS)
            with local_inventory(p/'merged',p/'cold',OPTIONS) as (h,store):
                h.set_admission_budget(32); routes=SourceProbeRoutes(h,key)
                with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('rediscovery')):
                    result=advance_one(h,routes,key,Counter())
                self.assertEqual(result['record'],forced['record']); self.assertFalse(result['admission_stopped'])
                admitted=set(h.admitted); self.assertTrue(admitted)
                advance_one(h,routes,key,Counter()); self.assertEqual(h.admitted,admitted)
                store.export_delta(p/'nodes')
            apply_delta(p/'merged',p/'nodes'); check_delta(p/'merged',p/'nodes',OPTIONS)

    def test_missing_and_corrupt_prefixes_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,_=seed(p/'parent')
            h=BudgetedInventory(p/'parent',**OPTIONS); h.set_admission_budget(0)
            routes=ContinuationRoutes(h)
            for _ in range(3): advance_one(h,routes,key,Counter())
            identity=encode([key,4,8]); h.close()
            for mode in ('missing','foreign','bad_trace'):
                path=p/mode; shutil.copyfile(p/'parent',path); db=sqlite3.connect(path)
                if mode=='missing':
                    db.execute('DELETE FROM cnf_probe_continuations_v1 WHERE id=?',(encode([key,4,4]),))
                else:
                    window=encode([key,4]); payload=db.execute('SELECT payload FROM cnf_probe_windows_v1 WHERE id=?',(window,)).fetchone()[0]
                    row=json.loads(payload)
                    if mode=='foreign': row['source']='foreign'
                    else: row['probing']['attempts'][0]['value']=True
                    db.execute('UPDATE cnf_probe_windows_v1 SET payload=? WHERE id=?',(encode(row),window))
                db.commit(); db.close()
                with local_inventory(path,p/(mode+'-work'),OPTIONS) as (h,store):
                    h.set_admission_budget(0)
                    with self.assertRaises(ValueError): SourceProbeRoutes(h,key)._verify_saved(h,identity,Counter())

    def test_authoritative_collision_rollback_and_denied_queries(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,_=seed(p/'parent')
            with local_inventory(p/'parent',p/'local',OPTIONS) as (h,store):
                with self.assertRaises(ValueError):
                    store.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',(key,'{}'))
                for sql in ('SELECT id,payload FROM cnf_patterns_v1','DELETE FROM cnf_patterns_v1',
                            'SELECT payload FROM alien WHERE id=?'):
                    with self.assertRaises(ValueError): store.execute(sql,('x',))
                with self.assertRaises(RuntimeError):
                    with store:
                        store.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',('new','{}'))
                        raise RuntimeError('rollback')
                self.assertFalse(any(store.export_delta(p/'delta').values()))
                with self.assertRaises(ValueError):
                    SourceProbeRoutes(h,key).advance(h,'foreign',Counter())

    def test_nonempty_partial_store_cannot_override_authority(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); seed(p/'parent'); seed(p/'local')
            with self.assertRaises(ValueError):
                with local_inventory(p/'parent',p/'local',OPTIONS): pass

    def test_delta_corruption_rejected_after_merge(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); key,_=seed(p/'parent')
            with local_inventory(p/'parent',p/'local',OPTIONS) as (h,store):
                h.set_admission_budget(0)
                record=advance_one(h,SourceProbeRoutes(h,key),key,Counter())['record']
                store.export_delta(p/'delta')
            bad=copy.deepcopy(record); bad['probing']['attempts'][0]['value']=True
            db=sqlite3.connect(p/'delta'); db.execute('UPDATE cnf_probe_windows_v1 SET payload=?',(encode(bad),)); db.commit(); db.close()
            shutil.copyfile(p/'parent',p/'merged'); apply_delta(p/'merged',p/'delta')
            with self.assertRaises(ValueError): check_delta(p/'merged',p/'delta',OPTIONS)


if __name__=='__main__': unittest.main()
