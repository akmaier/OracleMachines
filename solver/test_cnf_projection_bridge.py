from collections import Counter, defaultdict
import copy
import gzip
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from experiments.cnf_projection_bridge import (discover, check, lift, projection,
    attach, record_key, verify_positive, KIND)
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_expanded_coverage import FORMAT


def explicit(cnf):
    return [list(c) for c in normalize(cnf, Counter())[0]]


SOURCE = explicit([[1,2],[-1,3],[2,3,4],[-4,2]])
TARGET = explicit([[-4,2],[2,3]])


class ProjectionBridgeTests(unittest.TestCase):
    def test_retained_real_leaves_have_exact_projection_bridge(self):
        report = json.loads(Path('experiments/results/cnf-split-cost-1299/report.json').read_text())
        with gzip.open(report['frontier_profiles']['path']) as f:
            rows = json.load(f)
        target, source = [json.loads(r['source'])[-1] for r in rows]
        proof = discover(source, target)
        self.assertEqual(proof['variable'], 16)
        self.assertEqual(len(proof['subsumers']), 1)
        counts = Counter(); check(source, target, proof, counts)
        self.assertEqual(counts['additive_elimination_checked_pairs'], 10)
        self.assertEqual(counts['bridge_removed_clauses'], 1)
        with self.assertRaises(ValueError):
            check(source, target, proof, pair_limit=9)

    def test_all_target_models_lift_and_false_models_fail(self):
        proof = discover(SOURCE, TARGET)
        self.assertIsNotNone(proof)
        for bits in itertools.product((False,True), repeat=3):
            model = dict(enumerate(bits,1))
            if holds(TARGET, model):
                self.assertTrue(holds(SOURCE, lift(SOURCE, TARGET, proof, model)))
            else:
                with self.assertRaises(ValueError): lift(SOURCE, TARGET, proof, model)
        with self.assertRaises(ValueError): lift(SOURCE, TARGET, proof, {1:True})

    def test_tampered_binding_and_deleted_essential_clauses_fail(self):
        proof = discover(SOURCE, TARGET)
        for mutate in (lambda p:p['names'].reverse(),
                       lambda p:p['subsumers'].clear(),
                       lambda p:p.update(variable=True),
                       lambda p:p['subsumers'][0].__setitem__(1,True),
                       lambda p:p.update(answer=False)):
            bad = copy.deepcopy(proof); mutate(bad)
            with self.assertRaises(ValueError): check(SOURCE, TARGET, bad)
        for bad_target in (explicit(TARGET+[[1]]), explicit([TARGET[0]])):
            with self.assertRaises(ValueError): check(SOURCE, bad_target, proof)

    def test_bound_misses_and_invalid_input_are_explicit(self):
        self.assertIsNone(discover(SOURCE, TARGET, candidate_limit=0))
        self.assertIsNone(discover(TARGET, SOURCE))
        self.assertIsNone(discover(SOURCE, TARGET, pair_limit=0))
        with self.assertRaises(ValueError): discover([[1,1]], [[1]])
        with self.assertRaises(ValueError): discover(SOURCE, TARGET, pair_limit=True)

    def test_exhaustive_small_cnf_projection_and_model_lifting(self):
        clauses = [tuple((i+1)*s for i,s in enumerate(signs) if s)
            for signs in itertools.product((-1,0,1), repeat=3)]
        accepted = 0
        for width in range(4):
            for selected in itertools.combinations(clauses, width):
                source = explicit(selected)
                n = len({abs(l) for c in source for l in c})
                for variable in range(1,n+1):
                    projected, names = projection(source, variable, Counter(), 64)
                    reduced = [c for c in projected if not any(set(d)<set(c) for d in projected)]
                    target = explicit(reduced); proof = discover(source, target)
                    if proof is None: continue
                    checked_names = check(source, target, proof)
                    v = proof['variable']; others = [x for x in range(1,n+1) if x!=v]
                    for bits in itertools.product((False,True), repeat=len(others)):
                        model = dict(zip(others,bits))
                        expected = any(holds(source,model|{v:value}) for value in (False,True))
                        local = {i:model[x] for i,x in enumerate(checked_names,1)}
                        self.assertEqual(holds(target,local), expected)
                        if expected: self.assertTrue(holds(source,lift(source,target,proof,local)))
                    accepted += 1
        self.assertGreater(accepted, 1000)

    def test_positive_replay_requires_proved_target_and_exact_bridge(self):
        h = BudgetedInventory(':memory:', max_depth=0)
        try:
            h.set_admission_budget(32)
            source = h.inspect(SOURCE)['root']['key']; target = h.inspect(TARGET)['root']['key']
            record = dict(source=source, target=target, proof=discover(SOURCE,TARGET))
            routes = SimpleNamespace(by_source=defaultdict(list)); attach(h,routes,record,Counter())
            proof = dict(format=FORMAT,roots=[source],steps=[
                dict(source=target,rule=dict(kind='family'),children=[]),
                dict(source=source,rule=dict(kind=KIND,id=record_key(record)),children=[target])])
            h.set_admission_budget(0)
            with patch.object(h,'_discover',side_effect=AssertionError('fresh recognition')):
                verify_positive(h,proof,[source],[[],[],[],[],[]],[record],Counter())
                with self.assertRaises(ValueError):
                    verify_positive(h,proof,[source],[[],[],[],[],[]],[],Counter())
                bad = copy.deepcopy(proof); bad['steps'].reverse()
                with self.assertRaises(ValueError):
                    verify_positive(h,bad,[source],[[],[],[],[],[]],[record],Counter())
                bad = copy.deepcopy(proof); bad['steps'][-1]['children']=[]
                with self.assertRaises(ValueError):
                    verify_positive(h,bad,[source],[[],[],[],[],[]],[record],Counter())
        finally:
            h.close()


if __name__ == '__main__': unittest.main()
