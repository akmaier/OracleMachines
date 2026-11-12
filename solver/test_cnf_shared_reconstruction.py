from collections import Counter
import itertools
from pathlib import Path
import tempfile
import unittest

from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_shared_reconstruction import SharedRestriction, SharedReconstructionInventory
from experiments.cnf_residual_dag import restrict_scan
from experiments.cnf_pattern_inventory import encode
from solver.test_cnf_prepared_probes import hard_source


class SharedReconstructionTests(unittest.TestCase):
    def test_all_small_restrictions_repeated_assignments_and_edits(self):
        clauses=[()] + [(v,) for v in (-2,-1,1,2)] + list(itertools.product((-2,-1,1,2),repeat=2))
        assignments=[{i+1:v for i,v in enumerate(values) if v is not None}
                     for values in itertools.product((None,False,True),repeat=2)]
        engine=SharedRestriction(256,256);counts=Counter()
        for size in range(3):
            for cnf in itertools.product(clauses,repeat=size):
                for assigned in assignments:
                    expected=restrict_scan(cnf,assigned)
                    first=engine(cnf,assigned,counts);second=engine(cnf,dict(assigned),counts)
                    self.assertEqual(first,expected);self.assertEqual(second,expected)
                    if assigned:self.assertIs(first,second)
                    self.assertLessEqual(engine.result_state()['units'],256)
        self.assertGreater(counts['shared_restriction_hits'],0)
        mutable=[[1,2],[-1,3]];engine(mutable,{1:True});mutable[0][0]=-1
        self.assertEqual(engine(mutable,{1:True}),((2,),(3,)))
        for cnf in (((True,2),),((0,2),),([1,2],)):
            self.assertEqual(engine(cnf,{1:True}),restrict_scan(cnf,{1:True}))
        cnf=((1,2),(-1,3))
        for assigned in ({1:1},{True:False},{-1:True},{0:True}):
            self.assertEqual(engine(cnf,assigned),restrict_scan(cnf,assigned))
        self.assertEqual(engine(cnf+((4,),),{1:True}),((3,),(4,)))

    def test_result_budget_invalidation_and_disabled_path(self):
        cnf=((1,2),(-1,3));counts=Counter()
        for limit in (0,1,12):
            engine=SharedRestriction(256,limit)
            for _ in range(2):self.assertEqual(engine(cnf,{1:True},counts),((3,),))
            self.assertLessEqual(engine.result_state()['peak_units'],limit)
            self.assertEqual(engine.result_state()['entries'],0)
        engine=SharedRestriction(256,20)
        for value in (True,False,True):engine(cnf,{1:value},counts)
        self.assertGreater(counts['shared_restriction_evictions'],0)
        engine.clear();self.assertEqual(engine.result_state()['units'],0)
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):SharedRestriction(result_units=bad)
            with self.assertRaises(ValueError):SharedReconstructionInventory(restriction_result_units=bad)

    def test_integrated_evidence_and_cold_replay(self):
        sources=[hard_source(),[(1,2),(-1,3),(-2,-3)],[(1,),(-1,)]]
        with tempfile.TemporaryDirectory() as tmp:
            archives=[];results=[]
            for cls in (PreparedProbeInventory,SharedReconstructionInventory):
                path=Path(tmp)/cls.__name__;h=cls(path,max_depth=1);current=[]
                for source in sources:
                    h.prepared.inspect(source);r=h.inspect(source)
                    current.append((r['root'],r['profile'],r['summary']))
                results.append(encode(current));h.close();archives.append(path.read_bytes())
                h=cls(path,max_depth=1)
                for source in sources:
                    r=h.inspect(source);self.assertFalse(r['metrics'].get('inserted_nodes',0))
                if cls is SharedReconstructionInventory:
                    self.assertIs(h._restriction,h.prepared._restriction)
                    self.assertLessEqual(h.sharing_state()['restriction_results']['peak_units'],32768)
                h.close();self.assertEqual(path.read_bytes(),archives[-1])
            self.assertEqual(*archives);self.assertEqual(*results)


if __name__=='__main__':unittest.main()
