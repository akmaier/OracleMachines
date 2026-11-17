from copy import deepcopy
from unittest.mock import patch
import unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_deferred_support import SupportIndexExtractor
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_proof_choice import ProofChoiceBank,compose,audit_portfolio


class ProofChoiceTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);return s

    def frontier(self,cores,causal=False):
        return dict(cores=cores,all_cores=cores,origins=[],causal_unit_slicing=causal,deferred=True)

    def core(self,s,f):
        r=s.solve(f);return dict(source=f,root=r['root'],origin=r['root'])

    def test_ready_causal_wins_over_pending_legacy(self):
        s=self.make();f=[[-9],[1],[-1],[7,8]];s.solve(f)
        pending=SupportIndexExtractor(s).source_core(f)
        ready=self.core(s,[[2,3],[2,-3],[-2,3],[-2,-3]]);b=ProofChoiceBank(s,self.frontier([pending]),self.frontier([ready],True))
        self.assertIsNone(s._read(pending['root']))
        with patch.object(b.banks[0].extractor,'extract',side_effect=AssertionError('Unused pending derivation')):
            h=b.reuse(pending['source']+ready['source']+[[5,6]])
        self.assertEqual((h['bank'],h['choice']),('causal','ready'));self.assertEqual(b.counts['materialization_nodes'],0)

    def test_later_ready_legacy_wins_over_earlier_pending(self):
        s=self.make();f=[[-9],[1],[-1],[7,8]];s.solve(f);pending=SupportIndexExtractor(s).source_core(f)
        ready=self.core(s,[[2,3],[2,-3],[-2,3],[-2,-3]]);b=ProofChoiceBank(s,self.frontier([pending,ready]),self.frontier([],True))
        self.assertIsNone(s._read(pending['root']))
        h=b.reuse(pending['source']+ready['source']+[[5,6]]);self.assertEqual((h['bank'],h['local_core'],h['choice']),('legacy',1,'ready'))

    def test_causal_only_pending_uses_causal_materializer(self):
        s=self.make();f=[[-9],[1],[-1]];s.solve(f);pending=CausalSupportExtractor(s,materialize=False).source_core(f)
        b=ProofChoiceBank(s,self.frontier([]),self.frontier([pending],True));q=[[1],[-1],[3,4]]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            h=b.reuse(q);self.assertEqual((h['bank'],h['choice']),('causal','materialized'));self.assertFalse(s.solve(q)['answer'])
        self.assertGreater(b.counts['materialization_nodes'],0)

    def test_pending_legacy_keeps_original_derivation(self):
        s=self.make();source=[[-9],[1],[-1],[7,8]];s.solve(source);core=SupportIndexExtractor(s).source_core(source)
        self.assertIsNone(s._read(core['root']));b=ProofChoiceBank(s,self.frontier([core]),self.frontier([],True))
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):h=b.reuse(core['source']+[[6,7]])
        self.assertEqual((h['bank'],h['choice']),('legacy','materialized'));self.assertFalse(s._read(h['root'])['answer'])

    def test_no_containment_is_a_miss_and_publishes_nothing(self):
        s=self.make();core=self.core(s,[[1],[-1]]);b=ProofChoiceBank(s,self.frontier([core]),self.frontier([],True));before=s.archive_storage()
        self.assertIsNone(b.reuse([[1],[2]]));self.assertEqual(s.archive_storage(),before)

    def test_forged_root_and_positive_core_reject(self):
        s=self.make();core=self.core(s,[[1],[-1]]);bad=deepcopy(core);bad['root']='wrong'
        b=ProofChoiceBank(s,self.frontier([bad]),self.frontier([],True))
        with self.assertRaises(ValueError):b.reuse([[1],[-1],[2]])
        positive=self.core(s,[[1]]);b=ProofChoiceBank(s,self.frontier([positive]),self.frontier([],True))
        with self.assertRaises(ValueError):b.reuse([[1],[2]])

    def test_materializer_policy_rejects_wrong_causal_index(self):
        s=self.make()
        with self.assertRaises(ValueError):ProofChoiceBank(s,self.frontier([]),self.frontier([]))

    def test_composition_keeps_stable_bank_references(self):
        s=self.make();core=self.core(s,[[1],[-1]]);indices=dict(legacy=self.frontier([core]),causal=self.frontier([core],True))
        bindings={n:dict(path=n,sha256=n) for n in indices};result=compose(indices,bindings)
        self.assertEqual(result['cores'],[core,core]);self.assertEqual(result['all_cores'],[dict(bank='legacy',index=0),dict(bank='causal',index=0)])
        self.assertEqual(compose(dict(reversed(list(indices.items()))),bindings),result)
        with self.assertRaises(ValueError):compose(indices,{'legacy':bindings['legacy']})

    def test_both_lineages_checked_in_complete_unchanged_snapshot(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from experiments.cnf_deferred_support import discover
        from experiments.cnf_causal_support import discover_causal
        from solver.test_cnf_cofactor_support import CORE,record
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:
                r=record(s,CORE,[3]);catalogs=[('old',[r])]
                indices=dict(legacy=discover(s,catalogs),causal=discover_causal(s,catalogs))
            finally:s.close()
            prepared=compose(indices,{n:dict(path=n,sha256=n) for n in indices});before=path.read_bytes()
            result=audit_portfolio(path,[r],prepared,catalogs,indices)
            for n in indices:self.assertEqual(result['lineage'][n]['prior_sources_checked'],1)
            self.assertEqual(result['snapshot']['censuses'],1);self.assertEqual(before,path.read_bytes())
            bad=deepcopy(indices);bad['causal']['origins'][0]['query_root']='foreign'
            with self.assertRaises(ValueError):audit_portfolio(path,[r],prepared,catalogs,bad)
            self.assertEqual(before,path.read_bytes())

    def test_changed_composite_rejects_before_audit(self):
        indices=dict(legacy=self.frontier([]),causal=self.frontier([],True));prepared=compose(indices,{n:{} for n in indices})
        prepared['all_cores']=[dict(bank='legacy',index=0)]
        with self.assertRaises(ValueError):audit_portfolio('not opened',[],prepared,[],indices)


if __name__=='__main__':unittest.main()
