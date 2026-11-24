from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json,random,unittest
from experiments.cnf_archive_parts import split_archive,restore_archive
from experiments import compare_cnf_bootstrap as legacy


class ArchivePartsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.raw=self.root/'raw'
        self.raw.write_bytes(random.Random(314159).randbytes(8192))
        packed=self.root/'packed';packed.mkdir();self.old=legacy.archive(self.raw,packed)

    def parts(self):return split_archive(self.old,self.root/'parts',1000)

    def rewrite(self,entry,change):
        entry=deepcopy(entry);path=Path(entry['path']);d=json.loads(path.read_text());change(d)
        path.write_text(json.dumps(d));entry['sha256']=legacy.sha(path);return entry

    def test_legacy_and_split_restore_identical_bytes_without_removing_source(self):
        a=self.root/'legacy';restore_archive(self.old,a)
        entry=self.parts();b=self.root/'split';restore_archive(entry,b)
        self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(b.read_bytes(),self.raw.read_bytes())
        self.assertEqual(legacy.sha(self.old['path']),self.old['sha256'])
        d=json.loads(Path(entry['path']).read_text());self.assertGreater(len(d['parts']),1)
        self.assertTrue(all(p['bytes']<=1000 for p in d['parts']))

    def test_changed_part_is_rejected_without_destination(self):
        entry=self.parts();part=next((self.root/'parts').glob('*.part-*'));part.write_bytes(b'bad')
        target=self.root/'dest'
        with self.assertRaises(ValueError):restore_archive(entry,target)
        self.assertFalse(target.exists())

    def test_reordering_or_omission_cannot_publish_a_database(self):
        for action in ('reverse','pop'):
            with self.subTest(action=action):
                entry=split_archive(self.old,self.root/action,1000)
                entry=self.rewrite(entry,lambda d:getattr(d['parts'],action)())
                target=self.root/('dest-'+action)
                with self.assertRaises(ValueError):restore_archive(entry,target)
                self.assertFalse(target.exists())

    def test_wrong_database_binding_rejected_after_full_stream(self):
        entry=self.parts();entry['database_sha256']='0'*64
        entry=self.rewrite(entry,lambda d:d.update(database_sha256='0'*64))
        target=self.root/'dest'
        with self.assertRaises(ValueError):restore_archive(entry,target)
        self.assertFalse(target.exists())

    def test_untrusted_descriptor_edit_and_existing_destination_rejected(self):
        entry=self.parts();target=self.root/'dest';target.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):restore_archive(entry,target)
        self.assertEqual(target.read_bytes(),b'preserve')
        Path(entry['path']).write_text('{}')
        with self.assertRaises(ValueError):restore_archive(entry,self.root/'new')

    def test_invalid_limit_or_source_hash_does_not_create_parts(self):
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):split_archive(self.old,self.root/'parts',value)
        bad={**self.old,'sha256':'0'*64}
        with self.assertRaises(ValueError):split_archive(bad,self.root/'parts')
        self.assertFalse((self.root/'parts').exists())


if __name__=='__main__':unittest.main()
