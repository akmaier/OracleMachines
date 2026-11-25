"""Budget expansion preserves checked discoveries, not total-cost guarantees."""
from collections import Counter
from itertools import product
import random,unittest
from experiments import cnf_shortening_prepared_source as detector
from experiments import cnf_residual_dag as native
from solver.test_cnf_guard_shortening import chain


class ShorteningBudgetFrontierTests(unittest.TestCase):
    def compare(self,source,templates,budgets=(1,2,4,8,64,96,128,256)):
        before=None
        for roots in budgets:
            c=Counter();p=detector.discover(source,templates,c,root_limit=roots,filters='endpoint')
            self.assertLessEqual(c['reach_roots'],roots)
            self.assertLessEqual(c['reach_edge_visits']+c['reuse_invalidation_checks']+c['cache_admission_edge_checks'],16384)
            self.assertLessEqual(c['rounds'],33);self.assertLessEqual(c['cache_peak_vertices'],16384)
            if before:
                self.assertEqual(before['steps'],p['steps'][:len(before['steps'])])
                if before['reason']!='root_limit':self.assertEqual(before,p)
            if p['status']=='refuted':detector.validate(source,templates,p,Counter())
            before=p
        return before

    def test_conditioned_chains_preserve_completed_programs(self):
        for depth in (1,4,8,16):
            for padding in (0,8,64):
                p=self.compare(*chain(depth,padding))
                self.assertEqual(p['status'],'refuted')

    def test_random_unlabelled_formulas_and_truth(self):
        rng=random.Random(242501)
        for _ in range(180):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,7),rng.randrange(2,5))] for _ in range(rng.randrange(4,25))])[0]
            p=self.compare(source,[])
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=6)]
            models=[m for m in models if native.holds(source,m)]
            for step in p['steps']:self.assertTrue(all(m[abs(step['forced'])]==(step['forced']>0) for m in models))
            if p['status']=='refuted':self.assertFalse(models)

    def test_more_roots_do_not_supply_missing_graph_consequences(self):
        # An empty binary abstraction does not decide a wider-clause CNF.
        source=native.normalize([(1,2,3),(-1,-2,-3)])[0]
        p=self.compare(source,[]);self.assertEqual(p['reason'],'no_useful_forced_literal')
        self.assertEqual(p['status'],'unresolved')

    def test_other_limits_still_stop_discovery(self):
        source,ts=chain(16,64)
        for kw in ({'edge_limit':1},{'round_limit':1},{'path_limit':1}):
            a=detector.discover(source,ts,Counter(),root_limit=64,filters='endpoint',**kw)
            b=detector.discover(source,ts,Counter(),root_limit=256,filters='endpoint',**kw)
            self.assertEqual(a,b);self.assertEqual(b['status'],'unresolved')


if __name__=='__main__':unittest.main()
