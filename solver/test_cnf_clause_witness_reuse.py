from collections import Counter
from itertools import product
from unittest.mock import patch
import json,unittest
from experiments.cnf_clause_deletion_guard import ExtensionBank
from experiments.cnf_clause_witness_reuse import reuse_witness,check_witness
from experiments.cnf_residual_dag import ResidualSolver,holds


class ClauseWitnessReuseTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);return s
    def test_sparse_coordinate_transfer_publishes_without_search(self):
        s=self.make();strong=[[10,20],[-10,20]];weak=[[-10,20]];old=s.solve(strong)
        bank=ExtensionBank([dict(source=strong,root=old['root'])]);counts=Counter()
        with patch.object(s,'_expand',side_effect=AssertionError('fresh search')):
            cert=reuse_witness(s,bank,weak,counts);self.assertIsNotNone(cert)
            r=s.solve(weak);self.assertTrue(holds(weak,r['model']));self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
            self.assertIsNone(reuse_witness(s,bank,weak,counts))
        self.assertEqual(counts['published_witness_roots'],1)
    def test_support_loss_and_self_contained_cold_certificate(self):
        s=self.make();strong=[[10],[20]];weak=[[20]];old=s.solve(strong)
        cert=reuse_witness(s,ExtensionBank([dict(source=strong,root=old['root'])]),weak)
        self.assertEqual(check_witness(s,weak,cert),{20:True})
        key=s._canonical(weak)[2];payload=s.db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()[0]
        cold=self.make();cold.db.execute('INSERT INTO cnf_residual_v1 VALUES (?,?)',(key,payload));cold.db.commit()
        with patch.object(cold,'_expand',side_effect=AssertionError('fresh search')):
            self.assertEqual(cold.solve(weak)['model'],{20:True})
    def test_missing_and_unsat_premises_do_not_publish(self):
        s=self.make();strong=[[1],[-1]];root=s._canonical(strong)[2];bank=ExtensionBank([dict(source=strong,root=root)])
        self.assertIsNone(reuse_witness(s,bank,[[-1]]));s.solve(strong)
        self.assertIsNone(reuse_witness(s,bank,[[-1]]));self.assertIsNone(s._read(s._canonical([[-1]])[2]))
    def test_tampered_binding_and_model_reject(self):
        s=self.make();strong=[[1],[2]];weak=[[2]];old=s.solve(strong)
        cert=reuse_witness(s,ExtensionBank([dict(source=strong,root=old['root'])]),weak)
        bad={**cert,'removed_clause':[-1]}
        with self.assertRaises(ValueError):check_witness(s,weak,bad)
        with self.assertRaises(ValueError):check_witness(s,weak,{**cert,'stronger_root':'wrong'})
        cold=self.make();node=json.loads(s.db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(old['root'],)).fetchone()[0]);node['model']=[False,False]
        cold.db.execute('INSERT INTO cnf_residual_v1 VALUES (?,?)',(old['root'],json.dumps(node)));cold.db.commit()
        with self.assertRaises(ValueError):check_witness(cold,weak,cert)
    def test_non_deletion_and_changed_polarity_miss(self):
        s=self.make();strong=[[1],[2]];old=s.solve(strong);bank=ExtensionBank([dict(source=strong,root=old['root'])])
        self.assertIsNone(reuse_witness(s,bank,[[-2]]));self.assertIsNone(reuse_witness(s,bank,[]))
    def test_every_satisfiable_two_variable_formula_and_clause_deletion(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2) if any(signs)]
        assignments=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        for mask in range(1,1<<len(clauses)):
            strong=[c for i,c in enumerate(clauses) if mask>>i&1]
            if not any(holds(strong,a) for a in assignments):continue
            s=ResidualSolver()
            try:
                old=s.solve(strong);bank=ExtensionBank([dict(source=strong,root=old['root'])])
                with patch.object(s,'_expand',side_effect=AssertionError('fresh search')):
                    for clause in strong:
                        weak=[c for c in strong if c!=clause];reuse_witness(s,bank,weak)
                        result=s.solve(weak);self.assertTrue(result['answer']);self.assertTrue(holds(weak,result['model']))
            finally:s.close()


if __name__=='__main__':unittest.main()
