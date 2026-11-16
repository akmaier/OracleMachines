from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,random,unittest
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_clause_deletion_guard import FORMAT,check_guard,replay
from experiments.cnf_unsat_support import CoreBank
from experiments.cnf_cofactor_support import prepare


CORE=[[1,2],[1,-2],[-1,2],[-1,-2]]


def record(solver,source,clause,case=0):
    stronger=source+[clause];premise=solver.solve(stronger)
    guard=dict(format=FORMAT,stronger=stronger,stronger_root=premise['root'],removed_clause=sorted(clause))
    fixed,target=check_guard(solver,source,guard);child=solver.solve(target)
    return dict(case=case,source=source,query_root=solver._canonical(source)[2],guard=guard,child=child,answer=child['answer'],model=child['model'])


class CofactorSupportTests(unittest.TestCase):
    def make(self):
        solver=ResidualSolver();self.addCleanup(solver.close);return solver
    def test_transfer_between_different_guards_and_fresh_target(self):
        s=self.make();source=[[-3]]+[[3]+c for c in CORE]
        old=record(s,source,[3]);query=[[-4]]+[[4]+c for c in CORE]+[[5,6]]
        premise=s.solve(query+[[4]])
        guard=dict(format=FORMAT,stronger=query+[[4]],stronger_root=premise['root'],removed_clause=[4])
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            prepared=prepare(s,[('old',[old])]);bank=CoreBank(s,prepared['cores'])
            fixed,target=check_guard(s,query,guard);self.assertIsNone(s._read(s._canonical(target)[2]))
            hit=bank.reuse(target);self.assertTrue(hit['inserted']);child=s.solve(target)
            self.assertFalse(replay(s,query,guard,child)['answer'])
            self.assertIsNone(s._read(s._canonical(query)[2]))
    def test_antichain_preserves_all_superset_matches(self):
        s=self.make();records=[record(s,CORE, [3]),record(s,CORE+[[5,6]],[4],1),record(s,[[1],[-1]],[3],2)]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):data=prepare(s,[('old',records)])
        members=[{tuple(sorted(c)) for c in x['source']} for x in data['all_cores']]
        retained=data['retained_indices'];self.assertTrue(retained)
        for d in data['dominance']:self.assertLessEqual(members[d['retained']],members[d['core']])
        clauses=sorted(set().union(*members))
        for mask in range(1<<len(clauses)):
            source={c for i,c in enumerate(clauses) if mask>>i&1}
            self.assertEqual(any(m<=source for m in members),any(members[i]<=source for i in retained))
    def test_changed_query_guard_or_child_identity_rejects(self):
        s=self.make();original=record(s,[[-3]]+[[3]+c for c in CORE],[3])
        for field in ('query','child','guard','model','child_model'):
            bad=copy.deepcopy(original)
            if field=='query':bad['query_root']='foreign'
            elif field=='child':bad['child']['root']='foreign'
            elif field=='guard':bad['guard']['removed_clause']=[-3]
            elif field=='model':bad['model']={1:True}
            else:bad['child']['model']={1:True}
            with self.subTest(field=field),self.assertRaises(ValueError):prepare(s,[('bad',[bad])])
    def test_positive_or_unguarded_records_do_not_supply_negative_support(self):
        s=self.make();positive=record(s,[[-1]],[1]);self.assertTrue(positive['answer'])
        direct=dict(answer=False,guard=None)
        self.assertEqual(prepare(s,[('old',[positive,direct])])['cores'],[])
    def test_missing_negative_child_rejects(self):
        s=self.make();r=record(s,[[-3]]+[[3]+c for c in CORE],[3]);key=r['child']['root']
        s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(key,));s.db.commit();s.checked.clear()
        with self.assertRaisesRegex(ValueError,'Missing checked'):prepare(s,[('old',[r])])
    def test_duplicate_origins_and_empty_cofactor(self):
        s=self.make();r=record(s,[[1],[-1]],[3])
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):data=prepare(s,[('a',[r]),('b',[r])])
        self.assertEqual(len(data['origins']),2);self.assertEqual(len(data['all_cores']),1)
        empty=record(s,[[1],[-1]],[1,2])
        data=prepare(s,[('empty',[empty])]);self.assertEqual(data['cores'][0]['source'],[[]])
    def test_cold_supports_use_ordinary_checker(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);r=record(s,[[-3]]+[[3]+c for c in CORE],[3]);data=prepare(s,[('old',[r])])
            target=data['cores'][0]['source']+[[7,8]];CoreBank(s,data['cores']).reuse(target);s.close();cold=ResidualSolver(path)
            try:
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):
                    for key, in cold.db.execute('SELECT id FROM cnf_residual_v1'):cold._read(key)
                    self.assertFalse(cold.solve(target)['answer'])
            finally:cold.close()
    def test_random_small_guards_against_truth_tables(self):
        rng=random.Random(2026111618);clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=3) if any(signs)]
        assignments=[dict(zip((1,2,3),bits)) for bits in product((False,True),repeat=3)];tested=0
        for _ in range(120):
            source=rng.sample(clauses,rng.randrange(5,18))
            if any(holds(source,a) for a in assignments):continue
            absent=[list(c) for c in clauses if c not in source]
            if not absent:continue
            s=ResidualSolver()
            try:
                r=record(s,[list(c) for c in source],rng.choice(absent));data=prepare(s,[('small',[r])]);tested+=1
                for core in data['cores']:self.assertFalse(any(holds(core['source'],a) for a in assignments))
            finally:s.close()
        self.assertGreater(tested,10)


if __name__=='__main__':unittest.main()
