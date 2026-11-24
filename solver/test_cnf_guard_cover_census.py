from collections import Counter
from itertools import product
import unittest
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover,compile_cover
from experiments.cnf_guard_cover_cases import family
from experiments.cnf_guard_cover_observer import CoverObserver
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_interactions import local_hints


class GuardCoverCensusTests(unittest.TestCase):
    def test_observer_preserves_decision_and_restores_hook(self):
        source,templates,_,_,_=family();original=native.two_cnf
        for cls in (ContextGuardClosureSolver,CoverObserver):
            s=cls(templates=templates);self.addCleanup(s.close)
            s.guard_source=source;s.closure_counts=Counter();s.closure_records=None
            s.guard_parents=[dict(cnf=source,mapping={v:v for v in range(1,13)},fixed={})]
            self.assertIsNone(s._guard_closure(source));self.assertIs(native.two_cnf,original)
            if cls is CoverObserver:
                self.assertEqual(len(s.cover_events),1)
                self.assertIsNotNone(s.cover_events[0]['cover'])
                self.assertFalse(s.cover_events[0]['site_closed'])
                with patch('experiments.cnf_guard_cover_observer.discover',side_effect=RuntimeError('probe failure')):
                    with self.assertRaises(RuntimeError):s._guard_closure(source)
                self.assertIs(native.two_cnf,original)

    def test_overlapping_learned_paths_under_stronger_prefixes(self):
        # Encode graph edges with independent auxiliaries. Paths share wide-clause
        # variables, so prior false assignments alter later path supports.
        universe=[(-1,2),(-1,-2),(-2,3),(-2,-3),(-3,1),(-3,-1)];found=0
        for mask in range(64):
            binary=[tuple(sorted(universe[i])) for i in range(6) if mask>>i&1]
            if len(binary)<3:continue
            graph_model,proof=native.two_cnf(binary,Counter())
            if graph_model is None or proof is not None:continue
            gadgets=[tuple(sorted(tuple(sorted(cl+(sign*(4+i),))) for sign in (-1,1))) for i,cl in enumerate(binary)]
            ts=[conditional_unit(g,[[abs(l),l<0] for l in cl],Counter()) for g,cl in zip(gadgets,binary)]
            for signs in product((-1,1),repeat=3):
                wide=tuple(sorted(sign*v for v,sign in enumerate(signs,1)))
                source=native.normalize([cl for g in gadgets for cl in g]+[wide])[0]
                event=dict(root=native.token(source,Counter()),mapping=[[v,v] for v in range(1,len(binary)+4)],fixed=[])
                _,hints,_=local_hints(source,ts,event,Counter())
                graph=sorted(tuple(h['clause']) for h in hints)
                cover=discover(source,graph,graph_model,Counter())
                if cover is None:continue
                found+=1;s=native.ResidualSolver()
                try:
                    root=compile_cover(s,source,hints,graph,cover,Counter())
                    self.assertFalse(s._read(root)['answer'])
                    self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=len(binary)+3)))
                finally:s.close()
        self.assertGreater(found,0)


if __name__=='__main__':unittest.main()
