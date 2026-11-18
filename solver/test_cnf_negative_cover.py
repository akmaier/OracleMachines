from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_negative_cover import select,publish_cover
from experiments.cnf_mixed_completion import select as previous
from experiments.cnf_residual_dag import ResidualSolver,propagate,restrict,two_cnf,holds


def colouring(vertices,edges):
    v=lambda i,c:3*i+c+1
    return ([[v(i,c) for c in range(3)] for i in range(vertices)]
        +[[-v(i,a),-v(i,b)] for i in range(vertices) for a,b in combinations(range(3),2)]
        +[[-v(i,c),-v(j,c)] for i,j in edges for c in range(3)])


def supplied(s,source,clause):
    d=dict(attempts=[],completions=[])
    for literal in clause:
        cnf,_,root=s._canonical(source+[[literal]]);fixed,trace,conflict=propagate(cnf,Counter())
        assert conflict is None
        residual=restrict(cnf,fixed);counts=Counter();model,proof=two_cnf(residual,counts);assert model is None
        index=len(d['attempts']);d['attempts'].append(dict(clause=[literal],screen=dict(root=root,trace=trace,conflict=None,residual_literals=sum(map(len,residual)))))
        d['completions'].append(dict(index=index,mixed=dict(model=None,proof=proof,metrics=dict(counts))))
    return dict(kind='negative-cover',root=s._canonical(source)[2],clause_index=0,clause=sorted(clause),attempts=list(range(len(clause)))),d


class NegativeCoverTests(unittest.TestCase):
    def solver(self,**kw):
        s=ResidualSolver(**kw);self.addCleanup(s.close);return s

    def test_compiles_k4_without_search_or_scc_rediscovery(self):
        source=colouring(4,list(combinations(range(4),2)));s=self.solver(node_limit=0);counts=Counter()
        with patch.object(s,'_expand',side_effect=AssertionError('Selection search')),patch.object(s,'_store',side_effect=AssertionError('Selection publication')):
            choice,t=select(s,source,counts=counts)
        self.assertEqual(t['reason'],'negative-cover')
        with patch.object(s,'_visit',side_effect=AssertionError('Acquisition')),patch('experiments.cnf_mixed_completion.two_cnf',side_effect=AssertionError('SCC rediscovery')):
            r=publish_cover(s,source,choice,t['discovery'])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
        self.assertLessEqual(r['archive_nodes'],8)
        self.assertEqual(s.solve(source)['answer'],False)

    def test_restriction_turns_retained_cycle_into_unit_conflict(self):
        source=[[1,2]]+[[-1,a,b] for a in (-2,2) for b in (-3,3)]+[[-2,a,b] for a in (-1,1) for b in (-4,4)]
        s=self.solver(node_limit=0);choice,d=supplied(s,source,[1,2]);r=publish_cover(s,source,choice,d)
        self.assertFalse(r['answer']);self.assertGreater(r['metrics'].get('cover_path_repairs',0),0)
        self.assertEqual(s.solve(source)['answer'],False)

    def test_missing_or_corrupt_condition_rejected_before_publication(self):
        source=colouring(4,list(combinations(range(4),2)))
        for mutation in ('root','missing','literal','path','reason','clause','duplicate'):
            s=self.solver();choice,t=select(s,source);d=t['discovery']
            if mutation=='root':choice['root']+='x'
            elif mutation=='missing':choice['attempts'].pop()
            elif mutation=='literal':d['attempts'][choice['attempts'][0]]['clause']=[-choice['clause'][0]]
            elif mutation=='path':d['completions'][choice['attempts'][0]]['mixed']['proof']['forward']=[]
            elif mutation=='reason':d['attempts'][choice['attempts'][0]]['screen']['trace'][0][1]=-1
            elif mutation=='clause':choice['clause_index']=len(source)
            else:choice['attempts'][-1]=choice['attempts'][0]
            with self.assertRaises((ValueError,KeyError,TypeError)):publish_cover(s,source,choice,d)
            self.assertEqual(s.archive_storage()[0],0)

    def test_negative_subset_does_not_refute_parent(self):
        source=colouring(4,[(0,1),(0,2),(0,3),(1,2),(2,3)])
        s=self.solver();choice,t=select(s,source)
        self.assertNotEqual(t['reason'],'negative-cover');self.assertTrue(s.solve(source)['answer'])
        source=[[1,2],[-1,-2]]+[[1,a,b] for a in (-3,3) for b in (-4,4)]
        s=self.solver();choice,t=select(s,source)
        self.assertEqual(t['reason'],'inline-positive-model')
        self.assertTrue(holds(source,dict(choice['model'])))

    def test_cold_replay_uses_unmodified_native_verifier_and_preserves_nodes(self):
        source=colouring(4,list(combinations(range(4),2)))
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path,node_limit=0)
            try:
                choice,t=select(s,source);r=publish_cover(s,source,choice,t['discovery'])
                before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                again=publish_cover(s,source,choice,t['discovery'])
                self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Cold publication')):
                    self.assertFalse(s.solve(source)['answer']);self.assertEqual(select(s,source)[1]['reason'],'known-target')
            finally:s.close()

    def test_transport_with_forced_prefix_and_signed_names(self):
        source=colouring(4,list(combinations(range(4),2)))
        source=[[20]]+source
        for raw in (source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
            s=self.solver(node_limit=0,leaves=False);choice,t=select(s,raw)
            self.assertEqual(t['reason'],'negative-cover')
            self.assertFalse(publish_cover(s,raw,choice,t['discovery'])['answer'])

    def test_guarded_source_clause_remains_an_explicit_miss(self):
        source=colouring(4,list(combinations(range(4),2)))
        source=[[20]]+[[-20]+c for c in source]
        s=self.solver(leaves=False);choice,t=select(s,source)
        self.assertEqual(t['reason'],'retained-prefix')
        self.assertEqual((choice,t),previous(s,source))
        self.assertFalse(s.solve(source)['answer'])

    def test_exhaustive_four_vertex_graphs_with_coordinates(self):
        edges=list(combinations(range(4),2));covers=0
        for mask in range(64):
            chosen=[e for i,e in enumerate(edges) if mask>>i&1]
            expected=any(all(bits[i]!=bits[j] for i,j in chosen) for bits in product(range(3),repeat=4))
            source=colouring(4,chosen)
            for raw in (source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
                s=ResidualSolver()
                try:
                    choice,t=select(s,raw)
                    if t['reason']=='negative-cover':
                        covers+=1;self.assertFalse(expected)
                        self.assertFalse(publish_cover(s,raw,choice,t['discovery'])['answer'])
                    else:
                        self.assertEqual((choice,t),previous(s,raw))
                    self.assertEqual(s.solve(raw)['answer'],expected)
                finally:s.close()
        self.assertGreater(covers,0)


if __name__=='__main__':unittest.main()
