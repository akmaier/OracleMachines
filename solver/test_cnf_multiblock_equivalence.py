from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json,unittest
from experiments.cnf_multiblock_equivalence import MultiEquivalenceSolver,MultiEquivalenceStore,discover_all,check_blocks,dependency,TABLE,FORMAT
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,discover
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,TABLE as V2,FORMAT as F2
from experiments.cnf_binary_core_cache import CachedBinaryEquivalenceSolver
from experiments.cnf_residual_dag import normalize,holds,token
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_cross_family import truth_table,generate
from solver.test_cnf_binary_equivalence import negative


def two_blocks(unsat=False):
    core=[[-1,2],[1,-2],[-3,-4],[3,4]]
    wide=[list(c) for c in product((1,-1),(3,-3),(5,-5))]
    return core+(wide if unsat else wide[:2])


def table(s,t):return dict(s.db.execute(f'SELECT id,payload FROM {t}'))


class MultiBlockEquivalenceTests(unittest.TestCase):
    def test_two_signed_blocks_substitute_once_and_lift(self):
        cnf,_=normalize(two_blocks());e=discover_all(cnf,Counter());self.assertEqual(len(e),2)
        counts=Counter();target,mapping=check_blocks(cnf,e,counts)
        self.assertEqual(len(mapping),4);self.assertEqual(counts['equivalence_substitution_literal_visits'],sum(map(len,cnf)))
        s=MultiEquivalenceSolver();self.addCleanup(s.close);r=s.solve(two_blocks())
        self.assertTrue(r['answer']);self.assertTrue(holds(two_blocks(),r['model']));self.assertEqual(r['metrics']['multi_applied_merges'],2)

    def test_all_small_cores_first_block_matches_previous_policy(self):
        binary=[tuple(sorted(c)) for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        for mask in range(1<<len(binary)):
            cnf=tuple(sorted([c for i,c in enumerate(binary) if mask>>i&1]+[(1,2,3)]))
            old=discover(cnf,Counter());new=discover_all(cnf,Counter())
            self.assertEqual(old,None if new is None else new[0])
            if new:
                target,mapping=check_blocks(cnf,new,Counter())
                self.assertEqual(truth_table(cnf)['answer'],truth_table(target)['answer'])

    def test_exhaustive_wide_mixtures_and_assignment_lifting(self):
        wide=[list(c) for c in product((1,-1),(3,-3),(5,-5))]
        for sign_a,sign_b in product((1,-1),repeat=2):
            for mask in range(1,256):
                raw=[[-1,sign_a*2],[1,-sign_a*2],[-3,sign_b*4],[3,-sign_b*4]]+[c for i,c in enumerate(wide) if mask>>i&1]
                cnf,_=normalize(raw);blocks=discover_all(cnf,Counter());self.assertEqual(len(blocks),2)
                target,mapping=check_blocks(cnf,blocks,Counter())
                for bits in product((False,True),repeat=5):
                    a=dict(enumerate(bits,1));lift=dict(a)
                    for v,rep in mapping.items():lift[v]=a[abs(rep)] if rep>0 else not a[abs(rep)]
                    self.assertEqual(holds(target,a),holds(cnf,lift))
                    if holds(cnf,a):self.assertEqual(a,lift)

    def test_rejects_overlap_corrupt_trees_and_wrong_dependencies(self):
        s=MultiEquivalenceSolver();self.addCleanup(s.close);cnf,_=normalize(two_blocks(True));e=discover_all(cnf,Counter())
        bad=copy.deepcopy(e);bad[1]['forward'][0][2]=len(cnf)
        for blocks in ([],[e[0],e[0]],bad):
            with self.assertRaises(ValueError):check_blocks(cnf,blocks,Counter())
        key=token(cnf,Counter());node=dict(format=FORMAT,answer=False,evidence=e)
        with self.assertRaises(ValueError):dependency(s,key,node)
        result=s.solve(two_blocks(True));self.assertEqual(result['authority'],FORMAT)
        source,child=dependency(s,key,node)
        for x,y in (((),child),(source,key)):
            with self.assertRaises(ValueError):s.equivalences.publish(key,x,e,y)
        for change in (dict(answer=True),dict(format=F2),dict(child=child),dict(evidence=e[:1])):
            bad=dict(node,**change)
            with self.assertRaises(ValueError):dependency(s,key,bad)

    def test_cold_multiple_and_legacy_formats_preserved(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=CompactBinaryEquivalenceSolver(path)
            try:old=s.solve(negative());before=table(s,V2)
            finally:s.close()
            s=MultiEquivalenceSolver(path)
            try:
                self.assertEqual(s.solve(negative())['authority'],F2)
                new=s.solve(two_blocks(True));self.assertEqual(new['authority'],FORMAT);self.assertEqual(table(s,V2),before)
                with patch.object(s.binary_cores,'find',side_effect=AssertionError('Warm discovery')),patch.object(s,'_expand',side_effect=AssertionError('Warm search')):
                    self.assertFalse(s.solve(two_blocks(True))['answer'])
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:
                store=MultiEquivalenceStore(s);self.assertEqual(store.read(old['root'])['format'],F2);self.assertEqual(store.read(new['root'])['format'],FORMAT)
            finally:s.close()

    def test_single_block_retains_previous_certificate_bytes(self):
        a=CachedBinaryEquivalenceSolver(persistent_cache=False);b=MultiEquivalenceSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        x=a.solve(negative());y=b.solve(negative());self.assertEqual(x['authority'],y['authority'])
        for t in ('cnf_residual_v1',V2):self.assertEqual(table(a,t),table(b,t))
        self.assertEqual(table(b,TABLE),{})

    def test_multiblock_cache_transports_both_trees_and_edits_miss(self):
        s=MultiEquivalenceSolver();self.addCleanup(s.close);cnf,_=normalize(two_blocks());e=s.binary_cores.find(cnf)
        edited=tuple(sorted(cnf+((-5,-4,-3),)))
        with patch('experiments.cnf_multiblock_equivalence.discover_all',side_effect=AssertionError('Repeated graph')):
            got=s.binary_cores.find(edited)
        self.assertEqual(got,discover_all(edited,Counter()));check_blocks(edited,got,Counter())
        got[0]['forward'].clear();self.assertEqual(s.binary_cores.find(cnf),e)
        dropped=tuple(c for c in cnf if c!=next(c for c in cnf if len(c)==2))
        self.assertEqual(s.binary_cores.find(dropped),discover_all(dropped,Counter()));self.assertEqual(s.counts['multi_cache_misses'],2)

    def test_growing_blocks_and_eligibility(self):
        for n in (2,4,8,16):
            source=[tuple(sorted(c)) for i in range(n) for c in ((-(2*i+1),2*i+2),(2*i+1,-(2*i+2)))]+[(1,3,2*n+1)]
            cnf=tuple(sorted(source));counts=Counter();e=discover_all(cnf,counts);self.assertEqual(len(e),n)
            self.assertEqual(counts['multi_certificate_edges'],2*n);self.assertEqual(counts['multi_graph_edges'],4*n)
            target,mapping=check_blocks(cnf,e,Counter());self.assertEqual(len(mapping),2*n)
        for cnf in ((),((),),((1,),),((1,2),),((1,2,3),),((-2,-1),(-2,1),(-1,2),(1,2),(1,2,3))):
            self.assertIsNone(discover_all(cnf,Counter()))

    def test_generated_truth_and_disabled_discovery(self):
        for f in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for i in range(3):
                raw=generate(f,12,i,36)
                for cached in (True,False):
                    s=MultiEquivalenceSolver(cache=cached)
                    try:r=s.solve(raw);self.assertEqual(r['answer'],truth_table(raw)['answer'])
                    finally:s.close()
        s=MultiEquivalenceSolver(leaves=False);self.addCleanup(s.close)
        with patch.object(s.binary_cores,'find',side_effect=AssertionError('Disabled')):self.assertFalse(s.solve(two_blocks(True))['answer'])


if __name__=='__main__':unittest.main()
