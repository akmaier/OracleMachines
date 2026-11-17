from copy import deepcopy
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.cnf_retained_causal import load_causal,retained_bank
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_residual_dag import ResidualSolver
from experiments import cnf_causal_support


class RetainedCausalTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);source=[[-9],[1],[-1]];s.solve(source)
        core=CausalSupportExtractor(s,materialize=False).source_core(source)
        return s,dict(causal_unit_slicing=True,deferred=True,cores=[core])

    def save(self,value):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);p=Path(td.name)/'bank.json'
        p.write_text(json.dumps(value));return p,hashlib.sha256(p.read_bytes()).hexdigest()

    def test_load_preserves_all_saved_fields_without_discovery(self):
        _,value=self.make();value['history']={'origins':[2,5],'pending':True,'counts':{'support_nodes':123}}
        p,h=self.save(value)
        with patch.object(cnf_causal_support,'discover_causal',side_effect=AssertionError('Repeated discovery')):
            self.assertEqual(load_causal(p,h),value)

    def test_mutated_archive_rejects_before_parsing(self):
        _,value=self.make();p,h=self.save(value);p.write_text(p.read_text()+' ')
        with self.assertRaises(ValueError):load_causal(p,h)

    def test_wrong_policy_rejects_even_with_matching_fingerprint(self):
        s,value=self.make()
        for key in ('causal_unit_slicing','deferred'):
            for wrong in (None,False,1,'true'):
                bad=deepcopy(value);bad[key]=wrong;p,h=self.save(bad)
                with self.assertRaises(ValueError):load_causal(p,h)
                with self.assertRaises(ValueError):retained_bank(s,bad)

    def test_pending_core_uses_causal_materializer_and_cold_proof(self):
        s,value=self.make();core=value['cores'][0];self.assertIsNone(s._read(core['root']))
        p,h=self.save(value);loaded=load_causal(p,h);bank=retained_bank(s,loaded);query=[[-1],[1],[3,5]]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh materialization solving')):
            hit=bank.reuse(query);self.assertIsNotNone(hit);self.assertFalse(s.solve(query)['answer'])
            self.assertFalse(s._read(core['root'])['answer'])
            for key, in s.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(s._read(key))
        self.assertEqual(loaded,value);self.assertGreater(bank.counts['materialization_nodes'],0)

    def test_ready_proof_skips_extraction_but_remains_checked(self):
        s,value=self.make();core=value['cores'][0];CausalSupportExtractor(s).extract(core['origin']);bank=retained_bank(s,value)
        with patch.object(bank.extractor,'extract',side_effect=AssertionError('Repeated derivation')):
            self.assertIsNotNone(bank.reuse([[-1],[1],[4,6]]))
        self.assertEqual(bank.counts['existing_core_proofs'],1)

    def test_malformed_matched_hint_cannot_publish(self):
        s,value=self.make();value['cores'][0]['root']='wrong';bank=retained_bank(s,value);before=s.archive_storage()
        with self.assertRaises(ValueError):bank.reuse([[-1],[1],[2,3]])
        self.assertEqual(s.archive_storage(),before)


if __name__=='__main__':unittest.main()
