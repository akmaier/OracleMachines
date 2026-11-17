from copy import deepcopy
from unittest.mock import patch
import unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_conditioned_core import project_core,check_record,acquire_core as narrow
from experiments.cnf_exposed_core import acquire_core


class ExposedCoreTests(unittest.TestCase):
    def solver(self):
        s=ResidualSolver();self.addCleanup(s.close);return s

    def projected(self,s,cnf,gate):
        parent=[list(c)+[gate] for c in cnf]+[[-gate]];core=dict(source=parent,root=s.solve(parent)['root']);return project_core(s,core,{gate:False})

    def test_unit_conflict_in_wide_cofactor_reuses_trace(self):
        s=self.solver();cnf=[[-6,-2],[-5],[-4,1,3],[-3,2,5],[-1],[1,6],[4,5]];r=self.projected(s,cnf,7)
        with self.assertRaises(ValueError):narrow(s,r)
        with patch.object(s,'_expand',side_effect=AssertionError('Repeated acquisition search')):child=acquire_core(s,r)
        self.assertFalse(child['answer']);self.assertEqual(child['metrics']['screen_trace_publications'],1);self.assertEqual(child['conditioning_screen_counts']['propagation_literal_visits'],23);check_record(s,r)

    def test_unit_prefix_reuses_known_two_cnf_residual(self):
        s=self.solver();cnf=[[1],[-1,2,3],[-1,-2,3],[-1,2,-3],[-1,-2,-3]];r=self.projected(s,cnf,4)
        with patch.object(s,'_expand',side_effect=AssertionError('Known residual search')):child=acquire_core(s,r)
        self.assertFalse(child['answer']);self.assertIsNone(child['conditioning_screen']['conflict']);self.assertEqual(child['metrics']['screen_trace_publications'],1);check_record(s,r)

    def test_wide_unexposed_residual_is_rejected(self):
        s=self.solver();source=[[10,20],[-10,20],[10,-20],[-10,-20],[30,40,50,60]];core=dict(source=source,root=s.solve(source)['root']);r=project_core(s,core,{30:False});before=s.archive_storage()
        with patch.object(s,'_expand',side_effect=AssertionError('Unbounded search')):
            with self.assertRaises(ValueError):acquire_core(s,r)
        self.assertEqual(s.archive_storage(),before)

    def test_bound_projection_and_warm_reuse(self):
        s=self.solver();r=self.projected(s,[[1],[-1]],2);acquire_core(s,r)
        with patch.object(s,'_store',side_effect=AssertionError('Repeated publication')),patch.object(s,'_expand',side_effect=AssertionError('Repeated search')):self.assertFalse(acquire_core(s,r)['answer'])
        bad=deepcopy(r);bad['source']=[[99]]
        with self.assertRaises(ValueError):acquire_core(s,bad)


if __name__=='__main__':unittest.main()
