from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover,compile_cover
from experiments.cnf_guard_cover_support import select_support,compile_support_cover
from experiments.cnf_guard_cover_cases import family
from experiments.cnf_conditional_unit_support import transport
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


def padded(width=3, amount=8):
    source,_,hints,graph,model=family(width)
    source=native.normalize(list(source)+[[1,4*width+i+1] for i in range(amount)])[0]
    return source,hints,graph,discover(source,graph,model,Counter())


class GuardCoverSupportTests(unittest.TestCase):
    def test_subset_wrapper_and_shared_variables(self):
        source,hints,graph,cover=padded();s=native.ResidualSolver();self.addCleanup(s.close);c=Counter()
        root=compile_support_cover(s,source,hints,graph,cover,c)
        node=s._read(root);self.assertFalse(node['answer']);self.assertEqual(node['proof']['kind'],'component')
        subset=tuple(source[i] for i in node['proof']['clauses'])
        self.assertEqual(len(subset),13);self.assertGreater(len(source),len(subset))
        self.assertIn(1,{abs(l) for cl in source if cl not in subset for l in cl})
        self.assertEqual(c['support_root_publications'],1);self.assertEqual(c['support_wrappers'],1)

    def test_full_support_fallback_and_exact_repeat(self):
        source,_,hints,graph,model=family();cover=discover(source,graph,model,Counter())
        s=native.ResidualSolver();self.addCleanup(s.close);c=Counter()
        root=compile_support_cover(s,source,hints,graph,cover,c)
        self.assertEqual(c['full_support_fallbacks'],1);c=Counter()
        self.assertEqual(compile_support_cover(s,source,hints,graph,cover,c),root)
        self.assertEqual(c['enclosing_root_hits'],1);self.assertEqual(c['published_nodes'],0)

    def test_new_context_reuses_persistent_support_after_cold_open(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';first=padded(amount=4);s=native.ResidualSolver(path)
            try:root=compile_support_cover(s,*first,Counter());child=s._read(root)['proof']['child']
            finally:s.close()
            s=native.ResidualSolver(path)
            try:
                before=s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0];c=Counter()
                second=compile_support_cover(s,*padded(amount=17),c)
                self.assertEqual(c['support_root_hits'],1);self.assertEqual(c['published_nodes'],0)
                self.assertEqual(s._read(second)['proof']['child'],child)
                self.assertEqual(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],before+1)
            finally:s.close()
            reader=CanonicalVerifySnapshot(path)
            try:self.assertFalse(reader._read(second)['answer'])
            finally:reader.close()

    def test_sparse_support_coordinates_and_signed_renamings(self):
        rng=random.Random(202611241719)
        for _ in range(12):
            source,hints,graph,cover=padded(amount=6);n=18;names=list(range(1,n+1));rng.shuffle(names)
            mapping={v:names[v-1]*rng.choice((-1,1)) for v in range(1,n+1)}
            def lit(l):return mapping[abs(l)]*(1 if l>0 else -1)
            changed=native.normalize([[lit(l) for l in cl] for cl in source])[0]
            hs=[dict(template=transport(h['template'],mapping),clause=sorted(lit(l) for l in h['clause'])) for h in hints]
            gs=sorted(tuple(h['clause']) for h in hs);model,proof=native.two_cnf(gs,Counter());self.assertIsNone(proof)
            cv=discover(changed,gs,model,Counter());self.assertIsNotNone(cv)
            s=native.ResidualSolver()
            try:self.assertFalse(s._read(compile_support_cover(s,changed,hs,gs,cv,Counter()))['answer'])
            finally:s.close()

    def test_bad_evidence_is_rejected_before_any_publication(self):
        source,hints,graph,cover=padded();variants=[]
        bad=deepcopy(cover);bad['clause_index']=-1;variants.append((source,hints,graph,bad))
        bad=deepcopy(cover);bad['paths'][0][0][1]=True;variants.append((source,hints,graph,bad))
        variants.append((source,hints[1:],graph,cover))
        bad=deepcopy(hints);bad[0]['template']['trace'][0][1]=100000;variants.append((source,bad,graph,cover))
        removed=tuple(cl for cl in source if cl!=tuple(hints[0]['template']['clauses'][0]))
        bad=deepcopy(cover);bad['clause_index']=removed.index(tuple(cover['clause']));variants.append((removed,hints,graph,bad))
        for args in variants:
            s=native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):compile_support_cover(s,*args,Counter())
                self.assertEqual(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],0)
            finally:s.close()

    def test_changed_wrapper_indices_cannot_reuse_an_unrelated_subset(self):
        source,hints,graph,cover=padded();s=native.ResidualSolver();self.addCleanup(s.close)
        root=compile_support_cover(s,source,hints,graph,cover,Counter());bad=deepcopy(s._read(root))
        bad['proof']['clauses']=[i for i,cl in enumerate(source) if len(cl)==2]
        with self.assertRaises(ValueError):s._verify(root,bad)

    def test_original_edges_and_all_signed_wide_clauses(self):
        universe=[(-2,-1),(-1,2),(-3,-2),(-2,3),(-3,-1),(-3,1)];found=0
        for mask in range(64):
            graph=tuple(sorted(cl for i,cl in enumerate(universe) if mask>>i&1))
            model,proof=native.two_cnf(graph,Counter())
            if model is None or proof is not None:continue
            for signs in product((-1,1),repeat=3):
                wide=tuple(sorted(s*v for v,s in enumerate(signs,1)))
                source=native.normalize(graph+(wide,(1,4)))[0]
                cover=discover(source,graph,model,Counter())
                if cover is None:continue
                found+=1;s=native.ResidualSolver()
                try:self.assertFalse(s._read(compile_support_cover(s,source,[],graph,cover,Counter()))['answer'])
                finally:s.close()
                self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4)))
        self.assertGreater(found,0)

    def test_irrelevant_assumption_coordinate_falls_back_safely(self):
        # An inconsistent support entails clauses with an irrelevant variable.
        source=native.normalize([[-1],[1],[2,3,4],[5,6]])[0]
        hints=[dict(clause=sorted([-v]),template=dict(clauses=[[-1],[1]],assumptions=[[v,True]],trace=[[-1,0]],conflict=1)) for v in (2,3,4)]
        graph=[(-4,),(-3,),(-2,)];model,proof=native.two_cnf(graph,Counter())
        cover=discover(source,graph,model,Counter());self.assertIsNotNone(cover)
        # Include intermediate variable 5 not in the source support through
        # weakened binary consequences; the actual wide clause keeps 2,3,4.
        hints=[dict(clause=cl,template=dict(clauses=[[-1],[1]],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[[-1,0]],conflict=1))
               for cl in ([-2,5],[-5,-2],[-3],[-4])]
        graph=sorted(tuple(h['clause']) for h in hints)
        cover=dict(clause_index=source.index((2,3,4)),clause=[2,3,4],paths=[[[5,graph.index((-2,5))],[-2,graph.index((-5,-2))]],
                 [[-3,graph.index((-3,))]],[[-4,graph.index((-4,))]]])
        c=Counter();s=native.ResidualSolver();self.addCleanup(s.close)
        self.assertFalse(s._read(compile_support_cover(s,source,hints,graph,cover,c))['answer'])
        self.assertEqual(c['absent_coordinate_fallbacks'],1)


if __name__=='__main__':unittest.main()
