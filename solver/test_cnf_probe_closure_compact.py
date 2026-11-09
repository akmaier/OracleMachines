from pathlib import Path
import tempfile
import unittest

from experiments.cnf_probe_closure_compact import CompactProbeClosureInventory
from experiments.cnf_probe_closure_reuse import ProbeClosureReuseInventory
from experiments.cnf_probe_learning import ProbeLearningInventory
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_probe_closure_reuse import active_source
from solver.test_cnf_probe_learning import learning_source, equivalence_source


class CompactProbeClosureTests(unittest.TestCase):
    def test_distinct_policy_identity_same_proofs_and_cold_coexistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'; saved = {}
            profiles = []; summaries = []; keys = []
            for cls in (ProbeLearningInventory, ProbeClosureReuseInventory, CompactProbeClosureInventory):
                h = cls(path, max_depth=1)
                records = [h.inspect(s) for s in (active_source(), learning_source(), equivalence_source())]
                for r in records: check_fused_tree(h, r['root']['key'])
                for k, payload in saved.items():
                    self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (k,)).fetchone()[0], payload)
                saved = dict(h.db.execute('SELECT * FROM cnf_patterns_v1'))
                profiles.append([r['profile'] for r in records]); summaries.append([r['summary'] for r in records])
                keys.append([r['root']['key'] for r in records]); h.close()
            self.assertEqual(profiles[1], profiles[2])
            self.assertEqual(summaries[0], summaries[1]); self.assertEqual(summaries[1], summaries[2])
            self.assertTrue(all(len(set(k)) == 3 for k in zip(*keys)))
            raw = path.read_bytes()
            h = CompactProbeClosureInventory(path, max_depth=1)
            for source in (active_source(), learning_source(), equivalence_source()):
                self.assertEqual(h.inspect(source)['metrics'].get('inserted_nodes', 0), 0)
            h.close(); self.assertEqual(raw, path.read_bytes())
