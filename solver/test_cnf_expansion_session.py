from collections import Counter
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_trace_split import candidates
from experiments.compare_cnf_projection_bridge import routes_for, add_splits
from experiments.cnf_route_composition import compose
from experiments.compare_cnf_probe_continuation import TABLES
from solver.test_cnf_source_local import OPTIONS


class ExpansionSessionTests(unittest.TestCase):
    def prepare(self, root):
        path=root/'history';h=BudgetedInventory(path,**OPTIONS);self.addCleanup(h.close)
        for t in TABLES:h.db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit();h.set_admission_budget(32)
        key=h._edge(json.loads(Path('solver/fixtures/trace-split.json').read_text()),0)['key']
        h.set_admission_budget(0);ev=[[],[],[],[],[]]
        session=ExpansionSession(h,ev,[])
        rec=candidates(h,key,session.maintenance.routes,Counter())[0]['record']
        return h,key,ev,session,rec

    def test_interrupted_batch_resumes_with_same_catalog_and_new_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td));m=s.begin(1,ev,[]);catalog=m.routes
            op=WarmExpansion(h,state_limit=1).advance(key,m.routes,Counter(),pending_split=rec)
            self.assertTrue(op['pending']);entered=set(h.admitted);self.assertTrue(entered)
            ev=add_splits(ev,[rec]);m.refresh(op,ev,[])
            checked=h.checked;prepared=h.prepared.checked
            self.assertIs(s.begin(32,ev,[]),m)
            self.assertFalse(h.admitted);self.assertFalse(h.admission_counts)
            self.assertIs(h.checked,checked);self.assertIs(h.prepared.checked,prepared);self.assertIs(m.routes,catalog)
            op=WarmExpansion(h).advance(key,m.routes,Counter(),pending_split=rec)
            m.refresh(op,ev,[])
            self.assertTrue(entered & h.admitted)  # unfinished inputs are charged again
            fresh=routes_for(h,ev,[])
            self.assertEqual(dict(m.routes.by_source),dict(fresh.by_source))
            self.assertEqual(compose(h,[key],m.routes,Counter()),compose(h,[key],fresh,Counter()))
            self.assertEqual(s.batches,2)

    def test_unmaintained_writes_admissions_sidecars_and_policy_rejected(self):
        for kind in ['write','admission','sidecar','policy','prepared_policy']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                h,key,ev,s,rec=self.prepare(Path(td));s.begin(32,ev,[])
                if kind=='write':
                    with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=payload WHERE id=?',(key,))
                elif kind=='admission':h.admitted.add('unreported')
                elif kind=='sidecar':ev=add_splits(ev,[rec])
                elif kind=='policy':h.config['max_depth']+=1
                else:h.prepared.config['max_depth']+=1
                before=set(h.admitted)
                with self.assertRaisesRegex(ValueError,'Unmaintained'):s.begin(32,ev,[])
                self.assertEqual(h.admitted,before);self.assertEqual(s.batches,1)

    def test_external_writer_and_schema_change_rejected(self):
        for schema in [False,True]:
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as td:
                root=Path(td);h,key,ev,s,rec=self.prepare(root)
                if schema:h.db.execute('CREATE TABLE extra (x)');h.db.commit()
                else:
                    other=sqlite3.connect(root/'history')
                    try:
                        with other:other.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?",(key,))
                    finally:other.close()
                with self.assertRaisesRegex(ValueError,'reopen'):s.begin(32,ev,[])
                self.assertEqual(s.batches,0)

    def test_open_transaction_active_check_and_bad_limit_preserve_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td));s.begin(32,ev,[])
            h.db.execute('BEGIN')
            with self.assertRaisesRegex(ValueError,'Finish'):s.begin(32,ev,[])
            with self.assertRaisesRegex(ValueError,'Finish'):ExpansionSession(h,ev,[])
            h.db.rollback();h.prepared.active.add(key)
            with self.assertRaisesRegex(ValueError,'Finish'):s.begin(32,ev,[])
            h.prepared.active.clear()
            with self.assertRaises(ValueError):s.begin(-1,ev,[])
            self.assertEqual(s.batches,1);self.assertEqual(h.admission_limit,32);self.assertFalse(h.db.in_transaction)


if __name__=='__main__':unittest.main()
