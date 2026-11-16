from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json,unittest
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_unsat_support import SupportExtractor
from experiments.cnf_cofactor_support import prepare
from experiments.cnf_deferred_support import SupportIndexExtractor,DeferredCoreBank,discover
from solver.test_cnf_cofactor_support import CORE,record


def rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))


class DeferredSupportTests(unittest.TestCase):
    def make(self,**kwargs):
        s=ResidualSolver(**kwargs);self.addCleanup(s.close);return s
    def fixture(self,s):return record(s,CORE+[[9,10]],[3])
    def test_exhaustive_small_support_indices_equal_eager(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2)]
        assignments=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            if any(holds(source,a) for a in assignments):continue
            s=ResidualSolver()
            try:
                key=s.solve(source)['root'];before=rows(s)
                with patch.object(s,'_store',side_effect=AssertionError('Discovery publication')):proposal=SupportIndexExtractor(s).extract(key)
                self.assertEqual(rows(s),before)
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):actual=SupportExtractor(s).extract(key)
                self.assertEqual(proposal,actual)
            finally:s.close()
    def test_split_unit_hall_component_and_reduction_indices(self):
        full=[list(c) for c in product(*[(-i,i) for i in (1,2,3)])]
        hall=[[3*i+1,3*i+2,3*i+3] for i in range(4)]+[[-(3*i+h),-(3*j+h)] for h in (1,2,3) for i in range(4) for j in range(i+1,4)]
        cases=[(full+[[9],[9,10]],dict(leaves=False,decompose=False,matching=False,positive_subsumption=False)),
               (CORE,{}),(full+[[4,5,6]],{}),(hall+[[1,2,3,13]],{}),(hall,{})]
        kinds=set()
        for source,opts in cases:
            s=self.make(**opts);key=s.solve(source)['root'];e=SupportIndexExtractor(s);before=rows(s)
            with patch.object(s,'_store',side_effect=AssertionError('Discovery publication')):proposed=e.extract(key)
            self.assertEqual(rows(s),before);self.assertEqual(proposed,SupportExtractor(s).extract(key))
            kinds.update(k.removeprefix('support_kind_') for k in e.counts if k.startswith('support_kind_'))
        self.assertTrue({'units','split','implications','hall-v1','component','positive-subsumption-v1'}<=kinds)
    def test_discovery_and_miss_do_not_publish(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False);r=self.fixture(s);before=rows(s)
        with patch.object(s,'_store',side_effect=AssertionError('Premature publication')),patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            data=discover(s,[('old',[r])]);bank=DeferredCoreBank(s,data['cores']);self.assertIsNone(bank.reuse([[42]]))
        self.assertEqual(rows(s),before);self.assertNotIn(data['cores'][0]['root'],before)
    def test_match_materializes_and_repeated_match_reuses(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False);r=self.fixture(s);data=discover(s,[('old',[r])]);bank=DeferredCoreBank(s,data['cores'])
        source=data['cores'][0]['source']+[[11,12],[12,13]]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            hit=bank.reuse(source);self.assertTrue(hit['inserted']);self.assertFalse(s.solve(source)['answer']);before=rows(s)
            self.assertFalse(bank.reuse(source)['inserted']);self.assertEqual(rows(s),before)
        self.assertEqual(bank.counts['materialization_attempts'],1);self.assertGreater(bank.counts['materialization_nodes'],0)
    def test_proposal_cannot_refute_satisfiable_target(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False);r=self.fixture(s);data=discover(s,[('old',[r])]);bad=copy.deepcopy(data['cores'])
        bad[0]['source']=[[99]];bad[0]['root']=s._canonical([[99]])[2];bank=DeferredCoreBank(s,bad)
        with self.assertRaisesRegex(ValueError,'Proposal differs'):bank.reuse([[99],[100]])
        self.assertTrue(s.solve([[99],[100]])['answer'])
    def test_missing_positive_and_unbound_origins_reject(self):
        s=self.make();r=self.fixture(s);data=discover(s,[('old',[r])])
        for value in ('missing',s.solve([[31]])['root']):
            bad=copy.deepcopy(data['cores']);bad[0]['origin']=value
            with self.assertRaises(ValueError):DeferredCoreBank(s,bad)
        bad=copy.deepcopy(data['cores']);bad[0]['root']='foreign'
        with self.assertRaises(ValueError):DeferredCoreBank(s,bad)
    def test_provenance_and_antichain_equal_eager(self):
        s=self.make();records=[self.fixture(s),record(s,[[1],[-1]],[3],1)];data=discover(s,[('old',records)]);eager=prepare(s,[('old',records)])
        for field in ('cores','all_cores','origins','dominance','retained_indices'):self.assertEqual(data[field],eager[field])
    def test_pending_proposals_and_materialized_proofs_survive_reopen(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path,leaves=False,decompose=False,matching=False,positive_subsumption=False)
            data=discover(s,[('old',[self.fixture(s)])]);s.close();data=json.loads(json.dumps(data));s=ResidualSolver(path)
            try:
                self.assertIsNone(s._read(data['cores'][0]['root']));source=data['cores'][0]['source']+[[13,14],[14,15]]
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh resumed search')):DeferredCoreBank(s,data['cores']).reuse(source)
            finally:s.close()
            cold=ResidualSolver(path)
            try:
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):
                    for key in rows(cold):cold._read(key)
                    self.assertFalse(cold.solve(source)['answer'])
            finally:cold.close()


if __name__=='__main__':unittest.main()
