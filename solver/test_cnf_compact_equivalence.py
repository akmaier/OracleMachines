from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json,unittest
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,CompactEquivalenceStore,source_from_key,dependency,TABLE,FORMAT
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,EquivalenceStore,discover,check_substitution,TABLE as OLD_TABLE,FORMAT as OLD_FORMAT
from experiments.cnf_residual_dag import ResidualSolver,normalize,token,holds,FORMAT as NATIVE_FORMAT
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_binary_equivalence import positive,negative


class CompactEquivalenceTests(unittest.TestCase):
    def test_payload_omits_formulas_and_dependency_reconstructs(self):
        s=CompactBinaryEquivalenceSolver();self.addCleanup(s.close);r=s.solve(negative())
        self.assertFalse(r['answer']);self.assertEqual(r['authority'],FORMAT)
        node=s.equivalences.read(r['root']);self.assertEqual(set(node),{'format','answer','evidence'})
        cnf,child=dependency(s,r['root'],node);self.assertEqual(cnf,normalize(negative())[0])
        self.assertFalse(s._read(child)['answer']);self.assertIsNone(s._read(r['root']))
        self.assertEqual(set(s.equivalences.checked[r['root']]),set(node))
        with patch('experiments.cnf_binary_equivalence.discover',side_effect=AssertionError('Repeated discovery')),patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
            self.assertFalse(s.solve(negative())['answer'])

    def test_key_is_exact_canonical_identity(self):
        s=ResidualSolver();self.addCleanup(s.close);cnf,_=normalize(negative());key=token(cnf,Counter())
        self.assertEqual(source_from_key(s,key),cnf)
        bad=['wrong:'+key,key+' ',NATIVE_FORMAT+':null',NATIVE_FORMAT+':{}',NATIVE_FORMAT+':[[true]]',NATIVE_FORMAT+':[[2]]',NATIVE_FORMAT+':[[1,1]]',NATIVE_FORMAT+':[[1],[-1]]']
        for k in bad:
            with self.assertRaises(ValueError):source_from_key(s,k)

    def test_publication_rejects_wrong_source_child_and_positive_dependency(self):
        s=CompactBinaryEquivalenceSolver();self.addCleanup(s.close);r=s.solve(negative());node=s.equivalences.read(r['root']);cnf,child=dependency(s,r['root'],node)
        for source,target in (((),child),(cnf,r['root'])):
            with self.assertRaises(ValueError):s.equivalences.publish(r['root'],source,node['evidence'],target)
        pos,_=normalize(positive());e=discover(pos,Counter());target,_=check_substitution(pos,e,Counter());_,poschild=s._visit(target)
        with self.assertRaises(ValueError):s.equivalences.publish(token(pos,Counter()),pos,e,poschild)
        self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],1)

    def test_corrupt_tree_and_wrong_headers_fail_before_publication(self):
        s=CompactBinaryEquivalenceSolver();self.addCleanup(s.close);cnf,_=normalize(negative());key=token(cnf,Counter());e=discover(cnf,Counter())
        node=dict(format=FORMAT,answer=False,evidence=e)
        for field,value in (('format',OLD_FORMAT),('answer',True),('child','forged')):
            bad=copy.deepcopy(node);bad[field]=value
            with self.assertRaises(ValueError):dependency(s,key,bad)
        bad=copy.deepcopy(node);bad['evidence']['backward']=[]
        with self.assertRaises(ValueError):dependency(s,key,bad)
        self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)

    def test_legacy_and_compact_coexist_without_rewriting(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BinaryEquivalenceSolver(path)
            try:
                r=s.solve(negative());old=dict(s.db.execute(f'SELECT id,payload FROM {OLD_TABLE}'));node=copy.deepcopy(s.equivalences.read(r['root']))
                before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            s=CompactBinaryEquivalenceSolver(path)
            try:
                with patch('experiments.cnf_binary_equivalence.discover',side_effect=AssertionError('Legacy discovery')),patch.object(s,'_expand',side_effect=AssertionError('Legacy search')):
                    got=s.solve(negative());self.assertEqual(got['authority'],OLD_FORMAT)
                self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)
                cnf,_=normalize(node['cnf']);s.equivalences.publish(r['root'],cnf,node['evidence'],node['child'])
                self.assertEqual(dict(s.db.execute(f'SELECT id,payload FROM {OLD_TABLE}')),old)
                self.assertEqual(dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')),before)
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:
                self.assertEqual(CompactEquivalenceStore(s).read(r['root'])['format'],FORMAT)
                self.assertEqual(EquivalenceStore(s).read(r['root'])['format'],OLD_FORMAT)
            finally:s.close()

    def test_readers_handle_legacy_only_and_native_only_archives(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'legacy';s=BinaryEquivalenceSolver(path)
            try:r=s.solve(negative())
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:self.assertEqual(CompactEquivalenceStore(s).read(r['root'])['format'],OLD_FORMAT)
            finally:s.close()
            path=Path(td)/'native';s=ResidualSolver(path);s.solve([[1]]);s.close();s=SnapshotResidualSolver(path)
            try:self.assertIsNone(CompactEquivalenceStore(s).read(r['root']))
            finally:s.close()

    def test_exhaustive_small_decisions_and_payloads_match_v1(self):
        binary=[c for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        a=BinaryEquivalenceSolver();b=CompactBinaryEquivalenceSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        for mask in range(1<<len(binary)):
            raw=[c for i,c in enumerate(binary) if mask>>i&1]+[(1 if mask&1 else -1,2,-3)]
            x=a.solve(raw);y=b.solve(raw);self.assertEqual(x['answer'],y['answer']);self.assertEqual(x['model'],y['model'])
        self.assertEqual(dict(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),dict(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))
        old=dict(a.db.execute(f'SELECT id,payload FROM {OLD_TABLE}'));new=dict(b.db.execute(f'SELECT id,payload FROM {TABLE}'))
        self.assertEqual(set(old),set(new))
        for key,payload in new.items():
            before=json.loads(old[key]);after=json.loads(payload);self.assertEqual(before['evidence'],after['evidence'])
            _,child=dependency(b,key,after);self.assertEqual(child,before['child'])

    def test_signed_sources_edits_and_disabled_discovery(self):
        for family in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for sample in range(2):
                source=generate(family,12,sample,36)
                for raw in (source,source[:-1],source+[[1,-2,3]]):
                    s=CompactBinaryEquivalenceSolver()
                    try:
                        r=s.solve(raw);self.assertEqual(r['answer'],truth_table(raw)['answer'])
                        if r['answer']:self.assertTrue(holds(raw,r['model']))
                    finally:s.close()
        s=CompactBinaryEquivalenceSolver(leaves=False);self.addCleanup(s.close)
        with patch('experiments.cnf_binary_equivalence.discover',side_effect=AssertionError('Disabled')):
            self.assertFalse(s.solve(negative())['answer'])


if __name__=='__main__':unittest.main()
