from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose
from experiments.cnf_learning_continuation import ContinuedLearningRoutes, LearningBlocks, base_id, record_key as block_key
from experiments.cnf_probe_continuation import ContinuationRoutes, record_key as continuation_key
from experiments.cnf_trace_split import candidates, verify, attach
from experiments.cnf_selected_routes import SelectedRoutes, verify_selected_plan
import solver.test_cnf_learning_continuation as learning_fixture


TABLES = ('cnf_pivot_trials_v1', 'cnf_coupled_trials_v1', 'cnf_growth_trials_v1',
          'cnf_probe_windows_v1', 'cnf_probe_continuations_v1')


class SelectedRoutesTests(unittest.TestCase):
    def history(self, path):
        h = BudgetedInventory(path, max_depth=2, probe_limit=4, learn_limit=4, clause_growth_limit=2)
        for table in TABLES:
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit()
        return h

    def split(self, h):
        source = json.loads(Path('solver/fixtures/trace-split.json').read_text())
        h.set_admission_budget(32)
        root = h._edge(source, 0)['key']
        routes = ContinuedLearningRoutes(h)
        record = candidates(h, root, routes, Counter())[0]['record']
        for target in verify(h, record, Counter())[0]:
            h._edge(target, 0)
        attach(h, routes, record, Counter())
        closed, plan = compose(h, [root], routes, Counter())
        self.assertEqual(closed, [True])
        return root, plan, [[], [], [], [record], []]

    def test_cold_positive_replay_ignores_unrelated_bad_route(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'
            h = self.history(path)
            root, plan, evidence = self.split(h)
            h.db.execute('INSERT INTO cnf_growth_trials_v1 VALUES (?,?)', ('unrelated', '{}'))
            h.db.commit(); h.close()
            before = path.read_bytes()
            h = self.history(path); h.set_admission_budget(0)
            with patch.object(h, '_discover', side_effect=AssertionError('rediscovery')):
                counts = Counter()
                selected = verify_selected_plan(h, plan, [root], evidence, counts)
                self.assertEqual(counts['verified_steps'], len(plan['steps']))
                self.assertEqual(selected.counts['selected_sql_lookups'], 0)
                self.assertFalse(h.admitted)
                with self.assertRaises((ValueError, KeyError)):
                    ContinuedLearningRoutes(h)
            h.close(); self.assertEqual(before, path.read_bytes())

    def test_missing_branch_binding_and_plan_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            h = self.history(Path(td)/'h'); root, plan, evidence = self.split(h)
            for mutation in (
                    lambda p: p['steps'].reverse(),
                    lambda p: p['steps'].pop(0),
                    lambda p: p['steps'].append(p['steps'][0]),
                    lambda p: p['roots'].append('foreign'),
                    lambda p: p['steps'][-1].update(rule={'kind': 'base'}),
                    lambda p: p['steps'][-1].update(source='foreign')):
                bad = copy.deepcopy(plan); mutation(bad)
                with self.assertRaises(ValueError):
                    verify_selected_plan(h, bad, [root], evidence, Counter())
            for mutation in (
                    lambda r: r['edges'].pop(),
                    lambda r: r['edges'][0].update(names=[999]),
                    lambda r: r['references'][0].update(id='foreign')):
                bad = copy.deepcopy(evidence); mutation(bad[3][0])
                with self.assertRaises(ValueError):
                    verify_selected_plan(h, plan, [root], bad, Counter())
            with self.assertRaises(ValueError):
                verify_selected_plan(h, plan, [root], [[], [], [], [], []], Counter())
            h.close()

    def test_missing_checked_child_and_changed_configuration_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = self.history(path)
            root, plan, evidence = self.split(h)
            child = evidence[3][0]['edges'][0]['key']
            h.db.execute('DELETE FROM cnf_patterns_v1 WHERE id=?', (child,)); h.db.commit(); h.close()
            h = self.history(path)
            with self.assertRaises(ValueError):
                verify_selected_plan(h, plan, [root], evidence, Counter())
            h.close()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = self.history(path)
            root, plan, evidence = self.split(h); h.close()
            h = BudgetedInventory(path, max_depth=1)
            with self.assertRaises(ValueError):
                verify_selected_plan(h, plan, [root], evidence, Counter())
            h.close()

    def test_selected_continuation_checks_missing_and_corrupt_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = self.history(path); h.set_admission_budget(32)
            cnf = json.loads(Path('solver/fixtures/probe-continuation.json').read_text())['forced']
            root = h._edge(cnf, 0)['key']; eager = ContinuationRoutes(h)
            eager.advance(h, root, Counter())
            _, record, target = eager.advance(h, root, Counter()); h._edge(target, 0); eager.refresh(h)
            rule = dict(kind='probe_continuation', id=continuation_key(record))
            selected = SelectedRoutes(h, [[], [], [], [], []]); selected.select(h, root, rule)
            self.assertEqual(selected.by_source[root], eager.by_source[root])
            self.assertEqual(len(selected.windows), 1)
            self.assertEqual(len(selected.verified), 1)
            identity, payload = h.db.execute('SELECT id,payload FROM cnf_probe_windows_v1').fetchone()
            bad = json.loads(payload); bad['probing']['attempts'][0]['variable'] = 999
            h.db.execute('UPDATE cnf_probe_windows_v1 SET payload=? WHERE id=?', (encode(bad), identity))
            with self.assertRaises(ValueError):
                SelectedRoutes(h, [[], [], [], [], []]).select(h, root, rule)
            h.db.execute('DELETE FROM cnf_probe_windows_v1')
            with self.assertRaises(ValueError):
                SelectedRoutes(h, [[], [], [], [], []]).select(h, root, rule)
            h.close()

    def test_learned_prefix_is_required_and_source_bound(self):
        f = json.loads(Path('solver/fixtures/learning-continuation.json').read_text())
        h = learning_fixture.MemoryHistory(f)
        try:
            blocks = LearningBlocks(h, [f['base']]); identity = base_id(f['base'])
            first, _ = blocks.advance(h, identity, Counter())
            second, target = blocks.advance(h, identity, Counter()); h.add_child(second, target)
            rule = dict(kind='learning_continuation', id=block_key(second))
            evidence = [[], [f['base']], [second, first], [], []]
            with patch('experiments.cnf_learning_continuation.discover_equivalence_probes',
                       side_effect=AssertionError('rediscovery')):
                selected = SelectedRoutes(h, evidence); selected.select(h, f['source'], rule)
            self.assertEqual(len(selected.learned_blocks.verified), 2)
            self.assertEqual(len(selected.learned_blocks.contexts), 1)
            for broken in ([[], [f['base']], [second], [], []], [[], [], [first, second], [], []]):
                with self.assertRaises(ValueError):
                    SelectedRoutes(h, broken).select(h, f['source'], rule)
            with self.assertRaises(ValueError):
                SelectedRoutes(h, evidence).select(h, 'foreign', rule)
            bad = copy.deepcopy(evidence); bad[2][1]['probing']['attempts'][0]['variable'] = 999
            with self.assertRaises(ValueError):
                SelectedRoutes(h, bad).select(h, f['source'], rule)
        finally:
            h.db.close()

    def test_unknown_rule_and_conflicting_sidecar_fail(self):
        with tempfile.TemporaryDirectory() as td:
            h = self.history(Path(td)/'h'); root, plan, evidence = self.split(h)
            plan['steps'][-1]['rule'] = dict(kind='unchecked', id='x')
            with self.assertRaises(ValueError):
                verify_selected_plan(h, plan, [root], evidence, Counter())
            duplicate = copy.deepcopy(evidence[3][0]); duplicate['edges'][0]['names'] = [999]
            evidence[3].append(duplicate)
            with self.assertRaises(ValueError): SelectedRoutes(h, evidence)
            h.close()


if __name__ == '__main__':
    unittest.main()
