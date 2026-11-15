from collections import Counter
import copy
import json
import unittest
from unittest.mock import patch

from experiments.cnf_coverage_union import (capture_part, empty_rows, inventory,
    make_bundle, merge_rows, replay_union, roots_for, validate_claim)
from experiments.cnf_expanded_coverage import expand, verifier_views
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_selected_routes import SelectedRoutes
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_retained_plans import RetainedPlanInventory


def fixture():
    claim = dict(sources=[[[1], [3]], [[-7, 9]], [], [[]]],
        policies=dict(old=dict(reader='retained', options=dict(max_depth=0)),
                      new=dict(reader='expanded', options=dict(max_depth=0, clause_growth_limit=2))),
        partition=dict(old=[0, 2], new=[1, 3]))
    rows = empty_rows(); parts = {}
    for name, policy in claim['policies'].items():
        h = inventory(':memory:', policy)
        try:
            if isinstance(h, BudgetedInventory):
                h.set_admission_budget(32)
            for i in claim['partition'][name]:
                h._edge(claim['sources'][i], 0)
            roots = roots_for(h, claim, name); evidence = [[], [], [], [], []]
            base = dict(roots=roots, steps=[dict(source=k, rule=dict(kind='base'))
                                           for k in dict.fromkeys(roots)])
            proof = expand(h, base, roots, SelectedRoutes(h, evidence), Counter())
            part = dict(proof=proof, evidence=evidence, bridges=[])
            for _, view in verifier_views(h):
                view.checked.clear()
            if isinstance(h, BudgetedInventory):
                h.set_admission_budget(0)
            captured, _ = capture_part(h, claim, name, part)
            merge_rows(rows, captured); parts[name] = part
        finally:
            h.close()
    return make_bundle(claim, parts, rows), claim


class CoverageUnionTests(unittest.TestCase):
    def test_complete_source_bound_union_without_discovery(self):
        bundle, claim = fixture()
        with patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('acquisition')), \
             patch.object(RetainedPlanInventory, '_discover', side_effect=AssertionError('acquisition')):
            result = replay_union(json.loads(encode(bundle)), claim)
        self.assertEqual(result['covered'], 4)
        self.assertEqual([p['roots'] for p in result['parts'].values()], [2, 2])
        self.assertGreater(result['parts']['old']['steps'], 2)

    def test_partition_rejects_missing_duplicate_outside_boolean_and_reordered_indices(self):
        _, claim = fixture()
        for changed in ([0], [0, 0, 2], [0, 4], [False, 2], [2, 0]):
            bad = copy.deepcopy(claim); bad['partition']['old'] = changed
            with self.assertRaises(ValueError):
                validate_claim(bad)
        bad = copy.deepcopy(claim); bad['partition']['new'] = [0, 1, 3]
        with self.assertRaises(ValueError):
            validate_claim(bad)

    def test_changed_input_policy_partition_or_scope_is_not_the_requested_claim(self):
        bundle, claim = fixture()
        mutations = (
            lambda c: c['sources'][0].append([-1]),
            lambda c: c['policies']['old']['options'].update(max_depth=1),
            lambda c: c['partition'].update(old=[1, 2], new=[0, 3]),
        )
        for mutate in mutations:
            changed = copy.deepcopy(claim); mutate(changed)
            with self.assertRaises(ValueError):
                replay_union(bundle, changed)
        bad = copy.deepcopy(bundle); bad['scope'] = 'SAT-answer'
        with self.assertRaises(ValueError):
            replay_union(bad, claim)

    def test_recomputed_partition_cannot_bind_a_foreign_policy_proof(self):
        bundle, claim = fixture()
        bad = copy.deepcopy(bundle)
        bad['parts']['old'], bad['parts']['new'] = bad['parts']['new'], bad['parts']['old']
        with self.assertRaises(ValueError):
            replay_union(bad, claim)
        bad = copy.deepcopy(bundle)
        bad['claim']['partition'] = dict(old=[1, 2], new=[0, 3])
        with self.assertRaises(ValueError):
            replay_union(bad, bad['claim'])

    def test_omitted_component_and_root_are_rejected(self):
        bundle, claim = fixture()
        bad = copy.deepcopy(bundle)
        step = next(s for s in bad['parts']['old']['proof']['steps']
                    if s['rule']['kind'] == 'components')
        step['children'].pop()
        with self.assertRaises(ValueError):
            replay_union(bad, claim)
        bad = copy.deepcopy(bundle); bad['parts']['new']['proof']['roots'].pop()
        with self.assertRaises(ValueError):
            replay_union(bad, claim)

    def test_missing_corrupt_or_unused_rows_rejected(self):
        bundle, claim = fixture()
        for i in range(len(bundle['rows']['cnf_patterns_v1'])):
            bad = copy.deepcopy(bundle); bad['rows']['cnf_patterns_v1'].pop(i)
            with self.assertRaises(ValueError):
                replay_union(bad, claim)
        bad = copy.deepcopy(bundle)
        node = json.loads(bad['rows']['cnf_patterns_v1'][0][1]); node['cnf'] = [[777]]
        bad['rows']['cnf_patterns_v1'][0][1] = encode(node)
        with self.assertRaises(ValueError):
            replay_union(bad, claim)
        bad = copy.deepcopy(bundle); bad['rows']['cnf_growth_trials_v1'].append(['unused', '{}'])
        with self.assertRaisesRegex(ValueError, 'Unused'):
            replay_union(bad, claim)

    def test_exact_key_conflict_cannot_be_silently_deduplicated(self):
        bundle, _ = fixture(); rows = empty_rows(); merge_rows(rows, bundle['rows'])
        bad = copy.deepcopy(bundle['rows']); bad['cnf_patterns_v1'][0][1] = '{}'
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            merge_rows(rows, bad)


if __name__ == '__main__':
    unittest.main()
