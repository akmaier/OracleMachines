"""A fixed root budget makes complement scheduling non-monotone."""
from collections import Counter
import unittest
from experiments import cnf_complement_probes as paired
from experiments import cnf_wide_guard_probes as frozen
from experiments import cnf_residual_dag as native


class ComplementProbeScopeTests(unittest.TestCase):
    def test_open_promoted_branch_can_displace_a_decisive_probe(self):
        # The failed -10 probe promotes an open 10 probe. Both signs of 9 refute.
        # Wider clauses rank -10 first, followed by -9 and 9. Promoting 10
        # spends the third-probe opportunity, so this is a real budget loss.
        source=native.normalize([(10,1),(10,-1),(-9,2),(-9,-2),
                                 (9,3),(9,-3),(-10,9,11),(-10,-9,12)])[0]
        a=frozen.discover(source,[],Counter(),probe_limit=3)
        c=Counter();b=paired.discover(source,[],c,probe_limit=3)
        self.assertEqual(a['status'],'refuted')
        self.assertEqual((b['status'],b['reason']),('unresolved','probe_limit'))
        self.assertEqual(c['probe_roots'],3);self.assertEqual(c['complement_open_opposites'],1)
        frozen.validate(source,[],a,Counter());paired.validate(source,[],b,Counter())
        later=paired.discover(source,[],Counter(),probe_limit=4)
        self.assertEqual(later['status'],'refuted');paired.validate(source,[],later,Counter())


if __name__=='__main__':unittest.main()
