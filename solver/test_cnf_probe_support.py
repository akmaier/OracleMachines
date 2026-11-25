from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import cnf_probe_support as compact
from experiments import cnf_complement_probes as probes
from experiments import cnf_residual_dag as native
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_conditional_unit_support import transport
from experiments import cnf_shortening_prepared_source as binary
from solver.test_cnf_wide_guard_probes import fixture
from solver.test_cnf_guard_shortening import chain


class ProbeSupportTests(unittest.TestCase):
    def test_selected_guard_support_and_both_cold_readers(self):
        source,ts=fixture();source=native.normalize(list(source)+[(8,9),(9,10),(10,11)])[0]
        p=probes.discover(source,ts,Counter());c=Counter();plan=compact.prepare_support(source,ts,p,c)
        self.assertLess(len(plan['indices']),len(source))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';s=native.ResidualSolver(path)
            try:
                root=compact.compile_program(s,source,ts,p,c);self.assertFalse(s._read(root)['answer'])
                self.assertEqual(s._read(root)['proof']['kind'],'component')
                before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                self.assertEqual(root,compact.compile_program(s,source,ts,p,c))
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path)
                try:self.assertFalse(r._read(root)['answer'])
                finally:r.close()

    def test_causal_slice_discards_unneeded_units(self):
        source=native.normalize([(1,),(2,),(-2,3),(-3,)])[0]
        p=probes.discover(source,[],Counter());c=Counter();plan=compact.prepare_support(source,[],p,c)
        self.assertLess(c['support_trace_kept'],c['support_trace_steps'])
        self.assertNotIn(source.index((1,)),plan['indices'])
        s=native.ResidualSolver()
        try:self.assertFalse(s._read(compact.compile_program(s,source,[],p,Counter()))['answer'])
        finally:s.close()

    def test_independent_branch_removes_absent_split_coordinate(self):
        source=native.normalize([(1,),(-1,),(2,3)])[0];_,_,clauses,_=compact.frozen.prepare(source,[],'all',Counter());idx=compact.frozen.UnitIndex(clauses,Counter())
        rows=[dict(assumption=l,proof=idx.probe(l,Counter(),lambda:9999,256)) for l in (-2,2)]
        p=dict(status='refuted',reason='opposite_probes',mode='all',probes=rows,terminal=dict(low=0,high=1),trace_limit=256)
        c=Counter();plan=compact.prepare_support(source,[],p,c)
        self.assertEqual(plan['program']['reason'],'units');self.assertEqual(c['support_independent_branch'],1)
        s=native.ResidualSolver()
        try:self.assertFalse(s._read(compact.compile_program(s,source,[],p,Counter()))['answer'])
        finally:s.close()

    def test_random_refutations_match_truth(self):
        rng=random.Random(242506);compiled=0
        for _ in range(180):
            source=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(18)])[0]
            p=probes.discover(source,[],Counter())
            if p['status']!='refuted':continue
            self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=5)))
            s=native.ResidualSolver()
            try:self.assertFalse(s._read(compact.compile_program(s,source,[],p,Counter()))['answer'])
            finally:s.close()
            compiled+=1
        self.assertGreater(compiled,50)

    def test_signed_guards_and_source_renaming(self):
        rng=random.Random(242507);source,ts=fixture()
        for _ in range(12):
            names=list(range(1,8));rng.shuffle(names);mapping={v:n*rng.choice((-1,1)) for v,n in enumerate(names,1)}
            changed=native.normalize([[mapping[abs(l)]*(1 if l>0 else -1) for l in cl] for cl in source])[0]
            templates=[transport(t,mapping) for t in ts];p=probes.discover(changed,templates,Counter());s=native.ResidualSolver()
            try:self.assertFalse(s._read(compact.compile_program(s,changed,templates,p,Counter()))['answer'])
            finally:s.close()

    def test_invalid_original_program_rejected_even_after_root_cached(self):
        source,ts=fixture();p=probes.discover(source,ts,Counter());s=native.ResidualSolver()
        try:
            compact.compile_program(s,source,ts,p,Counter());before=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
            for kind in ('trace','support','opposite','unresolved'):
                bad=deepcopy(p);templates=deepcopy(ts)
                if kind=='trace':bad['probes'][0]['proof']['conflict']=99999
                elif kind=='support':templates[0]['clauses'][0]=[99999]
                elif kind=='opposite':bad['terminal']['high']=bad['terminal']['low']
                else:bad.update(status='unresolved',reason='probe_limit',terminal=None)
                with self.assertRaises(ValueError):compact.compile_program(s,source,templates,bad,Counter())
                self.assertEqual(before,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))
        finally:s.close()

    def test_binary_prefix_and_empty_terminal(self):
        source,ts=chain(4,8);prefix=dict(binary.discover(source,ts,Counter()),status='unresolved',reason='partial',terminal=None)
        _,state=compact.frozen.bind_prefix(source,ts,prefix,Counter());p=probes.discover(state['local'],[h['template'] for h in state['hints']],Counter());s=native.ResidualSolver()
        try:self.assertFalse(s._read(compact.compile_extension(s,source,ts,prefix,p,Counter()))['answer'])
        finally:s.close()
        source=((),);p=probes.discover(source,[],Counter());s=native.ResidualSolver()
        try:self.assertFalse(s._read(compact.compile_program(s,source,[],p,Counter()))['answer'])
        finally:s.close()


if __name__=='__main__':unittest.main()
