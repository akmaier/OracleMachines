from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_original_binding import bind_original_focus
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_route_composition import compose
from experiments.compare_cnf_probe_continuation import TABLES, digests
from experiments.compare_cnf_projection_bridge import routes_for
from solver.test_cnf_source_local import OPTIONS


class OriginalBindingTests(unittest.TestCase):
    def prepare(self, root):
        path=root/'history'; options=dict(OPTIONS,max_depth=0)
        h=BudgetedInventory(path,**options);self.addCleanup(h.close)
        for t in TABLES:h.db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit();h.set_admission_budget(32)
        cnf=json.loads(Path('solver/fixtures/probe-continuation.json').read_text())['clear']
        opened=h._edge(cnf,0)['key'];closed=h._edge([[1]],0)['key']
        cases=[dict(source=cnf,original_case=10),dict(source=[[1]],original_case=11),dict(source=cnf,original_case=12)]
        h.set_admission_budget(0);ev=[[],[],[],[],[]];session=ExpansionSession(h,ev,[])
        session.begin(0,ev,[])
        return h,session,ev,cases,opened,closed

    def test_shared_original_binding_is_read_only_and_detached(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);h,s,ev,cases,opened,_=self.prepare(root)
            before=digests(root/'history');changes=h.db.total_changes
            with patch.object(h,'_discover',side_effect=AssertionError('fresh recognition')):
                got=bind_original_focus(h,s.maintenance.routes,cases,opened,[0,2])
                self.assertEqual([r['original_case'] for r in got['bindings']],[10,12])
                got['bindings'][0]['leaves'].clear()
                self.assertTrue(bind_original_focus(h,s.maintenance.routes,cases,opened,[0])['bindings'][0]['leaves'])
            self.assertEqual(before,digests(root/'history'));self.assertEqual(changes,h.db.total_changes)
            self.assertFalse(h.admitted)

    def test_invalid_indices_and_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h,s,ev,cases,opened,_=self.prepare(Path(td))
            for source,indices in [(opened,[]),(opened,[0,0]),(opened,[-1]),(opened,[3]),
                                   (opened,[True]),(opened,(0,)),('',[0]),(None,[0])]:
                with self.subTest(source=source,indices=indices), self.assertRaisesRegex(ValueError,'Invalid'):
                    bind_original_focus(h,s.maintenance.routes,cases,source,indices)
            self.assertFalse(h.admitted)

    def test_closed_original_and_unrelated_focus_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h,s,ev,cases,opened,closed=self.prepare(Path(td))
            for source,indices in [(closed,[1]),(opened,[1]),(closed,[0]),('missing',[0]),(opened,[0,1])]:
                with self.subTest(source=source,indices=indices), self.assertRaisesRegex(ValueError,'not an open'):
                    bind_original_focus(h,s.maintenance.routes,cases,source,indices)
            self.assertFalse(h.admitted)

    def test_closed_query_then_new_original_keeps_checked_objects(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);h,s,ev,cases,opened,closed=self.prepare(root)
            checked=h.checked;routes=s.maintenance.routes
            self.assertEqual(compose(h,[closed],routes,Counter())[0],[True])
            with patch.object(h,'_discover',side_effect=AssertionError('fresh recognition')):
                got=bind_original_focus(h,routes,cases,opened,[0]);s.begin(32,ev,[])
            self.assertIs(h.checked,checked);self.assertIs(s.maintenance.routes,routes)
            self.assertIn(closed,checked);self.assertFalse(h.admitted)
            fresh=BudgetedInventory(root/'history',**dict(OPTIONS,max_depth=0))
            try:
                fresh.set_admission_budget(0)
                expected=bind_original_focus(fresh,routes_for(fresh,ev,[]),cases,opened,[0])
                # Counts depend on cache hits; the exact binding does not.
                self.assertEqual(got['bindings'],expected['bindings'])
            finally:fresh.close()


if __name__=='__main__':unittest.main()
