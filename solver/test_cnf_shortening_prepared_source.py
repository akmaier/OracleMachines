from collections import Counter
from copy import deepcopy
from dataclasses import FrozenInstanceError
from itertools import product
from pathlib import Path
from unittest.mock import patch
import ast,random,tempfile,unittest
from experiments import cnf_shortening_prepared_source as prepared
from experiments import cnf_shortening_clause_filters as control
from experiments import cnf_guard_shortening_context as frozen
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import check_template,transport
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_guard_shortening import chain


class PreparedSourceTests(unittest.TestCase):
    def test_discovery_changes_only_source_and_state_preparation(self):
        text=Path(prepared.__file__).read_text()
        text=text.replace('prepared=PreparedSource.prepare(source,templates,counts);','source=frozen._source(source,templates,counts);')
        text=text.replace('state=prepared.state(fixed,counts);','state=frozen._state(source,templates,fixed,counts);')
        def discovery(text):
            return ast.dump(next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='discover'),include_attributes=False)
        self.assertEqual(discovery(text),discovery(Path(control.__file__).read_text()))
        self.assertIs(prepared.compile_program,frozen.compile_program)
        self.assertIs(prepared.validate,frozen.validate)

    def test_all_assignments_have_exact_current_binding(self):
        source,ts=chain();owned=prepared.PreparedSource.prepare(source,ts,Counter())
        for bits in product((None,False,True),repeat=6):
            fixed={i+1:b for i,b in enumerate(bits) if b is not None}
            c=Counter();actual=owned.state(fixed,c)
            expected=frozen._state(source,ts,fixed,Counter())
            self.assertEqual(actual,expected)
            self.assertEqual(c['templates_checked'],c['verified_core_hints'])
        source=((-2,1),(-1,3),(1,))
        ts=[dict(clauses=[list(cl) for cl in source],assumptions=[[3,False]],trace=[[1,2]],conflict=1)]
        owned=prepared.PreparedSource.prepare(source,ts,Counter())
        self.assertEqual(owned.state({1:True},Counter()),frozen._state(source,ts,{1:True},Counter()))

    def test_caller_edits_cannot_change_owned_preparation(self):
        source,ts=chain();source=[list(cl) for cl in source]
        owned=prepared.PreparedSource.prepare(source,ts,Counter());expected=owned.state({},Counter())
        source[0][0]=999;ts[0]['clauses'][0][0]=999;ts[0]['trace'].clear();ts[0]['assumptions'][0][1]=False;ts.clear()
        self.assertEqual(owned.state({},Counter()),expected)
        with self.assertRaises(FrozenInstanceError):owned.source=()
        with self.assertRaises(TypeError):owned.templates[0]['conflict']=999
        with self.assertRaises(TypeError):owned.templates[0]['clauses'][0][0]=999
        a=owned.state({},Counter());a['hints'][0]['template']['clauses'].clear()
        self.assertEqual(owned.state({},Counter()),expected)

    def test_assignment_and_cofactor_checks_are_not_cached(self):
        source,ts=chain();owned=prepared.PreparedSource.prepare(source,ts,Counter())
        for fixed in ({True:False},{1:0},{0:True},{999:False}):
            with self.assertRaises(ValueError):owned.state(fixed,Counter())
        # The transported-template checker and exact-position RUP checker still
        # execute on every compatible cofactor, including a repeated assignment.
        for name in ('check_template','check_bound_rup'):
            with patch('experiments.cnf_shortening_transport.'+name,side_effect=ValueError('cofactor check')):
                with self.assertRaisesRegex(ValueError,'cofactor check'):owned.state({},Counter())

    def test_bad_support_or_trace_fails_before_search(self):
        source,ts=chain()
        for key in ('clauses','trace','conflict','assumptions'):
            bad=deepcopy(ts)
            if key=='clauses':bad[0][key][0]=[999]
            elif key=='trace':bad[0][key][0][1]=999
            elif key=='conflict':bad[0][key]=999
            else:bad[0][key][0][1]=0
            with self.assertRaises(ValueError):prepared.discover(source,bad,Counter())
        with self.assertRaises(ValueError):prepared.discover(((2,),),[],Counter())

    def test_exact_programs_and_counted_removed_work(self):
        for depth in (1,2,4,8):
            for padding in (0,8,64):
                source,ts=chain(depth,padding);static=Counter();native.normalize(source,static)
                for t in ts:check_template(t,static)
                for order in ('priority','numeric'):
                    for filters in ('endpoint','weak'):
                        a=Counter();b=Counter()
                        self.assertEqual(control.discover(source,ts,a,order=order,filters=filters),prepared.discover(source,ts,b,order=order,filters=filters))
                        removed=Counter({k:v*b['rounds'] for k,v in static.items()})
                        for k in ('source_preparations','prepared_templates','prepared_input_slots'):b.pop(k,None)
                        b.update(removed);self.assertEqual(a,b)

    def test_exhaustive_deletions_and_random_truth(self):
        source,ts=chain();cases=[]
        for mask in range(256):
            subset=tuple(cl for i,cl in enumerate(source) if mask>>i&1)
            local,names=native.normalize(subset)
            templates=[transport(t,{v:i+1 for i,v in enumerate(names)}) for t in ts if set(map(tuple,t['clauses']))<=set(subset)]
            cases.append((local,templates))
        rng=random.Random(242227)
        for _ in range(100):
            local=native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,7),rng.randrange(1,5))] for _ in range(20)])[0]
            cases.append((local,[]))
        for source,ts in cases:
            actual=prepared.discover(source,ts,Counter(),filters='endpoint')
            self.assertEqual(actual,control.discover(source,ts,Counter(),filters='endpoint'))
            if actual['status']=='refuted':
                self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=6)))

    def test_limits_and_independent_native_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            paths=[Path(td)/str(i) for i in range(2)]
            for padding in (4,16,64):
                source,ts=chain(4,padding);tables=[]
                for module,path in zip((control,prepared),paths):
                    p=module.discover(source,ts,Counter());s=native.ResidualSolver(path)
                    try:
                        before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'));c=Counter()
                        root=module.compile_program(s,source,ts,p,c)
                        after=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'));tables.append(after)
                        self.assertTrue(all(after[k]==v for k,v in before.items()))
                        if padding>4:self.assertEqual(len(after)-len(before),1);self.assertEqual(c['support_hits'],1)
                    finally:s.close()
                    r=CanonicalVerifySnapshot(path)
                    try:self.assertFalse(r._read(root)['answer'])
                    finally:r.close()
                self.assertEqual(*tables)
        for kw in ({'edge_limit':1},{'root_limit':1},{'round_limit':1},{'path_limit':1}):
            self.assertEqual(prepared.discover(source,ts,Counter(),**kw),control.discover(source,ts,Counter(),**kw))


if __name__=='__main__':unittest.main()
