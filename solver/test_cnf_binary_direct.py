from collections import Counter
import itertools
import random
import unittest

from experiments.cnf_binary_direct import BinaryDirectInventory, discover_direct_paths
from experiments.cnf_binary_paths import check_binary_paths
from experiments.cnf_residual_dag import normalize, holds
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_binary_paths import check_tree


class BinaryDirectTests(unittest.TestCase):
    def test_only_direct_subsumption_and_retained_reasons(self):
        source=((-1,2),(-2,3),(-1,2,4),(-1,3,4))
        cert=discover_direct_paths(source,Counter())
        self.assertEqual([c for c,_ in cert['removed']],[2])
        reduced=check_binary_paths(source,cert,Counter())
        for model in assignments(source):self.assertEqual(holds(source,model),holds(reduced,model))
        self.assertEqual(discover_direct_paths(source,Counter(),root_limit=0),dict(proof=[],removed=[]))

    def test_random_integrated_models_and_complete_direct_deletion(self):
        rng=random.Random(202611091651);h=BinaryDirectInventory(max_depth=1)
        for _ in range(60):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,6),rng.choice((2,3,4)))) for _ in range(16)]
            cnf,_=normalize(source);cert=discover_direct_paths(cnf,Counter())
            expected=[i for i,c in enumerate(cnf) if len(c)>2 and any(set(d)<=set(c) for d in cnf if len(d)==2)]
            self.assertEqual([c for c,_ in cert['removed']],expected)
            reduced=check_binary_paths(cnf,cert,Counter())
            for model in assignments(cnf):self.assertEqual(holds(cnf,model),holds(reduced,model))
            result=h.inspect(cnf);check_tree(h,result['root']['key'])
        h.close()
