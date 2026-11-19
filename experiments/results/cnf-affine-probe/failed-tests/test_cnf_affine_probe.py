from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,sqlite3,unittest
from experiments.cnf_affine_probe import AffineProbeSolver,bounded_extract
from experiments.cnf_affine_patterns import extract_affine,check_affine
from experiments.cnf_affine_negative import NegativeStore,TABLE,FORMAT
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_cross_family import truth_table


def xor(variables,rhs):
    return [[-v if b else v for v,b in zip(variables,bits)]
            for bits in product((False,True),repeat=len(variables)) if sum(bits)%2!=rhs]


class AffineProbeTests(unittest.TestCase):
    def make(self,cls=AffineProbeSolver,*args,**kwargs):
        s=cls(*args,**kwargs);self.addCleanup(s.close);return s

    def test_conflict_without_native_search_and_exact_cold_replay(self):
        source=xor([10,20,30],0)+xor([10,20,30],1)+[[40,50,60]]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=AffineProbeSolver(path)
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('Native acquisition')):r=s.solve(source)
                self.assertFalse(r['answer']);self.assertEqual(r['authority'],FORMAT)
                self.assertEqual(r['affine_archive_nodes'],1);self.assertEqual(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],0)
            finally:s.close()
            s=AffineProbeSolver(path)
            try:
                with patch('experiments.cnf_affine_probe.bounded_extract',side_effect=AssertionError('Fresh probe')),patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
                    q=s.solve(list(reversed(source)))
                self.assertEqual(q['root'],r['root']);self.assertEqual(q['metrics']['affine_probe_exact_hits'],1)
            finally:s.close()
            s=SnapshotResidualSolver(path)
            try:self.assertIsNotNone(NegativeStore(s).read(r['root']))
            finally:s.close()

    def test_consistent_subsystem_does_not_decide_coupling_cnf(self):
        a=self.make();b=self.make(PlannedNegativeSolver)
        for source in (xor([1,2,3],0)+[[4,5,6]],xor([1,2,3],0)+[[1],[2],[3]],[[1,2,3]]):
            x=a.solve(source);y=b.solve(source);self.assertEqual(x['answer'],y['answer'])
            if x['answer']:self.assertTrue(holds(source,x['model']))
        self.assertEqual(a.counts['affine_probe_misses'],1)

    def test_size_and_xor_budget_stop_fall_back(self):
        source=xor([1,2,3],0)+xor([1,2,3],1)
        for kw in (dict(affine_variables=2),dict(affine_clauses=1),dict(affine_literals=1),dict(affine_xors=1)):
            s=self.make(**kw);r=s.solve(source);self.assertFalse(r['answer']);self.assertEqual(r['authority'],'native')
            self.assertEqual(s.affine.storage()[0],0)
            self.assertGreater(r['metrics'].get('affine_probe_size_skips',0)+r['metrics'].get('affine_probe_xor_stops',0),0)
            self.assertLessEqual(r['metrics'].get('affine_elimination_xors',0),s.affine_xors)

    def test_invalid_probe_limits(self):
        for kw in (dict(affine_variables=False),dict(affine_clauses=0),dict(affine_literals=-1),dict(affine_xors=0)):
            with self.assertRaises(ValueError):AffineProbeSolver(**kw)

    def test_extraction_matches_existing_checker(self):
        for width in range(1,6):
            for rhs in (0,1):
                cnf,_=normalize(xor(list(range(1,width+1)),rhs)+[[width+1,width+2]])
                a=bounded_extract(cnf,Counter(),65536);self.assertEqual(a,extract_affine(cnf,Counter()));check_affine(cnf,a,Counter())

    def test_tampered_discovery_is_rejected_before_publication(self):
        s=self.make();source=[[1,2,3]]
        fake=extract_affine(normalize([[1],[-1]])[0],Counter())
        with patch('experiments.cnf_affine_probe.bounded_extract',return_value=fake):
            with self.assertRaises(ValueError):s.solve(source)
        self.assertEqual(s.affine.storage()[0],0);self.assertFalse(s.affine.checked)

    def test_commit_failure_does_not_publish_checked_hint(self):
        s=self.make();original=s.db
        class FailCommit:
            def __getattr__(self,name):return getattr(original,name)
            def __enter__(self):original.__enter__();return self
            def __exit__(self,*args):original.rollback();raise sqlite3.OperationalError('Injected affine commit failure')
        s.db=FailCommit()
        try:
            with self.assertRaises(sqlite3.OperationalError):s.solve([[1],[-1]])
            self.assertFalse(s.affine.checked);self.assertEqual(s.affine.storage()[0],0)
        finally:s.db=original
        self.assertFalse(s.solve([[1],[-1]])['answer'])

    def test_corrupt_cold_record_is_rejected(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=AffineProbeSolver(path)
            try:r=s.solve([[1],[-1]])
            finally:s.close()
            con=sqlite3.connect(path)
            try:
                node=json.loads(con.execute(f'SELECT payload FROM {TABLE}').fetchone()[0]);node['proof']['decision']['row']=0
                with con:con.execute(f'UPDATE {TABLE} SET payload=?',(json.dumps(node),))
            finally:con.close()
            s=AffineProbeSolver(path)
            try:
                with self.assertRaises(ValueError):s.solve([[1],[-1]])
            finally:s.close()

    def test_exhaustive_two_variable_stream(self):
        s=self.make();clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];r=s.solve(source)
            self.assertEqual(r['answer'],truth_table(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))


if __name__=='__main__':unittest.main()
