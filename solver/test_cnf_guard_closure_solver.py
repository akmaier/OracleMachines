from collections import Counter
from itertools import product
from pathlib import Path
import random
import tempfile
import unittest

from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_closure_solver import GuardClosureSolver, transport_short
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_guard_interactions import local_hints
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class GuardClosureTests(unittest.TestCase):
    def encoded(self, clauses):
        n = max(abs(lit) for cl in clauses for lit in cl)
        source = [list(cl) + [sign * (n+i+1)]
                  for i, cl in enumerate(clauses) for sign in (-1, 1)]
        return native.normalize(source)[0]

    def prepared(self, source, templates, **kwargs):
        solver = GuardClosureSolver(templates=templates, **kwargs)
        self.addCleanup(solver.close)
        solver.guard_source = source
        solver.closure_counts = Counter()
        solver.closure_records = None
        names = {abs(lit) for cl in source for lit in cl}
        solver.guard_parents = [dict(cnf=source, mapping={v: v for v in names}, fixed={})]
        return solver

    def test_binary_closure_publishes_native_source_proof(self):
        clauses = [[1,2], [1,-2], [-1,2], [-1,-2]]
        source = self.encoded(clauses)
        ts = [conditional_unit(source, [[abs(lit), lit<0] for lit in cl], Counter()) for cl in clauses]
        solver = self.prepared(source, ts)
        proof = solver._guard_closure(source)
        self.assertEqual(solver.closure_counts['closed_binary_guards'], 1)
        key = solver._canonical(source)[2]
        solver._store(key, dict(format=native.FORMAT, cnf=list(map(list,source)), answer=False, proof=proof))
        self.assertFalse(solver._read(key)['answer'])
        units = self.prepared(source, ts, closure_mode='units')
        self.assertIsNone(units._guard_closure(source))

    def test_opposite_units_and_exhausted_budget(self):
        source = native.normalize([[1,2,3],[1,2,-3],[1,-2],[-1,4,5],[-1,4,-5],[-1,-4]])[0]
        ts = [conditional_unit(source, [[1, b]], Counter()) for b in (False, True)]
        solver = self.prepared(source, ts)
        self.assertIsNotNone(solver._guard_closure(source))
        self.assertEqual(solver.closure_counts['closed_opposite_units'], 1)
        for limit in (dict(closure_checks=1), dict(closure_literals=1), dict(closure_edges=1)):
            limited = self.prepared(source, ts, **limit)
            self.assertIsNone(limited._guard_closure(source))
        live = GuardClosureSolver(templates=ts)
        self.addCleanup(live.close)
        self.assertFalse(live.solve(source)['answer'])
        self.assertEqual(live.closure_summary['counts']['closed_opposite_units'], 1)
        self.assertEqual(live.guard_summary['pending_end'], 0)

    def test_satisfiable_consequence_graph_never_refutes_source(self):
        source = self.encoded([[1,2], [1,-2]])
        ts = [conditional_unit(source, [[1,False],[2,b]], Counter()) for b in (False,True)]
        solver = self.prepared(source, ts)
        self.assertIsNone(solver._guard_closure(source))
        self.assertTrue(solver.solve(source)['answer'])

    def test_empty_guard_and_component_missing_support(self):
        source = native.normalize([[-1,2], [-2], [3,4,5]])[0]
        template = conditional_unit(source, [[1,True]], Counter())
        raw = native.restrict_scan(source, {1:True}, Counter())
        local, names = native.normalize(raw)
        parent = dict(fixed={1:True}, mapping=dict(enumerate(names,1)))
        hint = transport_short(local, template, [], parent, Counter())
        self.assertEqual(hint['clause'], [])
        subset, names = native.normalize(((3,4,5),))
        parent['mapping'] = dict(enumerate(names,1))
        self.assertIsNone(transport_short(subset, template, [], parent, Counter()))

    def test_transport_matches_checked_offline_reference(self):
        source = self.encoded([[1,2], [1,-2], [-1,2]])
        templates = [conditional_unit(source, [[1,a],[2,b]], Counter())
                     for a,b in product((False,True),repeat=2)]
        templates = [t for t in templates if t is not None]
        variables = sorted({abs(lit) for cl in source for lit in cl})
        for values in product((None,False,True), repeat=2):
            fixed = {v:b for v,b in zip(variables,values) if b is not None}
            local, names = native.normalize(native.restrict_scan(source,fixed,Counter()))
            parent = dict(mapping=dict(enumerate(names,1)),fixed=fixed)
            event = dict(root=native.token(local,Counter()), mapping=list(parent['mapping'].items()),fixed=list(map(list,fixed.items())))
            _, expected, _ = local_hints(source,templates,event,Counter())
            actual = []
            for t in templates:
                if any(v in fixed and fixed[v]!=b for v,b in t['assumptions']):continue
                missing = [(v,b) for v,b in t['assumptions'] if v not in fixed]
                hint = transport_short(local,t,missing,parent,Counter())
                if hint is not None:actual.append(hint)
            self.assertEqual(actual,[{k:v for k,v in h.items() if k!='origin_template'} for h in expected])

    def test_unlabelled_truth_and_cold_replay(self):
        rng = random.Random(202611241112)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs.sqlite3'
            for sample in range(40):
                source = native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(15)])[0]
                templates = []
                for bits in product((False,True),repeat=3):
                    t = conditional_unit(source,list(map(list,enumerate(bits,1))),Counter())
                    if t is not None:templates.append(t)
                expected = any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4))
                for mode in ('units','binary'):
                    solver = GuardClosureSolver(path, templates=templates, closure_mode=mode, node_limit=1000)
                    try:
                        self.assertEqual(solver.solve(source)['answer'],expected)
                        self.assertEqual(solver.guard_summary['pending_end'],0)
                    finally:solver.close()
            reader = CanonicalVerifySnapshot(path)
            try:
                for (key,) in reader.db.execute('SELECT id FROM cnf_residual_v1').fetchall():
                    self.assertIsNotNone(reader._read(key))
            finally:reader.close()

    def test_empty_bank_preserves_tracking_control(self):
        source = self.encoded([[1,2],[1,-2],[-1,2]])
        control = GuardProbeSolver(templates=(),guard_mode='tracking')
        solver = GuardClosureSolver(templates=())
        self.addCleanup(control.close);self.addCleanup(solver.close)
        self.assertEqual(control.solve(source)['answer'],solver.solve(source)['answer'])
        self.assertEqual(control.counts,solver.counts)
        self.assertEqual(control.db.execute('SELECT * FROM cnf_residual_v1').fetchall(),
                         solver.db.execute('SELECT * FROM cnf_residual_v1').fetchall())

    def test_deleted_support_and_corrupt_template(self):
        source = self.encoded([[1],[-1]])
        templates = [conditional_unit(source,[[1,b]],Counter()) for b in (False,True)]
        solver = GuardClosureSolver(templates=templates)
        self.addCleanup(solver.close)
        self.assertTrue(solver.solve(source[:-1])['answer'])
        templates[0]['conflict'] = 10000
        bad = GuardClosureSolver(templates=templates)
        self.addCleanup(bad.close)
        with self.assertRaises(ValueError):bad.solve(source)

    def test_invalid_limits(self):
        for kwargs in (dict(closure_mode='unknown'),dict(closure_checks=0),dict(closure_edges=True),
                       dict(closure_literals=-1),dict(path_limit=0),dict(guard_mode='guided')):
            with self.assertRaises(ValueError):GuardClosureSolver(**kwargs)


if __name__ == '__main__':unittest.main()
