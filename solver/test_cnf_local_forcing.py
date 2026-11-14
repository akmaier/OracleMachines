from collections import Counter
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_source_local import advance_one,check_delta,local_inventory,SourceProbeRoutes
from experiments.continue_cnf_source_local import worker
from experiments.compare_cnf_probe_continuation import apply_delta
from solver.test_cnf_source_local import seed,OPTIONS


class LocalForcingTests(unittest.TestCase):
    def test_matched_forced_acquisition_delta_and_cold_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);key,_=seed(p/'authority','forced')
            h=BudgetedInventory(p/'authority',**OPTIONS);h.set_admission_budget(0)
            advance_one(h,ContinuationRoutes(h),key,Counter());h.close()
            claim=dict(source=key,options=OPTIONS,state_limit=32)
            eager=worker('eager',p/'authority',claim,p/'eager-delta')
            local=worker('local',p/'authority',claim,p/'local-delta')
            for field in ('result','admitted','counts','delta_rows','delta_sha256'):
                self.assertEqual(eager[field],local[field])
            self.assertTrue(local['admitted']);self.assertFalse(local['result']['admission_stopped'])
            self.assertEqual(local['result']['record']['probing']['status'],'forced')
            shutil.copyfile(p/'authority',p/'merged');apply_delta(p/'merged',p/'local-delta')
            self.assertGreater(check_delta(p/'merged',p/'local-delta',OPTIONS)['checked_delta_rows'],1)
            with local_inventory(p/'merged',p/'reopened',OPTIONS) as (h,store):
                h.set_admission_budget(0)
                with patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('rediscovery')),patch(
                    'experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('reprobe')):
                    result=advance_one(h,SourceProbeRoutes(h,key),key,Counter())
                self.assertEqual(result,local['result']);self.assertFalse(h.admitted)
                self.assertFalse(any(store.export_delta(p/'empty-delta').values()))

    def test_matched_zero_allowance_keeps_forced_pending_edge(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);key,_=seed(p/'authority','forced')
            h=BudgetedInventory(p/'authority',**OPTIONS);h.set_admission_budget(0)
            advance_one(h,ContinuationRoutes(h),key,Counter());h.close()
            claim=dict(source=key,options=OPTIONS,state_limit=0)
            eager=worker('eager',p/'authority',claim,p/'eager')
            local=worker('local',p/'authority',claim,p/'local')
            self.assertEqual(eager['result'],local['result']);self.assertEqual(eager['delta_sha256'],local['delta_sha256'])
            self.assertTrue(local['result']['admission_stopped']);self.assertFalse(local['admitted'])
            self.assertEqual(local['delta_rows']['cnf_patterns_v1'],0)
            self.assertIsNotNone(local['result']['record']['edge'])


if __name__=='__main__':unittest.main()
