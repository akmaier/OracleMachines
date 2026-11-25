from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_wide_guard_probes as probes
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments import cnf_shortening_prepared_source as binary
from solver.test_cnf_guard_shortening import chain


def fixture():
    support=((2,3,4,-5),(2,3,4,5))
    source=native.normalize(list(support)+[(-1,-2),(-1,-3),(1,7),(1,-7),(-4,6),(-4,-6)])[0]
    support=tuple(sorted(tuple(sorted(cl)) for cl in support))
    template=conditional_unit(support,[[2,False],[3,False],[4,False]],Counter())
    return source,[template]


class WideGuardProbeTests(unittest.TestCase):
    def test_wider_guard_adds_joint_propagation(self):
        source,ts=fixture();a=probes.discover(source,ts,Counter(),mode='source');b=probes.discover(source,ts,Counter(),mode='binary');c=Counter();p=probes.discover(source,ts,c)
        self.assertEqual(a['status'],'unresolved');self.assertEqual(b['status'],'unresolved');self.assertEqual(p['status'],'refuted')
        self.assertEqual(c['probe_index_builds'],1);self.assertGreater(c['unit_probes'],1)
        for program in (a,b,p):probes.validate(source,ts,program,Counter())
        self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=7)))

    def test_native_publication_warm_and_cold(self):
        source,ts=fixture();p=probes.discover(source,ts,Counter())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';s=native.ResidualSolver(path)
            try:
                root=probes.compile_program(s,source,ts,p,Counter());before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                self.assertEqual(root,probes.compile_program(s,source,ts,p,Counter()))
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()
            r=CanonicalVerifySnapshot(path)
            try:self.assertFalse(r._read(root)['answer'])
            finally:r.close()

    def test_index_matches_scan_unit_closure_on_random_inputs(self):
        rng=random.Random(242502)
        for _ in range(180):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(16)])[0]
            idx=probes.UnitIndex(source,Counter());variables=sorted({abs(l) for cl in source for l in cl})
            for assumption in [None]+[s*v for v in variables for s in (-1,1)]:
                c=Counter();proof=idx.probe(assumption,c,lambda:100000,256)
                restricted=native.restrict_scan(source,{} if assumption is None else {abs(assumption):assumption>0},Counter())
                _,trace,conflict=native.propagate(restricted,Counter())
                self.assertEqual(proof is not None,conflict is not None)
                if proof is not None:probes.check_trace(source,source,assumption,proof,Counter(),256)

    def test_random_programs_against_exhaustive_truth(self):
        rng=random.Random(242503)
        for _ in range(100):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(18)])[0]
            p=probes.discover(source,[],Counter());probes.validate(source,[],p,Counter())
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=5)];models=[m for m in models if native.holds(source,m)]
            for row in p['probes']:self.assertTrue(all(m[abs(row['assumption'])]!=(row['assumption']>0) for m in models))
            if p['status']=='refuted':
                self.assertFalse(models);s=native.ResidualSolver()
                try:self.assertFalse(s._read(probes.compile_program(s,source,[],p,Counter()))['answer'])
                finally:s.close()

    def test_bad_provenance_trace_and_terminal_rejected_before_write(self):
        source,ts=fixture();p=probes.discover(source,ts,Counter())
        for kind in ('support','trace','opposite'):
            templates=deepcopy(ts);bad=deepcopy(p)
            if kind=='support':templates[0]['clauses'][0]=[999]
            elif kind=='trace':bad['probes'][0]['proof']['conflict']=999
            else:bad['terminal']['high']=bad['terminal']['low']
            s=native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):probes.compile_program(s,source,templates,bad,Counter())
                self.assertEqual(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],0)
            finally:s.close()

    def test_limits_return_only_unresolved_and_preserve_valid_prefixes(self):
        source,ts=fixture()
        for kw in ({'probe_limit':1},{'work_limit':1},{'trace_limit':1}):
            c=Counter();p=probes.discover(source,ts,c,**kw);self.assertEqual(p['status'],'unresolved');probes.validate(source,ts,p,Counter())
            self.assertLessEqual(c['probe_occurrence_visits'],kw.get('work_limit',262144))
            s=native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):probes.compile_program(s,source,ts,p,Counter())
                self.assertEqual(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],0)
            finally:s.close()

    def test_empty_source_empty_clause_and_unconditional_units(self):
        for source,expected in (((),False),(((),),True),(((-1,),(1,)),True)):
            source=native.normalize(source)[0];p=probes.discover(source,[],Counter());self.assertEqual(p['status']=='refuted',expected)
            probes.validate(source,[],p,Counter())
            if expected:
                s=native.ResidualSolver()
                try:self.assertFalse(s._read(probes.compile_program(s,source,[],p,Counter()))['answer'])
                finally:s.close()

    def test_extension_replays_binary_prefix_before_native_lift(self):
        source,ts=chain(4,8);complete=binary.discover(source,ts,Counter())
        # Replay a valid partial certificate stopping before the binary terminal;
        # this does not assert that one-pass probing closes a multi-round chain.
        prefix=dict(complete,status='unresolved',reason='partial',terminal=None)
        frames,state=probes.bind_prefix(source,ts,prefix,Counter())
        p=probes.discover(state['local'],[h['template'] for h in state['hints']],Counter())
        self.assertEqual(p['status'],'refuted');s=native.ResidualSolver()
        try:self.assertFalse(s._read(probes.compile_extension(s,source,ts,prefix,p,Counter()))['answer'])
        finally:s.close()


if __name__=='__main__':unittest.main()
