from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import sqlite3
import shutil
import unittest
from unittest.mock import patch
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import TABLE, WindowRoutes, search, verify_window, choices
from experiments.cnf_route_composition import compose, verify_plan


class ProbeWindowTests(unittest.TestCase):
    def test_seven_table_delta_roundtrip_and_conflict(self):
        from experiments.compare_cnf_probe_window import TABLES,export_delta,apply_delta,digests
        with tempfile.TemporaryDirectory() as tmp:
            seed,history,delta,rebuilt=[Path(tmp)/n for n in ('seed','history','delta','rebuilt')]
            db=sqlite3.connect(seed)
            for table in TABLES:
                db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                db.execute(f'INSERT INTO {table} VALUES (?,?)',('old','old'))
            db.commit();db.close();shutil.copyfile(seed,history)
            db=sqlite3.connect(history)
            for table in TABLES:db.execute(f'INSERT INTO {table} VALUES (?,?)',('new','new'))
            db.commit();db.close();preserved,added=export_delta(seed,history,delta)
            self.assertTrue(all(preserved[t]==added[t]==1 for t in TABLES))
            shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
            self.assertEqual(digests(history),digests(rebuilt))
            before=rebuilt.read_bytes();apply_delta(rebuilt,delta);self.assertEqual(before,rebuilt.read_bytes())
            db=sqlite3.connect(delta);db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?',('bad','new'));db.commit();db.close()
            with self.assertRaises(ValueError):apply_delta(rebuilt,delta)
            self.assertEqual(before,rebuilt.read_bytes())

    def setup_history(self, path):
        h = BudgetedInventory(path,max_depth=2,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        for table in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1',TABLE):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit(); return h

    def test_pending_restart_reuse_and_exact_plan(self):
        source = json.loads(Path('experiments/results/cnf-coupled-pivots-originals/core-admission-audit.json').read_text())['cores'][0]['source']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history'; h = self.setup_history(path); h.set_admission_budget(32)
            root = h._edge(source,0)['key']; routes = WindowRoutes(h)
            self.assertEqual(choices(h,root,4,Counter())[1], [14,15,23,1])
            result = search(h,root,routes,Counter(),state_limit=0)
            self.assertIsNotNone(result['budget_stop']); self.assertEqual(len(routes.windows),1)
            self.assertEqual(compose(h,[root],routes,Counter())[0],[False])
            saved = dict(h.db.execute(f'SELECT id,payload FROM {TABLE}')); h.close()
            h = self.setup_history(path); routes = WindowRoutes(h)
            self.assertEqual(routes.counts['pending_probe_windows'],1)
            counts = Counter(); result = search(h,root,routes,counts)
            self.assertIsNone(result['budget_stop']); self.assertEqual(len(routes.windows),2)
            self.assertEqual(counts['reused_probe_windows'],1); self.assertLessEqual(len(h.admitted),32)
            for key,payload in saved.items():
                self.assertEqual(h.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone(),(payload,))
            closed, plan = compose(h,[root],routes,Counter()); self.assertEqual(closed,[True])
            verify_plan(h,plan,[root],routes,Counter())
            before = h.storage(); counts = Counter()
            with patch('experiments.cnf_probe_window.discover_probes',side_effect=AssertionError('rediscovery')):
                search(h,root,routes,counts,state_limit=0)
            self.assertEqual(counts['reused_probe_windows'],2); self.assertEqual(h.storage(),before)
            record = next(iter(routes.windows.values()))
            for field,value in [('width',True),('width',5),('edge',None),('source','missing')]:
                bad = copy.deepcopy(record); bad[field] = value
                with self.assertRaises(ValueError): verify_window(h,bad,Counter())
            bad = copy.deepcopy(record); bad['probing']['attempts'][-1]['certificate']['conflict'] = None
            with self.assertRaises(ValueError): verify_window(h,bad,Counter())
            h.close()

    def test_inconclusive_window_is_not_a_coverage_edge(self):
        source = json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        with tempfile.TemporaryDirectory() as tmp:
            h = self.setup_history(Path(tmp)/'history'); h.set_admission_budget(200)
            root = h._edge(source,0)['key']
            from experiments.cnf_coupled_pivots import FrontierIndex
            from experiments.cnf_probe_window import acquire_record
            leaves = FrontierIndex(h).frontier(root); leaf = next(iter(leaves)); known = {}
            record,_ = acquire_record(h,leaf,known,Counter(),width=0)
            self.assertEqual(record['probing'],dict(status='clear',attempts=[])); self.assertIsNone(record['edge'])
            verify_window(h,record,Counter(),width=0)
            bad = copy.deepcopy(record); bad['edge'] = dict(key=root,names=[])
            with self.assertRaises(ValueError): verify_window(h,bad,Counter(),width=0)
            h.close()


if __name__=='__main__': unittest.main()
