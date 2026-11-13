from collections import Counter
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_probe_batch_control import ObservedRoutes
from experiments.cnf_target_probe import search
from experiments.cnf_trace_learning import LearnedTraceRoutes
from experiments.cnf_route_composition import compose, verify_plan
from solver import test_cnf_target_probe as fixtures


class ProbeBatchControlTests(unittest.TestCase):
    def compare(self, name, state_limit):
        fixture = fixtures.TargetProbeTests()
        with tempfile.TemporaryDirectory() as td:
            seed = Path(td)/'seed'
            h = fixture.history(seed)
            root = fixture.seed(h, name)
            h.close()
            results = []
            for arm in ('plain', 'batch', 'sequential'):
                path = Path(td)/arm
                shutil.copyfile(seed, path)
                h = fixture.history(path)
                routes = LearnedTraceRoutes(h)
                observed = None if arm == 'plain' else ObservedRoutes(
                    h, routes, [root], LearnedTraceRoutes if arm == 'sequential' else None)
                with patch.object(h, 'set_admission_budget', wraps=h.set_admission_budget) as reset:
                    result = search(h, root, routes if observed is None else observed,
                                    Counter(), state_limit=state_limit)
                self.assertEqual(reset.call_count, 1)
                observation = None if observed is None else observed.finish()
                active = routes if observed is None else observed
                closed, plan = compose(h, [root], active, Counter())
                verify_plan(h, plan, plan['roots'], active, Counter())
                tables = {name: list(h.db.execute(f'SELECT * FROM {name} ORDER BY 1'))
                          for name, in h.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                results.append((result, sorted(h.admitted), tables, closed, observation))
                h.close()
            self.assertEqual(results[0][:4], results[1][:4])
            self.assertEqual(results[0][:4], results[2][:4])
            self.assertEqual(results[1][4]['prefixes'], results[2][4]['prefixes'])
            self.assertEqual(len(results[2][4]['repeated_preparation_seconds']),
                             max(0, len(results[0][0]['visits'])-1))
            return results[0][0]

    def test_clear_exhaustion_matches_uninstrumented_search_at_every_prefix(self):
        self.assertIsNone(self.compare('clear', 0)['stop'])

    def test_forced_acquisition_matches_with_one_shared_budget(self):
        self.assertNotEqual(self.compare('forced', 32)['stop'], 'admission_limit')

    def test_interrupted_acquisition_retains_identical_pending_evidence(self):
        self.assertEqual(self.compare('forced', 0)['stop'], 'admission_limit')

    def test_rebuild_cannot_replace_the_admission_allowance(self):
        fixture = fixtures.TargetProbeTests()
        with tempfile.TemporaryDirectory() as td:
            h = fixture.history(Path(td)/'h');root = fixture.seed(h, 'clear')
            def bad_rebuild(inv):
                inv.set_admission_budget(32)
                return LearnedTraceRoutes(inv)
            observed = ObservedRoutes(h, LearnedTraceRoutes(h), [root], bad_rebuild)
            with self.assertRaisesRegex(ValueError, 'shared admission budget'):
                search(h, root, observed, Counter(), state_limit=0)
            h.close()


if __name__ == '__main__':
    unittest.main()
