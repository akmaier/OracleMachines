import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.continue_cnf_transfer_split import advance, replay, restore_checkpoint
from experiments.compare_cnf_subsumption_transfer import sha
from solver import test_cnf_trace_split as split_fixture

OPTIONS=dict(max_depth=2,probe_limit=4,learn_limit=4,clause_growth_limit=2)


def seed(path):
    fixture=split_fixture.TraceSplitTests();h=fixture.history(path)
    try:
        source,_,record=fixture.seed(h)
        return source,record
    finally:
        h.close()


class TransferSplitTests(unittest.TestCase):
    def test_pending_both_branches_survive_zero_budget_and_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,record=seed(path)
            h=CompleteAdmissionInventory(path,**OPTIONS)
            try:
                before=dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'))
                row=advance(h,record,0)
                self.assertFalse(row['split_closed']);self.assertEqual(row['entered'],0)
                self.assertTrue(all(b['pending'] for b in row['branches']))
                self.assertEqual(dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')),before)
            finally:
                h.close()
            h=CompleteAdmissionInventory(path,**OPTIONS)
            try:
                row=advance(h,json.loads(json.dumps(record)),32)
                self.assertTrue(row['split_closed']);self.assertFalse(any(b['pending'] for b in row['branches']))
                self.assertTrue(before.items()<=dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')).items())
                self.assertLessEqual(row['entered'],32)
            finally:
                h.close()
            checked=replay(path,OPTIONS,record,[source],[True])
            self.assertTrue(checked['no_acquisition']);self.assertTrue(checked['positive']['steps'])
            h=CompleteAdmissionInventory(path,**OPTIONS)
            try:
                with patch.object(h,'_admit',side_effect=AssertionError('new state')):
                    repeated=advance(h,record,0)
                self.assertTrue(repeated['split_closed']);self.assertEqual(repeated['entered'],0)
                self.assertEqual(repeated['stored'],0);self.assertEqual(repeated['probes'],0)
            finally:
                h.close()

    def test_partial_batch_preserves_children_and_shared_allowance(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';_,record=seed(path);h=CompleteAdmissionInventory(path,**OPTIONS)
            try:
                row=advance(h,record,1)
                self.assertLessEqual(row['entered'],1);self.assertLessEqual(row['stored'],1)
                self.assertFalse(row['split_closed'])
                saved=dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'))
                resumed=advance(h,record,32);self.assertTrue(resumed['split_closed'])
                self.assertTrue(saved.items()<=dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')).items())
            finally:
                h.close()

    def test_invalid_branch_binding_cannot_acquire(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';_,record=seed(path);h=CompleteAdmissionInventory(path,**OPTIONS)
            try:
                for field in ('edges','references'):
                    bad=copy.deepcopy(record);bad[field].pop()
                    with patch.object(h,'_admit',side_effect=AssertionError('acquired before validation')):
                        with self.assertRaises(ValueError):advance(h,bad,32)
            finally:
                h.close()

    def test_source_only_control_is_not_restorable_full_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);sample=root/'source_only-0';sample.mkdir();report=sample/'report.json'
            report.write_text(json.dumps(dict(mode='source_only')))
            frozen=root/'frozen.json';frozen.write_text('{}')
            (root/'report.json').write_text(json.dumps(dict(samples=[dict(path=str(report),sha256=sha(report))],
                frozen_sha256=sha(frozen))))
            target=root/'must-not-exist'
            with self.assertRaises(ValueError):restore_checkpoint(report,target)
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
