"""Retention pressure, shared DAG dependencies, branch switching and recovery."""
import random
import tempfile
import unittest
from pathlib import Path

from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded


class IncrementalRetentionTests(unittest.TestCase):
    def test_many_tight_cap_updates_do_not_scan_live_closure(self):
        rng=random.Random(1810);size=256;height=8;cap=(2*size-1)*256
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db',native_layer_cells=cap) as s:
            first=s.layered(4,append=[rng.getrandbits(256)|1 for _ in range(size)],left=1,right=1)
            state=first['state']
            for i in range(128):
                r=s.layered(4,state,replace={i%size:rng.getrandbits(256)|1},left=1,right=1)
                self.assertTrue(r['answer']);state=r['state'];m=r['layered']
                self.assertEqual(m['native_definitions'],height+1)
                self.assertEqual(m['native_evictions'],height+1)
                self.assertEqual(m['retention_visits'],height+1)
                self.assertLessEqual(m['reachability_updates'],4*height+2)
                self.assertLess(m['node_reads'],100)
                self.assertLessEqual(m['native_cells'],cap)
            same=s.layered(4,state,left=1,right=1)
            self.assertEqual(same['layered']['reachability_updates'],0)
            self.assertEqual(same['layered']['retention_visits'],0)
            self.assertTrue(s.layered(4,first['state'],left=1,right=1)['answer'])

    def test_shared_children_random_branches_match_independent_linear_reachability(self):
        rng=random.Random(1811)
        def expected(edges):
            reachable={0}
            for mask in edges:
                reachable={y for x in reachable for y in range(4) if mask&(1<<(4*x+y))}
            return bool(reachable & {0})
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db';versions=[]
            with PersistentSolver(path,native_layer_cells=63*16) as s:
                edges=[0x8421]*31
                r=s.layered(2,append=edges,left=1,right=1);versions.append((r['state'],edges))
                for _ in range(80):
                    base,edges=rng.choice(versions);edges=list(edges)
                    index=rng.randrange(len(edges));edges[index]=rng.getrandbits(16)
                    r=s.layered(2,base,replace={index:edges[index]},left=1,right=1,witness=True)
                    self.assertEqual(r['answer'],expected(edges));versions.append((r['state'],edges))
            with PersistentSolver(path,native_layer_cells=63*16) as s:
                for state,edges in versions[::8]:
                    self.assertEqual(s.layered(2,state,left=1,right=1)['answer'],expected(edges))

    def test_native_rejects_deletion_of_referenced_child(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db') as s:
            r=s.layered(1,append=[9,15],left=1,right=1)
            node=s.layers.read(r['root'])
            with self.assertRaisesRegex(ValueError,'referenced'):
                s._request(dict(mode='layered_drop',ids=[node['left']]))
            self.assertTrue(s.layered(1,r['state'],left=1,right=1)['answer'])

    def test_refusal_does_not_poison_next_query_or_saved_roots(self):
        rng=random.Random(1812)
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db',native_layer_cells=31*256) as s:
            a=s.layered(4,append=[rng.getrandbits(256)|1 for _ in range(16)],left=1,right=1)
            with self.assertRaises(BudgetExceeded):
                s.layered(4,a['state'],append=[rng.getrandbits(256)|1])
            self.assertTrue(s.layered(4,a['state'],left=1,right=1)['answer'])


if __name__=='__main__':unittest.main()
