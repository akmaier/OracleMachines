"""Source edits against exhaustive truth tables, adversarial transport and replay."""
import itertools
import random
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded


def sat(clauses,n):
    return any(all(any(a[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses)
               for a in itertools.product((False,True),repeat=n))


class SourceUpdateTests(unittest.TestCase):
    def test_global_grouping_matches_every_complete_assignment(self):
        rng=random.Random(1901)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,3):
                names=[(1<<80)+113*k for k in range(1,3*width+1)]
                rng.shuffle(names)
                layers=[names[i*width:(i+1)*width] for i in range(3)]
                positions={v:i for i,block in enumerate(layers) for v in block}
                for _ in range(20):
                    clauses=[]
                    for _ in range(rng.randrange(9)):
                        edge=rng.randrange(2);scope=layers[edge]+layers[edge+1]
                        clause=[rng.choice(scope)*rng.choice((-1,1)) for _ in range(rng.randrange(5))]
                        clauses.append(clause)
                        if rng.randrange(4)==0:clauses.append(list(clause))
                    rng.shuffle(clauses)
                    expected=[[],[]]
                    for clause in clauses:
                        edge=min(min((positions[abs(lit)] for lit in clause),default=0),1)
                        expected[edge].append(clause)
                    compiled=s._request(dict(mode='layered_compile',width=width,layers=layers,clauses=clauses))
                    self.assertEqual(compiled['buckets'],expected)
                    self.assertEqual(Counter(map(tuple,clauses)),Counter(tuple(c) for b in compiled['buckets'] for c in b))
                    satisfiable=False;states=1<<width
                    for bits in itertools.product((False,True),repeat=len(names)):
                        values=dict(zip(names,bits))
                        words=[sum(int(values[v])<<j for j,v in enumerate(block)) for block in layers]
                        original=all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses)
                        grouped=all(bool(mask&(1<<(words[i]*states+words[i+1]))) for i,mask in enumerate(compiled['masks']))
                        self.assertEqual(grouped,original)
                        satisfiable |= original
                    result=s.source_cnf(width,clauses,layers,witness=True)
                    self.assertEqual(result['answer'],satisfiable)
                    if result['answer']:
                        values={v:bool(result['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                        self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses))

    def test_nonempty_local_relations_can_have_no_consistent_global_path(self):
        layers=[[10],[20],[30]];clauses=[[10],[-10,20],[-20],[30]]
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            compiled=s._request(dict(mode='layered_compile',width=1,layers=layers,clauses=clauses))
            self.assertTrue(all(compiled['masks']))
            self.assertFalse(s.source_cnf(1,clauses,layers)['answer'])

    def test_grouping_preserves_repeated_empty_clauses_and_last_block_units(self):
        clauses=[[77],[],[9],[77],[],[9],[-77]]
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            compiled=s._request(dict(mode='layered_compile',width=2,layers=[[9],[],[77]],clauses=clauses))
            self.assertEqual(compiled['buckets'],[[[],[9],[],[9]],[[77],[77],[-77]]])
            self.assertEqual(compiled['masks'],[0,0])

    def test_grouping_large_partition_and_repeated_input_are_stack_safe(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            layers=[[] for _ in range(65536)]+[[77]]
            compiled=s._request(dict(mode='layered_compile',width=1,layers=layers,clauses=[[77],[77]]))
            self.assertEqual(compiled['edges'],65536)
            self.assertEqual(compiled['buckets'][:-1],[[]]*65535)
            self.assertEqual(compiled['buckets'][-1],[[77],[77]])
            self.assertEqual(compiled['masks'][:-1],[15]*65535)
            self.assertEqual(compiled['masks'][-1],10)
            clauses=[[10]]*12000
            repeated=s._request(dict(mode='layered_compile',width=1,layers=[[10],[20]],clauses=clauses))
            self.assertEqual(repeated['buckets'],[clauses])
            self.assertEqual(repeated['masks'],[12])

    def test_native_translation_matches_every_boundary_assignment(self):
        # Sparse IDs and permuted slots prevent accidental index-based agreement.
        rng=random.Random(1897)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,3,4):
                names=[(1<<80)+101*k for k in range(1,2*width+1)]
                rng.shuffle(names)
                layers=[names[:width],names[width:]]
                s._request(dict(mode='source_init',id=f'mapping-{width}',width=width,layers=layers))
                cases=[[],[[]],[[names[0]],[-names[0]]],[[names[-1]]]]
                cases += [[[rng.choice(names)*rng.choice((-1,1)) for _ in range(rng.randrange(5))]
                           for _ in range(rng.randrange(6))] for _ in range(24)]
                for clauses in cases:
                    expected=0;states=1<<width
                    for x,y in itertools.product(range(states),repeat=2):
                        values={v:bool(word&(1<<j)) for word,block in zip((x,y),layers)
                                for j,v in enumerate(block)}
                        if all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses):
                            expected |= 1<<(x*states+y)
                    initial=s._request(dict(mode='layered_compile',width=width,layers=layers,clauses=clauses))
                    edited=s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
                    self.assertEqual(initial['masks'],[expected])
                    self.assertEqual(edited['masks'],[expected])

    def test_short_empty_blocks_unused_variables_and_restart(self):
        layers=[[900,7],[],[51],[3000,2]]
        clauses=[[900],[-7],[51,2],[-3000]]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path) as s:
                first=s.source_cnf(4,clauses,layers,witness=True)
                self.assertTrue(first['answer'])
                values={v:bool(first['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses))
                negative=s.source_cnf(base=first['state'],replace={1:[[51],[-51]]})
                self.assertFalse(negative['answer'])
                restored=s.source_cnf(base=negative['state'],replace={1:[]})
                self.assertTrue(restored['answer'])
            with PersistentSolver(path) as s:
                for version in (first,negative,restored):
                    self.assertEqual(s.source_cnf(base=version['state'])['answer'],version['answer'])
                self.assertTrue(s.source_cnf(4,[],[[],[]])['answer'])
                self.assertFalse(s.source_cnf(4,[[]],[[],[]])['answer'])

    def test_native_mapping_rejects_invalid_names_and_nonlocal_literals(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for layers in ([[1,1],[]],[[1],[1]],[[0],[3]],[[1,2,3],[4]]):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_init',id='bad-map',width=2,layers=layers))
            s._request(dict(mode='source_init',id='valid-map',width=2,layers=[[9],[],[77]]))
            for clauses in ([[0]],[[88]],[[77]],[[9,77]]):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
            with self.assertRaises(ValueError):
                s._request(dict(mode='layered_compile',width=2,layers=[[9],[],[77]],clauses=[[9,77]]))
            self.assertEqual(s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=[])]))['masks'],[65535])

    def test_translation_accumulation_handles_large_clause_and_bucket(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='large-map',width=1,layers=[[10],[20]]))
            for clauses in ([[10]*30000+[-10]],[[10]]*12000):
                result=s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
                self.assertEqual(result['masks'],[15 if len(clauses)==1 else 12])

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
