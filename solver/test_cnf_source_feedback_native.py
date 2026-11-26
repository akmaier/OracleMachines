from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,random,tempfile,unittest
from unittest.mock import patch
from experiments import cnf_source_feedback_native as c
from experiments.cnf_fresh_seed_panel import panel,truth,cube
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

OUT=Path('experiments/results/cnf-fresh-seed-feedback')


def cold(db,source,root):
    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
        reader=cls(db)
        try:
            result=reader.solve(source)
            assert result['root']==root and result['answer'] is False
        finally:reader.close()


class SourceFeedbackTests(unittest.TestCase):
    def test_exhaustive_two_variable_and_seeded_sources(self):
        clauses=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(271127)
        sources=[[clauses[i] for i in range(8) if mask>>i&1] for mask in range(256)]
        sources += [[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),3)] for _ in range(22)] for _ in range(40)]
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'db';solver=c.native.ResidualSolver(db)
            try:
                for source in sources:
                    chain,_=c.feedback.discover(source,Counter())
                    if chain['status']=='refuted':
                        self.assertFalse(truth(source)['answer'])
                        root=c.compile_program(solver,source,chain,Counter(),shortcut='off');cold(db,source,root)
            finally:solver.close()

    def test_frozen_panel_and_all_refutations_without_historical_prepare(self):
        rows,descriptions=panel();self.assertEqual(rows,json.loads((OUT/'panel.json').read_text()))
        self.assertEqual(descriptions,json.loads((OUT/'descriptions.json').read_text()));closed=0
        for row in rows:
            chain=json.loads((OUT/(row['id']+'-chain.json')).read_text())
            if chain['status']!='refuted':continue
            closed+=1;self.assertFalse(truth(row['source'])['answer'])
            for shortcut in ('off','all'):
                with tempfile.TemporaryDirectory() as td:
                    db=Path(td)/'db';solver=c.native.ResidualSolver(db);cc=Counter()
                    try:
                        with patch('experiments.cnf_b13_probe_feedback.prepare',side_effect=AssertionError('Historical base used')):
                            root=c.compile_program(solver,row['source'],chain,cc,shortcut=shortcut)
                        if row['id']=='p32':
                            self.assertEqual(cc['source_feedback_prepared_levels'],2)
                            self.assertGreater(cc['source_feedback_cross_expansions'],0)
                    finally:solver.close()
                    cold(db,row['source'],root)
        self.assertEqual(closed,8)

    def test_sparse_names_normalization_and_repeated_input(self):
        source=[[l*101 for l in row] for row in cube(3)];chain,_=c.feedback.discover(source,Counter())
        solver=c.native.ResidualSolver()
        try:
            root=c.compile_program(solver,source,chain,Counter());size=solver.archive_storage()
            equivalent=[list(reversed(cl))+cl[:1] for cl in reversed(source)]+source+[[999,-999]]
            cc=Counter();self.assertEqual(c.compile_program(solver,equivalent,chain,cc),root)
            self.assertEqual(size,solver.archive_storage());self.assertEqual(cc['source_feedback_root_hits'],1)
            self.assertGreater(cc['feedback_checked_levels'],0)
        finally:solver.close()

    def test_changed_provenance_rejected_before_warm_publication(self):
        rows,_=panel();source=next(r['source'] for r in rows if r['id']=='p32');chain=json.loads((OUT/'p32-chain.json').read_text())
        solver=c.native.ResidualSolver()
        try:
            c.compile_program(solver,source,chain,Counter());before=solver.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall()
            for kind in ('source','seed','level','assumption','proof'):
                src=deepcopy(source);bad=deepcopy(chain)
                if kind=='source':src.pop()
                elif kind=='seed':bad['levels'][0]['seed'][0].append(9999)
                elif kind=='level':bad['levels'].reverse()
                elif kind=='assumption':bad['levels'][0]['lemmas'][0]['assumption']*=-1
                else:bad['levels'][-1]['proof']['conflict']=999999
                with self.assertRaises(ValueError,msg=kind):c.compile_program(solver,src,bad,Counter())
                self.assertEqual(before,solver.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall())
        finally:solver.close()

    def test_unresolved_is_not_native_authority_even_with_cached_root(self):
        source=cube(4);chain,_=c.feedback.discover(source,Counter());self.assertEqual(chain['reason'],'no_new_units')
        solver=c.native.ResidualSolver()
        try:
            self.assertFalse(solver.solve(source)['answer'])
            with self.assertRaises(ValueError):c.compile_program(solver,source,chain,Counter())
        finally:solver.close()

    def test_empty_conflict_and_invalid_bounds(self):
        solver=c.native.ResidualSolver()
        try:
            chain,_=c.feedback.discover([[]],Counter());root=c.compile_program(solver,[[]],chain,Counter())
            self.assertFalse(solver._read(root)['answer'])
            for kwargs in (dict(shortcut='guess'),dict(unit_work_limit=0),dict(unit_trace_limit=True)):
                with self.assertRaises(ValueError):c.compile_program(solver,[[]],chain,Counter(),**kwargs)
        finally:solver.close()

    def test_one_global_shortcut_allowance(self):
        rows,_=panel();source=next(r['source'] for r in rows if r['id']=='p32');chain=json.loads((OUT/'p32-chain.json').read_text())
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'db';solver=c.native.ResidualSolver(db);cc=Counter()
            try:root=c.compile_program(solver,source,chain,cc,unit_work_limit=1)
            finally:solver.close()
            self.assertLessEqual(sum(cc[x] for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),1)
            self.assertGreater(cc['direct_budget_skips'],0);cold(db,source,root)

    def test_nondefault_ordering_is_bound_and_checked(self):
        source=cube(3);order=list(reversed(source));chain,_=c.feedback.discover(source,Counter(),order_source=order)
        solver=c.native.ResidualSolver()
        try:
            c.compile_program(solver,source,chain,Counter(),order_source=order)
            with self.assertRaises(ValueError):c.compile_program(solver,source,chain,Counter())
        finally:solver.close()


if __name__=='__main__':unittest.main()
