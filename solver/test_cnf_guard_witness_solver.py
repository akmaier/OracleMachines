from collections import Counter
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_witness_solver import WitnessGuardClosureSolver
from experiments.cnf_guard_closure_solver import GuardClosureSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class WitnessGuardTests(unittest.TestCase):
    def fixtures(self, clauses):
        n=max(abs(l) for cl in clauses for l in cl)
        gadgets=[tuple(sorted(tuple(sorted(list(cl)+[sign*(n+i+1)])) for sign in (-1,1)))
                 for i,cl in enumerate(clauses)]
        source=tuple(sorted(cl for g in gadgets for cl in g))
        ts=[conditional_unit(g,[[abs(l),l<0] for l in cl],Counter()) for g,cl in zip(gadgets,clauses)]
        return source,gadgets,ts

    def prepared(self, source, templates, raw=None, **kwargs):
        local,names=native.normalize(source if raw is None else raw)
        s=WitnessGuardClosureSolver(templates=templates,**kwargs)
        s.guard_source=source;s.closure_counts=Counter();s.closure_records=None
        s.guard_parents=[dict(cnf=local,mapping=dict(enumerate(names,1)),fixed={})]
        return s,local

    def publish(self,s,local,proof):
        key=s._canonical(local)[2]
        s._store(key,dict(format=native.FORMAT,cnf=list(map(list,local)),answer=False,proof=proof))
        self.assertFalse(s._read(key)['answer'])

    def test_satisfiable_graph_needs_no_support_transport(self):
        source,_,ts=self.fixtures([[1,2],[1,-2]])
        s,local=self.prepared(source,ts)
        try:
            with patch('experiments.cnf_guard_witness_solver.transport_short',side_effect=AssertionError('Unneeded transport')):
                self.assertIsNone(s._guard_closure(local))
            self.assertEqual(s.closure_counts['witness_support_checks'],0)
            self.assertGreater(s.closure_counts['tentative_satisfiable_graphs'],0)
        finally:s.close()

    def test_binary_paths_publish_actual_source_refutation(self):
        source,_,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        s,local=self.prepared(source,ts)
        try:
            self.publish(s,local,s._guard_closure(local))
            self.assertEqual(s.closure_counts['closed_binary_guards'],1)
        finally:s.close()

    def test_missing_support_invalidates_tentative_contradiction(self):
        source,gadgets,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        raw=tuple(cl for g in gadgets[:-1] for cl in g)
        s,local=self.prepared(source,ts,raw)
        try:
            self.assertIsNone(s._guard_closure(local))
            self.assertGreater(s.closure_counts['local_support_misses'],0)
            self.assertGreater(s.closure_counts['unsupported_witness_retries'],0)
        finally:s.close()

    def test_alternative_support_is_not_lost_with_a_bad_first_proof(self):
        source,gadgets,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2],[1,2]])
        raw=tuple(cl for g in gadgets[1:] for cl in g)
        s,local=self.prepared(source,ts,raw)
        try:
            self.publish(s,local,s._guard_closure(local))
            self.assertEqual(s.closure_counts['local_support_misses'],1)
        finally:s.close()

    def test_all_small_binary_subsets_with_adversarial_extra_candidates(self):
        clauses=[(1,),(-1,),(2,),(-2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        source,gadgets,ts=self.fixtures(clauses)
        for mask in range(256):
            raw=tuple(cl for i,g in enumerate(gadgets) if mask>>i&1 for cl in g)
            selected=[cl for i,cl in enumerate(clauses) if mask>>i&1]
            sat=any(native.holds(selected,dict(enumerate(bits,1))) for bits in product((False,True),repeat=2))
            s,local=self.prepared(source,ts,raw)
            try:
                proof=s._guard_closure(local)
                self.assertEqual(proof is None,sat,mask)
                if proof is not None:self.publish(s,local,proof)
            finally:s.close()

    def test_live_routing_keeps_eager_proof_bytes(self):
        source=native.normalize([[1,2,3],[1,2,-3],[1,-2],[-1,4,5],[-1,4,-5],[-1,-4]])[0]
        ts=[conditional_unit(source,[[1,b]],Counter()) for b in (False,True)]
        old=GuardClosureSolver(templates=ts);new=WitnessGuardClosureSolver(templates=ts)
        try:
            self.assertFalse(old.solve(source)['answer']);self.assertFalse(new.solve(source)['answer'])
            self.assertEqual(new.closure_summary['counts']['closed_opposite_units'],1)
            self.assertEqual(new.guard_summary['pending_end'],0)
            self.assertEqual(old.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall(),
                             new.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall())
        finally:old.close();new.close()

    def test_empty_candidate_requires_local_unit_proof(self):
        source=((-2,),(-1,2),(3,4,5))
        template=conditional_unit(source,[[1,True]],Counter())
        s,local=self.prepared(source,[template],native.restrict_scan(source,{1:True},Counter()))
        s.guard_parents[-1]['fixed']={1:True}
        # The helper's map must use original source names after conditioning.
        try:
            self.publish(s,local,s._guard_closure(local))
            self.assertEqual(s.closure_counts['closed_empty'],1)
        finally:s.close()
        s,local=self.prepared(source,[template],((3,4,5),))
        s.guard_parents[-1]['fixed']={1:True}
        try:
            self.assertIsNone(s._guard_closure(local))
            self.assertEqual(s.closure_counts['closed_empty'],0)
        finally:s.close()

    def test_exhausted_allowances_fall_back(self):
        source,gadgets,ts=self.fixtures([[1,2],[1,-2],[-1,2],[-1,-2]])
        for kwargs in (dict(closure_literals=1),dict(closure_edges=1),dict(path_limit=1)):
            s,local=self.prepared(source,ts,**kwargs)
            try:self.assertIsNone(s._guard_closure(local))
            finally:s.close()
        s,local=self.prepared(source,ts,tuple(cl for g in gadgets[:-1] for cl in g),witness_retries=1)
        try:
            self.assertIsNone(s._guard_closure(local))
            self.assertEqual(s.closure_counts['witness_retry_limit_misses'],1)
        finally:s.close()
        s,local=self.prepared(source,ts,graph_checks=1);s.closure_counts['tentative_graph_checks']=1
        try:
            self.assertIsNone(s._guard_closure(local))
            self.assertEqual(s.closure_counts['graph_limit_misses'],1)
        finally:s.close()

    def test_unlabelled_truth_and_cold_native_replay(self):
        rng=random.Random(202611241213)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'proofs.sqlite3'
            for _ in range(40):
                source=native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(15)])[0]
                ts=[]
                for bits in product((False,True),repeat=3):
                    t=conditional_unit(source,list(map(list,enumerate(bits,1))),Counter())
                    if t is not None:ts.append(t)
                expected=any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4))
                s=WitnessGuardClosureSolver(path,templates=ts,node_limit=1000)
                try:self.assertEqual(s.solve(source)['answer'],expected)
                finally:s.close()
            reader=CanonicalVerifySnapshot(path)
            try:
                for (key,) in reader.db.execute('SELECT id FROM cnf_residual_v1').fetchall():self.assertIsNotNone(reader._read(key))
            finally:reader.close()

    def test_invalid_limits(self):
        for kwargs in (dict(witness_retries=0),dict(witness_retries=True),dict(graph_checks=-1)):
            with self.assertRaises(ValueError):WitnessGuardClosureSolver(**kwargs)


if __name__=='__main__':unittest.main()
