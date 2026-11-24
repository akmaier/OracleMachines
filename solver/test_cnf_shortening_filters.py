from collections import Counter,deque
from itertools import product
import random,unittest
from experiments import cnf_shortening_filters as candidate
from experiments import cnf_shortening_priority as priority
from experiments import cnf_residual_dag as native
from solver.test_cnf_guard_shortening import chain


def adjacency(edges):
    result={}
    for i,(a,b) in enumerate(edges):result.setdefault(a,[]).append((b,i))
    return result


def reachable(edges,root):
    seen={root};queue=deque([root]);graph=adjacency(edges)
    while queue:
        for end,cid in graph.get(queue.popleft(),()):
            if end not in seen:seen.add(end);queue.append(end)
    return seen


class ShorteningFilterTests(unittest.TestCase):
    def test_exhaustive_directed_graph_filters(self):
        vertices=(-1,1,2);universe=[(a,b) for a in vertices for b in vertices if a!=b]
        for bits in product((False,True),repeat=len(universe)):
            edges=[e for e,b in zip(universe,bits) if b]
            for weak in (False,True):
                f=candidate.NoPathFilter(adjacency(edges),Counter(),weak=weak)
                for root in (-2,-1,1,2):
                    if f.excludes(root):self.assertNotIn(-root,reachable(edges,root))

    def test_components_are_lazy_and_endpoint_rejections_do_not_build_them(self):
        c=Counter();f=candidate.NoPathFilter(adjacency([(1,2),(3,-1)]),c)
        self.assertTrue(f.excludes(4));self.assertEqual(c['filter_component_builds'],0)
        self.assertTrue(f.excludes(1));self.assertEqual(c['filter_disconnected'],1)
        self.assertEqual(c['filter_component_builds'],1)
        self.assertTrue(f.excludes(1));self.assertEqual(c['filter_component_builds'],1)

    def test_changed_graph_requires_new_filter(self):
        graph=[(1,2),(3,-1)];f=candidate.NoPathFilter(adjacency(graph),Counter())
        self.assertTrue(f.excludes(1))
        g=candidate.NoPathFilter(adjacency(graph+[(2,3)]),Counter())
        self.assertFalse(g.excludes(1));self.assertIn(-1,reachable(graph+[(2,3)],1))

    def test_same_component_does_not_assert_reachability(self):
        graph=[(1,2),(-1,2),(3,-1)]
        f=candidate.NoPathFilter(adjacency(graph),Counter())
        self.assertFalse(f.excludes(1));self.assertNotIn(-1,reachable(graph,1))

    def test_chain_proofs_keep_native_authority_and_caps(self):
        for depth in (1,2,4,8):
            source,ts=chain(depth,8)
            for order in ('numeric','priority'):
                for filters in ('endpoint','weak'):
                    c=Counter();p=candidate.discover(source,ts,c,order=order,filters=filters)
                    self.assertEqual(p['status'],'refuted');s=native.ResidualSolver()
                    try:self.assertFalse(s._read(candidate.compile_program(s,source,ts,p,Counter()))['answer'])
                    finally:s.close()
                    self.assertLessEqual(c['reach_roots'],64)
                    self.assertLessEqual(c['reach_edge_visits']+c['reuse_invalidation_checks'],16384)

    def test_unlabelled_cnf_against_exhaustive_truth(self):
        rng=random.Random(242223)
        for _ in range(180):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))]
                for _ in range(rng.randrange(2,24))])[0]
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=5)]
            models=[m for m in models if native.holds(source,m)]
            for order in ('numeric','priority'):
                for filters in ('endpoint','weak'):
                    p=candidate.discover(source,[],Counter(),order=order,filters=filters)
                    for step in p['steps']:self.assertTrue(all(m[abs(step['forced'])]==(step['forced']>0) for m in models))
                    if p['status']=='refuted':
                        self.assertFalse(models);s=native.ResidualSolver()
                        try:self.assertFalse(s._read(candidate.compile_program(s,source,[],p,Counter()))['answer'])
                        finally:s.close()

    def test_filtering_preserves_unbounded_reference_programs_on_small_inputs(self):
        rng=random.Random(242224)
        for _ in range(80):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,7),rng.choice((2,3)))] for _ in range(20)])[0]
            old=priority.discover(source,[],Counter(),root_limit=10000,edge_limit=100000)
            for filters in ('endpoint','weak'):
                new=candidate.discover(source,[],Counter(),root_limit=10000,edge_limit=100000,filters=filters)
                self.assertEqual(old,new)


if __name__=='__main__':unittest.main()
