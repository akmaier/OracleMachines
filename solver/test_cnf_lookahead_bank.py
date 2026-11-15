from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_lookahead_bank import LookaheadInventory,TABLE
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted
from experiments.cnf_pattern_inventory import encode

SOURCE=json.loads(Path('solver/fixtures/trace-split.json').read_text())
OPTIONS=dict(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)


class LookaheadBankTests(unittest.TestCase):
    def test_scout_reuses_probes_after_restart_with_identical_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';h=LookaheadInventory(path,**OPTIONS)
            try:
                h.set_admission_budget(8);h.scout(SOURCE,0)
                self.assertGreater(h.counts['probe_attempts'],0)
                saved=dict(h.db.execute(f'SELECT id,payload FROM {TABLE}'))
                self.assertTrue(saved);self.assertEqual(h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0],0)
            finally:h.close()
            h=LookaheadInventory(path,**OPTIONS);plain=CompleteAdmissionInventory(**OPTIONS)
            try:
                h.set_admission_budget(32);plain.set_admission_budget(32)
                with patch('experiments.cnf_ordered_propagation_inventory.OrderedPropagationInventory._discover_probes',side_effect=AssertionError('fresh probe')):
                    a=h._edge(SOURCE,0)
                b=plain._edge(SOURCE,0);self.assertEqual(a,b)
                self.assertEqual(dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')),dict(plain.db.execute('SELECT id,payload FROM cnf_patterns_v1')))
                self.assertEqual(h.counts['probe_attempts'],0);self.assertGreater(h.counts['lookahead_bank_hits'],0)
                self.assertEqual(dict(h.db.execute(f'SELECT id,payload FROM {TABLE}')),saved)
            finally:h.close();plain.close()

    def test_zero_allowance_blocks_scout_before_profile(self):
        h=LookaheadInventory(**OPTIONS)
        try:
            h.set_admission_budget(0)
            with patch.object(h,'_profile',side_effect=AssertionError('profile before admission')):
                with self.assertRaises(AdmissionExhausted):h.scout(SOURCE,0)
            self.assertEqual(h.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)
        finally:h.close()

    def test_tampered_trace_and_policy_rejected(self):
        h=LookaheadInventory(**OPTIONS)
        try:
            h.set_admission_budget(8);h.scout(SOURCE,0)
            key,payload=h.db.execute(f'SELECT id,payload FROM {TABLE}').fetchone()
            bad=json.loads(payload);bad['attempts']=[]
            with self.assertRaises(ValueError):h.check_bank_row(key,encode(bad))
            identity=json.loads(key);identity[1]['probe_limit']=1
            with self.assertRaises(ValueError):h.check_bank_row(encode(identity),payload)
            with h.db:h.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?',(encode(bad),key))
            h.set_admission_budget(8)
            with self.assertRaises(ValueError):h._edge(SOURCE,0)
        finally:h.close()

    def test_ordinary_discovery_does_not_populate_bank(self):
        h=LookaheadInventory(**OPTIONS)
        try:
            h.set_admission_budget(32);h._edge(SOURCE,0)
            self.assertEqual(h.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)
            self.assertGreater(h.counts['probe_attempts'],0)
        finally:h.close()


if __name__=='__main__':unittest.main()
