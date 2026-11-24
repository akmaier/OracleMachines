from collections import Counter
from copy import deepcopy
from itertools import product
import json,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit,make_open_plan
from experiments.cnf_guard_frontier import make_frontier_plan,closed_mass,guard_census
from experiments.cnf_partial_proof_plan import check_plan,recompose
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver


class GuardFrontierTests(unittest.TestCase):
    def supports(self,source):
        source=native.normalize(source)[0];n=len({abs(l) for cl in source for l in cl});result=[]
        for bits in product((None,False,True),repeat=n):
            t=conditional_unit(source,[[i+1,b] for i,b in enumerate(bits) if b is not None],Counter())
            if t is not None and t not in result:result.append(t)
        return source,result

    def test_exhaustive_small_inputs_caps_and_truth(self):
        clauses=[[-1],[-2],[1,2],[-1,2],[1,-2]]
        for mask in range(32):
            source,ts=self.supports([c for i,c in enumerate(clauses) if mask>>i&1])
            for cap in (1,2,3,7,129):
                counts=Counter();plan=make_frontier_plan(source,ts,node_limit=cap,counts=counts)
                check_plan(plan,node_limit=cap);self.assertLessEqual(2*counts['frontier_splits']+1,cap)
                hits=0
                for bits in product((False,True),repeat=2):
                    assignment=dict(enumerate(bits,1));node=plan['tree']
                    while 'variable' in node:node=node['high' if assignment[node['variable']] else 'low']
                    t=plan['templates'][node['leaf']]
                    if not t.get('open'):
                        hits+=1;self.assertFalse(native.holds(source,assignment))
                        self.assertTrue(all(assignment[v]==b for v,b in t['assumptions']))
                self.assertEqual(closed_mass(plan),hits/4)

    def test_deleted_support_is_filtered_before_selection(self):
        source,ts=self.supports([[-1,-2],[-1,2],[1,-2],[1,2]])
        target=source[1:];c=Counter();plan=make_frontier_plan(target,ts,counts=c)
        self.assertGreater(c['frontier_invalidated_templates'],0)
        s=LazyBinaryClosureSolver();self.addCleanup(s.close)
        r=recompose(s,target,plan,256)
        self.assertFalse(r['stopped']);self.assertTrue(s._read(r['root'])['answer'])

    def test_shorter_guard_wins_over_first_template(self):
        source=native.normalize([[-1,-2,-3],[-4]])[0]
        ts=[conditional_unit(source,[[1,True],[2,True],[3,True]],Counter()),
            conditional_unit(source,[[4,True]],Counter())]
        plan=make_frontier_plan(source,ts,node_limit=3)
        self.assertEqual(closed_mass(plan),0.5)
        self.assertGreater(closed_mass(plan),closed_mass(make_open_plan(ts,node_limit=3)))

    def test_same_guards_keep_alternative_source_supports(self):
        source=[[-1,2],[-2],[-1,3],[-3]]
        ts=[conditional_unit(source[:2],[[1,True]],Counter()),conditional_unit(source[2:],[[1,True]],Counter())]
        self.assertEqual(guard_census(ts)['unique_guards'],1)
        target=source[2:];plan=make_frontier_plan(target,ts)
        self.assertEqual(closed_mass(plan),0.5)

    def test_complete_cover_uses_native_authority(self):
        source,ts=self.supports([[-1,-2],[-1,2],[1,-2],[1,2]])
        plan=make_frontier_plan(source,ts);self.assertEqual(closed_mass(plan),1)
        s=LazyBinaryClosureSolver();self.addCleanup(s.close)
        r=recompose(s,source,plan,0)
        self.assertFalse(r['stopped']);self.assertFalse(s._read(r['root'])['answer'])

    def test_empty_bank_remains_open_and_roundtrips(self):
        plan=make_frontier_plan([[1,2]],[]);self.assertEqual(closed_mass(plan),0)
        restored=json.loads(json.dumps(plan));self.assertEqual(restored,plan);check_plan(restored)
        s=LazyBinaryClosureSolver();self.addCleanup(s.close)
        self.assertTrue(recompose(s,[[1,2]],restored,0)['stopped'])

    def test_inputs_not_mutated_and_bad_templates_rejected(self):
        source,ts=self.supports([[-1,-2],[-1,2],[1,-2],[1,2]])
        original=deepcopy(ts);make_frontier_plan(source,ts);self.assertEqual(ts,original)
        ts[0]['conflict']=999
        with self.assertRaises(ValueError):make_frontier_plan(source,ts)
        for cap in (0,130,True):
            with self.assertRaises(ValueError):make_frontier_plan(source,[],node_limit=cap)


if __name__=='__main__':unittest.main()
