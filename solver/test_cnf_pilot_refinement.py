from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_pilot_refinement import PilotRefinement,base

PARENT=Path('experiments/results/cnf-saved-split-reuse')


class PilotRefinementTests(unittest.TestCase):
    def history(self,path):
        cp=base.load(PARENT/'checkpoint.json');target=base.load(PARENT/'next-discovery.json')
        base.restore_archive(cp['archive'],path);h=base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
        root=base.load(cp['queries']['path'])[target['case']]['roots'][0]
        return h,root,target['source']

    def test_one_shared_budget_and_preserved_initial_rows(self):
        with tempfile.TemporaryDirectory() as td:
            h,root,source=self.history(Path(td)/'h')
            try:
                initial=base.rows(h);s=PilotRefinement(h,root,source);r=s.batch(state_limit=32,pair_limit=16)
                self.assertLessEqual(r['entered'],32);self.assertTrue(initial.items()<=base.rows(h).items())
                self.assertLessEqual(sum(e['entered'] for e in r['pilot_state']['events']),r['entered'])
                self.assertLessEqual(sum(e['assumptions'] for e in r['pilot_state']['events']),r['selection_counts'].get('bootstrap_fresh_assumptions',0))
            finally:h.close()

    def test_pending_pilot_stays_on_its_arm_across_cold_resume(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,root,source=self.history(path)
            try:
                initial=base.rows(h);s=PilotRefinement(h,root,source);r=s.batch(state_limit=0,pair_limit=16)
                state=r['pilot_state'];self.assertEqual(r['entered'],0);self.assertEqual(state['completed'],0)
                self.assertTrue(state['events'][-1]['pending']);self.assertEqual(initial,base.rows(h))
                frontier=r['frontier'];saved=base.rows(h)
            finally:h.close()
            h=base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
            try:
                with base.no_acquisition(),patch.object(base.split,'discover_simplification',side_effect=AssertionError('restart acquired')):
                    s=PilotRefinement(h,root,source,state);self.assertEqual(s.frontier(),frontier)
                r=s.batch(state_limit=128,pair_limit=1)
                self.assertGreaterEqual(r['pilot_state']['completed'],1);self.assertTrue(saved.items()<=base.rows(h).items())
            finally:h.close()

    def test_restart_matches_uninterrupted_choice_and_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            finals=[]
            for restart in (False,True):
                path=Path(td)/str(restart);h,root,source=self.history(path)
                try:
                    s=PilotRefinement(h,root,source);first=s.batch(state_limit=128,pair_limit=2)
                    self.assertEqual(first['pilot_state']['completed'],2)
                    if restart:
                        h.close();h=base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
                        s=PilotRefinement(h,root,source,first['pilot_state'])
                    for _ in range(4):
                        if s.coverage.closed()[0]:break
                        s.batch(state_limit=128,pair_limit=16)
                    self.assertTrue(s.coverage.closed()[0])
                    flags,plan=base.compose(h,[root],s.registry,Counter());proof=base.expand(h,plan,[root],s.registry,Counter())
                    base.split.verify_positive(h,proof,[root],list(s.records.values()),Counter())
                    finals.append((base.rows(h),dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}')),s.state(),proof))
                finally:h.close()
            self.assertEqual(finals[0],finals[1])

    def test_foreign_or_inconsistent_schedule_and_source_fail(self):
        with tempfile.TemporaryDirectory() as td:
            h,root,source=self.history(Path(td)/'h')
            try:
                state=PilotRefinement(h,root,source).state()
                for field,value in [('root','foreign'),('completed',True),('completed',2),('candidates',['foreign','another'])]:
                    bad=copy.deepcopy(state);bad[field]=value
                    with self.assertRaises(ValueError):PilotRefinement(h,root,source,bad)
                with self.assertRaises(ValueError):PilotRefinement(h,root,'foreign')
            finally:h.close()


if __name__=='__main__':unittest.main()
