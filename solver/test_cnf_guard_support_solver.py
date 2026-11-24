from collections import Counter
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_support_solver import SupportGuardClosureSolver, witness_support
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_guard_witness_solver import WitnessGuardClosureSolver


class GuardSupportTests(unittest.TestCase):
    def fixtures(self, clauses):
        n=max(abs(l) for cl in clauses for l in cl)
        gadgets=[tuple(sorted(tuple(sorted(list(cl)+[sign*(n+i+1)])) for sign in (-1,1)))
                 for i,cl in enumerate(clauses)]
        source=tuple(sorted(cl for g in gadgets for cl in g))
        ts=[conditional_unit(g,[[abs(l),l<0] for l in cl],Counter()) for g,cl in zip(gadgets,clauses)]
        return source,gadgets,ts

    def prepared(self, source, templates, raw=None, path=':memory:', **kwargs):
        local,names=native.normalize(source if raw is None else raw)
        s=SupportGuardClosureSolver(path,templates=templates,**kwargs)
        s.guard_source=source;s.closure_counts=Counter();s.closure_records=None
        s.guard_parents=[dict(cnf=local,mapping=dict(enumerate(names,1)),fixed={})]
        return s,local

    def publish(self,s,local,proof):
        key=s._canonical(local)[2]
        s._store(key,dict(format=native.FORMAT,cnf=list(map(list,local)),answer=False,proof=proof))
        self.assertFalse(s._read(key)['answer'])
        return key

    def test_compact_subset_and_sparse_split_coordinates(self):
        source,_,ts=self.fixtures([[2,5],[2,-5],[-2,5],[-2,-5]])
        source=tuple(sorted(source+((1,3,4),)))
        s,local=self.prepared(source,ts)
        try:
            proof=s._guard_closure(local);self.publish(s,local,proof)
            self.assertEqual(proof['kind'],'component')
            self.assertLess(len(proof['clauses']),len(local))
            self.assertEqual(s.closure_counts['support_root_publications'],1)
        finally:s.close()

    def test_full_support_uses_existing_compiler(self):
        source,_,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        s,local=self.prepared(source,ts)
        try:
            proof=s._guard_closure(local);self.publish(s,local,proof)
            self.assertEqual(proof['kind'],'split')
            self.assertEqual(s.closure_counts['support_full_context_fallbacks'],1)
        finally:s.close()

    def test_shared_support_cold_reuse_across_enclosing_formulas(self):
        core,_,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'proofs.sqlite3';roots=[]
            for index,padding in enumerate((((1,7,8),),((2,7,8),(1,7,9)))):
                source=tuple(sorted(core+padding));s,local=self.prepared(source,ts,path=db)
                try:
                    proof=s._guard_closure(local);self.publish(s,local,proof);roots.append(proof['child'])
                    self.assertEqual(s.closure_counts['support_root_hits'],index)
                    if index:self.assertEqual(s.closure_counts['composed_splits'],0)
                finally:s.close()
            self.assertEqual(*roots)
            for cls in (native.ResidualSolver,CanonicalVerifySnapshot):
                reader=cls(db)
                try:
                    for (key,) in reader.db.execute('SELECT id FROM cnf_residual_v1').fetchall():self.assertIsNotNone(reader._read(key))
                finally:reader.close()

    def test_absent_contradictory_variable_needs_no_illegal_split(self):
        source=((-2,),(1,3,4),(2,))
        ts=[dict(clauses=[[-2],[2]],assumptions=[[1,b]],trace=[[-2,0]],conflict=1) for b in (False,True)]
        s,local=self.prepared(source,ts)
        try:
            proof=s._guard_closure(local);self.publish(s,local,proof)
            self.assertEqual(proof['kind'],'component')
            self.assertEqual(s.closure_counts['support_absent_premise_lifts'],1)
        finally:s.close()

    def test_original_binary_edges_are_included_in_support(self):
        core,_,ts=self.fixtures([[1]])
        source=tuple(sorted(core+((-1,3),(-3,),(1,4,5))))
        s,local=self.prepared(source,ts)
        try:
            proof=s._guard_closure(local);self.publish(s,local,proof)
            selected={local[i] for i in proof['clauses']}
            self.assertIn((-1,3),selected);self.assertIn((-3,),selected)
        finally:s.close()

    def test_missing_support_or_consequence_is_rejected(self):
        graph=[(-1,),(1,)];proof=dict(forward=[[-1,0]],backward=[[1,1]],variable=1)
        with self.assertRaises(ValueError):witness_support(((1,),),[],graph,proof,Counter())
        bad=dict(clause=[-1],template=dict(clauses=[[-2]]))
        with self.assertRaises(ValueError):witness_support(((1,),),[bad],graph,proof,Counter())

    def test_all_binary_subsets_with_unsupported_candidates_and_padding(self):
        clauses=[(1,),(-1,),(2,),(-2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        source,gadgets,ts=self.fixtures(clauses);source=tuple(sorted(source+((1,11,12),)))
        for mask in range(256):
            raw=tuple(cl for i,g in enumerate(gadgets) if mask>>i&1 for cl in g)+((1,11,12),)
            selected=[cl for i,cl in enumerate(clauses) if mask>>i&1]
            sat=any(native.holds(selected,dict(enumerate(bits,1))) for bits in product((False,True),repeat=2))
            s,local=self.prepared(source,ts,raw)
            try:
                proof=s._guard_closure(local);self.assertEqual(proof is None,sat,mask)
                if proof is not None:self.publish(s,local,proof)
            finally:s.close()

    def test_live_answers_and_native_budget(self):
        source=native.normalize([[1,2,3],[1,2,-3],[1,-2],[-1,4,5],[-1,4,-5],[-1,-4],[1,6,7]])[0]
        ts=[conditional_unit(source,[[1,b]],Counter()) for b in (False,True)]
        old=WitnessGuardClosureSolver(templates=ts);new=SupportGuardClosureSolver(templates=ts)
        try:
            self.assertFalse(old.solve(source)['answer']);self.assertFalse(new.solve(source)['answer'])
            self.assertEqual(new.guard_summary['pending_end'],0)
            self.assertEqual(new.closure_summary['counts']['support_wrappers'],1)
        finally:old.close();new.close()

    def test_allowances_precede_support_publication(self):
        core,_,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        source=tuple(sorted(core+((1,7,8),)))
        for kwargs in (dict(closure_edges=1),dict(path_limit=1)):
            s,local=self.prepared(source,ts,**kwargs)
            try:
                self.assertIsNone(s._guard_closure(local));self.assertEqual(s.closure_counts['support_wrappers'],0)
            finally:s.close()

    def test_unlabelled_small_inputs_truth_table(self):
        rng=random.Random(202611241318)
        for _ in range(40):
            source=native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(15)])[0]
            ts=[]
            for bits in product((False,True),repeat=3):
                t=conditional_unit(source,list(map(list,enumerate(bits,1))),Counter())
                if t is not None:ts.append(t)
            expected=any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4))
            s=SupportGuardClosureSolver(templates=ts,node_limit=1000)
            try:self.assertEqual(s.solve(source)['answer'],expected)
            finally:s.close()


if __name__=='__main__':unittest.main()
