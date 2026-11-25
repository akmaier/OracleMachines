"""Keep the observed one-pass limitation and signed guard transport explicit."""
from collections import Counter
import random,unittest
from experiments import cnf_wide_guard_probes as probes
from experiments import cnf_shortening_prepared_source as binary
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import transport
from solver.test_cnf_guard_shortening import chain
from solver.test_cnf_wide_guard_probes import fixture


class WideGuardScopeTests(unittest.TestCase):
    def test_one_pass_does_not_chain_learned_exclusions(self):
        source,ts=chain(4,8);prefix=binary.discover(source,ts,Counter(),round_limit=1)
        _,state=probes.bind_prefix(source,ts,prefix,Counter());templates=[h['template'] for h in state['hints']]
        program=probes.discover(state['local'],templates,Counter())
        self.assertEqual(program['status'],'unresolved')
        self.assertEqual(program['reason'],'complete')
        self.assertGreater(len(program['probes']),0)
        probes.validate(state['local'],templates,program,Counter())

    def test_signed_renamings_keep_guards_source_bound(self):
        rng=random.Random(242504);source,ts=fixture()
        for _ in range(12):
            names=list(range(1,8));rng.shuffle(names);mapping={v:n*rng.choice((-1,1)) for v,n in enumerate(names,1)}
            changed=native.normalize([[mapping[abs(l)]*(1 if l>0 else -1) for l in cl] for cl in source])[0]
            templates=[transport(t,mapping) for t in ts];p=probes.discover(changed,templates,Counter());self.assertEqual(p['status'],'refuted')
            s=native.ResidualSolver()
            try:self.assertFalse(s._read(probes.compile_program(s,changed,templates,p,Counter()))['answer'])
            finally:s.close()


if __name__=='__main__':unittest.main()
