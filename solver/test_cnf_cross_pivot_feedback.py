from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_cross_pivot_feedback as s
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
k=s.joint;c=k.conditioned


def partitions(source):
    return [c.discover(source,v,Counter()) for v in sorted({abs(l) for cl in source for l in cl})]


def real(name):
    p=s.base.load(s.PARENT/'protocol.json');case=s.old.bound(p['cases'][name]);prepared=s.prior.seed(case,Counter())
    history=s.base.load(s.PARENT/f'census-conditioned-0/{name}.json')
    full=k.collect(prepared[29],history['trials'],Counter(),order_source=prepared[0])
    return case,prepared,full


class CrossPivotFeedbackTests(unittest.TestCase):
    def test_exhaustive_small_and_random_implication_soundness(self):
        signed=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112622)
        cases=[(2,[signed[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(rng.randrange(1,25))]) for _ in range(80)]
        for n,source in cases:
            result=k.collect(source,partitions(source),Counter());k.validate(source,result,Counter());small=k.compact(source,result,Counter());k.validate(source,small,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if k.k.native.holds(source,dict(enumerate(bits,1)))]
            if result['status']=='refuted':self.assertFalse(models)
            self.assertEqual(result['status'],small['status'])
            for row in result['lemmas']:
                lit=row['assumption'];self.assertTrue(all(m[abs(lit)]!=(lit>0) for m in models))

    def test_one_failed_branch_only_proves_a_unit(self):
        source=[[1,*cl] for cl in ((2,3),(2,-3),(-2,3),(-2,-3))];p=c.discover(source,1,Counter());self.assertEqual(p['status'],'unresolved')
        summary=k.collect(source,[p],Counter());self.assertEqual(summary['status'],'unresolved')
        self.assertEqual([r['assumption'] for r in summary['lemmas']],[-1]);self.assertIn([1,True],summary['closure']['assignment'])
        self.assertEqual(k.compact(source,summary,Counter()),summary)

    def test_real_cross_pivot_joint_proofs_and_support_sizes(self):
        for name,before,after in (('61-0',9,7),('67-0',10,3),('61-50',2,2)):
            case,prepared,full=real(name);small=k.compact(prepared[29],full,Counter(),order_source=prepared[0])
            self.assertEqual(len(full['lemmas']),before);self.assertEqual(len(small['lemmas']),after)
            self.assertEqual(full['status'],'unresolved' if name=='61-50' else 'refuted')
            self.assertEqual(small,k.compact(prepared[29],small,Counter(),order_source=prepared[0]))
            self.assertTrue(all(t['status']=='unresolved' for t in s.base.load(s.PARENT/f'census-conditioned-0/{name}.json')['trials']))

    def test_native_joint_certificates_and_both_cold_readers(self):
        for name in ('61-0','67-0'):
            case,prepared,full=real(name);summary=k.compact(prepared[29],full,Counter(),order_source=prepared[0]);cc=Counter()
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';solver=s.compiler.native.ResidualSolver(path)
                try:
                    root=s.compile_case(solver,case,summary,cc);self.assertEqual(root,case['root']);self.assertGreater(cc['cross_native_branch_expansions'],0)
                    self.assertLessEqual(sum(cc[x] for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                    tables=s.old.tables(solver.db);wc=Counter();self.assertEqual(s.compile_case(solver,case,summary,wc),root)
                    self.assertEqual(wc['cross_native_extension_hits'],1);self.assertEqual(tables,s.old.tables(solver.db))
                finally:solver.close()
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    reader=cls(path)
                    try:self.assertFalse(reader._read(root)['answer'])
                    finally:reader.close()

    def test_warm_hits_still_reject_corrupted_provenance(self):
        case,p,full=real('61-0');summary=k.compact(p[29],full,Counter(),order_source=p[0])
        with tempfile.TemporaryDirectory() as td:
            solver=s.compiler.native.ResidualSolver(Path(td)/'db')
            try:
                s.compile_case(solver,case,summary,Counter());before=s.old.tables(solver.db)
                for kind in ('source','prefix','seed','assumption','proof','branch'):
                    badcase=deepcopy(case);bad=deepcopy(summary)
                    if kind=='source':badcase['source'][0].append(9999)
                    elif kind=='prefix':badcase['prefix']['status']='refuted'
                    elif kind=='seed':bad['seed'][0].append(9999)
                    elif kind=='assumption':bad['lemmas'][0]['assumption']*=-1
                    elif kind=='proof':bad['proof']['conflict']=999999
                    else:bad['lemmas'][0]['saturation']['status']='unresolved'
                    with self.assertRaises(ValueError,msg=kind):s.compile_case(solver,badcase,bad,Counter())
                self.assertEqual(before,s.old.tables(solver.db))
            finally:solver.close()

    def test_empty_support_sparse_coordinates_and_reindexing(self):
        source=[[10],[-10],[20,30]];summary=k.collect(source,partitions(source),Counter());small=k.compact(source,summary,Counter())
        self.assertEqual(small['lemmas'],[]);self.assertEqual(small['status'],'refuted');k.validate(source,small,Counter())
        cube=[list(row) for row in product((10,-10),(20,-20),(30,-30))]
        summary=k.collect(cube,partitions(cube),Counter());small=k.compact(cube,summary,Counter());self.assertEqual(small['status'],'refuted');k.validate(cube,small,Counter())

    def test_summary_is_owned_and_drops_open_siblings(self):
        source=[[1,*cl] for cl in ((2,3),(2,-3),(-2,3),(-2,-3))];saved=partitions(source);original=deepcopy(saved)
        result=k.collect(source,saved,Counter());self.assertEqual(saved,original);saved[0]['low']['status']='broken';k.validate(source,result,Counter())
        self.assertTrue(all(row['saturation']['status']=='refuted' for row in result['lemmas']))

    def test_invalid_lemmas_and_outcomes_rejected(self):
        source=[list(row) for row in product((1,-1),(2,-2),(3,-3))];result=k.collect(source,partitions(source),Counter())
        for kind in ('duplicate','bool','empty','open','status','ordering','extra'):
            bad=deepcopy(result)
            if kind=='duplicate':bad['lemmas'].append(deepcopy(bad['lemmas'][0]))
            elif kind=='bool':bad['lemmas'][0]['assumption']=True
            elif kind=='empty':bad['lemmas']=[]
            elif kind=='open':bad['lemmas'][0]['saturation']['status']='unresolved'
            elif kind=='status':bad['status']='sat'
            elif kind=='ordering':bad['order_source'][0].append(99)
            else:bad['unchecked']=True
            with self.assertRaises(ValueError,msg=kind):k.validate(source,bad,Counter())

    def test_overlay_preserves_the_remaining_row(self):
        binding=s.base.load(s.PARENT/'checkpoint.json')['conditioned_saturation']['remaining'];rows=s.rows()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay.json';s.compact(path,dict(parent=binding,excluded=[[61,0],[67,0]]))
            self.assertEqual(s.load_frontier(s.old.binding(path)),[r for r in rows if (r['target'],r['event'])==(61,50)])
            for excluded in ([[61,0],[61,0]],[[999,0]]):
                s.compact(path,dict(parent=binding,excluded=excluded))
                with self.assertRaises(ValueError):s.load_frontier(s.old.binding(path))


if __name__=='__main__':unittest.main()
