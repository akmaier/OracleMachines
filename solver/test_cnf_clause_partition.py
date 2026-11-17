from copy import deepcopy
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import json,tempfile,unittest
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record,check_record,PartitionBank
from experiments.cnf_clause_deletion_guard import FORMAT as GUARD_FORMAT,check_guard
from experiments.cnf_residual_dag import ResidualSolver,holds


class ClausePartitionTests(unittest.TestCase):
    def solve(self,s,target,missing):
        core=target+missing;hint=dict(source=core,root=s.solve(core)['root'])
        with patch.object(s,'_expand',side_effect=AssertionError('Premise search')):_,root=publish_premise(s,target,hint,missing)
        children=[]
        for _,_,child in branch_sources(target,missing)[1]:
            children.append(s.solve(child))
            if children[-1]['answer']:break
        return make_record(s,target,[],missing,root,children)

    def test_disjoint_cover_exhaustive_two_variable_cnfs(self):
        clauses=[tuple(sorted(sign*(i+1) for i,sign in enumerate(bits) if sign)) for bits in product((-1,0,1),repeat=2)]
        models=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)];seen=set()
        for mask in range(512):
            target=[list(c) for i,c in enumerate(clauses) if mask>>i&1];variables={abs(l) for c in target for l in c}
            absent=[list(c) for c in clauses if c and list(c) not in target and {abs(l) for l in c}<=variables]
            for missing in combinations(absent,2):
                if any(holds(target+list(missing),a) for a in models):continue
                branches=branch_sources(target,list(missing))[1]
                for a in models:
                    hits=[all(a[v]==b for v,b in fixed.items()) and holds(child,a) for _,fixed,child in branches]
                    self.assertEqual(sum(hits),int(holds(target,a)))
                seen.add(any(holds(target,a) for a in models))
        self.assertEqual(seen,{False,True})

    def test_sat_second_branch_counters_simultaneous_falsification(self):
        s=ResidualSolver();self.addCleanup(s.close)
        # T forces y and not z: the first branch is UNSAT, the second SAT.
        target=[[1,2],[-1,2],[-2,-3]];missing=[[2],[3]]
        r=self.solve(s,target,missing);self.assertTrue(r['answer']);self.assertEqual([c['answer'] for c in r['children']],[False,True])
        both={abs(l):l<0 for c in missing for l in c};self.assertFalse(any(holds(target,a) and all(a[v]==b for v,b in both.items()) for a in [dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)]))

    def test_negative_partition_cold_replay_and_normalized_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);target=[[1],[-1],[2,-3]];missing=[[2],[3]]
            try:r=self.solve(s,target,missing)
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Publication')):
                    bank=PartitionBank(s,[json.loads(json.dumps(r))]);self.assertFalse(bank.lookup(target)['answer']);self.assertFalse(bank.lookup([[10*l for l in c] for c in target])['answer'])
            finally:s.close()

    def test_guard_prefix_and_sat_lifting(self):
        s=ResidualSolver();self.addCleanup(s.close);source=[[4],[1,2],[-1,2],[-2,-3]];stronger=source+[[-4]]
        guard=dict(format=GUARD_FORMAT,stronger=stronger,stronger_root=s.solve(stronger)['root'],removed_clause=[-4]);_,target=check_guard(s,source,guard)
        r=self.solve(s,[list(c) for c in target],[[2],[3]])
        result=make_record(s,source,[guard],r['missing_clauses'],r['stronger_root'],r['children']);self.assertTrue(result['model'][4]);self.assertTrue(holds(source,result['model']))
        self.assertIsNone(s._read(result['query_root']))

    def test_incomplete_or_reordered_negative_partition_rejected(self):
        s=ResidualSolver();self.addCleanup(s.close);r=self.solve(s,[[1],[-1],[2,-3]],[[2],[3]])
        for field in ('children','missing_clauses','stronger_root','query_root','answer'):
            bad=deepcopy(r)
            if field=='children':bad[field].pop()
            elif field=='missing_clauses':bad[field].reverse()
            elif field=='answer':bad[field]=True
            else:bad[field]='wrong'
            with self.subTest(field=field),self.assertRaises(ValueError):check_record(s,bad)

    def test_missing_child_never_searches_and_bad_premise_rejected(self):
        s=ResidualSolver();self.addCleanup(s.close);r=self.solve(s,[[1,2],[-1,2],[-2,-3]],[[2],[3]])
        s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(r['children'][-1]['root'],));s.db.commit();s.checked.clear()
        with patch.object(s,'_expand',side_effect=AssertionError('Search')),self.assertRaises(ValueError):check_record(s,r)
        with self.assertRaises(ValueError):branch_sources([[1,2]],[[1],[1]])
        with self.assertRaises(ValueError):branch_sources([[1,2]],[[3]])
        with self.assertRaises(ValueError):branch_sources([[1,2]],[[]])
        with self.assertRaises(ValueError):branch_sources([[1,2]],[[1,2]])

    def test_sat_records_against_independent_three_variable_truth_tables(self):
        clauses=[[1,2],[-1,2],[-2,-3],[1,3],[-1,-3],[2,3]];models=[dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)];tested=0
        for mask in range(1,64):
            target=[c for i,c in enumerate(clauses) if mask>>i&1];variables={abs(l) for c in target for l in c}
            missing=[[1],[2],[3]]
            if variables!={1,2,3} or any(holds(target+missing,a) for a in models):continue
            s=ResidualSolver()
            try:
                r=self.solve(s,target,missing);self.assertEqual(check_record(s,r)['answer'],any(holds(target,a) for a in models));tested+=1
            finally:s.close()
        self.assertGreater(tested,0)


if __name__=='__main__':unittest.main()
