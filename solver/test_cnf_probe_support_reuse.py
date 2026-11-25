from collections import Counter
from pathlib import Path
import tempfile,unittest
from experiments import cnf_probe_support as support
from experiments import cnf_complement_probes as probes
from experiments import cnf_residual_dag as native
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_wide_guard_probes import fixture


class ProbeSupportReuseTests(unittest.TestCase):
    def test_growing_supersets_add_only_a_wrapper_after_cold_reopen(self):
        base,ts=fixture()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';prior={};roots=[];child=None
            for size in (1,4,16):
                source=native.normalize(list(base)+[(8+i,9+i) for i in range(size)])[0]
                program=probes.discover(source,ts,Counter());s=native.ResidualSolver(path)
                try:
                    c=Counter();root=support.compile_program(s,source,ts,program,c);node=s._read(root)
                    self.assertFalse(node['answer']);self.assertEqual(node['proof']['kind'],'component')
                    current=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                    self.assertTrue(all(current[k]==v for k,v in prior.items()))
                    if child is not None:
                        self.assertEqual(node['proof']['child'],child)
                        self.assertEqual(set(current)-set(prior),{root})
                        self.assertEqual(c['probe_native_root_hits'],1)
                    child=node['proof']['child'];prior=current;roots.append(root)
                finally:s.close()
            r=CanonicalVerifySnapshot(path)
            try:
                for root in roots:self.assertFalse(r._read(root)['answer'])
            finally:r.close()


if __name__=='__main__':unittest.main()
