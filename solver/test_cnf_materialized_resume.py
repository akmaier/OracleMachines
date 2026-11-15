import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import cnf_materialized_resume as resume
from experiments.cnf_materialized_checkpoint import sha


class MaterializedResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.code = self.root/'indirect-helper.py'
        self.code.write_text('historically checked helper\n')
        self.ledger = self.root/'validation.json'
        self.ledger.write_text(json.dumps(dict(report_sha256='parent',
            source_fingerprints={str(self.code):sha(self.code)})))
        self.digest = sha(self.ledger)

    def test_indirect_source_change_is_rejected(self):
        self.assertEqual(resume.check_source_ledger(self.ledger, self.digest, 'parent'), 1)
        self.code.write_text('changed indirect helper\n')
        with self.assertRaisesRegex(ValueError, 'historical implementation'):
            resume.check_source_ledger(self.ledger, self.digest, 'parent')

    def test_ledger_mutation_and_parent_mismatch_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'another checkpoint'):
            resume.check_source_ledger(self.ledger, self.digest, 'different')
        self.ledger.write_text(self.ledger.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'source ledger'):
            resume.check_source_ledger(self.ledger, self.digest, 'parent')

    def test_resume_checks_before_delegating_and_charges_guard(self):
        order=[];metrics={}
        def check(*args): order.append('ledger');return 125
        def restore(*args): order.append('restore');return ('parent',[],[],[],[],[])
        with patch.object(resume,'check_source_ledger',side_effect=check),patch.object(resume,'restore_bound_snapshot',side_effect=restore):
            result=resume.restore_checkpoint('report','history','tmp',metrics=metrics)
        self.assertEqual(order,['ledger','restore']);self.assertEqual(result[0],'parent')
        self.assertEqual(metrics['historical_source_files'],125)
        self.assertGreaterEqual(metrics['guarded_restore_seconds'],metrics['source_ledger_seconds'])

    def test_failed_ledger_never_opens_snapshot_or_fallback(self):
        with patch.object(resume,'check_source_ledger',side_effect=ValueError('stale ledger')),patch.object(resume,'restore_bound_snapshot') as loader:
            with self.assertRaisesRegex(ValueError,'stale ledger'):
                resume.restore_checkpoint('report','history','tmp')
        loader.assert_not_called()


if __name__ == '__main__': unittest.main()
