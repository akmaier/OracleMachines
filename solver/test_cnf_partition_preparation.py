from collections import Counter
from copy import deepcopy
from dataclasses import FrozenInstanceError,fields,replace
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,unittest
from experiments import cnf_partition_preparation as new,cnf_clause_partition as original
from experiments.cnf_probed_partition import run as old_run
from experiments.cnf_transported_partition import native_query
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import normalize,holds


def rows(s):return list(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))


class PartitionPreparationTests(unittest.TestCase):
    def solver(self,**kw):
        s=InputSafeAffineProbeSolver(**kw);self.addCleanup(s.close);return s
    def candidate(self,s,source):
        core=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
        root=native_query(s,core,256)['root'];cnf,names=normalize(source)
        return dict(origin=root,origin_names=list(normalize(core)[1]),target=[list(c) for c in cnf],target_names=list(names))
    def complete(self,s,source,missing):
        core=source+missing;root=native_query(s,core,256)['root'];p=new.prepare(source,missing,Counter())
        _,premise=new.publish_prepared(s,p,dict(source=core,root=root),Counter());children=[]
        for _,_,child in p.branches:
            r=native_query(s,child,256);children.append(r)
            if r['answer']:break
        return p,premise,children

    def test_immutable_inputs_and_shared_prefixes(self):
        source=[[30,10,10],[-30,20]];missing=[[20,-10],[-20,10]];saved=deepcopy((source,missing))
        p=new.prepare(source,missing,Counter());ordered,branches=original.branch_sources(*saved)
        source[0][0]=999;missing[0][0]=999
        self.assertEqual(p.source,tuple(map(tuple,saved[0])));self.assertEqual(p.ordered,tuple(map(tuple,ordered)))
        with self.assertRaises(FrozenInstanceError):p.source=()
        for a,b in zip(p.branches,branches):
            self.assertEqual(a[0],tuple(map(tuple,b[0])));self.assertEqual(dict(a[1]),b[1]);self.assertEqual(a[2],b[2])
            self.assertIs(a[0][0],p.source[0])

    def test_invalid_missing_and_literal_inputs_rejected(self):
        for source,missing in [([[1,2]],[]),([[1,2]],((1,),)),([[1,2]],[[1,2]]),([[1,2]],[[1],[1]]),
            ([[1,2]],[[]]),([[1,2]],[[3]]),([[1,2]],[[1,-1]]),([[True,2]],[[1]]),([[1.0,2]],[[1]]),([[0,2]],[[2]]),([[1,2]],[[True]])]:
            with self.assertRaises(ValueError):new.prepare(source,missing,Counter())

    def test_prefixes_are_exact_first_false_regions(self):
        source=[[1,2],[-1,3]];missing=[[-2,3],[1,-3],[-1,-2]]
        for order in (missing,list(reversed(missing))):
            p=new.prepare(source,order,Counter())
            for bits in product((False,True),repeat=3):
                model=dict(zip((1,2,3),bits));selected=[]
                for i,(prefix,fixed,child) in enumerate(p.branches):
                    matches=all(model[v]==b for v,b in fixed)
                    if matches and holds(child,model):selected.append(i)
                    self.assertEqual(matches and holds(prefix,model),matches and holds(child,model))
                whole=holds(source,model);all_missing=holds(order,model)
                self.assertEqual(len(selected),int(whole and not all_missing))
                if selected:self.assertEqual(selected[0],next(i for i,c in enumerate(order) if not holds([c],model)))

    def test_sat_and_unsat_records_identical_and_independently_checked(self):
        for source,missing in [([[1,2],[-1,-2]],[[1,-2],[-1,2]]),([[1],[-1],[2,3]],[[2],[-2]])]:
            s=self.solver();p,root,children=self.complete(s,source,missing)
            expected=original.make_record(s,source,[],missing,root,children)
            with patch.object(original,'branch_sources',wraps=original.branch_sources) as check:
                actual=new.make_prepared_record(s,p,root,children)
            self.assertEqual(actual,expected);self.assertEqual(check.call_count,1)
            if actual['answer']:self.assertTrue(holds(source,actual['model']))

    def test_sidecar_tampering_and_stale_dependencies_rejected(self):
        s=self.solver();source=[[1],[-1],[2,3]];missing=[[2],[-2]];p,root,children=self.complete(s,source,missing)
        record=new.make_prepared_record(s,p,root,children)
        for field,value in [('source',[[1,2,3]]),('missing_clauses',list(reversed(missing))),('stronger_root','absent'),('children',record['children'][:1]),('answer',True)]:
            bad=deepcopy(record);bad[field]=value
            with self.assertRaises(ValueError):original.check_record(s,bad)
        with patch.object(s,'_read',return_value=None):
            with self.assertRaises(ValueError):new.make_prepared_record(s,p,root,children)
        other=replace(p,source=((1,2,3),))
        with self.assertRaises(ValueError):new.make_prepared_record(s,other,root,children)

    def test_premise_requires_exact_core_and_checked_negative(self):
        s=self.solver();p=new.prepare([[1,2]],[[1],[-1]],Counter())
        with self.assertRaises(ValueError):new.publish_prepared(s,p,dict(source=[[1],[-1]],root='absent'),Counter())
        with patch.object(s,'_read',return_value={'answer':True}):
            with self.assertRaises(ValueError):new.publish_prepared(s,p,dict(source=[[1,2],[1],[-1]],root='absent'),Counter())
        with patch.object(s,'_read',return_value=None):
            with self.assertRaises(ValueError):new.publish_prepared(s,p,dict(source=[[1,2],[1],[-1]],root='absent'),Counter())

    def test_retained_size_conservatively_bounds_shared_graph(self):
        def size(obj,seen):
            if id(obj) in seen:return 0
            seen.add(id(obj));n=sys.getsizeof(obj)
            if isinstance(obj,new.Preparation):n+=sum(size(getattr(obj,f.name),seen) for f in fields(obj))
            elif isinstance(obj,(tuple,frozenset)):n+=sum(size(x,seen) for x in obj)
            return n
        for v in (3,2**150):
            counts=Counter();p=new.prepare([[1,2,v],[-v,2]],[[1],[-1],[2]],counts)
            self.assertLessEqual(size(p,set()),counts['partition_prepared_charge'])
            self.assertEqual(counts['partition_branches_built'],3)

    def test_policy_matches_baseline_and_builds_once_plus_checker(self):
        for source in ([[-3,-2,-1],[1,2,3]],[[1,2,3]],[[1],[-1],[2,3]]):
            a=self.solver();b=self.solver();ca=self.candidate(a,source);cb=self.candidate(b,source)
            x=old_run(a,ca,'reverse6')
            with patch.object(original,'branch_sources',wraps=original.branch_sources) as checker:
                y=new.run(b,cb,'reverse6')
            for k in ('status','result','partition','expanded_nodes'):
                if k=='result':self.assertEqual(x[k]['answer'],y[k]['answer'])
                else:self.assertEqual(x[k],y[k])
            self.assertEqual(rows(a),rows(b))
            if y['partition'] is not None:self.assertEqual(checker.call_count,1)

    def test_budget_exception_and_cold_replay(self):
        source=[[-3,-2,-1],[1,2,3]]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=InputSafeAffineProbeSolver(path)
            try:
                c=self.candidate(s,source);r=new.run(s,c,'reverse6',0)
                self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['partition'])
                with patch.object(new,'make_prepared_record',side_effect=RuntimeError('injected')):
                    with self.assertRaisesRegex(RuntimeError,'injected'):new.run(s,c,'reverse6')
                r=new.run(s,c,'reverse6');keys=[k for k,v in rows(s)]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(reader._read(key))
                    with patch.object(reader,'_expand',side_effect=AssertionError('Unexpected cold expansion')):original.check_record(reader,r['partition'])
                finally:reader.close()

    def test_exhaustive_small_inputs_match_truth_and_payloads(self):
        clauses=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
        a=self.solver();b=self.solver()
        for mask in range(1,255):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            ca=self.candidate(a,source);cb=self.candidate(b,source)
            x=old_run(a,ca,'reverse6');y=new.run(b,cb,'reverse6')
            self.assertEqual(x['partition'],y['partition']);self.assertEqual(x['expanded_nodes'],y['expanded_nodes'])
            expected=any(holds(source,dict(zip((1,2,3),bits))) for bits in product((False,True),repeat=3))
            self.assertEqual(y['result']['answer'],expected)
        self.assertEqual(rows(a),rows(b))


if __name__=='__main__':unittest.main()
