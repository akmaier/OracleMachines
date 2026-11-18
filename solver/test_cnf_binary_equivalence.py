from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json,unittest
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,EquivalenceStore,discover,check_substitution,TABLE,FORMAT
from experiments.cnf_targeted_backbone import TargetedBackboneSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import ResidualSolver,normalize,holds
from experiments.cnf_cross_family import generate,truth_table


def positive():return [[-1,2],[1,-2],[1,2,3]]
def negative():return [[-1,2],[1,-2]]+[[a,2 if a>0 else -2,b] for a,b in product((1,-1),(3,-3))]


class BinaryEquivalenceTests(unittest.TestCase):
    def test_two_shared_trees_replace_repeated_paths(self):
        n=24;source=[[-i,i+1] for i in range(1,n)]+[[-n,1],[1,n,n+1]]
        cnf,_=normalize(source);counts=Counter();e=discover(cnf,counts)
        self.assertEqual(counts['equiv_tree_searches'],2)
        self.assertEqual(len(e['forward'])+len(e['backward']),2*(n-1))
        target,mapping=check_substitution(cnf,e,Counter());self.assertEqual(len(mapping),n)
        self.assertEqual(len({abs(l) for c in target for l in c}),2)

    def test_full_substitution_and_sat_lift(self):
        s=BinaryEquivalenceSolver();self.addCleanup(s.close)
        r=s.solve(positive());self.assertTrue(r['answer']);self.assertTrue(holds(positive(),r['model']))
        self.assertEqual(r['authority'],'native');self.assertEqual(r['metrics']['equiv_positive_lifts'],1)
        self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)

    def test_negative_extension_original_native_child_and_cold_read(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BinaryEquivalenceSolver(path)
            try:
                s.solve([[999]]);old=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                r=s.solve(negative());self.assertFalse(r['answer']);self.assertEqual(r['authority'],FORMAT)
                self.assertIsNone(s._read(r['root']))
                self.assertTrue(old.items()<=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')).items())
                with patch('experiments.cnf_binary_equivalence.discover',side_effect=AssertionError('Repeated discovery')),patch.object(s,'_expand',side_effect=AssertionError('Warm search')):
                    self.assertFalse(s.solve(negative())['answer'])
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:
                node=EquivalenceStore(s).read(r['root']);self.assertFalse(node['answer'])
                self.assertFalse(s._read(node['child'])['answer']);self.assertIsNone(s._read(r['root']))
            finally:s.close()

    def test_corrupt_edges_support_and_cycles_rejected(self):
        cnf,_=normalize(positive());e=discover(cnf,Counter())
        variants=[]
        a=copy.deepcopy(e);a['forward'][0][2]=next(i for i,c in enumerate(cnf) if len(c)>2);variants.append(a)
        a=copy.deepcopy(e);a['backward']=[];variants.append(a)
        a=copy.deepcopy(e);a['forward']*=2;variants.append(a)
        a=copy.deepcopy(e);a['representative']=True;variants.append(a)
        for bad in variants:
            with self.assertRaises(ValueError):check_substitution(cnf,bad,Counter())
        # Supported edges on a disjoint cycle do not prove reachability to rep.
        cnf,_=normalize([[-1,2],[1,-2],[-3,4],[3,-4],[1,2,3]])
        edge=lambda a,b:[a,b,cnf.index(tuple(sorted((-a,b))))]
        bad=dict(representative=1,forward=[edge(1,2),edge(3,4),edge(4,3)],backward=[edge(2,1),edge(3,4),edge(4,3)])
        with self.assertRaises(ValueError):check_substitution(cnf,bad,Counter())

    def test_wrong_child_source_and_positive_dependency_rejected(self):
        s=BinaryEquivalenceSolver();self.addCleanup(s.close);r=s.solve(negative())
        node=copy.deepcopy(s.equivalences.read(r['root']));good=node['child']
        node['child']=r['root']
        with self.assertRaises(ValueError):s.equivalences.verify(r['root'],node)
        node['child']=good;node['cnf']=node['cnf'][:-1]
        with self.assertRaises(ValueError):s.equivalences.verify(r['root'],node)
        cnf,_=normalize(positive());e=discover(cnf,Counter());target,_=check_substitution(cnf,e,Counter())
        _,child=s._visit(target);_,_,root=s._canonical(cnf)
        with self.assertRaises(ValueError):s.equivalences.publish(root,cnf,e,child)

    def test_signed_names_and_eliminated_representative_lift(self):
        names={1:-91,2:17,3:-42}
        for raw in (positive(),negative(),[[-1,2],[1,-2],[1,-2,3]]):
            source=[[(1 if l>0 else -1)*names[abs(l)] for l in c] for c in reversed(raw)]
            s=BinaryEquivalenceSolver();self.addCleanup(s.close);r=s.solve(source)
            self.assertEqual(r['answer'],truth_table(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))

    def test_exhaustive_small_truth_and_quotient_semantics(self):
        binary=[c for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        assignments=[dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)]
        s=BinaryEquivalenceSolver();self.addCleanup(s.close)
        for mask in range(1<<len(binary)):
            raw=[c for i,c in enumerate(binary) if mask>>i&1]+[(1 if mask&1 else -1,2,-3)]
            cnf,_=normalize(raw);e=discover(cnf,Counter());expected=any(holds(raw,a) for a in assignments)
            self.assertEqual(s.solve(raw)['answer'],expected)
            if e:
                target,mapping=check_substitution(cnf,e,Counter())
                self.assertEqual(any(holds(target,a) for a in assignments),expected)
                for a in assignments:
                    if holds(cnf,a):self.assertTrue(holds(target,a))
                    if holds(target,a):
                        lifted=dict(a)
                        for v,signed in mapping.items():lifted[v]=a[abs(signed)] if signed>0 else not a[abs(signed)]
                        self.assertTrue(holds(cnf,lifted))

    def test_cross_family_edits_and_disabled_leaves(self):
        for family in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for sample in range(2):
                source=generate(family,12,sample,36)
                for edited in (source,source[:-1],source+[[1,-2,3]]):
                    s=BinaryEquivalenceSolver()
                    try:self.assertEqual(s.solve(edited)['answer'],truth_table(edited)['answer'])
                    finally:s.close()
        s=BinaryEquivalenceSolver(leaves=False);self.addCleanup(s.close)
        with patch('experiments.cnf_binary_equivalence.discover',side_effect=AssertionError('Disabled')):
            self.assertFalse(s.solve(negative())['answer'])


if __name__=='__main__':unittest.main()
