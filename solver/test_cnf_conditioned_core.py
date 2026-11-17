from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_conditioned_core import project_core,acquire_core,check_record,assignment


class ConditionedCoreTests(unittest.TestCase):
    def solver(self):
        s=ResidualSolver();self.addCleanup(s.close);return s

    def test_acquisition_is_checked_and_persists(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            try:
                source=[[10],[-10]];core=dict(source=source,root=s.solve(source)['root']);r=project_core(s,core,{10:True});before=s.archive_storage()[0]
                with self.assertRaises(ValueError):check_record(s,r)
                child=acquire_core(s,r);self.assertFalse(child['answer']);self.assertEqual(s.archive_storage()[0],before+1);check_record(s,r)
            finally:s.close()
            s=ResidualSolver(path)
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('Repeated acquisition')),patch.object(s,'_store',side_effect=AssertionError('Repeated publication')):
                    self.assertFalse(acquire_core(s,r)['answer']);check_record(s,r)
            finally:s.close()

    def test_parent_and_assignment_tampering(self):
        s=self.solver();source=[[10],[-10]];core=dict(source=source,root=s.solve(source)['root']);r=project_core(s,core,{10:True});acquire_core(s,r)
        for field,value in [('parent_root','bad'),('root','bad'),('source',[[20]]),('assignment',[[10,1]]),('parent_source',[[10]])]:
            bad=deepcopy(r);bad[field]=value
            with self.assertRaises(ValueError):check_record(s,bad)
        for value in ([[0,True]],[[1,True],[1,False]],[[True,False]],{'1':True}):
            with self.assertRaises(ValueError):assignment(value)

    def test_pending_and_positive_parents_cannot_supply_cores(self):
        s=self.solver()
        for source,ready in (([[1],[-1]],False),([[1]],True)):
            root=s.solve(source)['root'] if ready else s._canonical(source)[2]
            with self.assertRaises(ValueError):project_core(s,dict(source=source,root=root),{})

    def test_missing_wide_cofactor_does_not_trigger_search(self):
        s=self.solver();source=[[10,20],[-10,20],[10,-20],[-10,-20],[30,40,50,60]];core=dict(source=source,root=s.solve(source)['root']);r=project_core(s,core,{30:False});before=s.archive_storage()
        with patch.object(s,'_expand',side_effect=AssertionError('Unbounded acquisition')):
            with self.assertRaises(ValueError):acquire_core(s,r)
        self.assertEqual(s.archive_storage(),before)

    def test_projection_binds_raw_coordinates(self):
        s=self.solver();source=[[10],[-10],[20,30]];core=dict(source=source,root=s.solve(source)['root']);r=project_core(s,core,{30:False});acquire_core(s,r);check_record(s,r)
        bad=deepcopy(r);bad['source']=[[1],[-1],[2]]
        self.assertEqual(s._canonical(bad['source'])[2],r['root'])
        with self.assertRaises(ValueError):check_record(s,bad)

    def test_exhaustive_negative_two_variable_restrictions(self):
        clauses=[[i*sign for i,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            if any(holds(source,dict(zip((1,2),values))) for values in product((False,True),repeat=2)):continue
            s=ResidualSolver()
            try:
                core=dict(source=source,root=s.solve(source)['root'])
                for values in product((None,False,True),repeat=2):
                    fixed={i:v for i,v in enumerate(values,1) if v is not None};r=project_core(s,core,fixed,Counter());self.assertFalse(acquire_core(s,r)['answer']);check_record(s,r)
            finally:s.close()


if __name__=='__main__':unittest.main()
