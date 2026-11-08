"""Source edits against exhaustive truth tables, adversarial transport and replay."""
import itertools
import random
import tempfile
import unittest
from pathlib import Path

from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded


def sat(clauses,n):
    return any(all(any(a[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses)
               for a in itertools.product((False,True),repeat=n))


class SourceUpdateTests(unittest.TestCase):
    def test_random_edits_deletions_branches_and_restart_match_exhaustive_cnf(self):
        rng=random.Random(1820)
        for width in (1,2):
            layers=[list(range(i*width+1,(i+1)*width+1)) for i in range(4)]
            def bucket(edge):
                scope=layers[edge]+layers[edge+1]
                return [[rng.choice(scope)*rng.choice((-1,1)) for _ in range(rng.randrange(4))]
                        for _ in range(rng.randrange(5))]
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'s.db';versions=[]
                with PersistentSolver(path,native_layer_cells=7*(1<<width)**2) as s:
                    first=s.source_cnf(width,[],layers)
                    versions.append((first['state'],[[],[],[]]))
                    for _ in range(60):
                        base,buckets=rng.choice(versions);buckets=list(buckets)
                        changes={i:bucket(i) for i in rng.sample(range(3),rng.randrange(1,4))}
                        for i,clauses in changes.items():buckets[i]=clauses
                        result=s.source_cnf(base=base,replace=changes,witness=True)
                        flat=[clause for group in buckets for clause in group]
                        self.assertEqual(result['answer'],sat(flat,4*width))
                        if result['answer']:
                            values={v:bool(result['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                            self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in flat))
                        self.assertEqual(result['source_updates']['binding_visits'],0)
                        versions.append((result['state'],buckets))
                with PersistentSolver(path,native_layer_cells=7*(1<<width)**2) as s:
                    for state,buckets in versions[::10]:
                        result=s.source_cnf(base=state)
                        self.assertEqual(result['answer'],sat([c for b in buckets for c in b],4*width))

    def test_flat_source_binding_and_nonconsecutive_variable_names(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            r=s.source_cnf(2,[[100],[-42],[100,9999]],[[100],[9999],[42]],witness=True)
            self.assertTrue(r['answer']);self.assertEqual(r['witness'][0]&1,1);self.assertEqual(r['witness'][2]&1,0)
            r=s.source_cnf(base=r['state'],replace={1:[[42],[-42]]})
            self.assertFalse(r['answer'])
            self.assertTrue(s.source_cnf(base=r['state'],replace={1:[]})['answer'])

    def test_source_cannot_change_unedited_subtree_or_forge_leaf(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.source_cnf(1,[],[[1],[2],[3],[4],[5]])
            b=s.source_cnf(base=a['state'],replace={3:[[]]})
            with self.assertRaisesRegex(ValueError,'unedited'):
                s._request(dict(mode='source_patch',base=a['root'],root=b['root'],
                    edits=[dict(edge=0,clauses=[])],witness=False))
            node=s.source_layers.read(a['root'])
            while node['height']:node=s.source_layers.read(node['left'])
            forged=dict(node,id='forged-source',mask=0)
            with self.assertRaisesRegex(ValueError,'mask'):
                s._request(dict(mode='source_define',nodes=[forged]))
            with self.assertRaisesRegex(ValueError,'Original source'):
                s._request(dict(mode='source_bind',root=a['root'],width=1,layers=[[1],[2],[3],[4],[5]],
                    clauses=[[]],witness=False))
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_locality_validation_and_failed_updates_preserve_base(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.source_cnf(1,[],[[1],[2],[3]])
            for changes in ({0:[[3]]},{0:[[0]]},{2:[]},{0:[], '0':[]},{-1:[]}):
                with self.assertRaises(ValueError):s.source_cnf(base=a['state'],replace=changes)
                self.assertTrue(s.source_cnf(base=a['state'])['answer'])
            for blocks in ([[1],[1]],[[0],[1]],[[1,2],[3]]):
                with self.assertRaises(ValueError):s.source_cnf(1,[],blocks)
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])
            b=s.source_cnf(1,[[]],[[10],[20]])
            self.assertFalse(b['answer'])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_tight_cap_source_edits_have_local_evidence_and_measured_reservation(self):
        size=256;height=8;cells=4;cap=(2*size-1)*cells
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_layer_cells=cap) as s:
            a=s.source_cnf(1,[],[[i+1] for i in range(size+1)])
            for i in range(40):
                edge=i%size
                r=s.source_cnf(base=a['state'],replace={edge:[[edge+1]]})
                self.assertTrue(r['answer']);self.assertIsNone(r['witness']);m=r['source_updates']
                self.assertEqual(m['native_definitions'],height+1)
                self.assertEqual(m['inserted_objects'],height+3)
                self.assertEqual(m['native_evictions'],height+1)
                self.assertEqual(m['patch_visits'],2*height+1)
                self.assertEqual(m['binding_visits'],0)
                self.assertEqual(m['layout_replays'],0)
                self.assertLess(m['node_reads'],100)
                self.assertEqual(m['native_cells'],cap)
                self.assertEqual(m['peak_native_cells'],cap+(height+1)*cells)
                a=r
            same=s.source_cnf(base=a['state']);m=same['source_updates']
            self.assertEqual(m['native_definitions'],0)
            self.assertEqual(m['reachability_updates'],0)
            self.assertEqual(m['inserted_objects'],0)

    def test_source_working_set_refusal_keeps_other_version(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_layer_cells=12) as s:
            a=s.source_cnf(1,[],[[1],[2],[3]])
            with self.assertRaises(BudgetExceeded):s.source_cnf(1,[],[[1],[2],[3],[4],[5]])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_caller_mutation_cannot_change_saved_source_or_cached_replay(self):
        from solver.resources import stop_process
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            layers=[[1],[2],[3]];clauses=[[1]]
            a=s.source_cnf(1,clauses,layers)
            bucket=[[1],[-1]]
            b=s.source_cnf(base=a['state'],replace={0:bucket})
            layers[0][0]=99;clauses[0][0]=99;bucket[1][0]=1
            stop_process(s.process);s.process=None
            self.assertFalse(s.source_cnf(base=b['state'])['answer'])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_old_engine_source_replays_clauses_instead_of_importing_answer(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path) as s:
                a=s.source_cnf(1,[],[[1],[2],[3]])
                b=s.source_cnf(base=a['state'],replace={1:[[]]})
                with s.db:
                    s.db.execute("UPDATE source_states SET engine='older-engine',answer=1-answer")
                before=[tuple(r) for r in s.db.execute('SELECT * FROM source_states ORDER BY id')]
            with PersistentSolver(path) as s:
                for prior,expected in ((a,True),(b,False)):
                    r=s.source_cnf(base=prior['state'])
                    self.assertEqual(r['answer'],expected)
                    self.assertTrue(r['revalidated_source'])
                    self.assertGreater(r['source_updates']['native_definitions'],0)
                    self.assertFalse(s.source_cnf(base=prior['state'])['revalidated_source'])
                self.assertEqual([tuple(r) for r in s.db.execute("SELECT * FROM source_states WHERE engine='older-engine' ORDER BY id")],before)
                self.assertEqual(s.db.execute('SELECT count(*) FROM source_states').fetchone()[0],4)
                self.assertTrue(s.source_cnf(base=b['state'],replace={1:[]})['answer'])


if __name__=='__main__':unittest.main()
