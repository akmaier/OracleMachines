from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from experiments import cnf_direct_unit_closure as c
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from solver.test_cnf_cursor_feedback import fixture


def rows(solver):
    return list(solver.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))


class DirectUnitClosureTests(unittest.TestCase):
    def test_disabled_reproduces_baseline_authority_and_counts(self):
        args=fixture();program=c.prior.discover(*args,Counter());outputs=[]
        for compiler,options in ((c.prior,{}),(c,dict(shortcut='off'))):
            solver=c.native.ResidualSolver();counts=Counter()
            try:
                root=compiler.compile_program(solver,*args,program,counts,**options)
                outputs.append((root,rows(solver),counts,dict(solver.counts)))
            finally:solver.close()
        self.assertEqual(outputs[0],outputs[1])

    def test_compact_full_support_warm_and_both_cold_readers(self):
        args=fixture();program=c.prior.discover(*args,Counter())
        for mode,selected in product(('all','layer'),(False,True)):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';solver=c.native.ResidualSolver(path);counts=Counter()
                try:
                    key=c.compile_program(solver,*args,program,counts,shortcut=mode,select_support=selected)
                    self.assertGreater(counts['direct_refutations'],0)
                    self.assertLessEqual(sum(counts[k] for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                    before=rows(solver)
                    self.assertEqual(key,c.compile_program(solver,*args,program,Counter(),shortcut=mode))
                    self.assertEqual(before,rows(solver))
                finally:solver.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(key)['answer'])
                    finally:reader.close()

    def test_work_and_trace_budget_fall_back_without_asserting_a_fact(self):
        args=fixture();program=c.prior.discover(*args,Counter());outputs=[]
        for compiler,options in ((c.prior,{}),(c,dict(unit_work_limit=1))):
            solver=c.native.ResidualSolver()
            try:
                counts=Counter();compiler.compile_program(solver,*args,program,counts,**options);outputs.append(rows(solver))
                if options:self.assertEqual(counts['direct_gate_clauses'],1);self.assertEqual(counts['direct_attempts'],0)
            finally:solver.close()
        self.assertEqual(*outputs)
        solver=c.native.ResidualSolver()
        try:
            counts=Counter();direct=c.DirectUnits(counts,10000,1)
            frame=c.prepare_frame(solver,[(1,),(-1,2),(-2,)],counts)
            self.assertFalse(direct.close(frame));self.assertFalse(rows(solver));self.assertEqual(counts['direct_trace_limit_fallbacks'],1)
            for options in ({'shortcut':'guess'},{'unit_work_limit':True},{'unit_trace_limit':0}):
                with self.assertRaises(ValueError):c.compile_program(solver,*args,program,Counter(),**options)
        finally:solver.close()

    def test_exhaustive_two_variable_formulas(self):
        clauses=[tuple(sign*v for v,sign in enumerate(signs,1) if sign) for signs in product((-1,0,1),repeat=2)]
        checked=0
        for mask in range(1<<len(clauses)):
            raw=[cl for i,cl in enumerate(clauses) if mask>>i&1];solver=c.native.ResidualSolver();counts=Counter()
            try:
                frame=c.prepare_frame(solver,raw,counts);closed=c.DirectUnits(counts,10000,32).close(frame)
                if closed:
                    checked+=1
                    self.assertFalse(any(c.native.holds(raw,dict(enumerate(bits,1))) for bits in product((False,True),repeat=2)))
                    self.assertFalse(solver._read(frame[2])['answer'])
                else:self.assertFalse(rows(solver))
            finally:solver.close()
        self.assertGreater(checked,100)

    def test_native_checker_rejects_corrupt_shortcut(self):
        solver=c.native.ResidualSolver();counts=Counter()
        try:
            frame=c.prepare_frame(solver,[(1,),(-1,2),(-2,)],counts)
            with patch.object(c.frozen.UnitIndex,'probe',return_value=dict(units=[],conflict=99999)):
                with self.assertRaises(ValueError):c.DirectUnits(counts,10000,32).close(frame)
            self.assertFalse(rows(solver))
        finally:solver.close()

    def test_invalid_old_provenance_rejected_before_warm_lookup(self):
        args=fixture();program=c.prior.discover(*args,Counter());solver=c.native.ResidualSolver()
        try:
            c.compile_program(solver,*args,program,Counter());before=rows(solver)
            for kind in ('binding','old','top'):
                bad=deepcopy(args);p=deepcopy(program)
                if kind=='binding':bad[-1]['cursor']['binding']='changed'
                elif kind=='old':bad[2]['probes'][0]['proof']['conflict']=99999
                else:p['proof']['conflict']=99999
                with self.assertRaises(ValueError):c.compile_program(solver,*bad,p,Counter())
                self.assertEqual(before,rows(solver))
        finally:solver.close()

    def test_different_residuals_share_budget_but_not_an_index_or_claim(self):
        solver=c.native.ResidualSolver();counts=Counter();direct=c.DirectUnits(counts,10000,32)
        try:
            conflict=c.prepare_frame(solver,[(11,),(-11,23),(-23,)],counts)
            opened=c.prepare_frame(solver,[(11,),(-11,23)],counts)
            self.assertTrue(direct.close(conflict));before=rows(solver)
            self.assertFalse(direct.close(opened));self.assertEqual(before,rows(solver))
            self.assertEqual(counts['direct_probe_index_builds'],2)
        finally:solver.close()

    def test_guarded_source_extension(self):
        args=fixture(True);program=c.prior.discover(*args,Counter());solver=c.native.ResidualSolver()
        try:
            prefix=dict(status='unresolved',steps=[],path_limit=256)
            key=c.compile_extension(solver,args[0],args[1],prefix,*args[2:],program,Counter())
            self.assertFalse(solver._read(key)['answer'])
        finally:solver.close()


if __name__=='__main__':unittest.main()
