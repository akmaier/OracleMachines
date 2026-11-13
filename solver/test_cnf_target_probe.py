from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_learning import LearnedTraceRoutes
from experiments.cnf_target_probe import search,remaining
from experiments.cnf_route_composition import compose,verify_plan


class TargetProbeTests(unittest.TestCase):
    def history(self,path):
        h=BudgetedInventory(path,max_depth=2,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        for t in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1',
                  'cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit();return h

    def seed(self,h,name):
        cnf=json.loads(Path('solver/fixtures/probe-continuation.json').read_text())[name]
        h.set_admission_budget(32);key=h._edge(cnf,0)['key']
        self.assertEqual(h._load(key)['kind'],'unresolved');return key

    def test_clear_source_advances_across_blocks_without_resetting_budget(self):
        with tempfile.TemporaryDirectory() as td:
            h=self.history(Path(td)/'h');root=self.seed(h,'clear');routes=LearnedTraceRoutes(h)
            counts=Counter();reset=h.set_admission_budget
            with patch.object(h,'set_admission_budget',wraps=reset) as budget:
                result=search(h,root,routes,counts,source_limit=1,state_limit=0)
            self.assertEqual(budget.call_count,1)
            self.assertEqual([v['offset'] for v in result['visits']],[0,4,8,12,16,None])
            self.assertEqual(result['distinct_sources'],1);self.assertIsNone(result['stop'])
            self.assertEqual(len(h.admitted),0);self.assertEqual(counts['probe_attempts'],36)
            rows=remaining(h,[dict(source=root,target=root)],routes,Counter())
            self.assertFalse(rows[0]['closed']);self.assertEqual(rows[0]['leaves'][0]['remaining_ranked_variables'],[])
            with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('rediscovery')):
                again=search(h,root,routes,Counter(),state_limit=0)
            self.assertEqual(len(again['visits']),1);h.close()

    def test_pending_forced_target_restart_and_finite_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h=self.history(path);root=self.seed(h,'forced');routes=LearnedTraceRoutes(h)
            result=search(h,root,routes,Counter(),source_limit=1,state_limit=0)
            self.assertEqual(result['stop'],'admission_limit');self.assertEqual(len(result['visits']),2)
            self.assertEqual(result['visits'][-1]['status'],'forced')
            pending=remaining(h,[dict(source=root,target=root)],routes,Counter())
            self.assertTrue(pending[0]['leaves'][0]['pending']);self.assertFalse(compose(h,[root],routes,Counter())[0][0])
            saved={t:dict(h.db.execute(f'SELECT id,payload FROM {t}')) for t in ('cnf_probe_windows_v1','cnf_probe_continuations_v1')};h.close()
            h=self.history(path);routes=LearnedTraceRoutes(h);counts=Counter()
            with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('rediscovery')):
                result=search(h,root,routes,counts,step_limit=1,state_limit=32)
            self.assertNotEqual(result['stop'],'admission_limit');self.assertEqual(counts.get('probe_attempts',0),0)
            self.assertLessEqual(len(h.admitted),32)
            for t,rows in saved.items():self.assertEqual(rows,dict(h.db.execute(f'SELECT id,payload FROM {t}')))
            _,plan=compose(h,[root],routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter());h.close()

    def test_step_and_source_limits_do_not_erase_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            h=self.history(Path(td)/'h');root=self.seed(h,'clear');routes=LearnedTraceRoutes(h)
            counts=Counter();none=search(h,root,routes,counts,step_limit=0)
            self.assertEqual(none['stop'],'step_limit');self.assertFalse(routes.windows)
            none=search(h,root,routes,counts,source_limit=0)
            self.assertEqual(none['stop'],'source_limit');self.assertFalse(routes.windows)
            first=search(h,root,routes,Counter(),step_limit=1)
            self.assertEqual(first['stop'],'step_limit');self.assertEqual(first['visits'][0]['offset'],0)
            second=search(h,root,routes,Counter(),step_limit=1)
            self.assertEqual(second['visits'][0]['offset'],4);self.assertEqual(len(routes.windows),1)
            for name in ('step_limit','source_limit','state_limit'):
                with self.assertRaises(ValueError):search(h,root,routes,Counter(),**{name:True})
            h.close()


if __name__=='__main__':unittest.main()
