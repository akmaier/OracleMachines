from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sqlite3,unittest
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_transported_partition import lift_names,prepare_support,native_query,run
from experiments.cnf_clause_partition import check_record,PartitionBank
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_support_plan import CausalPlan,SupportBudget

CORE=[[-20,-10],[-20,10],[-10,20],[10,20]]

class TransportedPartitionTests(unittest.TestCase):
    def make(self,path=':memory:',**kw):
        s=InputSafeAffineProbeSolver(path,**kw);self.addCleanup(s.close);return s
    def candidate(self,s,target):
        origin=native_query(s,CORE,256)['root'];cnf,names=normalize(target)
        return dict(origin=origin,origin_names=[10,20],target=[list(c) for c in cnf],target_names=names)
    def test_read_only_preparation_and_transport(self):
        s=self.make();c=self.candidate(s,[[-10],[10,20]])
        with patch.object(s,'_store',side_effect=AssertionError('Preparation publication')):
            plan,d=prepare_support(s,c)
        self.assertEqual(d['source'],CORE);self.assertEqual(len(d['missing']),3);self.assertEqual(d['outside'],[])
        self.assertGreater(plan.counts['support_nodes'],0)
    def test_later_sat_branch_lifts_to_external_ids(self):
        s=self.make();c=self.candidate(s,[[-10],[10,20]])
        r=run(s,c,'forward');self.assertEqual(r['status'],'sat');self.assertGreater(len(r['branches']),1)
        self.assertTrue(holds([[-10],[10,20]],r['result']['model']));check_record(s,r['partition'])
    def test_unsat_requires_every_branch(self):
        target=CORE+[[-40,-30],[-40,30],[-30,40],[30,40]]
        target=[c for c in target if c not in CORE[:3]]
        s=self.make();c=self.candidate(s,target);r=run(s,c,'forward')
        self.assertEqual(r['status'],'unsat');self.assertEqual(len(r['branches']),3);check_record(s,r['partition'])
        bad=deepcopy(r['partition']);bad['children'].pop()
        with self.assertRaises(ValueError):check_record(s,bad)
    def test_one_shared_budget_and_no_partial_verdict(self):
        s=self.make();c=self.candidate(s,[[-10],[10,20]]);budgets=[]
        def query(s,source,budget,screen=None):
            budgets.append(budget);s.counts.clear()
            if budget==0:raise RuntimeError(BUDGET_MESSAGE)
            n=2 if len(budgets)==1 else 1;s.counts['expanded_nodes']=n
            return dict(answer=False,model=None,root='unused',metrics=dict(s.counts))
        with patch('experiments.cnf_transported_partition.native_query',side_effect=query):r=run(s,c,'forward',3)
        self.assertEqual(budgets,[3,1,0]);self.assertEqual(r['expanded_nodes'],3)
        self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['partition']);self.assertIsNone(r['result'])
    def test_budget_costs_retained_and_native_fallback(self):
        s=self.make();c=self.candidate(s,[[-10],[10,20]])
        def stop(plan,key):plan.counts['support_nodes']+=1;raise SupportBudget('Injected')
        with patch.object(CausalPlan,'prepare',stop):r=run(s,c,'screen')
        self.assertEqual(r['route'],'fallback');self.assertEqual(r['plan_counts']['support_nodes'],1);self.assertEqual(r['status'],'sat')
    def test_terminal_gate_skips_candidate(self):
        s=self.make();cnf,names=normalize([[10],[-10]])
        c=dict(target=[list(c) for c in cnf],target_names=names,origin='absent',origin_names=[])
        r=run(s,c,'screen',0);self.assertEqual(r['route'],'terminal');self.assertEqual(r['status'],'unsat')
        self.assertEqual(r['expanded_nodes'],0);self.assertEqual(s.archive_storage()[0],1)
    def test_map_validation_and_missing_origin_fail_closed(self):
        for names in ([20,10],[10,10],[True,20],[10],[-10,20]):
            with self.assertRaises(ValueError):lift_names([[-2,1]],names)
        s=self.make();c=self.candidate(s,[[-10],[10,20]]);c['origin']='absent'
        with self.assertRaises(ValueError):run(s,c,'forward')
    def test_corrupted_plan_not_authority(self):
        s=self.make();c=self.candidate(s,[[-10],[10,20]])
        with patch.object(CausalPlan,'emit',return_value=None):
            # Existing full core is still valid, so instead corrupt the descriptor.
            real=prepare_support
            def corrupt(s,c,p):
                plan,d=real(s,c,p);d['root']='wrong';return plan,d
            with patch('experiments.cnf_transported_partition.prepare_support',side_effect=corrupt):
                with self.assertRaises(ValueError):run(s,c,'forward')
    def test_failed_batch_does_not_publish_or_poison_recovery(self):
        s=self.make()
        with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):native_query(s,[[10],[-10]],256)
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending)
        self.assertFalse(native_query(s,[[10],[-10]],256)['answer'])
    def test_native_iterators_and_invalid_budget(self):
        s=self.make();r=native_query(s,iter(iter(c) for c in [[10],[-10,20]]),256)
        self.assertTrue(r['answer']);self.assertTrue(holds([[10],[-10,20]],r['model']))
        for b in (-1,True,1.5):
            with self.assertRaises(ValueError):native_query(s,[],b)
            with self.assertRaises(ValueError):run(s,{},'screen',b)
    def test_partition_cold_replay_without_search(self):
        with TemporaryDirectory() as td:
            p=Path(td)/'db';s=InputSafeAffineProbeSolver(p)
            try:c=self.candidate(s,[[-10],[10,20]]);r=run(s,c,'reverse')
            finally:s.close()
            s=CanonicalVerifySnapshot(p)
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')):
                    bank=PartitionBank(s,[r['partition']]);got=bank.lookup([[-10],[10,20]])
                    self.assertTrue(got['answer']);self.assertTrue(holds([[-10],[10,20]],got['model']))
            finally:s.close()
    def test_exhaustive_subsets_of_binary_core(self):
        for mode in ('forward','reverse','screen'):
            for mask in range(16):
                target=[c for i,c in enumerate(CORE) if mask>>i&1]
                s=InputSafeAffineProbeSolver()
                try:
                    c=self.candidate(s,target);r=run(s,c,mode)
                    expected=any(holds(target,dict(zip((10,20),bits))) for bits in product((False,True),repeat=2))
                    self.assertEqual(r['result']['answer'],expected)
                    if expected:self.assertTrue(holds(target,r['result']['model']))
                    if r['partition'] is not None:check_record(s,r['partition'])
                finally:s.close()

if __name__=='__main__':unittest.main()
