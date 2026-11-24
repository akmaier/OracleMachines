#!/usr/bin/env python3
"""Matched full-snapshot and parent-plus-delta publication of 173 checked rows."""
from pathlib import Path
import resource,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_history_layers as layers
from experiments import compare_cnf_guard_support as previous
from experiments.cnf_archive_parts import split_archive
from experiments.validate_cnf_guard_closure import SnapshotResidualSolver,CanonicalVerifySnapshot,TerminalStore,MultiEquivalenceStore,BinaryCoreCache
base=previous.base;old=previous.old;TABLES=layers.TABLES
PARENT=Path('experiments/results/cnf-guard-support')
FILES=('experiments/cnf_history_layers.py','solver/test_cnf_history_layers.py','experiments/compare_cnf_history_layers.py')


def prepare(out):
    out.mkdir(parents=True,exist_ok=True);assert not (out/'protocol.json').exists()
    target=base.load(PARENT/'checkpoint.json');parent=old.bound(target['parent_checkpoint'])
    for f,h in target['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent_checkpoint=old.binding(PARENT/'checkpoint.json'),
        parent_manifest=old.binding(PARENT/'manifest.json'),base_checkpoint=target['parent_checkpoint'],
        base_archive=parent['reference_union'],target_archive=target['reference_union'],
        orders=[['full','layer'],['layer','full']],
        source_fingerprints={**target['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'This is publication of the already checked support-composition expansion: exactly the same parent and target rows, with no new SAT acquisition or coverage experiment.',
            'Both policies charge snapshot identity, old-payload/schema/accounting preservation checks, publication, cold restoration, exact logical comparison and new-proof dependency replay through both readers. Shared input restoration is reported separately; imports and source hashing precede worker timing.',
            'Full uses the preceding gzip-and-parts publisher unchanged. Layer exports the prepared append set, compresses only the delta, reconstructs once to bind physical SQLite bytes, and publishes a bound descriptor referencing the immutable parent.',
            'An unchanged dirty accounting ledger is preserved as stale metadata, never trusted for row or resource counts. Clean ledgers must follow exact append accounting; changed dirty metadata requires a full snapshot.',
            'Logical table/ledger equality is required. Physical target-file identity is not required for the layer, because applying appends in one transaction can change SQLite layout/header bytes. Each restored layer must match its own declared physical hash.',
            'The old AppendDelta cursor exports a different eight-table schema on a live connection; it cannot be reused unchanged. The new closed-snapshot diff preserves its append/conflict discipline for the six current tables and existing accounting triggers.',
            'A layer still needs its parent, full materialized disk space and cold parent reads. Preparation scans/checks old history and retains new IDs; costs are not proportional only to new rows. Chains are capped at 32 layers and unsupported/non-append changes require a full snapshot.',
            'The parent and target are closed and exclusively owned between preparation and export. Hashes authenticate bytes relative to trusted experiment entries, not arbitrary SAT claims. Prior full-history proof authority is reused, while all new roots and dependencies are replayed.',
            'Two serial repetitions in reverse order on one exposed historical expansion; no general scale or peak-memory theorem. The frozen full-snapshot checkpoint remains available.']))


def inputs(out,work):
    p=base.load(out/'protocol.json');work.mkdir(exist_ok=False);times={}
    for name,field in (('parent','base_archive'),('target','target_archive')):
        tick=time.perf_counter();layers.restore_archive(p[field],work/name);times[name]=time.perf_counter()-tick
    base.write(out/'input-preparation.json',dict(protocol=old.binding(out/'protocol.json'),restore_seconds=times,
        note='Shared restoration of two immutable inputs; additional to each matched publication worker.'))


def equal_tables(a,b):
    db=layers.readonly(a)
    try:
        db.execute('ATTACH DATABASE ? AS other',(Path(b).resolve().as_uri()+'?mode=ro',))
        assert layers.schema(db)==layers.schema(db,'other') and layers.ledger(db)==layers.ledger(db,'other')
        counts={}
        for t in TABLES:
            counts[t]=db.execute(f'SELECT count(*) FROM main.{t}').fetchone()[0]
            assert counts[t]==db.execute(f'SELECT count(*) FROM other.{t}').fetchone()[0]
            assert db.execute(f'SELECT count(*) FROM main.{t} a LEFT JOIN other.{t} b ON a.id=b.id WHERE b.id IS NULL OR a.payload!=b.payload').fetchone()[0]==0
        return counts
    finally:db.close()


def replay(path,ids):
    checks={}
    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
        s=cls(path);affine=TerminalStore(s);equiv=MultiEquivalenceStore(s);cache=BinaryCoreCache(s)
        try:
            for key in ids[TABLES[0]]:assert s._read(key) is not None
            for key in ids[TABLES[1]]:assert affine.read(key) is not None
            for table in TABLES[2:5]:
                for key in ids[table]:assert equiv.read(key) is not None
            for key in ids[TABLES[-1]]:
                row=s.db.execute(f'SELECT payload FROM {TABLES[-1]} WHERE id=?',(key,)).fetchone();assert row is not None;cache.verify(key,row[0])
            checks[cls.__name__]=dict(s.counts)
        finally:s.close()
    return checks


def trial(out,work,mode,repeat):
    p=base.load(out/'protocol.json');assert mode in ('full','layer')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    dest=out/f'{mode}-{repeat}';dest.mkdir();started=time.perf_counter()
    prepared=layers.prepare_append(p['base_archive'],work/'parent',work/'target',p['target_archive']['database_sha256'])
    tick=time.perf_counter()
    if mode=='full':
        packed=dest/'packed';packed.mkdir();single=base.archive(work/'target',packed)
        entry=split_archive(single,dest/'parts');Path(single['path']).unlink()
        stats=dict(publication_seconds=time.perf_counter()-tick,preparation_seconds=prepared['seconds'],gzip_seconds=entry['gzip_seconds'])
    else:entry,stats=layers.publish_layer(prepared,dest/'layer')
    publication_complete_seconds=time.perf_counter()-started
    retained=sum(f.stat().st_size for f in dest.rglob('*') if f.is_file())
    with tempfile.TemporaryDirectory() as td:
        restored=Path(td)/'history';tick=time.perf_counter();layers.restore_archive(entry,restored)
        restore_seconds=time.perf_counter()-tick;tick=time.perf_counter();counts=equal_tables(restored,work/'target')
        equality_seconds=time.perf_counter()-tick;before=base.sha(restored);tick=time.perf_counter()
        readers=replay(restored,prepared['added_ids']);replay_seconds=time.perf_counter()-tick
        assert base.sha(restored)==before
    base.write(dest/'report.json',dict(protocol=old.binding(out/'protocol.json'),mode=mode,repeat=repeat,
        archive=entry,statistics=stats,publication_complete_seconds=publication_complete_seconds,
        cold_restore_seconds=restore_seconds,logical_equality_seconds=equality_seconds,
        new_dependency_replay_seconds=replay_seconds,complete_worker_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        new_retained_bytes=retained,required_compressed_bytes=entry['compressed_bytes'],
        added_rows=prepared['added_rows'],added_ids=prepared['added_ids'],preserved_rows=prepared['preserved_rows'],
        counts=counts,readers=readers,byte_identical_to_target=entry['database_sha256']==p['target_archive']['database_sha256']))


def run(out,work):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            subprocess.run([sys.executable,__file__,'trial',str(out),str(work),mode,str(repeat)],check=True)
            path=out/f'{mode}-{repeat}'/'report.json';r=base.load(path);samples.append(old.binding(path))
            print(mode,repeat,'publication',round(r['publication_complete_seconds'],4),'restore',round(r['cold_restore_seconds'],4),'new bytes',r['new_retained_bytes'],flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='inputs':inputs(out,Path(sys.argv[3]))
    elif action=='run':run(out,Path(sys.argv[3]))
    elif action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4],int(sys.argv[5]))
