from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import PatternInventory, encode
from experiments.cnf_expanded_coverage import FORMAT, expand, verify_expanded
from experiments.cnf_selected_routes import verify_selected_plan
from experiments.cnf_positive_primitives import verify_positive
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_affine_projection import ProjectionPatternInventory
from experiments.cnf_probe_equivalence import ProbeEquivalenceInventory
from experiments.cnf_binary_paths import discover_binary_paths, check_binary_paths
from experiments.cnf_polarity_horn import discover_polarity, check_polarity
from experiments.cnf_simplification import discover_simplification, check_simplification
from solver.test_cnf_pattern_inventory import assignments, parity
import solver.test_cnf_selected_routes as selected_fixtures

EMPTY = [[], [], [], [], []]


def expanded(h, root):
    old = dict(roots=[root], steps=[dict(source=root, rule=dict(kind='base'))])
    routes = verify_selected_plan(h, old, [root], EMPTY, Counter())
    return expand(h, old, [root], routes, Counter())


def save(h, key, node):
    h.db.execute('INSERT OR REPLACE INTO cnf_patterns_v1 VALUES (?,?)', (key, encode(node)))
    h.db.commit()


def edge_proof(h, source, kind, target, **fields):
    cnf, _, key = h._canonical(source, 0)
    child, names, child_key = h._canonical(target, 0)
    save(h, child_key, dict(kind='family', cnf=[list(c) for c in child], depth=0))
    node = dict(kind=kind, cnf=[list(c) for c in cnf], depth=0,
                edge=dict(key=child_key, names=names), **fields)
    save(h, key, node)
    return dict(format=FORMAT, roots=[key], steps=[
        dict(source=child_key, rule=dict(kind='family'), children=[]),
        dict(source=key, rule=dict(kind='edge'), children=[child_key])]), node


class PositivePrimitiveTests(unittest.TestCase):
    def test_selected_conditioning_ignores_history_but_checks_both_bindings(self):
        h = PatternInventory(max_depth=1, candidate_limit=1, parity_width=0)
        try:
            root = h.inspect([[-1,-2,-3], [1,2,3], [1,-2,4]])['root']['key']
            proof = expanded(h, root); node = copy.deepcopy(h._load(root))
            self.assertEqual(node['kind'], 'or')
            # Losing proposals and discovery summaries do not license semantics.
            node['alternatives'].append({'untrusted_losing_policy':True})
            node['selected'] = 999; node['summary'] = {}; node['profile'] = {}
            save(h, root, node); h.checked.clear()
            with patch.object(h, '_load', side_effect=AssertionError('historical validation')):
                verify_positive(h, proof, [root], EMPTY, Counter())
                for mutation in (
                        lambda p: p['steps'][-1]['children'].pop(),
                        lambda p: p['steps'][-1]['children'].reverse(),
                        lambda p: p['steps'].reverse(),
                        lambda p: p['steps'][-1]['rule'].update(index=False)):
                    bad = copy.deepcopy(proof); mutation(bad)
                    with self.assertRaises(ValueError): verify_positive(h, bad, [root], EMPTY, Counter())
                for mutate in (lambda n: n['alternatives'][0]['edges'][0].update(names=[999]),
                               lambda n: n['alternatives'][0].update(variable=True)):
                    bad = copy.deepcopy(node); mutate(bad); save(h, root, bad)
                    with self.assertRaises(ValueError): verify_positive(h, proof, [root], EMPTY, Counter())
                save(h, root, node)
            self.assertEqual(h.checked, {})
            with self.assertRaises((ValueError, KeyError)): verify_expanded(h, proof, [root], EMPTY, Counter())
        finally: h.close()

    def test_retained_reference_and_shared_component_multiplicity(self):
        h = BudgetedInventory(max_depth=0)
        try:
            h.prepared._edge(((1,), (3,)), 0); h.set_admission_budget(10)
            root = h._edge(((1,), (3,)), 0)['key']; proof = expanded(h, root)
            h.checked.clear(); h.prepared.checked.clear()
            with (patch.object(h, '_load', side_effect=AssertionError('history')),
                  patch.object(h.prepared, '_load', side_effect=AssertionError('prepared history'))):
                verify_positive(h, proof, [root], EMPTY, Counter())
                and_step = next(s for s in proof['steps'] if s['rule']['kind']=='components')
                self.assertEqual(len(and_step['children']), 2)
                self.assertEqual(len(set(and_step['children'])), 1)
                bad = copy.deepcopy(proof)
                next(s for s in bad['steps'] if s['rule']['kind']=='components')['children'].pop()
                with self.assertRaises(ValueError): verify_positive(h, bad, [root], EMPTY, Counter())
                row = json.loads(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(root,)).fetchone()[0])
                row['reference'] = root; save(h, root, row)
                with self.assertRaises(ValueError): verify_positive(h, proof, [root], EMPTY, Counter())
            self.assertEqual(h.checked, {}); self.assertEqual(h.prepared.checked, {})
        finally: h.close()

    def test_exhaustive_two_variable_elimination_semantics(self):
        h = BudgetedInventory(max_depth=0); accepted = 0
        try:
            clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                       for signs in itertools.product((-1,0,1),repeat=2)]
            with patch.object(h, '_load', side_effect=AssertionError('history')):
                for mask in range(512):
                    cnf, _ = normalize([c for i,c in enumerate(clauses) if mask>>i&1])
                    for v in {abs(l) for c in cnf for l in c}:
                        target = check_additive_elimination(cnf, dict(variable=v), Counter())
                        proof, _ = edge_proof(h, cnf, 'eliminate', target, additive_elimination=dict(variable=v))
                        verify_positive(h, proof, proof['roots'], EMPTY, Counter()); accepted += 1
                        names = sorted({abs(l) for c in target for l in c})
                        feasible = {tuple(a[v] for v in names) for a in assignments(cnf) if holds(cnf,a)}
                        for a in assignments(target):
                            self.assertEqual(holds(target,a), tuple(a[v] for v in names) in feasible)
            self.assertEqual(accepted, 504); self.assertEqual(h.checked, {})
        finally: h.close()

    def test_elimination_missing_resolvent_and_false_family_rejected(self):
        h = BudgetedInventory(max_depth=0)
        try:
            cnf, _ = normalize([(-1,3), (1,2)])
            target = check_additive_elimination(cnf, dict(variable=1), Counter())
            good, node = edge_proof(h, cnf, 'eliminate', target, additive_elimination=dict(variable=1))
            verify_positive(h, good, good['roots'], EMPTY, Counter())
            # The weakened child is trivially recognized, but omits (2 OR 3).
            bad, _ = edge_proof(h, cnf, 'eliminate', [], additive_elimination=dict(variable=1))
            with self.assertRaises(ValueError): verify_positive(h, bad, bad['roots'], EMPTY, Counter())
            for certificate in (dict(variable=None), dict(variable=True), dict(variable=999)):
                node['additive_elimination'] = certificate; save(h, good['roots'][0], node)
                with self.assertRaises(ValueError): verify_positive(h, good, good['roots'], EMPTY, Counter())
            source = [[-1,-2,-3],[1,2,3],[1,-2,4]]
            cnf, _, root = h._canonical(source, 0)
            save(h, root, dict(cnf=[list(c) for c in cnf], depth=0, kind='family',
                              summary=dict(closed=True), profile=dict(outcomes=dict(horn='recognized'))))
            fake = dict(format=FORMAT, roots=[root], steps=[dict(source=root,rule=dict(kind='family'),children=[])])
            with self.assertRaises(ValueError): verify_positive(h, fake, [root], EMPTY, Counter())
        finally: h.close()

    def test_binary_reasons_and_source_edits(self):
        h = BudgetedInventory(max_depth=0)
        try:
            cnf, _ = normalize([(-1,2),(-2,3),(-1,3,4)])
            cert = discover_binary_paths(cnf, Counter()); target = check_binary_paths(cnf, cert, Counter())
            proof, node = edge_proof(h, cnf, 'binary_paths', target, binary_paths=cert)
            verify_positive(h, proof, proof['roots'], EMPTY, Counter())
            for mutate in (lambda n:n['binary_paths']['proof'][-1].__setitem__(-1,999),
                           lambda n:n['cnf'].pop(), lambda n:n['edge'].update(names=[True,2,3])):
                bad = copy.deepcopy(node); mutate(bad); save(h, proof['roots'][0], bad)
                with self.assertRaises(ValueError): verify_positive(h, proof, proof['roots'], EMPTY, Counter())
        finally: h.close()

    def test_projection_and_probe_replay_without_historical_checker(self):
        for constructor, source, expected in (
                (ProjectionPatternInventory, parity((1,2,3,4),1)+parity((3,4,5,6),1)+[(1,6)], 'project'),
                (ProbeEquivalenceInventory, [(-4,-2,-1),(-3,1),(-2,4),(2,3)], 'probe')):
            h = constructor(max_depth=0)
            try:
                root = h.inspect(source)['root']['key']; self.assertEqual(h._load(root)['kind'], expected)
                proof = expanded(h, root); node = copy.deepcopy(h._load(root)); h.checked.clear()
                with patch.object(h, '_load', side_effect=AssertionError('history')):
                    verify_positive(h, proof, [root], EMPTY, Counter())
                    if expected == 'project': node['profile']['projection']['keep'] = []
                    else: node['profile']['probing']['attempts'][0]['certificate']['units'][0][1] = 999
                    save(h, root, node)
                    with self.assertRaises(ValueError): verify_positive(h, proof, [root], EMPTY, Counter())
                self.assertEqual(h.checked, {})
            finally: h.close()

    def test_polarity_simplification_and_fused_branch_transport(self):
        h = BudgetedInventory(max_depth=1)
        try:
            cnf, _ = normalize([(1,2,3),(-1,-2)])
            cert = discover_polarity(cnf,Counter()); target = check_polarity(cnf,cert,Counter())
            proof, _ = edge_proof(h,cnf,'polarity',target,polarity=cert)
            verify_positive(h,proof,proof['roots'],EMPTY,Counter())
            cnf, _ = normalize([(1,),(2,3),(-2,4)])
            cert = discover_simplification(cnf,Counter(),pure=False)
            target, _ = check_simplification(cnf,cert,Counter(),pure=False)
            proof, _ = edge_proof(h,cnf,'simplify',target,profile=dict(simplification=dict(certificate=cert)))
            verify_positive(h,proof,proof['roots'],EMPTY,Counter())
            # Sparse surviving names after conditioning, then unit closure.
            source, _, root = h._canonical([(-1,2),(1,3),(2,3,4)],1)
            edges=[]; steps=[]; seen=set()
            from experiments.cnf_residual_dag import restrict
            for value in (False,True):
                intermediate,names=normalize(restrict(source,{1:value},Counter()))
                cert=discover_simplification(intermediate,Counter(),pure=False)
                target,_=check_simplification(intermediate,cert,Counter(),pure=False)
                child,local,key=h._canonical(target,0)
                save(h,key,dict(kind='family',cnf=[list(c) for c in child],depth=0))
                edges.append(dict(key=key,names=[names[v-1] for v in local],closure=cert))
                if key not in seen:
                    steps.append(dict(source=key,rule=dict(kind='family'),children=[]));seen.add(key)
            node=dict(cnf=[list(c) for c in source],depth=1,kind='or',alternatives=[dict(variable=1,edges=edges)])
            save(h,root,node);steps.append(dict(source=root,rule=dict(kind='conditioning',index=0),children=[e['key'] for e in edges]))
            proof=dict(format=FORMAT,roots=[root],steps=steps)
            verify_positive(h,proof,[root],EMPTY,Counter())
            node['alternatives'][0]['edges'][0]['closure']['units'][0][1]=999;save(h,root,node)
            with self.assertRaises(ValueError):verify_positive(h,proof,[root],EMPTY,Counter())
        finally:h.close()

    def test_external_split_keeps_original_validator_and_two_branches(self):
        fixture = selected_fixtures.SelectedRoutesTests()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = fixture.history(path)
            root, old, evidence = fixture.split(h)
            routes = verify_selected_plan(h, old, [root], evidence, Counter())
            proof = expand(h, old, [root], routes, Counter()); h.close()
            h = fixture.history(path)
            try:
                counts = Counter(); verify_positive(h, proof, [root], evidence, counts)
                self.assertGreater(counts['positive_external_steps'], 0)
                self.assertGreater(len(h.checked), 0)
                for mutation in (lambda p:p['steps'][-1]['children'].pop(),
                                 lambda p:p['steps'].append(p['steps'][0]),
                                 lambda p:p['steps'][-1].update(rule=dict(kind='base'))):
                    bad=copy.deepcopy(proof); mutation(bad)
                    with self.assertRaises(ValueError): verify_positive(h,bad,[root],evidence,Counter())
                with self.assertRaises(ValueError): verify_positive(h,proof,[root],EMPTY,Counter())
            finally: h.close()


if __name__ == '__main__': unittest.main()
