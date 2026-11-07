import itertools
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.persistent import PersistentSolver
from solver.symbolic import BDD
from solver.test_fast import var, conj, disj
from solver.test_interfaces import chain, xor
from experiments.run_expanded import balanced


class ImprovementTests(unittest.TestCase):
    def test_relational_product_and_collection(self):
        rng=random.Random(917)
        for order in [(), (3, 1, 2, 0)]:
            b=BDD(order=order)
            for _ in range(20):
                roots=[]
                for _ in range(2):
                    r=1
                    for _ in range(5):
                        x,y=rng.sample(range(4),2)
                        a,c=b.node(x,0,1),b.node(y,0,1)
                        if rng.randrange(2):a=b.negate(a)
                        r=b.apply('and',r,b.apply('or',a,c))
                    roots.append(r)
                projected=b.and_exists(*roots,(1,3))
                for values in itertools.product((False,True),repeat=4):
                    a=dict(enumerate(values))
                    expected=any(b.evaluate(roots[0],dict(a,**{} )|{1:x,3:y}) and
                                 b.evaluate(roots[1],a|{1:x,3:y})
                                 for x,y in itertools.product((False,True),repeat=2))
                    self.assertEqual(b.evaluate(projected,a),expected)
                saved=b.dump(projected)
                before=len(b.nodes)
                kept=b.collect({'p':projected})['p']
                self.assertLessEqual(len(b.nodes),before)
                self.assertEqual(b.dump(kept),saved)
                restored=BDD(order=order);root=restored.restore(saved)
                for values in itertools.product((False,True),repeat=4):
                    self.assertEqual(restored.evaluate(root,dict(enumerate(values))),b.evaluate(kept,dict(enumerate(values))))

    def test_batch_commits_and_rollback_keep_prior_versions(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db',interfaces=True) as s:
            sql=[];s.db.set_trace_callback(sql.append)
            first=s.expand(add={'c':chain(16)})
            self.assertEqual(sum(q=='COMMIT' for q in sql),1)
            self.assertGreater(first['interfaces']['native_definitions'],first['interfaces']['native_definition_batches'])
            before=s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0]
            with patch.object(s.interfaces,'run',side_effect=ValueError('injected failure')):
                with self.assertRaises(ValueError):s.expand(first['state'],add={'new':var(17)})
            self.assertEqual(s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0],before)
            self.assertTrue(s.expand(first['state'],add={'new':var(17)})['answer'])

    def test_preflight_rejects_before_interface_writes_or_registration(self):
        bits=balanced([xor(i,j) for i in range(6) for j in range(i)],conj,'0010')
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db',interfaces=True,max_interface=1) as s:
            result=s.solve(bits,learn=False)
            self.assertFalse(result['answer'])
            self.assertEqual(result['interface_fallback']['metrics']['preflight_rejected'],1)
            self.assertEqual(s.db.execute('SELECT count(*) FROM interface_nodes').fetchone()[0],0)
            self.assertEqual(result['interface_fallback']['metrics']['native_definitions'],0)

if __name__=='__main__':unittest.main()
