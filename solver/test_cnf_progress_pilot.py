from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_progress_pilot import ProgressPilotRefinement, base
from experiments.cnf_scoped_refinement import ScopedNestedRefinement


class ProgressPilotTests(unittest.TestCase):
    def history(self, path, parent):
        directory = Path('experiments/results') / parent
        cp = base.load(directory / 'checkpoint.json')
        target = base.load(directory / 'next-discovery.json')
        base.restore_archive(cp['archive'], path)
        h = base.CompleteAdmissionInventory(path, **base.OPTIONS)
        h.set_admission_budget(0)
        root = base.load(cp['queries']['path'])[target['case']]['roots'][0]
        return h, root, target['source']

    def finish(self, h, s):
        for _ in range(4):
            if s.coverage.closed()[0]:
                break
            s.batch(state_limit=128, pair_limit=16)
        self.assertTrue(s.coverage.closed()[0])
        flags, plan = base.compose(h, [s.root], s.registry, Counter())
        proof = base.expand(h, plan, [s.root], s.registry, Counter())
        base.split.verify_positive(h, proof, [s.root], list(s.records.values()), Counter())
        return base.rows(h), dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}')), proof

    def test_decreasing_trial_skips_extra_work_and_matches_committed_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            results = []
            for gated in (False, True):
                h, root, source = self.history(Path(td) / str(gated), 'cnf-pilot-refinement')
                try:
                    s = ProgressPilotRefinement(h, root, source) if gated else ScopedNestedRefinement(h, root)
                    r = s.batch(state_limit=128, pair_limit=1)
                    if gated:
                        self.assertEqual(s.baseline[1], 610)
                        self.assertEqual(s.gate['after'][1], 539)
                        self.assertEqual(s.gate['action'], 'skip')
                        self.assertEqual(s.completed, 1)
                        self.assertEqual(s.chosen, s.candidates[0])
                    results.append(self.finish(h, s))
                finally:
                    h.close()
            self.assertEqual(results[0], results[1])

    def test_increasing_trial_explores_and_cold_resume_matches_uninterrupted(self):
        with tempfile.TemporaryDirectory() as td:
            results = []
            for restart in (False, True):
                path = Path(td) / str(restart)
                h, root, source = self.history(path, 'cnf-saved-split-reuse')
                try:
                    s = ProgressPilotRefinement(h, root, source)
                    s.batch(state_limit=128, pair_limit=1)
                    self.assertEqual(s.baseline[1], 1106)
                    self.assertEqual(s.gate['after'][1], 1535)
                    self.assertEqual(s.gate['action'], 'explore')
                    state = s.state()
                    if restart:
                        h.close(); h = base.CompleteAdmissionInventory(path, **base.OPTIONS)
                        h.set_admission_budget(0)
                        with base.no_acquisition():
                            s = ProgressPilotRefinement(h, root, source, state)
                            self.assertEqual(s.state(), state)
                    result = self.finish(h, s)
                    self.assertEqual(s.records[s.chosen]['variable'], 32)
                    results.append((result, s.state()))
                finally:
                    h.close()
            self.assertEqual(results[0], results[1])

    def test_partial_trial_preserves_baseline_and_one_shared_budget(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'h'
            h, root, source = self.history(path, 'cnf-pilot-refinement')
            try:
                initial = base.rows(h); s = ProgressPilotRefinement(h, root, source)
                r = s.batch(state_limit=2, pair_limit=16); state = s.state()
                self.assertLessEqual(r['entered'], 2)
                self.assertEqual(state['completed'], 0)
                self.assertIsNone(state['gate'])
                self.assertTrue(state['events'][-1]['pending'])
                self.assertTrue(initial.items() <= base.rows(h).items())
            finally:
                h.close()
            h = base.CompleteAdmissionInventory(path, **base.OPTIONS); h.set_admission_budget(0)
            try:
                with base.no_acquisition(), patch.object(base.split, 'discover_simplification', side_effect=AssertionError('restart acquisition')):
                    s = ProgressPilotRefinement(h, root, source, state)
                    self.assertEqual(s.state(), state)
                old_events = len(s.events)
                r = s.batch(state_limit=128, pair_limit=1)
                self.assertEqual(s.baseline, state['baseline'])
                self.assertEqual(s.gate['action'], 'skip')
                self.assertLessEqual(sum(e['entered'] for e in s.events[old_events:]), r['entered'])
                self.assertEqual(r['selection_counts'].get('bootstrap_fresh_assumptions', 0), 0)
            finally:
                h.close()

    def test_skip_decision_survives_cold_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'h'
            h, root, source = self.history(path, 'cnf-pilot-refinement')
            try:
                s = ProgressPilotRefinement(h, root, source)
                first = s.batch(state_limit=128, pair_limit=1); state = s.state()
            finally:
                h.close()
            h = base.CompleteAdmissionInventory(path, **base.OPTIONS); h.set_admission_budget(0)
            try:
                with base.no_acquisition():
                    s = ProgressPilotRefinement(h, root, source, state)
                    self.assertEqual(s.frontier(), first['frontier'])
                self.finish(h, s)
                self.assertEqual(s.completed, 1)
                self.assertEqual(len(s.events), 1)
            finally:
                h.close()

    def test_foreign_or_inconsistent_gate_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h, root, source = self.history(Path(td) / 'h', 'cnf-pilot-refinement')
            try:
                s = ProgressPilotRefinement(h, root, source)
                s.batch(state_limit=128, pair_limit=1); state = s.state()
                for field, value in [('root', 'foreign'), ('completed', True), ('chosen', None),
                                     ('baseline', [0, True, 1, 41]), ('gate', {'action': 'explore', 'after': state['gate']['after']})]:
                    bad = copy.deepcopy(state); bad[field] = value
                    with self.assertRaises(ValueError):
                        ProgressPilotRefinement(h, root, source, bad)
            finally:
                h.close()


if __name__ == '__main__':
    unittest.main()
