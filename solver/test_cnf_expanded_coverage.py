from collections import Counter
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import PatternInventory, encode
from experiments.cnf_route_composition import compose
from experiments.cnf_selected_routes import verify_selected_plan
from experiments.cnf_expanded_coverage import checked_inventory, expand, verify_expanded, owner
import solver.test_cnf_selected_routes as selected_fixture


class ExpandedCoverageTests(unittest.TestCase):
    def test_conditioning_and_shared_components_are_not_implicit_bases(self):
        for source, expected in (
                ([[-1,-2,-3], [1,2,3], [1,-2,4]], 'conditioning'),
                ([[1], [3]], 'components')):
            h = PatternInventory(max_depth=1, candidate_limit=1, parity_width=0)
            try:
                root = h.inspect(source)['root']['key']
                self.assertTrue(h._load(root)['summary']['closed'])
                evidence = [[], [], [], [], []]
                old = dict(roots=[root], steps=[dict(source=root, rule=dict(kind='base'))])
                routes = verify_selected_plan(h, old, [root], evidence, Counter())
                proof = expand(h, old, [root], routes, Counter())
                self.assertEqual(proof['steps'][-1]['rule']['kind'], expected)
                self.assertEqual(len(proof['steps'][-1]['children']), 2)
                verify_expanded(h, proof, [root], evidence, Counter())
                bad = copy.deepcopy(proof); bad['steps'][-1]['children'].pop()
                with self.assertRaises(ValueError): verify_expanded(h, bad, [root], evidence, Counter())
                if expected == 'conditioning':
                    bad = copy.deepcopy(proof); bad['steps'][-1]['rule']['index'] = False
                    with self.assertRaises(ValueError): verify_expanded(h, bad, [root], evidence, Counter())
                else:
                    self.assertEqual(len(set(proof['steps'][-1]['children'])), 1)
            finally:
                h.close()

    def test_retained_base_expands_both_policy_views_and_cold_replays(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = BudgetedInventory(path, max_depth=0)
            # Store a prepared-policy plan, then reuse it under the new policy.
            h.prepared._edge(((1,),), 0)
            h.set_admission_budget(8); root = h._edge(((1,),), 0)['key']
            self.assertEqual(h._load(root)['kind'], 'retained_plan')
            evidence = [[], [], [], [], []]
            old = dict(roots=[root], steps=[dict(source=root, rule=dict(kind='base'))])
            routes = verify_selected_plan(h, old, [root], evidence, Counter())
            proof = expand(h, old, [root], routes, Counter())
            self.assertGreater(len(proof['steps']), len(old['steps']))
            self.assertIn('retained_plan', {s['rule']['kind'] for s in proof['steps']})
            self.assertNotIn('base', {s['rule']['kind'] for s in proof['steps']})
            rows, stats = checked_inventory(h)
            self.assertGreater(stats['views']['current.prepared']['nodes'], 0)
            self.assertEqual(stats['unique_nodes'], len(h.checked)+len(h.prepared.checked))
            h.close(); before = path.read_bytes(); h = BudgetedInventory(path, max_depth=0)
            with patch.object(h, '_discover', side_effect=AssertionError('rediscovery')):
                counts = Counter(); verify_expanded(h, proof, [root], evidence, counts)
                self.assertEqual(counts['verified_expanded_steps'], len(proof['steps']))
            h.close(); self.assertEqual(path.read_bytes(), before)

    def test_saved_split_still_requires_two_ordered_children(self):
        helper = selected_fixture.SelectedRoutesTests()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = helper.history(path)
            root, old, evidence = helper.split(h)
            routes = verify_selected_plan(h, old, [root], evidence, Counter())
            proof = expand(h, old, [root], routes, Counter())
            last = proof['steps'][-1]
            self.assertEqual(last['rule']['kind'], 'trace_split')
            self.assertEqual(len(last['children']), 2)
            verify_expanded(h, proof, [root], evidence, Counter())
            for mutation in (
                    lambda p: p['steps'][-1]['children'].pop(),
                    lambda p: p['steps'][-1]['children'].reverse(),
                    lambda p: p['steps'].reverse(),
                    lambda p: p['steps'].pop(0),
                    lambda p: p['steps'].append(p['steps'][0]),
                    lambda p: p['steps'][-1].update(rule=dict(kind='base'), children=[]),
                    lambda p: p['roots'].append('foreign')):
                bad = copy.deepcopy(proof); mutation(bad)
                with self.assertRaises(ValueError): verify_expanded(h, bad, [root], evidence, Counter())
            h.close()

    def test_false_family_missing_reference_and_foreign_policy_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = BudgetedInventory(path, max_depth=0)
            h.prepared._edge(((1,),), 0); h.set_admission_budget(8)
            root = h._edge(((1,),), 0)['key']; reference = h._load(root)['reference']
            old = dict(roots=[root], steps=[dict(source=root, rule=dict(kind='base'))])
            evidence = [[], [], [], [], []]
            routes = verify_selected_plan(h, old, [root], evidence, Counter())
            proof = expand(h, old, [root], routes, Counter())
            bad = copy.deepcopy(proof); bad['steps'][-1].update(rule=dict(kind='family'), children=[])
            with self.assertRaises(ValueError): verify_expanded(h, bad, [root], evidence, Counter())
            with self.assertRaises(ValueError): owner(h, encode(['cnf-pattern-v1', {}, 0, []]))
            with self.assertRaises(ValueError): owner(h, 'invalid')
            h.db.execute('DELETE FROM cnf_patterns_v1 WHERE id=?', (reference,)); h.db.commit(); h.close()
            h = BudgetedInventory(path, max_depth=0)
            with self.assertRaises(ValueError): verify_expanded(h, proof, [root], evidence, Counter())
            h.close()

    def test_two_cache_accounting_deduplicates_and_detects_conflicts(self):
        node = dict(kind='family')
        older = SimpleNamespace(checked={'shared':node, 'old':node})
        h = SimpleNamespace(checked={'shared':node, 'new':node}, prepared=older)
        rows, stats = checked_inventory(h)
        self.assertEqual(set(rows), {'shared', 'old', 'new'})
        self.assertEqual((stats['unique_nodes'], stats['cache_occurrences'], stats['duplicate_cache_entries']), (3,4,1))
        older.checked['shared'] = dict(kind='unresolved')
        with self.assertRaises(ValueError): checked_inventory(h)
        older.prepared = h
        with self.assertRaises(ValueError): checked_inventory(h)


if __name__ == '__main__': unittest.main()
