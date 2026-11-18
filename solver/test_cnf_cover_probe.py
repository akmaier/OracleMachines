from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import unittest
from experiments.cnf_cover_probe import select,choose_gap,probe_gap,combined_discovery
from experiments.cnf_negative_cover import select as previous,publish_cover
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_positive_child import publish_model
from solver.test_cnf_negative_cover import colouring


class CoverProbeTests(unittest.TestCase):
    def solver(self,**kw):
        s=ResidualSolver(**kw);self.addCleanup(s.close);return s

    def test_one_probe_completes_k4_with_two_ranked_variables(self):
        source=colouring(4,list(combinations(range(4),2)));s=self.solver(node_limit=0);counts=Counter()
        old,old_trace=previous(s,source,2)
        with patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Publication')):
            choice,t=select(s,source,2,counts)
        self.assertEqual(t['reason'],'gap-negative-cover');self.assertEqual(counts['cover_gap_probes'],1)
        self.assertEqual(t['discovery'],old_trace['discovery'])
        self.assertNotIn([3],t['discovery']['candidates'])
        before=deepcopy(t)
        with patch.object(s,'_visit',side_effect=AssertionError('Search')),patch('experiments.cnf_cover_probe.two_cnf',side_effect=AssertionError('Rediscovery')):
            result=publish_cover(s,source,choice,combined_discovery(t))
        self.assertEqual(t,before);self.assertFalse(result['answer']);self.assertLessEqual(result['archive_nodes'],8)

    def test_candidate_ranking_overlap_and_already_attempted_literals(self):
        d=dict(completions=[dict(index=i,mixed=dict(model=None)) for i in range(2)],
               attempts=[dict(clause=[1]),dict(clause=[2]),dict(clause=[9])])
        # Wider, tautological and already attempted candidates cannot preempt [2,4].
        candidate=choose_gap([[1,2,3],[1,-1,6],[2,9],[2,4],[1,5]],d)
        self.assertEqual(candidate,dict(clause_index=3,clause=[2,4],literal=4))
        self.assertIsNone(choose_gap([[3,4],[1,2],[1,-1,6],[1,9]],d))

    def test_missing_condition_can_be_positive(self):
        source=[[1,2,3],[-1,-2],[-1,-3],[-2,-3]]
        source += [[-i,a,b] for i in (1,2) for a in (-4,4) for b in (-5,5)]
        s=self.solver(node_limit=0);choice,t=select(s,source,2)
        self.assertEqual(t['reason'],'gap-positive-model');self.assertEqual(t['gap']['outcome'],'positive')
        self.assertTrue(holds(source,dict(choice['model'])))
        self.assertTrue(publish_model(s,source,choice)['answer'])

    def test_nonbinary_and_unit_conflict_remain_explicit_misses(self):
        s=self.solver()
        for source,expected in (([[1,2,3]],'nonbinary'),([[4],[-4]],'unit-conflict')):
            counts=Counter();e,model=probe_gap(s,source,dict(clause_index=0,clause=[4],literal=4),counts)
            self.assertIsNone(model);self.assertEqual(e['outcome'],expected)
            self.assertEqual(counts['cover_gap_probes'],1);self.assertEqual(s.archive_storage()[0],0)

    def test_corrupt_extra_evidence_cannot_publish(self):
        source=colouring(4,list(combinations(range(4),2)))
        for mutation in ('path','root','assumption','missing'):
            s=self.solver();choice,t=select(s,source,2)
            if mutation=='path':t['gap']['completion']['mixed']['proof']['forward']=[]
            elif mutation=='root':t['gap']['attempt']['screen']['root']+='x'
            elif mutation=='assumption':t['gap']['attempt']['clause']=[-3]
            else:t.pop('gap')
            with self.assertRaises((ValueError,KeyError,IndexError)):
                publish_cover(s,source,choice,combined_discovery(t))
            self.assertEqual(s.archive_storage()[0],0)

    def test_existing_cover_disabled_and_known_targets_preserved(self):
        source=colouring(4,list(combinations(range(4),2)));s=self.solver()
        for limit in (0,3,4):
            counts=Counter();self.assertEqual(select(s,source,limit,counts),previous(s,source,limit))
            self.assertEqual(counts['cover_gap_probes'],0)
        s.solve(source);self.assertEqual(select(s,source,2)[1]['reason'],'known-target')
        with self.assertRaises(ValueError):select(s,source,-1)

    def test_forced_prefix_and_cold_replay(self):
        source=[[20]]+colouring(4,list(combinations(range(4),2)))
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:
                counts=Counter();choice,t=select(s,source,2,counts)
                self.assertEqual(t['reason'],'gap-negative-cover');self.assertEqual(counts['fallback_trace_reuses'],0)
                publish_cover(s,source,choice,combined_discovery(t));before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                publish_cover(s,source,choice,combined_discovery(t))
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')):self.assertFalse(s.solve(source)['answer'])
            finally:s.close()

    def test_all_four_vertex_graphs_in_two_coordinate_systems(self):
        edges=list(combinations(range(4),2));gaps=0
        for mask in range(64):
            chosen=[e for i,e in enumerate(edges) if mask>>i&1]
            truth=any(all(bits[i]!=bits[j] for i,j in chosen) for bits in product(range(3),repeat=4))
            source=colouring(4,chosen)
            for raw in (source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
                s=ResidualSolver()
                try:
                    counts=Counter();choice,t=select(s,raw,2,counts);self.assertLessEqual(counts['cover_gap_probes'],1)
                    if t['reason']=='gap-negative-cover':
                        gaps+=1;self.assertFalse(truth);self.assertFalse(publish_cover(s,raw,choice,combined_discovery(t))['answer'])
                    elif t['reason']=='gap-positive-model':self.assertTrue(truth);self.assertTrue(holds(raw,dict(choice['model'])))
                    else:self.assertEqual(choice,previous(s,raw,2)[0])
                    self.assertEqual(s.solve(raw)['answer'],truth)
                finally:s.close()
        self.assertGreater(gaps,0)


if __name__=='__main__':unittest.main()
