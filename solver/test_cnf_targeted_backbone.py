from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_targeted_backbone import TargetedBackboneSolver,inspect_targeted_backbone
from experiments.cnf_binary_backbone import inspect_backbones,check_path,excluded_child
from experiments.cnf_residual_dag import ResidualSolver,normalize,holds
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_binary_clause_cover import fixture


def positive():return [[-1,2],[-1,-2],[1,3,4],[1,-3,5]]
def negative():return [[-1,2],[-1,-2]]+[[1,a,b] for a,b in product((3,-3),(4,-4))]


class TargetedBackboneTests(unittest.TestCase):
    def test_target_without_a_whole_cover_candidate(self):
        cnf,_=normalize(positive());counts=Counter()
        self.assertEqual(inspect_backbones(cnf,Counter()),(None,None,None))
        proof,cover,partials=inspect_targeted_backbone(cnf,counts)
        self.assertIsNone(proof);self.assertIsNone(cover)
        self.assertEqual(partials[0]['literal'],1);check_path(cnf,partials[0],Counter())
        self.assertEqual(counts['binary_target_reach_roots'],1)
        self.assertEqual(counts['binary_cover_reach_roots'],0)

    def test_cover_keeps_priority_and_budget(self):
        cnf,_=normalize(fixture());counts=Counter()
        old=inspect_backbones(cnf,Counter());new=inspect_targeted_backbone(cnf,counts)
        self.assertEqual(new[:2],old[:2]);self.assertIsNone(new[2])
        self.assertEqual(counts['binary_target_calls'],0)
        counts=Counter();_,cover,partials=inspect_targeted_backbone(cnf,counts,root_limit=0)
        self.assertIsNone(cover);self.assertTrue(partials)
        self.assertEqual(counts['binary_cover_reach_roots'],0)
        self.assertEqual(counts['binary_target_reach_roots'],1)
        for limit in (-1,True):
            with self.assertRaises(ValueError):inspect_targeted_backbone(cnf,Counter(),root_limit=limit)

    def test_completed_cover_hits_and_misses_are_reused(self):
        for binary,found in (([[-1,2],[-1,-2],[-3,-4]],True),([[-1,2],[-3,-4]],False)):
            cnf,_=normalize(binary+[[1,3,4]]);counts=Counter()
            _,_,partials=inspect_targeted_backbone(cnf,counts)
            self.assertEqual(bool(partials),found)
            self.assertEqual(counts['binary_target_reach_hits'],1)
            self.assertEqual(counts['binary_target_reach_roots'],0)

    def test_absent_variable_avoids_graph_and_extra_search(self):
        cnf,_=normalize([[-1,2],[3,4,5],[3,-4,5],[3,4,-5]])
        counts=Counter();self.assertEqual(inspect_targeted_backbone(cnf,counts),(None,None,None))
        self.assertEqual(counts['binary_target_absent_variables'],1)
        self.assertEqual(counts['binary_cover_graph_edges'],0)

    def test_positive_lift_and_direct_excluded_compilation(self):
        s=TargetedBackboneSolver();self.addCleanup(s.close)
        with patch('experiments.cnf_targeted_backbone.excluded_child',side_effect=AssertionError('Unneeded negative')):
            r=s.solve(positive())
        self.assertTrue(holds(positive(),r['model']));self.assertEqual(r['metrics']['binary_backbone_positive_lifts'],1)
        cnf,_=normalize(positive());e=inspect_targeted_backbone(cnf,Counter())[2][0]
        s=ResidualSolver();self.addCleanup(s.close)
        with patch('experiments.cnf_residual_dag.propagate',side_effect=AssertionError('Repeated propagation')),patch.object(s,'_expand',side_effect=AssertionError('Search')):
            key=excluded_child(s,cnf,e)
        self.assertFalse(s.checked[key]['answer'])

    def test_negative_signed_transport_cold_replay_and_preservation(self):
        names={1:-31,2:10,3:-83,4:55}
        source=[[(1 if l>0 else -1)*names[abs(l)] for l in c] for c in reversed(negative())]
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=TargetedBackboneSolver(path)
            try:
                s.solve([[999]]);old=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                r=s.solve(source);self.assertFalse(r['answer'])
                self.assertGreater(r['metrics']['binary_backbone_negative_splits'],0)
                final=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'));self.assertTrue(old.items()<=final.items())
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Cold write')):
                    self.assertFalse(s.solve(source)['answer'])
                self.assertEqual(final,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()

    def test_exhaustive_small_truth_and_selected_binary_forcing(self):
        binary=[c for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        assignments=[dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)]
        s=TargetedBackboneSolver();self.addCleanup(s.close)
        for mask in range(1<<len(binary)):
            raw=[c for i,c in enumerate(binary) if mask>>i&1]+[(1 if mask&1 else -1,2,-3)]
            cnf,_=normalize(raw);counts=Counter();proof,cover,partials=inspect_targeted_backbone(cnf,counts)
            self.assertLessEqual(counts['binary_target_reach_roots'],1)
            self.assertLessEqual(counts['binary_cover_reach_roots'],8)
            self.assertEqual((proof,cover),inspect_backbones(cnf,Counter())[:2])
            expected=any(holds(raw,a) for a in assignments)
            self.assertEqual(s.solve(raw)['answer'],expected)
            if proof is None and cover is None and mask:
                freq=Counter(abs(l) for c in cnf for l in c);v=min(freq,key=lambda v:(-freq[v],v))
                models=[a for a in assignments if holds([c for c in cnf if len(c)==2],a)]
                forced=len({a[v] for a in models})==1
                self.assertEqual(bool(partials),forced,cnf)
                if partials:check_path(cnf,partials[0],Counter())

    def test_cross_family_edits_and_disabled_leaves(self):
        for family in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for sample in range(3):
                source=generate(family,12,sample,36)
                for edited in (source,source[:-1],source+[[1,-2,3]]):
                    s=TargetedBackboneSolver()
                    try:
                        r=s.solve(edited);self.assertEqual(r['answer'],truth_table(edited)['answer'])
                        with patch.object(s,'_expand',side_effect=AssertionError('Known source')):
                            self.assertEqual(s.solve(edited)['answer'],r['answer'])
                    finally:s.close()
        s=TargetedBackboneSolver(leaves=False);self.addCleanup(s.close)
        with patch('experiments.cnf_targeted_backbone.inspect_targeted_backbone',side_effect=AssertionError('Disabled')):
            self.assertFalse(s.solve(negative())['answer'])


if __name__=='__main__':unittest.main()
