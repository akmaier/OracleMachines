from collections import Counter
import copy
import gzip
import json
from pathlib import Path
import unittest

from experiments.cnf_projection_acquisition import propose, acquire_projection
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_projection_bridge import check
from solver.test_cnf_projection_lookup import Authority

SOURCE=[[1,2],[-1,3],[2,3,4],[-4,2]]


class ProjectionAcquisitionTests(unittest.TestCase):
    def test_saved_candidate_reconstructed_exactly(self):
        r=json.loads(Path('experiments/results/cnf-projection-bridge/report.json').read_text())
        with gzip.open(r['next_selection']['path']) as f:source=json.load(f)['source']
        q=json.loads(Path('experiments/results/cnf-projection-lookup/report.json').read_text())
        with gzip.open(q['selected_diagnostics']['path']) as f:target=json.load(f)[0]
        h=Authority();h.config=json.loads(source)[1];self.assertEqual(h.add(json.loads(source)[-1]),source)
        counts=Counter();record=propose(h,source,13,counts)
        self.assertEqual(record['target'],target['minimal_key'])
        self.assertEqual(len(record['proof']['subsumers']),1)
        check(json.loads(source)[-1],json.loads(record['target'])[-1],record['proof'])

    def test_pending_never_becomes_a_bridge_and_resume_is_exact(self):
        h=BudgetedInventory(':memory:',max_depth=0)
        try:
            h.set_admission_budget(32);source=h.inspect(SOURCE)['root']['key']
            record=propose(h,source,1,Counter());before=set(h.admitted)
            row=acquire_projection(h,record,target_limit=0)
            self.assertTrue(row['pending']);self.assertIsNone(row['bridge']);self.assertEqual(h.admitted,before)
            row=acquire_projection(h,record,target_limit=1)
            self.assertFalse(row['pending']);self.assertEqual(row['bridge'],record)
            self.assertTrue(before<=h.admitted);self.assertEqual(len(row['added']),1)
            before=set(h.admitted);again=acquire_projection(h,record,target_limit=0)
            self.assertFalse(again['pending']);self.assertFalse(again['added']);self.assertEqual(before,h.admitted)
        finally:h.close()

    def test_shared_budget_is_never_reset(self):
        h=BudgetedInventory(':memory:',max_depth=0)
        try:
            h.set_admission_budget(1);source=h.inspect(SOURCE)['root']['key'];self.assertEqual(len(h.admitted),1)
            record=propose(h,source,1,Counter());before=set(h.admitted)
            row=acquire_projection(h,record,state_limit=1,target_limit=32)
            self.assertTrue(row['pending']);self.assertEqual(h.admitted,before);self.assertEqual(h.admission_limit,1)
            with self.assertRaises(ValueError):acquire_projection(h,record,state_limit=32)
        finally:h.close()

    def test_tampered_proposal_cannot_acquire_unproved_target(self):
        h=BudgetedInventory(':memory:',max_depth=0)
        try:
            h.set_admission_budget(32);source=h.inspect(SOURCE)['root']['key'];record=propose(h,source,1,Counter())
            for mutate in (lambda x:x['proof'].update(variable=True),lambda x:x['proof']['subsumers'].clear(),
                           lambda x:x.update(target=h._canonical([[1]],0)[2])):
                bad=copy.deepcopy(record);mutate(bad);before=set(h.admitted)
                with self.assertRaises(ValueError):acquire_projection(h,bad)
                self.assertEqual(before,h.admitted)
        finally:h.close()

    def test_lost_support_in_subsumption_is_outside_current_bridge_contract(self):
        h=Authority();source=h.add([[1,2],[-1,2],[2,3]])
        with self.assertRaises(ValueError):propose(h,source,1,Counter())


if __name__=='__main__':unittest.main()
