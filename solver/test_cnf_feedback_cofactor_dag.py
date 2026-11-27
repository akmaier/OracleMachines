from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,random,tempfile,unittest
from experiments import cnf_feedback_cofactor_dag as k
from experiments.cnf_fresh_seed_panel import cube,truth
from experiments.cnf_conditioning_transfer_panel import panel
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

OUT=Path('experiments/results/cnf-feedback-cofactor-dag')


def cold(path,source,root):
    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
        reader=cls(path)
        try:
            r=reader.solve(source);assert r['root']==root and r['answer'] is False
        finally:reader.close()


class FeedbackCofactorTests(unittest.TestCase):
    def test_exhaustive_two_variable_and_generated_truth(self):
        clauses=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(27112702)
        cases=[[clauses[i] for i in range(8) if mask>>i&1] for mask in range(256)]
        cases += [[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.choice((3,4)))] for _ in range(25)] for _ in range(32)]
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'db';solver=k.native.ResidualSolver(db)
            try:
                for source in cases:
                    record,_=k.discover(source,Counter());k.validate(source,record,Counter())
                    if record['status']=='refuted':
                        self.assertFalse(truth(source)['answer']);root=k.compile_program(solver,source,record,Counter());cold(db,source,root)
            finally:solver.close()

    def test_cube_recurrence_and_depth_boundary(self):
        for n in range(3,7):
            records=[]
            for reuse in (False,True):
                cc=Counter();r,_=k.discover(cube(n),cc,reuse=reuse);k.validate(cube(n),r,Counter());d=min(2,n-3)
                self.assertEqual(cc['cofactor_feedback_calls'],d+1 if reuse else 2**(d+1)-1)
                self.assertEqual(r['status'],'refuted' if n<=5 else 'unresolved');records.append(r)
            self.assertEqual(records[0]['status'],records[1]['status'])

    def test_five_development_refutations_both_cold_readers(self):
        closed=[]
        for row in json.loads((OUT/'development.json').read_text()):
            r,_=k.discover(row['source'],Counter());k.validate(row['source'],r,Counter())
            if r['status']!='refuted':continue
            closed.append(row['id'])
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';solver=k.native.ResidualSolver(db);cc=Counter()
                try:root=k.compile_program(solver,row['source'],r,cc,unit_work_limit=1)
                finally:solver.close()
                self.assertLessEqual(sum(cc[x] for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),1)
                cold(db,row['source'],root)
        self.assertEqual(len(closed),5);self.assertNotIn('d-p23',closed)

    def test_frozen_heldout_inputs_and_metadata(self):
        rows,desc=panel();self.assertEqual(rows,json.loads((OUT/'heldout.json').read_text()))
        self.assertEqual(desc,json.loads((OUT/'heldout-descriptions.json').read_text()))

    def test_mutated_edges_status_context_and_cycle_rejected_warm(self):
        source=cube(5);r,_=k.discover(source,Counter());solver=k.native.ResidualSolver()
        try:
            k.compile_program(solver,source,r,Counter());before=solver.archive_storage()
            for kind in ('edge','depth','pivot','status','source','cycle','chain'):
                bad=deepcopy(r);root=bad['nodes'][bad['root']];src=source
                if kind=='edge':root['low']=0
                elif kind=='depth':bad['nodes'][0]['depth']+=1
                elif kind=='pivot':root['pivot']=999
                elif kind=='status':root['status']='sat'
                elif kind=='source':src=source[1:]
                elif kind=='cycle':root['high']=bad['root']
                else:bad['nodes'][0]['chain']['levels'][-1]['proof']['conflict']=9999
                with self.assertRaises(ValueError,msg=kind):k.compile_program(solver,src,bad,Counter())
                self.assertEqual(solver.archive_storage(),before)
        finally:solver.close()

    def test_state_budget_and_depth_are_never_sat_authority(self):
        for settings in (dict(state_limit=1),dict(depth_limit=0)):
            r,_=k.discover(cube(5),Counter(),**settings);k.validate(cube(5),r,Counter());self.assertEqual(r['status'],'unresolved')
            solver=k.native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):k.compile_program(solver,cube(5),r,Counter())
            finally:solver.close()
        for source in ([],cube(4)[1:]):
            r,_=k.discover(source,Counter());self.assertEqual(r['status'],'unresolved')
        for kwargs in (dict(depth_limit=-1),dict(state_limit=0),dict(reuse=1),dict(mystery=1)):
            with self.assertRaises(ValueError):k.discover([],Counter(),**kwargs)

    def test_native_graphs_equal_with_and_without_discovery_memo(self):
        source=cube(5);tables=[]
        for reuse in (False,True):
            r,_=k.discover(source,Counter(),reuse=reuse);solver=k.native.ResidualSolver()
            try:
                root=k.compile_program(solver,source,r,Counter());cc=Counter();self.assertEqual(k.compile_program(solver,source,r,cc),root)
                self.assertEqual(cc['cofactor_native_hits'],1);self.assertGreater(cc['cofactor_checked_nodes'],0)
                tables.append(solver.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall())
            finally:solver.close()
        self.assertEqual(tables[0],tables[1])

    def test_normalized_sources_and_branch_local_provenance(self):
        source=[[101*l for l in cl] for cl in cube(4)];r,_=k.discover(source,Counter());solver=k.native.ResidualSolver()
        try:
            root=k.compile_program(solver,source,r,Counter())
            self.assertEqual(k.compile_program(solver,list(reversed(source))+source+[[999,-999]],r,Counter()),root)
            bad=deepcopy(r);bad['nodes'][0]['chain']['seed'].append([999])
            with self.assertRaises(ValueError):k.compile_program(solver,source,bad,Counter())
        finally:solver.close()


if __name__=='__main__':unittest.main()
