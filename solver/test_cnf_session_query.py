from collections import Counter
import sqlite3
import tempfile
from pathlib import Path
import unittest

from solver import test_cnf_expansion_session as fixtures
from experiments.cnf_session_query import query, query_boundary
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.compare_cnf_projection_bridge import add_splits, routes_for


class SessionQueryTests(unittest.TestCase):
    prepare = fixtures.ExpansionSessionTests.prepare

    def test_query_after_interrupted_and_completed_expansion_preserves_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td))
            for limit in (1,32):
                m=s.begin(limit,ev,[])
                op=WarmExpansion(h,state_limit=limit).advance(key,m.routes,Counter(),pending_split=rec)
                ev=add_splits(ev,[rec]);m.refresh(op,ev,[])
                entered=set(h.admitted);counts=dict(h.admission_counts);batches=s.batches
                fresh=routes_for(h,ev,[])
                self.assertEqual(dict(m.routes.by_source),dict(fresh.by_source))
                a,sa,pa=query(s,ev,[],[key],'maintained')
                b,sb,pb=query(s,ev,[],[key],'rebuild')
                self.assertEqual((a['closed'],sa,pa),(b['closed'],sb,pb))
                self.assertEqual((h.admitted,dict(h.admission_counts),s.batches),(entered,counts,batches))
                self.assertFalse(h.db.in_transaction)

    def test_stale_state_rejected(self):
        for kind in ('write','admission','sidecar','policy','prepared_policy','external','schema'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);h,key,ev,s,rec=self.prepare(root)
                if kind=='write':
                    with h.db:h.db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?",(key,))
                elif kind=='admission':h.admitted.add('unreported')
                elif kind=='sidecar':ev=add_splits(ev,[rec])
                elif kind=='policy':h.config['max_depth']+=1
                elif kind=='prepared_policy':h.prepared.config['max_depth']+=1
                elif kind=='schema':h.db.execute('CREATE TABLE extra(x)');h.db.commit()
                else:
                    with sqlite3.connect(root/'history') as db:
                        db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?",(key,))
                with self.assertRaises(ValueError):query(s,ev,[],[key])
                self.assertFalse(h.db.in_transaction)

    def test_transaction_active_check_and_invalid_mode_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td))
            h.db.execute('BEGIN')
            with self.assertRaises(ValueError):query(s,ev,[],[key])
            self.assertTrue(h.db.in_transaction);h.db.rollback()
            h.prepared.active.add(key)
            with self.assertRaises(ValueError):query(s,ev,[],[key])
            h.prepared.active.clear()
            with self.assertRaises(ValueError):query(s,ev,[],[key],'unknown')

    def test_query_write_rolls_back_and_invalidates_session(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td))
            with self.assertRaises(ValueError):
                with query_boundary(s,ev,[]):
                    h.db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?",(key,))
            self.assertFalse(h.db.in_transaction)
            with self.assertRaises(ValueError):query(s,ev,[],[key])

    def test_exception_releases_boundary_without_resetting_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            h,key,ev,s,rec=self.prepare(Path(td));s.begin(32,ev,[])
            with self.assertRaisesRegex(RuntimeError,'stop'):
                with query_boundary(s,ev,[]):raise RuntimeError('stop')
            self.assertFalse(h.db.in_transaction);self.assertEqual(s.batches,1)
            query(s,ev,[],[key])


if __name__=='__main__':unittest.main()
