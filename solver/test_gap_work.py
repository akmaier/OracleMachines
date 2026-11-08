"""Regression tests for completion-aware routing and immutable delta indexes."""
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from solver.routing import Router
from solver.persistent import PersistentSolver
from solver.test_interfaces import var,neg,chain

class GapWorkTests(unittest.TestCase):
    def test_route_failures_are_not_fast_successes_and_recent_shift_matters(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            Router.create(db);r=Router(db,'test')
            r.profile=lambda *args:dict(reject=False,variables=8,density_bucket=2,reusable_sample=0)
            d=r.choose('010')
            r.observe(d|{'route':'checked'},100_000_000,True)
            r.observe(d|{'route':'interfaces'},1_000_000,False)
            answer=r.choose('010')
            self.assertEqual(answer['route'],'checked')
            self.assertIsNone(answer['scores_ns']['interfaces'])
            for _ in range(32):r.observe(d|{'route':'interfaces'},1_000_000,True)
            self.assertEqual(r.choose('010')['route'],'interfaces')
            self.assertEqual(db.execute('SELECT count(*) FROM route_observations').fetchone()[0],34)

    def test_delta_indexes_preserve_duplicate_sources_and_old_branches(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path,interfaces=True) as s:
                first=s.expand(add={'chain':chain(64),'a':var(0),'duplicate':var(0),'end':neg(var(64))})
                self.assertFalse(first['answer'])
                second=s.expand(first['state'],remove=['a'])
                self.assertFalse(second['answer'])
                self.assertEqual(second['interfaces']['source_comparisons'],0)
                self.assertEqual(second['interfaces']['plan_copy_entries'],0)
                self.assertEqual(second['interfaces']['source_delta_reads'],1)
                self.assertTrue(s.expand(second['state'],remove=['duplicate'])['answer'])
            with PersistentSolver(path,interfaces=True) as s:
                self.assertFalse(s.expand(first['state'])['answer'])
                edited=s.expand(first['state'],add={'end':var(64)})
                self.assertTrue(edited['answer'])
                self.assertEqual(edited['interfaces']['plan_copy_entries'],0)
                self.assertLessEqual(edited['interfaces']['source_delta_reads'],2)

class LayeredTests(unittest.TestCase):
    def test_layers_match_exhaustive_paths_and_preserve_versions(self):
        import itertools,random
        rng=random.Random(731)
        def brute(edges,left,right,q):
            return any(left&(1<<word[0]) and right&(1<<word[-1]) and
                all(mask&(1<<(q*word[i]+word[i+1])) for i,mask in enumerate(edges))
                for word in itertools.product(range(q),repeat=len(edges)+1))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db';history=[];edges=[];state=None
            with PersistentSolver(path) as s:
                for i in range(30):
                    if len(edges)<4:
                        a=[rng.randrange(1<<16)];changes={};edges+=a
                    else:
                        a=[];j=rng.randrange(4);edges[j]=rng.randrange(1<<16);changes={j:edges[j]}
                    left,right=rng.randrange(16),rng.randrange(16)
                    r=s.layered(2,state,append=a,replace=changes,left=left,right=right,witness=True)
                    self.assertEqual(r['answer'],brute(edges,left,right,4))
                    if r['answer']:
                        word=r['witness'];self.assertEqual(len(word),len(edges)+1)
                        self.assertTrue(all(e&(1<<(4*word[i]+word[i+1])) for i,e in enumerate(edges)))
                    state=r['state'];history.append((state,list(edges),left,right))
            with PersistentSolver(path) as s:
                for state,edges,left,right in history:
                    self.assertEqual(s.layered(2,state,left=left,right=right)['answer'],brute(edges,left,right,4))
                with self.assertRaises(ValueError):s.layered(1,state)

    def test_counter_layers_logarithmic_update_and_invalid_summary(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db') as s:
            q=8;increment=sum(1<<(q*x+(x+1)%q) for x in range(q));identity=sum(1<<(q*x+x) for x in range(q))
            first=s.layered(3,append=[increment]*256,left=1,right=1)
            changed=s.layered(3,first['state'],replace={127:identity},left=1,right=1)
            self.assertFalse(changed['answer'])
            self.assertEqual(changed['layered']['compositions'],8)
            self.assertEqual(changed['layered']['node_writes'],9)
            self.assertEqual(changed['layered']['composition_cell_bound'],8*q**3)
            positive=s.layered(3,changed['state'],left=1,right=1<<7,witness=True)
            self.assertTrue(positive['answer']);self.assertEqual(positive['witness'][-1],7)
            node=s.layers.read(positive['root'])
            with self.assertRaises(ValueError):s._request(dict(mode='layered_define',nodes=[dict(id='poison',**(node|{'mask':0}))]))
            self.assertTrue(s.layered(3,first['state'],left=1,right=1)['answer'])

    def test_small_active_payloads_and_checkpoints_preserve_archive(self):
        from solver.active_cache import PayloadCache
        cache=PayloadCache(40,2);cache['a']=[1];cache['a'].extend(range(100));cache.refresh()
        self.assertEqual(len(cache),0)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path,interfaces=True,active_cache_bytes=256,wal_checkpoint_bytes=1) as s:
                first=s.expand(add={'c':chain(8),'x':var(0)})
                second=s.expand(first['state'],add={'end':neg(var(8))})
                self.assertFalse(second['answer'])
                self.assertGreater(s.db.execute('SELECT count(*) FROM expansion_states').fetchone()[0],1)
                for cache in second['storage']['active_caches'].values():
                    self.assertLessEqual(cache['retained_payload_bytes'],256)
                self.assertIsNotNone(second['storage']['checkpoint_result'])
            with PersistentSolver(path,interfaces=True) as s:self.assertTrue(s.expand(first['state'])['answer'])

if __name__=='__main__':unittest.main()
