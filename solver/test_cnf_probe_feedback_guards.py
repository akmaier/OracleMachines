from collections import Counter
from copy import deepcopy
import random,unittest
from experiments import cnf_probe_feedback as feedback
from experiments import cnf_complement_probes as probes
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import transport
from solver.test_cnf_wide_guard_probes import fixture


class ProbeFeedbackGuardTests(unittest.TestCase):
    def test_signed_guarded_seed_prefixes_compile_with_both_representations(self):
        source,ts=fixture();rng=random.Random(242509)
        for _ in range(12):
            names=list(range(1,8));rng.shuffle(names);mapping={v:n*rng.choice((-1,1)) for v,n in enumerate(names,1)}
            changed=native.normalize([[mapping[abs(l)]*(1 if l>0 else -1) for l in cl] for cl in source])[0]
            templates=[transport(t,mapping) for t in ts];complete=probes.discover(changed,templates,Counter())
            self.assertEqual(complete['reason'],'opposite_probes')
            # A valid saved prefix ending after just one of the two failures.
            seed=dict(complete,status='unresolved',reason='probe_limit',terminal=None,
                      probes=[deepcopy(complete['probes'][complete['terminal']['low']])])
            p=feedback.discover(changed,templates,seed,Counter());self.assertEqual(p['status'],'refuted')
            for selected in (False,True):
                s=native.ResidualSolver()
                try:self.assertFalse(s._read(feedback.compile_program(s,changed,templates,seed,p,Counter(),select_support=selected))['answer'])
                finally:s.close()


if __name__=='__main__':unittest.main()
