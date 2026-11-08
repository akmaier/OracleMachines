"""Lossless shared batches: stable identities, admission, corruption and restart."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zlib

from experiments.affine_reference import equation
from solver.affine_archive import AffineArchive
from solver.knowledge_store import KnowledgeStore
from solver.persistent import PersistentSolver


def repeated_rows(width=32):
    return [equation(width,(i,width+i),False) for i in range(width)]*2


class AffineArchiveTests(unittest.TestCase):
    def archive(self,db):
        KnowledgeStore.create(db)
        return AffineArchive(db,'test')

    def test_sharing_is_lossless_and_keeps_legacy_identity(self):
        with closing(sqlite3.connect(':memory:')) as db:
            store=self.archive(db);rows=repeated_rows();versions=[]
            for i in range(12):
                value=dict(width=32,base=hashlib.sha256(str(i).encode()).hexdigest(),equations=rows)
                token=store.put('affine_version',value)[0];versions.append((token,value))
                raw=json.dumps(value,separators=(',',':'),sort_keys=True).encode()
                self.assertEqual(token,hashlib.sha256(b'affine_version\0'+raw).hexdigest())
                self.assertEqual(store.get(token,'affine_version'),value)
            self.assertEqual(db.execute("SELECT count(*) FROM knowledge_objects WHERE kind='affine_batch'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count(*) FROM knowledge_objects WHERE codec='affine_batch_ref_v1'").fetchone()[0],11)
            fresh=KnowledgeStore(db,'new')
            for token,value in versions:self.assertEqual(fresh.get(token,'affine_version'),value)
            # Callers cannot mutate the original source through a recovered list.
            recovered=fresh.get(versions[-1][0],'affine_version');recovered['equations'].clear()
            self.assertEqual(fresh.get(versions[-1][0],'affine_version'),versions[-1][1])

    def test_retries_and_novel_batches_do_not_admit_extra_objects(self):
        with closing(sqlite3.connect(':memory:')) as db:
            store=self.archive(db)
            value=dict(width=32,base='a'*64,equations=repeated_rows())
            token=store.put('affine_version',value)[0]
            before=list(db.execute('SELECT * FROM knowledge_objects'))
            for _ in range(10):self.assertEqual(store.put('affine_version',value)[0],token)
            self.assertEqual(list(db.execute('SELECT * FROM knowledge_objects')),before)
            for i in range(300):
                rows=repeated_rows()
                # Distinct ordered batches; all preserve the original dimensions.
                rows += [equation(32,(),bool((i>>j)&1)) for j in range(9)]
                store.put('affine_version',dict(width=32,base=str(i),equations=rows))
            self.assertEqual(db.execute("SELECT count(*) FROM knowledge_objects WHERE kind='affine_batch'").fetchone()[0],0)
            self.assertLessEqual(len(store.candidates),256)

    def test_corrupt_or_recursive_batch_references_are_rejected(self):
        with closing(sqlite3.connect(':memory:')) as db:
            store=self.archive(db);rows=repeated_rows()
            store.put('affine_version',dict(width=32,base='a'*64,equations=rows))
            token=store.put('affine_version',dict(width=32,base='b'*64,equations=rows))[0]
            payload=db.execute('SELECT payload FROM knowledge_objects WHERE id=?',(token,)).fetchone()[0]
            link=json.loads(payload);batch=link['batch']
            original=db.execute('SELECT payload,codec,raw_bytes FROM knowledge_objects WHERE id=?',(batch,)).fetchone()
            bad=[(b'broken','zlib',original[2]),(b'{}','raw',2),(b'{}','affine_batch_ref_v1',2)]
            for packed,codec,length in bad:
                db.execute('UPDATE knowledge_objects SET payload=?,codec=?,raw_bytes=? WHERE id=?',(packed,codec,length,batch))
                with self.assertRaises((ValueError,zlib.error)):
                    store.get(token,'affine_version')
            db.execute('UPDATE knowledge_objects SET payload=?,codec=?,raw_bytes=? WHERE id=?',(*original,batch))
            for change in (dict(link,batch='missing'),dict(link,width=31),dict(link,base='forged')):
                db.execute('UPDATE knowledge_objects SET payload=? WHERE id=?',(json.dumps(change).encode(),token))
                with self.assertRaises(ValueError):store.get(token,'affine_version')
            db.execute('UPDATE knowledge_objects SET payload=? WHERE id=?',(payload,token))
            self.assertEqual(store.get(token,'affine_version')['equations'],rows)

    def test_shared_history_restarts_with_sharing_disabled(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'archive.db';rows=repeated_rows()
            with PersistentSolver(path,native_affine_versions=2) as service:
                state=service.affine_grow(32)
                for _ in range(12):state=service.affine_grow(base=state['state'],equations=rows)
                last=state['state']
                self.assertGreater(service.db.execute("SELECT count(*) FROM knowledge_objects WHERE codec='affine_batch_ref_v1'").fetchone()[0],0)
                old=list(service.db.execute('SELECT * FROM knowledge_objects ORDER BY id'))
            with PersistentSolver(path,affine_share_batches=False,native_affine_versions=2) as service:
                state=service.affine_grow(base=last)
                self.assertTrue(state['answer']);self.assertEqual(state['steps'],12)
                for row in old:
                    self.assertEqual(tuple(service.db.execute('SELECT * FROM knowledge_objects WHERE id=?',(row['id'],)).fetchone()),tuple(row))

    def test_affine_options_require_booleans(self):
        with tempfile.TemporaryDirectory() as d:
            for option in ('affine_share_batches','affine_deduplicate','affine_reuse_metadata'):
                for value in (0,1,None,'true'):
                    with self.assertRaises(ValueError):PersistentSolver(Path(d)/'bad.db',**{option:value})

    def test_failed_shared_batch_admission_rolls_back_all_new_objects(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as service:
            rows=repeated_rows()
            first=service.affine_grow(32,rows)
            store=service.affine_growth.store
            before=[tuple(r) for r in service.db.execute('SELECT * FROM knowledge_objects ORDER BY id')]
            original=store.put
            def fail(kind,value):
                if kind=='affine_result':
                    self.assertEqual(service.db.execute("SELECT count(*) FROM knowledge_objects WHERE kind='affine_batch'").fetchone()[0],1)
                    raise RuntimeError('injected failure after shared admission')
                return original(kind,value)
            with patch.object(store,'put',side_effect=fail):
                with self.assertRaisesRegex(RuntimeError,'shared admission'):
                    service.affine_grow(base=first['state'],equations=rows)
            self.assertEqual([tuple(r) for r in service.db.execute('SELECT * FROM knowledge_objects ORDER BY id')],before)
            self.assertEqual(len(store.candidates),0)
            recovered=service.affine_grow(base=first['state'],equations=rows)
            self.assertTrue(recovered['answer'])
            self.assertEqual(recovered['affine_updates']['native_resets'],1)
            shared=service.affine_grow(base=recovered['state'],equations=rows)
            self.assertTrue(shared['answer'])
            self.assertEqual(shared['affine_updates']['batch_admissions'],1)
            self.assertEqual(store.get(shared['state'],'affine_version')['equations'],rows)
