from collections import Counter
from itertools import product
import random,unittest
from experiments import cnf_shortening_clause_filters as specialized
from experiments import cnf_shortening_filters as general
from experiments import cnf_residual_dag as native


def graph(clauses):
    adjacency={}
    for cid,cl in enumerate(clauses):
        a,b=cl[0],cl[-1];adjacency.setdefault(-a,[]).append((b,cid))
        if a!=b:adjacency.setdefault(-b,[]).append((a,cid))
    return adjacency


class ClauseFilterTests(unittest.TestCase):
    def test_all_two_variable_binary_graphs_have_redundant_endpoint_test(self):
        clauses=[(-1,),(-2,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        for bits in product((False,True),repeat=8):
            adjacency=graph([cl for cl,b in zip(clauses,bits) if b]);incoming={v for es in adjacency.values() for v,cid in es}
            edges={(u,v) for u,es in adjacency.items() for v,cid in es}
            self.assertTrue(all((-v,-u) in edges for u,v in edges))
            for weak in (False,True):
                c=Counter();a=specialized.NoPathFilter(adjacency,c,weak=weak);b=general.NoPathFilter(adjacency,Counter(),weak=weak)
                for root in (-3,-2,-1,1,2,3):
                    self.assertEqual(not adjacency.get(root),-root not in incoming)
                    self.assertEqual(a.excludes(root),b.excludes(root))
                self.assertEqual(c['filter_incoming_edges'],0)

    def test_specialization_retains_programs_on_random_unlabelled_cnf(self):
        rng=random.Random(242226)
        for _ in range(100):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,7),rng.randrange(1,5))] for _ in range(20)])[0]
            for order in ('numeric','priority'):
                for filters in ('endpoint','weak'):
                    c=Counter();a=specialized.discover(source,[],c,order=order,filters=filters)
                    b=general.discover(source,[],Counter(),order=order,filters=filters)
                    self.assertEqual(a,b);self.assertEqual(c['filter_incoming_edges'],0)


if __name__=='__main__':unittest.main()
