from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from pathlib import Path
import random,tempfile,unittest
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_context_solver import LocalContext,check_bound_rup,transport_bound,ContextGuardClosureSolver
from experiments.cnf_guard_support_solver import SupportGuardClosureSolver
from experiments.cnf_hint_transport import check_rup,discover_rup
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


def fixture(clauses):
    n=max(abs(l) for cl in clauses for l in cl)
    gs=[tuple(sorted(tuple(sorted(list(cl)+[sign*(n+i+1)])) for sign in (-1,1))) for i,cl in enumerate(clauses)]
    source=tuple(sorted(cl for g in gs for cl in g))
    ts=[conditional_unit(g,[[abs(l),l<0] for l in cl],Counter()) for g,cl in zip(gs,clauses)]
    return source,gs,ts


def prepared(cls,source,templates,raw=None,**kwargs):
    local,names=native.normalize(source if raw is None else raw)
    s=cls(templates=templates,**kwargs);s.guard_source=source;s.closure_counts=Counter();s.closure_records=None
    s.guard_parents=[dict(cnf=local,mapping=dict(enumerate(names,1)),fixed={})]
    return s,local


class GuardContextTests(unittest.TestCase):
    def context(self,cnf):
        return LocalContext.prepare(cnf,dict(cnf=cnf,mapping={v:v for cl in cnf for v in map(abs,cl)},fixed={}),Counter())

    def test_exhaustive_two_variable_rup_and_independent_truth(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            core,names=native.normalize([c for i,c in enumerate(clauses) if mask>>i&1]);ctx=self.context(core)
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=len(names))]
            for clause in clauses:
                if any(abs(l)>len(names) for l in clause):continue
                clause=tuple(sorted(clause));p=discover_rup(core,clause,Counter())
                if p is None:continue
                check_bound_rup(ctx,clause,p,Counter());check_rup(core,clause,p,Counter())
                self.assertTrue(all(not native.holds(core,a) or native.holds([clause],a) for a in models))

    def test_malformed_reason_conflict_and_clause_rejected(self):
        core=((-2,),(-1,2),(1,));ctx=self.context(core);proof=discover_rup(core,(),Counter())
        bads=[dict(units=[],conflict=1),dict(units=proof['units'],conflict=False),
              dict(units=proof['units'],conflict=999),dict(proof,extra=True),dict(units='bad',conflict=0)]
        p=deepcopy(proof);p['units'][0][1]=999;bads.append(p)
        p=deepcopy(proof);p['units'][0][0]=False;bads.append(p)
        for bad in bads:
            with self.assertRaises(ValueError):check_bound_rup(ctx,(),bad,Counter())
        for clause in ([False],[0],[3],[-1,1],[1,1],[2,1]):
            with self.assertRaises(ValueError):check_bound_rup(ctx,clause,proof,Counter())

    def test_context_rejects_noncanonical_source_or_wrong_binding(self):
        for core in (((2,),),((1,),(1,)),((1,-1),),((2,1),),((True,),),((0,),)):
            with self.assertRaises(ValueError):self.context(core)
        core=((1,),)
        with self.assertRaises(ValueError):LocalContext.prepare(core,dict(cnf=(),mapping={},fixed={}),Counter())

    def test_mutable_inputs_are_snapshotted_and_maps_are_read_only(self):
        core=[[-1],[1]];parent=dict(cnf=core,mapping={1:11},fixed={12:True})
        ctx=LocalContext.prepare(core,parent,Counter());core[0][0]=1;parent['mapping'][1]=99;parent['fixed'][12]=False
        self.assertEqual(ctx.core,((-1,),(1,)));self.assertEqual(dict(ctx.inverse),{11:1});self.assertTrue(ctx.fixed[12])
        with self.assertRaises(TypeError):ctx.positions[(1,)]=0
        with self.assertRaises(AttributeError):ctx.core=()
        check_bound_rup(ctx,(),dict(units=[[-1,0]],conflict=1),Counter())

    def test_satisfiable_graph_and_exhausted_budget_prepare_nothing(self):
        for clauses,kwargs in (([[1,2],[1,-2]],{}),([[1,2],[1,-2],[-1,2],[-1,-2]],dict(closure_literals=1))):
            source,_,ts=fixture(clauses);s,local=prepared(ContextGuardClosureSolver,source,ts,**kwargs)
            try:
                with patch.object(LocalContext,'prepare',side_effect=AssertionError('Unneeded context')):
                    self.assertIsNone(s._guard_closure(local))
            finally:s.close()

    def test_all_binary_subsets_preserve_native_records(self):
        cs=[(1,),(-1,),(2,),(-2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        source,gs,ts=fixture(cs);source=tuple(sorted(source+((1,11,12),)))
        for mask in range(256):
            raw=tuple(cl for i,g in enumerate(gs) if mask>>i&1 for cl in g)+((1,11,12),)
            rows=[];proofs=[]
            for cls in (SupportGuardClosureSolver,ContextGuardClosureSolver):
                s,local=prepared(cls,source,ts,raw)
                try:
                    p=s._guard_closure(local);proofs.append(p)
                    if p is not None:
                        key=s._canonical(local)[2];s._store(key,dict(format=native.FORMAT,cnf=list(map(list,local)),answer=False,proof=p))
                    rows.append(s.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall())
                finally:s.close()
            self.assertEqual(*proofs,mask);self.assertEqual(*rows,mask)

    def test_preparation_shared_but_context_does_not_survive_call(self):
        source,_,ts=fixture([[1,2],[1,-2],[-1,2],[-1,-2]])
        old,local=prepared(SupportGuardClosureSolver,source,ts);new,cnf=prepared(ContextGuardClosureSolver,source,ts)
        try:
            self.assertEqual(old._guard_closure(local),new._guard_closure(cnf))
            self.assertEqual(new.closure_counts['context_preparations'],1)
            self.assertGreater(old.closure_counts['position_clauses'],new.closure_counts['position_clauses'])
            self.assertEqual(old.closure_counts['verified_core_hints'],new.closure_counts['verified_core_hints'])
            new._guard_closure(cnf);self.assertEqual(new.closure_counts['context_preparations'],2)
            self.assertFalse(any(isinstance(x,LocalContext) for x in vars(new).values()))
        finally:old.close();new.close()

    def test_alternative_missing_support_and_changed_assignment(self):
        source,gs,ts=fixture([[1,2],[1,-2],[-1,2],[-1,-2],[1,2]])
        for raw in (tuple(cl for g in gs[1:] for cl in g),tuple(cl for g in gs[:-2] for cl in g)):
            old,local=prepared(SupportGuardClosureSolver,source,ts,raw);new,cnf=prepared(ContextGuardClosureSolver,source,ts,raw)
            try:self.assertEqual(old._guard_closure(local),new._guard_closure(cnf))
            finally:old.close();new.close()
        source=((-2,),(-1,2),(3,4,5));t=conditional_unit(source,[[1,True]],Counter())
        for bit in (True,False):
            raw=native.restrict_scan(source,{1:bit},Counter());rows=[]
            for cls in (SupportGuardClosureSolver,ContextGuardClosureSolver):
                s,local=prepared(cls,source,[t],raw);s.guard_parents[-1]['fixed']={1:bit}
                try:rows.append(s._guard_closure(local))
                finally:s.close()
            self.assertEqual(*rows)

    def test_fresh_unlabelled_queries_and_cold_native_replay(self):
        rng=random.Random(202611241520)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history'
            for _ in range(48):
                core=native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(15)])[0]
                templates=[t for bits in product((False,True),repeat=3) if (t:=conditional_unit(core,list(map(list,enumerate(bits,1))),Counter())) is not None]
                expected=any(native.holds(core,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4))
                s=ContextGuardClosureSolver(path,templates=templates,node_limit=1000)
                try:self.assertEqual(s.solve(core)['answer'],expected);self.assertEqual(s.guard_summary['pending_end'],0)
                finally:s.close()
            for cls in (native.ResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for (key,) in s.db.execute('SELECT id FROM cnf_residual_v1').fetchall():self.assertIsNotNone(s._read(key))
                finally:s.close()


if __name__=='__main__':unittest.main()
