from itertools import product
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import copy,json,random,unittest
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_cofactor_support import prepare
from experiments.cnf_deferred_support import discover,DeferredCoreBank
from experiments.cnf_incremental_support import extend,merge
from solver.test_cnf_cofactor_support import CORE,record

FIELDS=('cores','all_cores','origins','retained_indices','dominance')


class IncrementalSupportTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);return s
    def same(self,a,b):
        for f in FIELDS:self.assertEqual(a[f],b[f],f)
    def fixture(self,s):
        return [('old',[record(s,CORE,[3])])],[('new',[record(s,CORE+[[5,6]],[4]),record(s,[[1],[-1]],[3],1)])]
    def test_equal_to_complete_discovery_without_publication(self):
        s=self.make();old,new=self.fixture(s);prior=prepare(s,old);before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
        with patch.object(s,'_store',side_effect=AssertionError('Discovery publication')),patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            actual=extend(s,prior,old,new);expected=discover(s,old+new)
        self.same(actual,expected);self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
    def test_only_new_catalog_is_extracted(self):
        s=self.make();old,new=self.fixture(s);prior=prepare(s,old)
        with patch('experiments.cnf_incremental_support.discover',wraps=discover) as called:extend(s,prior,old,new)
        self.assertEqual(called.call_args.args[1],new)
    def test_duplicate_batches_reject_even_if_positive(self):
        s=self.make();old,new=self.fixture(s);prior=prepare(s,old)
        for duplicate in (old,new+new,[('old',[dict(case=0,answer=True,guard=None)])]):
            with self.assertRaisesRegex(ValueError,'Repeated source identity'):extend(s,prior,old,duplicate)
    def test_bad_old_provenance_and_dominance_reject(self):
        s=self.make();old,new=self.fixture(s);prior=prepare(s,old)
        for what in ('root','origin','dominance'):
            bad=copy.deepcopy(prior)
            if what=='root':bad['all_cores'][0]['root']='foreign'
            elif what=='origin':bad['origins'][0]['query_root']='foreign'
            else:bad['dominance'][0]['retained']=999
            with self.assertRaises((AssertionError,IndexError,ValueError)):extend(s,bad,old,new)
    def test_empty_delta_and_empty_start(self):
        s=self.make();old,new=self.fixture(s);prior=prepare(s,old)
        self.same(extend(s,prior,old,[]),prior)
        self.same(extend(s,prepare(s,[]),[],old+new),discover(s,old+new))
    def test_new_smaller_support_replaces_old_frontier_not_history(self):
        # Synthetic clause families exercise dominance, independent of proofs.
        a=[[1],[-1],[2]];b=[[1],[-1]]
        def bank(cs,name):
            cores=[dict(source=c,root=str(i),origin=str(i)) for i,c in enumerate(cs)]
            return dict(all_cores=cores,cores=cores,retained_indices=list(range(len(cs))),origins=[dict(catalog=name,case=i,core=i) for i in range(len(cs))],counts={},extraction_counts={})
        result=merge(bank([a],'old'),bank([b,a],'new'))
        self.assertEqual(len(result['all_cores']),2);self.assertEqual(result['retained_indices'],[1]);self.assertEqual(result['merge_counts']['duplicate_supports'],1)
        clauses=[(1,),(-1,),(2,)]
        for bits in product((False,True),repeat=3):
            source={c for c,keep in zip(clauses,bits) if keep}
            self.assertEqual(any(set(map(tuple,c))<=source for c in (a,b)),set(map(tuple,b))<=source)
    def test_random_small_batches_equal_full(self):
        rng=random.Random(2026111620);clauses=[list(x) for x in product(*[(-i,i) for i in (1,2,3)])]
        s=self.make();records=[]
        for i in range(24):
            source=CORE+[c for c in clauses if rng.choice((False,True))];records.append(record(s,source,[7+i],i))
        old=[('a',records[:12])];new=[('b',records[12:])];prior=prepare(s,old)
        self.same(extend(s,prior,old,new),discover(s,old+new))
    def test_persisted_delta_can_materialize_and_cold_replay(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);old,new=self.fixture(s);result=extend(s,prepare(s,old),old,new);s.close()
            result=json.loads(json.dumps(result));s=ResidualSolver(path)
            try:
                target=CORE+[[10,11],[11,12]]
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
                    self.assertIsNotNone(DeferredCoreBank(s,result['cores']).reuse(target));self.assertFalse(s.solve(target)['answer'])
            finally:s.close()
            cold=ResidualSolver(path)
            try:
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):self.assertFalse(cold.solve(target)['answer'])
            finally:cold.close()
    def test_pending_bank_extends_after_restart_without_reextracting(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path,leaves=False,decompose=False,matching=False,positive_subsumption=False)
            old=[('old',[record(s,[[21],[-21]],[22])])];prior=prepare(s,old)
            new=[('new',[record(s,CORE+[[9,10]],[3])])];pending=extend(s,prior,old,new);s.close()
            cold=ResidualSolver(path)
            try:
                with patch.object(cold,'_store',side_effect=AssertionError('Premature materialization')):
                    resumed=extend(cold,json.loads(json.dumps(pending)),old+new,[])
                self.assertGreater(resumed['prior_pending_roots'],0);self.same(resumed,pending)
            finally:cold.close()


if __name__=='__main__':unittest.main()
