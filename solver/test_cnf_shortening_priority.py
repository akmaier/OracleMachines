from collections import Counter
from itertools import product
import random,unittest
from experiments import cnf_shortening_priority as priority
from experiments import cnf_shortening_reach_bfs as frozen
from experiments import cnf_residual_dag as native
from solver.test_cnf_guard_shortening import chain


class ShorteningPriorityTests(unittest.TestCase):
    def test_score_is_exact_ternary_incidence_and_preserves_candidates(self):
        source=((-5,-4,-1),(-5,-3,-1),(-4,-3,-2),(-6,-4,-3,-2),(1,2))
        model={v:True for v in range(1,7)};counts=Counter()
        roots=priority.priority_roots(source,model,counts)
        expected=sorted({l for cl in source if len(cl)>2 for l in cl if model[abs(l)]!=(l>0)})
        self.assertEqual(set(roots),set(expected))
        self.assertEqual(roots,[-5,-4,-3,-1,-2,-6])
        self.assertEqual(counts['priority_literal_visits'],13)

    def test_uniform_ternary_scores_retain_numeric_ties(self):
        c=Counter();self.assertEqual(priority.priority_roots(((-4,-3,-2,-1),),dict.fromkeys(range(1,5),True),c),[-4,-3,-2,-1])
        self.assertEqual(priority.priority_roots(((1,2,3),),dict.fromkeys(range(1,4),True),Counter()),[])

    def test_supplied_chain_proofs_and_budgets(self):
        for depth in (1,2,4,8):
            for reuse in (False,True):
                source,ts=chain(depth,8);c=Counter();p=priority.discover(source,ts,c,reuse=reuse)
                self.assertEqual(p['status'],'refuted')
                s=native.ResidualSolver()
                try:self.assertFalse(s._read(priority.compile_program(s,source,ts,p,Counter()))['answer'])
                finally:s.close()
                self.assertLessEqual(c['reach_roots'],64)
                self.assertLessEqual(c['reach_edge_visits']+c['reuse_invalidation_checks'],16384)
                if not reuse:self.assertEqual(c['cache_stores'],0)

    def test_random_unlabelled_cnf_programs_against_truth(self):
        rng=random.Random(242123)
        for _ in range(240):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))]
                for _ in range(rng.randrange(2,22))])[0]
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=5)]
            models=[m for m in models if native.holds(source,m)]
            for reuse in (False,True):
                p=priority.discover(source,[],Counter(),reuse=reuse)
                for step in p['steps']:
                    self.assertTrue(all(m[abs(step['forced'])]==(step['forced']>0) for m in models))
                if p['status']=='refuted':
                    self.assertFalse(models);s=native.ResidualSolver()
                    try:self.assertFalse(s._read(priority.compile_program(s,source,[],p,Counter()))['answer'])
                    finally:s.close()

    def test_interrupted_traversals_remain_unresolved(self):
        source,ts=chain(8,8)
        for reuse in (False,True):
            c=Counter();p=priority.discover(source,ts,c,root_limit=1,edge_limit=1,reuse=reuse)
            self.assertEqual(p['status'],'unresolved');self.assertLessEqual(c['reach_edge_visits'],1)


if __name__=='__main__':unittest.main()
