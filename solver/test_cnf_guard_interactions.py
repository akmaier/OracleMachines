from collections import Counter
from copy import deepcopy
from itertools import product
import random,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_interactions import local_hints,binary_paths,inspect,compile_path
from experiments.cnf_hint_transport import check_rup


class GuardInteractionTests(unittest.TestCase):
    def event(self,source,fixed=None,subset=None):
        fixed=fixed or {};raw=native.restrict_scan(source,fixed,Counter()) if subset is None else subset
        local,names=native.normalize(raw)
        return dict(root=native.token(local,Counter()),mapping=[list(p) for p in enumerate(names,1)],fixed=sorted([list(p) for p in fixed.items()]))

    def encoded(self,clauses):
        source=[];n=max(abs(l) for cl in clauses for l in cl)
        for i,cl in enumerate(clauses,1):source.extend([list(cl)+[n+i],list(cl)+[-n-i]])
        return native.normalize(source)[0]

    def test_guard_pair_composes_a_new_forced_literal(self):
        source=self.encoded([[1,2],[1,-2]])
        ts=[conditional_unit(source,[[1,False],[2,b]],Counter()) for b in (False,True)]
        local,hints,whole=local_hints(source,ts,self.event(source),Counter());self.assertTrue(whole)
        result=inspect(local,hints,Counter());self.assertEqual(result['explicit_units'],[])
        self.assertIn(1,result['guard_composed']);self.assertEqual(result['profiles']['original']['paths'],{})
        s=native.ResidualSolver();self.addCleanup(s.close)
        key=compile_path(s,local,hints,result['profiles']['combined'],1,Counter())
        expected=s._canonical(native.restrict_scan(local,{1:False},Counter()))[2]
        self.assertEqual(key,expected);self.assertFalse(s._read(key)['answer'])
        self.assertTrue(s.solve(source)['answer'])  # Exclusion does not refute parent.

    def test_original_binary_and_guard_clause_interact(self):
        source=native.normalize(list(self.encoded([[1,2]]))+[[1,-2]])[0]
        t=conditional_unit(source,[[1,False],[2,False]],Counter())
        local,hints,_=local_hints(source,[t],self.event(source),Counter());r=inspect(local,hints,Counter())
        self.assertIn(1,r['mixed']);self.assertNotIn(1,r['profiles']['guards']['paths'])
        s=native.ResidualSolver();self.addCleanup(s.close)
        self.assertFalse(s._read(compile_path(s,local,hints,r['profiles']['combined'],1,Counter()))['answer'])

    def test_two_paths_refute_original_cnf_with_native_split(self):
        clauses=[[1,2],[1,-2],[-1,2],[-1,-2]];source=self.encoded(clauses)
        ts=[conditional_unit(source,[[abs(l),l<0] for l in cl],Counter()) for cl in clauses]
        local,hints,_=local_hints(source,ts,self.event(source),Counter());r=inspect(local,hints,Counter())
        self.assertTrue(r['profiles']['combined']['contradictory'])
        s=native.ResidualSolver();self.addCleanup(s.close);roots={}
        for lit in (-1,1):roots[lit]=compile_path(s,local,hints,r['profiles']['combined'],lit,Counter())
        key=s._canonical(local)[2]
        s._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in local],answer=False,
            proof=dict(kind='split',variable=1,low=roots[1],high=roots[-1])))
        self.assertFalse(s._read(key)['answer'])

    def test_missing_component_support_does_not_become_a_hint(self):
        source=native.normalize([[-1,-2],[2,3,4]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter());c=Counter()
        _,hints,whole=local_hints(source,[t],self.event(source,{1:True},((2,3,4),)),c)
        self.assertFalse(whole);self.assertEqual(hints,[]);self.assertEqual(c['local_support_misses'],1)

    def test_conditioning_renames_guard_and_reasons(self):
        source=native.normalize([[-1,-2,3],[-1,-2,-3]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter())
        local,hints,_=local_hints(source,[t],self.event(source,{1:True}),Counter())
        self.assertEqual(hints[0]['clause'],[-1]);check_rup(local,[-1],hints[0]['proof'],Counter())
        _,hints,_=local_hints(source,[t],self.event(source,{1:False}),Counter());self.assertEqual(hints,[])

    def test_invalid_mapping_evidence_and_limits_rejected(self):
        source=self.encoded([[1,2],[1,-2]])
        ts=[conditional_unit(source,[[1,False],[2,b]],Counter()) for b in (False,True)]
        event=self.event(source);bad=deepcopy(event);bad['mapping'][0][1]=10000
        with self.assertRaises(ValueError):local_hints(source,ts,bad,Counter())
        local,hints,_=local_hints(source,ts,event,Counter());r=inspect(local,hints,Counter())
        s=native.ResidualSolver();self.addCleanup(s.close)
        with self.assertRaises(ValueError):compile_path(s,local,hints,r['profiles']['combined'],1,Counter(),path_limit=1)
        bad=deepcopy(r['profiles']['combined']);bad['paths'][1][0][1]=10000
        with self.assertRaises(ValueError):compile_path(s,local,hints,bad,1,Counter())
        bad=deepcopy(hints);bad[0]['clause']=[-1]
        with self.assertRaises(ValueError):compile_path(s,local,bad,r['profiles']['combined'],1,Counter())

    def test_all_small_binary_graphs_match_truth(self):
        clauses=[(1,),(-1,),(2,),(-2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        for mask in range(1<<len(clauses)):
            cnf=tuple(cl for i,cl in enumerate(clauses) if mask>>i&1);r=binary_paths(cnf,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=2) if native.holds(cnf,dict(enumerate(bits,1)))]
            self.assertEqual(bool(r['contradictory']),not bool(models))
            if models:
                forced={sign*v for v in (1,2) for sign in (-1,1) if all(m[v]==(sign>0) for m in models)}
                self.assertEqual(set(r['paths']),forced)

    def test_unlabelled_small_conditional_hints_are_entailed(self):
        rng=random.Random(202611241014)
        for sample in range(30):
            source=native.normalize([rng.sample([-3,-2,-1,1,2,3],rng.randint(1,3)) for _ in range(8)])[0]
            ts=[]
            for values in product((False,True),repeat=3):
                t=conditional_unit(source,[list(p) for p in enumerate(values,1)],Counter())
                if t is not None:ts.append(t)
            for values in product((None,False,True),repeat=3):
                variables={abs(l) for cl in source for l in cl}
                fixed={i+1:b for i,b in enumerate(values) if b is not None and i+1 in variables}
                local,hints,_=local_hints(source,ts,self.event(source,fixed),Counter())
                for bits in product((False,True),repeat=3):
                    model=dict(enumerate(bits,1))
                    if native.holds(local,model):self.assertTrue(native.holds([h['clause'] for h in hints],model))

    def test_guard_graph_components_do_not_certify_source_independence(self):
        source=native.normalize([[1,3],[-3,1],[2,-3],[3,2]])[0]
        ts=[conditional_unit(source,[[v,False]],Counter()) for v in (1,2)]
        local,hints,_=local_hints(source,ts,self.event(source),Counter());r=inspect(local,hints,Counter())
        self.assertEqual(r['guard_components'],2);self.assertEqual(r['source_components'],1)
        self.assertEqual(r['support_overlap_pairs'],1)


if __name__=='__main__':unittest.main()
