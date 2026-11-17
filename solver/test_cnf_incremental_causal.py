from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,random,unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_causal_support import discover_causal
from experiments.cnf_incremental_causal import extend_causal,audit_extended_portfolio
from experiments.cnf_proof_choice import ProofChoiceBank,compose
from experiments.cnf_deferred_support import discover
from solver.test_cnf_cofactor_support import CORE,record

FIELDS=('cores','all_cores','origins','retained_indices','dominance')


class IncrementalCausalTests(unittest.TestCase):
    def make(self,**kwargs):
        s=ResidualSolver(**kwargs);self.addCleanup(s.close);return s
    def same(self,a,b):
        for f in FIELDS:self.assertEqual(a[f],b[f],f)
    def fixture(self,s):
        old=[('old',[record(s,CORE+[[9,10]],[3])])]
        new=[('new',[record(s,CORE+[[11,12]],[4]),record(s,[[-19],[1],[-1]],[7],1)])]
        return old,new
    def test_matches_full_discovery_without_search_or_publication(self):
        s=self.make();old,new=self.fixture(s);prior=discover_causal(s,old);before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'));saved=deepcopy(prior)
        with patch.object(s,'_store',side_effect=AssertionError('Publication')),patch.object(s,'_expand',side_effect=AssertionError('Search')):
            merged=extend_causal(s,prior,old,new);full=discover_causal(s,old+new)
        self.same(merged,full);self.assertEqual(prior,saved);self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
        self.assertEqual(merged['delta_origin_count'],2);self.assertTrue(merged['causal_unit_slicing'])
    def test_only_new_origins_enter_extractor(self):
        s=self.make();old,new=self.fixture(s);prior=discover_causal(s,old)
        with patch('experiments.cnf_incremental_causal.discover_causal',wraps=discover_causal) as called:extend_causal(s,prior,old,new)
        self.assertEqual(called.call_args.args[1],new)
    def test_duplicate_ids_and_unbound_old_catalog_reject(self):
        s=self.make();old,new=self.fixture(s);prior=discover_causal(s,old)
        for duplicate in (old,new+new,[('old',[dict(case=0,answer=True,guard=None)])]):
            with self.assertRaisesRegex(ValueError,'Repeated'):extend_causal(s,prior,old,duplicate)
        with self.assertRaisesRegex(ValueError,'Old catalog'):extend_causal(s,prior,[],new)
    def test_wrong_policy_and_tampered_new_origin_reject(self):
        s=self.make();old,new=self.fixture(s);prior=discover_causal(s,old);bad=deepcopy(prior);bad['causal_unit_slicing']=False
        with self.assertRaises(ValueError):extend_causal(s,bad,old,new)
        bad=deepcopy(new);bad[0][1][0]['child']['root']='foreign'
        with self.assertRaises(ValueError):extend_causal(s,prior,old,bad)
    def test_empty_delta_empty_start_and_chained_batches(self):
        s=self.make();old,new=self.fixture(s);prior=discover_causal(s,old)
        self.same(extend_causal(s,prior,old,[]),prior)
        result=extend_causal(s,discover_causal(s,[]),[],old);result=extend_causal(s,result,old,new)
        self.same(result,discover_causal(s,old+new))
    def test_random_mixtures_equal_full_and_keep_match_coverage(self):
        s=self.make();rng=random.Random(2026111702);clauses=[list(x) for x in product(*[(-i,i) for i in (1,2,3)])]
        rs=[record(s,CORE+[[-20-i]]+[c for c in clauses if rng.choice((False,True))],[40+i],i) for i in range(16)]
        old=[('a',rs[:8])];new=[('b',rs[8:])];prior=discover_causal(s,old);merged=extend_causal(s,prior,old,new)
        self.same(merged,discover_causal(s,old+new))
        for core in prior['cores']:self.assertTrue(any(set(map(tuple,c['source']))<=set(map(tuple,core['source'])) for c in merged['cores']))
    def test_pending_extension_restarts_and_materializes_without_search(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path,leaves=False,decompose=False,matching=False,positive_subsumption=False)
            try:
                old=[('old',[record(s,CORE+[[9,10]],[3])])];new=[('new',[record(s,[[-19],[1],[-1]],[7])])]
                prior=discover_causal(s,old);extended=extend_causal(s,prior,old,new)
            finally:s.close()
            cold=ResidualSolver(path)
            try:
                extended=json.loads(json.dumps(extended));target=[[1],[-1],[11,12]]
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh search')):
                    bank=ProofChoiceBank(cold,dict(cores=[]),extended);self.assertIsNotNone(bank.reuse(target));self.assertFalse(cold.solve(target)['answer'])
            finally:cold.close()
    def test_both_distinct_lineages_audited_and_bad_unused_origin_rejects(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:
                old,new=self.fixture(s);indices=dict(legacy=discover(s,old),causal=extend_causal(s,discover_causal(s,old),old,new))
            finally:s.close()
            binding={n:dict(path=n,sha256=n) for n in indices};prepared=compose(indices,binding);before=path.read_bytes();catalogs=dict(legacy=old,causal=old+new)
            result=audit_extended_portfolio(path,old[0][1]+new[0][1],prepared,catalogs,indices)
            self.assertEqual(result['lineage']['legacy']['prior_sources_checked'],1);self.assertEqual(result['lineage']['causal']['prior_sources_checked'],3)
            self.assertEqual(result['snapshot']['censuses'],1);self.assertEqual(before,path.read_bytes())
            bad=deepcopy(indices);bad['causal']['origins'][-1]['query_root']='foreign'
            with self.assertRaises(ValueError):audit_extended_portfolio(path,[],prepared,catalogs,bad)


if __name__=='__main__':unittest.main()
