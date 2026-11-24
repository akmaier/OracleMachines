from copy import deepcopy
from pathlib import Path
import json,shutil,sqlite3,tempfile,unittest
from experiments import cnf_history_layers as layers
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import ResidualSolver


class HistoryLayerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.parent=self.root/'parent';self.target=self.root/'target'
        s=AccountedResidualSolver(self.parent)
        try:
            s.solve([[1]])
            with s.db:
                for t in layers.TABLES[1:]:
                    s.db.execute(f'CREATE TABLE {t}(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                    s.db.execute(f'INSERT INTO {t} VALUES (?,?)',('old','original'))
        finally:s.close()
        packed=self.root/'packed';packed.mkdir();self.entry=layers.base.archive(self.parent,packed)
        shutil.copyfile(self.parent,self.target)
        s=AccountedResidualSolver(self.target)
        try:
            s.solve([[-1,2],[1,2],[-2]])
            with s.db:
                for t in layers.TABLES[1:]:s.db.execute(f'INSERT INTO {t} VALUES (?,?)',('new','appended'))
        finally:s.close()

    def prepare(self):
        return layers.prepare_append(self.entry,self.parent,self.target,layers.base.sha(self.target))

    def publish(self):
        return layers.publish_layer(self.prepare(),self.root/'layer')[0]

    def tables(self,path):
        db=layers.readonly(path)
        try:return {t:db.execute(f'SELECT * FROM {t} ORDER BY 1').fetchall() for t in (*layers.TABLES,layers.LEDGER)}
        finally:db.close()

    def rewrite(self,entry,change):
        entry=deepcopy(entry);p=Path(entry['path']);d=json.loads(p.read_text());change(d)
        p.write_text(json.dumps(d));entry['sha256']=layers.base.sha(p);return entry

    def test_all_tables_exactly_restore_and_native_proofs_replay(self):
        entry=self.publish();dest=self.root/'restored';layers.restore_archive(entry,dest)
        self.assertEqual(self.tables(dest),self.tables(self.target))
        self.assertEqual(layers.base.sha(dest),entry['database_sha256'])
        self.assertEqual(layers.base.sha(self.parent),self.entry['database_sha256'])
        for cls in (ResidualSolver,CanonicalVerifySnapshot):
            s=cls(dest)
            try:
                for (key,) in s.db.execute('SELECT id FROM cnf_residual_v1').fetchall():self.assertIsNotNone(s._read(key))
            finally:s.close()

    def test_unchanged_dirty_ledger_preserved_without_trusting_counters(self):
        for path in (self.parent,self.target):
            db=sqlite3.connect(path)
            with db:db.execute(f'UPDATE {layers.LEDGER} SET nodes=2,payload_units=3,dirty=1')
            db.close()
        packed=self.root/'dirty-packed';packed.mkdir();self.entry=layers.base.archive(self.parent,packed)
        entry=self.publish();dest=self.root/'dirty-restored';layers.restore_archive(entry,dest)
        self.assertEqual(self.tables(dest),self.tables(self.target))
        db=sqlite3.connect(self.target)
        with db:db.execute(f'UPDATE {layers.LEDGER} SET nodes=4')
        db.close()
        with self.assertRaisesRegex(ValueError,'dirty accounting'):self.prepare()

    def test_two_layers_and_depth_limit(self):
        first=self.publish();restored=self.root/'first';layers.restore_archive(first,restored)
        later=self.root/'later';shutil.copyfile(restored,later)
        db=sqlite3.connect(later)
        with db:db.execute(f'INSERT INTO {layers.TABLES[1]} VALUES (?,?)',('third','value'))
        db.close()
        prep=layers.prepare_append(first,restored,later,layers.base.sha(later))
        second=layers.publish_layer(prep,self.root/'layer2')[0]
        layers.restore_archive(second,self.root/'second',max_depth=2)
        self.assertEqual(self.tables(later),self.tables(self.root/'second'))
        with self.assertRaisesRegex(ValueError,'depth'):layers.restore_archive(second,self.root/'limited',max_depth=1)
        self.assertFalse((self.root/'limited').exists())

    def test_empty_delta_and_legacy_restore(self):
        prep=layers.prepare_append(self.entry,self.parent,self.parent,self.entry['database_sha256'])
        self.assertFalse(any(prep['added_rows'].values()))
        entry=layers.publish_layer(prep,self.root/'empty')[0]
        layers.restore_archive(entry,self.root/'empty-restored');layers.restore_archive(self.entry,self.root/'legacy')
        self.assertEqual(self.tables(self.root/'legacy'),self.tables(self.root/'empty-restored'))

    def test_changed_or_deleted_old_payloads_require_full_snapshot(self):
        for sql in ("UPDATE {t} SET payload='changed' WHERE id='old'","DELETE FROM {t} WHERE id='old'"):
            copy=self.root/'changed';shutil.copyfile(self.target,copy);db=sqlite3.connect(copy)
            with db:db.execute(sql.format(t=layers.TABLES[1]))
            db.close()
            with self.assertRaisesRegex(ValueError,'prior payload'):
                layers.prepare_append(self.entry,self.parent,copy,layers.base.sha(copy))

    def test_schema_and_accounting_changes_rejected(self):
        for sql in ('CREATE TABLE extra(x)',f'UPDATE {layers.LEDGER} SET dirty=1',
                    f'UPDATE {layers.LEDGER} SET payload_units=payload_units+1'):
            copy=self.root/'bad';shutil.copyfile(self.target,copy);db=sqlite3.connect(copy)
            with db:db.execute(sql)
            db.close()
            with self.assertRaises(ValueError):layers.prepare_append(self.entry,self.parent,copy,layers.base.sha(copy))

    def test_wrong_snapshot_binding_and_uncheckpointed_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'target'):layers.prepare_append(self.entry,self.parent,self.target,'0'*64)
        with self.assertRaisesRegex(ValueError,'parent'):layers.prepare_append({**self.entry,'database_sha256':'0'*64},self.parent,self.target,layers.base.sha(self.target))
        Path(str(self.target)+'-journal').write_bytes(b'pending')
        with self.assertRaisesRegex(ValueError,'checkpoint'):self.prepare()

    def test_duplicate_or_conflicting_delta_key_rolls_back(self):
        for value in ('original','changed'):
            prep=self.prepare();delta=self.root/('delta-'+value);layers.export_delta(prep,delta)
            db=sqlite3.connect(delta)
            with db:db.execute(f'INSERT INTO {layers.TABLES[1]} VALUES (?,?)',('old',value))
            db.close();counts=dict(prep['added_rows']);counts[layers.TABLES[1]]+=1
            dest=self.root/('dest-'+value);shutil.copyfile(self.parent,dest);before=self.tables(dest)
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                layers.apply_delta(dest,delta,prep['preserved_rows'],counts)
            self.assertEqual(self.tables(dest),before)

    def test_corrupt_delta_and_parent_archive_cannot_publish(self):
        entry=self.publish();d=json.loads(Path(entry['path']).read_text())
        path=Path(d['delta']['path']);raw=path.read_bytes();path.write_bytes(b'bad')
        with self.assertRaises(Exception):layers.restore_archive(entry,self.root/'bad-delta')
        self.assertFalse((self.root/'bad-delta').exists());path.write_bytes(raw)
        Path(self.entry['path']).write_bytes(b'bad')
        with self.assertRaises(Exception):layers.restore_archive(entry,self.root/'bad-parent')
        self.assertFalse((self.root/'bad-parent').exists())

    def test_wrong_counts_or_final_hash_cannot_publish(self):
        entry=self.publish();original=Path(entry['path']).read_text()
        for name,change in (
            ('count',lambda d:d['added_rows'].__setitem__(layers.TABLES[0],999)),
            ('hash',lambda d:d.update(database_sha256='0'*64))):
            Path(entry['path']).write_text(original);bad=self.rewrite(entry,change)
            if name=='hash':bad['database_sha256']='0'*64
            with self.assertRaises(ValueError):layers.restore_archive(bad,self.root/name)
            self.assertFalse((self.root/name).exists())

    def test_existing_destination_and_untrusted_descriptor_preserved(self):
        entry=self.publish();dest=self.root/'exists';dest.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):layers.restore_archive(entry,dest)
        self.assertEqual(dest.read_bytes(),b'keep')
        Path(entry['path']).write_text('{}')
        with self.assertRaises(ValueError):layers.restore_archive(entry,self.root/'changed-descriptor')
        self.assertFalse((self.root/'changed-descriptor').exists())


if __name__=='__main__':unittest.main()
