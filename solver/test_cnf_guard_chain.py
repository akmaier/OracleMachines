from copy import deepcopy
from itertools import product
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_clause_deletion_guard import FORMAT,check_guard
from experiments.cnf_guard_chain import propose_missing_clause,publish_guard,make_record,check_record,GuardChainBank


class GuardChainTests(unittest.TestCase):
    def fixture(self,s,negative=False):
        source=[[1],[2],[3,4]]+([[-5],[5]] if negative else [])
        stronger=source+[[-1]];root=s.solve(stronger)['root']
        first=dict(format=FORMAT,stronger=stronger,stronger_root=root,removed_clause=[-1])
        _,target=check_guard(s,source,first);core=[[2],[-2]];r=s.solve(core)
        hint=dict(source=core,root=r['root'],origin=r['root'])
        choice=propose_missing_clause(s,target,[hint]);self.assertEqual(choice,dict(core=0,missing_clause=[-2]))
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh premise search')):
            second,_,child_source,_=publish_guard(s,target,hint,choice['missing_clause'])
        child=s.solve(child_source);record=make_record(s,source,[first,second],child)
        return source,record

    def test_sat_chain_lifts_all_levels_and_normalized_reuse(self):
        s=ResidualSolver();self.addCleanup(s.close);source,r=self.fixture(s)
        self.assertIsNone(s._read(r['query_root']))
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh lookup')),patch.object(s,'_store',side_effect=AssertionError('Lookup publication')):
            bank=GuardChainBank(s,[json.loads(json.dumps(r))]);got=bank.lookup(source)
            self.assertTrue(got['answer']);self.assertTrue(holds(source,got['model']))
            renamed=[[10*l for l in c] for c in source];got=bank.lookup(renamed)
            self.assertTrue(holds(renamed,got['model']));self.assertIsNone(bank.lookup([[1],[2],[3]]))

    def test_negative_chain_and_cold_reconstruction(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:source,r=self.fixture(s,True)
            finally:s.close()
            cold=ResidualSolver(path)
            try:
                cold.db.execute('PRAGMA query_only=ON')
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):
                    self.assertIsNone(cold._read(r['query_root']))
                    for key, in cold.db.execute('SELECT id FROM cnf_residual_v1'):cold._read(key)
                    self.assertFalse(check_record(cold,r)['answer']);self.assertFalse(GuardChainBank(cold,[r]).lookup(source)['answer'])
            finally:cold.close()

    def test_child_and_conclusion_tampering_rejects(self):
        s=ResidualSolver();self.addCleanup(s.close);_,r=self.fixture(s)
        for field in ('query_root','answer','model','child','guards'):
            bad=deepcopy(r)
            if field=='query_root':bad[field]='wrong'
            elif field=='answer':bad[field]=False
            elif field=='model':bad[field]['1' if '1' in bad[field] else 1]=False
            elif field=='child':bad[field]['root']='wrong'
            else:bad[field].reverse()
            with self.subTest(field=field),self.assertRaises(ValueError):check_record(s,bad)

    def test_missing_child_never_triggers_solving(self):
        s=ResidualSolver();self.addCleanup(s.close);_,r=self.fixture(s)
        s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(r['child']['root'],));s.db.commit();s.checked.clear()
        with patch.object(s,'_expand',side_effect=AssertionError('Unexpected solving')),self.assertRaises(ValueError):check_record(s,r)

    def test_pending_positive_and_malformed_near_cores(self):
        s=ResidualSolver();self.addCleanup(s.close);source=[[1],[2,3]]
        pending=dict(source=[[1],[-1]],root=s._canonical([[1],[-1]])[2])
        self.assertIsNone(propose_missing_clause(s,source,[pending]))
        positive=[[1],[2]];hint=dict(source=positive,root=s.solve(positive)['root'])
        with self.assertRaises(ValueError):propose_missing_clause(s,source,[hint])
        with self.assertRaises(ValueError):publish_guard(s,source,pending,[-2])
        bad=dict(pending,root='foreign')
        with self.assertRaises(ValueError):publish_guard(s,source,bad,[-1])

    def test_sat_near_core_does_not_certify_unsat(self):
        s=ResidualSolver();self.addCleanup(s.close);source=[[1],[2,3]];core=[[1],[-1]]
        hint=dict(source=core,root=s.solve(core)['root'])
        choice=propose_missing_clause(s,source,[hint]);guard,_,target,_=publish_guard(s,source,hint,choice['missing_clause'])
        result=s.solve(target);self.assertTrue(result['answer'])
        r=make_record(s,source,[guard],result);self.assertTrue(check_record(s,r)['answer'])

    def test_two_variable_compositions_against_truth_tables(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(bits) if sign) for bits in product((-1,0,1),repeat=2)]
        models=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        positives=negatives=0
        for mask in range(1,512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];variables={abs(l) for c in source for l in c}
            expected=any(holds(source,a) for a in models)
            for clause in clauses:
                if not clause or clause in source or not {abs(l) for l in clause}<=variables:continue
                core=source+[clause]
                if any(holds(core,a) for a in models):continue
                s=ResidualSolver()
                try:
                    hint=dict(source=core,root=s.solve(core)['root'])
                    guard,_,target,_=publish_guard(s,source,hint,clause)
                    record=make_record(s,source,[guard],s.solve(target))
                    with patch.object(s,'_expand',side_effect=AssertionError('Fresh exhaustive replay')):
                        actual=check_record(s,record)
                    self.assertEqual(actual['answer'],expected)
                    if expected:self.assertTrue(holds(source,actual['model']));positives+=1
                    else:negatives+=1
                finally:s.close()
        self.assertGreater(positives,0);self.assertGreater(negatives,0)


if __name__=='__main__':unittest.main()
