"""Publish an append-only six-table history as an immutable parent plus delta.

Inputs are closed, exclusively owned snapshots of already checked histories.
Hashes bind bytes to the caller's trusted entry; they do not prove SAT claims.
Legacy archives remain readable, and native proof checking stays separate.
"""
from pathlib import Path
import json,os,shutil,sqlite3,tempfile,time
from experiments import cnf_archive_parts as parts
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_accounted_residuals import TABLE as LEDGER, TRIGGERS

FORMAT='cnf-history-layer-v1'
TABLES=('cnf_residual_v1','cnf_affine_negative_v1','cnf_binary_equivalence_v1',
        'cnf_binary_equivalence_v2','cnf_binary_equivalence_v3','cnf_binary_core_discovery_v1')
COLS=[(0,'id','TEXT',0,None,1),(1,'payload','TEXT',1,None,0)]


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)


def schema(db, prefix='main', *, delta=False):
    rows=db.execute(f'SELECT type,name,tbl_name,sql FROM {prefix}.sqlite_master ORDER BY type,name').fetchall()
    tables={r[1] for r in rows if r[0]=='table'}
    if tables!=set(TABLES)|({LEDGER} if not delta else set()):
        raise ValueError('Unsupported history tables; use a full snapshot')
    for t in TABLES:
        if db.execute(f'PRAGMA {prefix}.table_info({t})').fetchall()!=COLS:
            raise ValueError('Unsupported history columns')
    allowed_indexes={'sqlite_autoindex_'+t+'_1' for t in TABLES}
    wanted={LEDGER+'_'+suffix:'CREATE TRIGGER '+LEDGER+'_'+suffix+' '+body for suffix,body in TRIGGERS.items()}
    for kind,name,table,sql in rows:
        if kind=='table':continue
        if kind=='index' and name in allowed_indexes and sql is None:continue
        if not delta and kind=='trigger' and wanted.get(name)==sql:continue
        raise ValueError('Unsupported history schema object')
    if not delta and {r[1] for r in rows if r[0]=='trigger'}!=set(wanted):
        raise ValueError('Missing accounting triggers')
    return rows


def ledger(db, prefix='main'):
    rows=db.execute(f'SELECT singleton,nodes,payload_units,dirty FROM {prefix}.{LEDGER}').fetchall()
    if (len(rows)!=1 or rows[0][0]!=1 or rows[0][3] not in (0,1) or
            any(type(n) is not int or n<0 for n in rows[0][1:3])):
        raise ValueError('Invalid accounting state; use a full snapshot')
    return rows[0]


def prepare_append(parent_entry,parent_path,target_path,target_sha256):
    """Validate closed snapshot identity and exact old-payload preservation.

    The old AppendDelta cursor targets eight different tables and a live owned
    connection. Here two frozen snapshots require an explicit six-table diff.
    """
    started=time.perf_counter();parent_path=Path(parent_path);target_path=Path(target_path)
    for path in (parent_path,target_path):
        for suffix in ('-wal','-journal'):
            side=Path(str(path)+suffix)
            if side.exists() and side.stat().st_size:raise ValueError('Close and checkpoint the input')
    if base.sha(parent_path)!=parent_entry['database_sha256'] or parent_path.stat().st_size!=parent_entry['database_bytes']:
        raise ValueError('Changed parent snapshot')
    if base.sha(target_path)!=target_sha256:raise ValueError('Changed target snapshot')
    db=readonly(target_path);preserved={};added={};added_ids={}
    try:
        db.execute('ATTACH DATABASE ? AS prior',(parent_path.resolve().as_uri()+'?mode=ro',))
        if schema(db)!=schema(db,'prior'):raise ValueError('Changed schema; use a full snapshot')
        before=ledger(db,'prior');after=ledger(db)
        for t in TABLES:
            if db.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} n ON p.id=n.id WHERE n.id IS NULL OR n.payload!=p.payload').fetchone()[0]:
                raise ValueError('Changed prior payload; use a full snapshot')
            preserved[t]=db.execute(f'SELECT count(*) FROM prior.{t}').fetchone()[0]
            added_ids[t]=[r[0] for r in db.execute(f'SELECT n.id FROM main.{t} n WHERE NOT EXISTS (SELECT 1 FROM prior.{t} p WHERE p.id=n.id) ORDER BY n.rowid')]
            added[t]=len(added_ids[t])
            if db.execute(f"SELECT count(*) FROM main.{t} WHERE typeof(id)!='text' OR typeof(payload)!='text'").fetchone()[0]:
                raise ValueError('History rows must contain text')
        units=sum(db.execute('SELECT length(id)+length(payload) FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()[0] for key in added_ids[TABLES[0]])
        if before[3]:
            # Dirty counters are stale metadata, never resource authority.
            if after!=before:raise ValueError('Changed dirty accounting state')
        elif before[1]!=preserved[TABLES[0]] or after!=(1,before[1]+added[TABLES[0]],before[2]+units,0):
            raise ValueError('Changed accounting state')
    finally:db.close()
    return dict(parent=parent_entry,parent_path=str(parent_path),target_path=str(target_path),
        target_sha256=target_sha256,preserved_rows=preserved,added_rows=added,added_ids=added_ids,seconds=time.perf_counter()-started)


def export_delta(prepared,destination):
    """Preserve insertion order; export only rows absent from the checked parent."""
    destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    db=readonly(prepared['target_path']);out=sqlite3.connect(destination)
    try:
        with out:
            for t in TABLES:
                out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                for key in prepared['added_ids'][t]:
                    row=db.execute(f'SELECT id,payload FROM {t} WHERE id=?',(key,)).fetchone()
                    if row is None:raise ValueError('Missing prepared append row')
                    out.execute(f'INSERT INTO {t} VALUES (?,?)',row)
                if out.execute(f'SELECT count(*) FROM {t}').fetchone()[0]!=prepared['added_rows'][t]:
                    raise ValueError('Changed append set')
    finally:out.close();db.close()


def apply_delta(history,delta,preserved,added):
    db=sqlite3.connect(history);source=readonly(delta)
    try:
        schema(db);schema(source,delta=True);ledger(db)
        with db:
            for t in TABLES:
                if db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]!=preserved[t]:raise ValueError('Wrong parent row count')
                if source.execute(f'SELECT count(*) FROM {t}').fetchone()[0]!=added[t]:raise ValueError('Wrong append row count')
                for key,payload in source.execute(f'SELECT id,payload FROM {t} ORDER BY rowid'):
                    if type(key) is not str or type(payload) is not str:raise ValueError('Invalid append row')
                    if db.execute(f'SELECT 1 FROM {t} WHERE id=?',(key,)).fetchone() is not None:
                        raise ValueError('Duplicate or conflicting append key')
                    db.execute(f'INSERT INTO {t} VALUES (?,?)',(key,payload))
            ledger(db)
    finally:source.close();db.close()


def publish_layer(prepared,directory):
    """Publish from prepare_append's exclusively owned immutable inputs."""
    started=time.perf_counter();directory=Path(directory);directory.mkdir(exist_ok=False)
    parent=prepared['parent'];depth=parent.get('depth',0)+1
    if depth>32:raise ValueError('Compact the layer chain before publishing')
    with tempfile.TemporaryDirectory(dir=directory) as td:
        temp=Path(td);delta=temp/'delta';tick=time.perf_counter();export_delta(prepared,delta)
        delta_dir=directory/'delta';delta_dir.mkdir();packed=base.archive(delta,delta_dir)
        export_seconds=time.perf_counter()-tick
        tick=time.perf_counter();restored=temp/'restored';shutil.copyfile(prepared['parent_path'],restored)
        apply_delta(restored,delta,prepared['preserved_rows'],prepared['added_rows'])
        database_sha256=base.sha(restored);database_bytes=restored.stat().st_size
        reconstruction_seconds=time.perf_counter()-tick
    descriptor=dict(format=FORMAT,parent=parent,delta=packed,depth=depth,
        preserved_rows=prepared['preserved_rows'],added_rows=prepared['added_rows'],
        database_sha256=database_sha256,database_bytes=database_bytes,
        compressed_bytes=parent['compressed_bytes']+packed['compressed_bytes'])
    path=directory/'history.layer.json';base.write(path,descriptor)
    entry={k:descriptor[k] for k in ('format','depth','database_sha256','database_bytes','compressed_bytes')}
    entry.update(path=str(path),sha256=base.sha(path),incremental_compressed_bytes=packed['compressed_bytes'],
        incremental_retained_bytes=packed['compressed_bytes']+path.stat().st_size)
    return entry,dict(export_seconds=export_seconds,reconstruction_seconds=reconstruction_seconds,
        publication_seconds=time.perf_counter()-started,preparation_seconds=prepared['seconds'])


def restore_archive(entry,destination,*,max_depth=32):
    """Materialize in a temporary location; never publish partial restores."""
    if type(max_depth) is not int or max_depth<0:raise ValueError('Invalid layer depth limit')
    destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    with tempfile.TemporaryDirectory(dir=destination.parent) as td:
        temp=Path(td);raw=temp/'history'
        if entry.get('format')!=FORMAT:
            parts.restore_archive(entry,raw)
        else:
            if max_depth==0:raise ValueError('Layer depth limit exceeded')
            path=Path(entry['path'])
            if base.sha(path)!=entry['sha256']:raise ValueError('Changed layer descriptor')
            d=json.loads(path.read_text())
            if set(d)!={'format','parent','delta','depth','preserved_rows','added_rows','database_sha256','database_bytes','compressed_bytes'}:
                raise ValueError('Invalid layer fields')
            for k in ('format','depth','database_sha256','database_bytes','compressed_bytes'):
                if d[k]!=entry[k]:raise ValueError('Changed layer binding')
            if type(d['depth']) is not int or d['depth']!=d['parent'].get('depth',0)+1 or d['depth']>max_depth:
                raise ValueError('Invalid layer depth')
            if d['compressed_bytes']!=d['parent']['compressed_bytes']+d['delta']['compressed_bytes']:
                raise ValueError('Incorrect dependency size')
            for field in ('preserved_rows','added_rows'):
                if set(d[field])!=set(TABLES) or any(type(n) is not int or n<0 for n in d[field].values()):
                    raise ValueError('Invalid layer row counts')
            restore_archive(d['parent'],raw,max_depth=max_depth-1)
            delta=temp/'delta';restore_archive(d['delta'],delta,max_depth=0)
            apply_delta(raw,delta,d['preserved_rows'],d['added_rows'])
            if raw.stat().st_size!=d['database_bytes'] or base.sha(raw)!=d['database_sha256']:
                raise ValueError('Changed reconstructed history')
        os.link(raw,destination)
