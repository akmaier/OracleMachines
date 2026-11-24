"""Transport a checked gzip history in bounded files without changing its bytes.

A trusted descriptor binds every part, the concatenated gzip, and the complete
uncompressed database. Byte identity is not a replacement for SAT verification.
Legacy single-file archives remain readable. Sources are never removed here.
"""
import gzip,hashlib,json,os
from pathlib import Path
import tempfile,time
from experiments import compare_cnf_bootstrap as legacy

FORMAT='cnf-history-parts-v1'
BLOCK=1024*1024


def split_archive(entry,directory,part_bytes=48*1024*1024):
    started=time.perf_counter()
    if type(part_bytes) is not int or part_bytes<1:raise ValueError('Invalid archive part size')
    if 'format' in entry:raise ValueError('Expected a single gzip archive')
    source=Path(entry['path']);directory=Path(directory)
    if legacy.sha(source)!=entry['sha256'] or source.stat().st_size!=entry['compressed_bytes']:
        raise ValueError('Changed source archive')
    directory.mkdir(parents=True,exist_ok=False);parts=[]
    with source.open('rb') as inp:
        while True:
            raw=inp.read(part_bytes)
            if not raw:break
            path=directory/f'history.gz.part-{len(parts):04d}'
            with path.open('xb') as dst:dst.write(raw)
            parts.append(dict(path=str(path),bytes=len(raw),sha256=legacy.sha(path)))
    descriptor=dict(format=FORMAT,parts=parts,compressed_sha256=entry['sha256'],
        compressed_bytes=entry['compressed_bytes'],database_sha256=entry['database_sha256'],
        database_bytes=entry['database_bytes'])
    path=directory/'history.parts.json'
    with path.open('x') as dst:json.dump(descriptor,dst,indent=2,sort_keys=True);dst.write('\n')
    descriptor_sha=legacy.sha(path);elapsed=time.perf_counter()-started
    return dict(format=FORMAT,path=str(path),sha256=descriptor_sha,
        compressed_bytes=entry['compressed_bytes'],database_sha256=entry['database_sha256'],
        database_bytes=entry['database_bytes'],seconds=entry['seconds']+elapsed,
        gzip_seconds=entry['seconds'],split_seconds=elapsed)


def restore_archive(entry,destination):
    if 'format' not in entry:return legacy.restore_archive(entry,destination)
    if entry['format']!=FORMAT:raise ValueError('Unknown archive format')
    source=Path(entry['path']);destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    if legacy.sha(source)!=entry['sha256']:raise ValueError('Changed archive descriptor')
    d=json.loads(source.read_text())
    if set(d)!={'format','parts','compressed_sha256','compressed_bytes','database_sha256','database_bytes'}:
        raise ValueError('Invalid archive descriptor')
    if d['format']!=FORMAT or not isinstance(d['parts'],list) or not d['parts']:
        raise ValueError('Invalid archive parts')
    for key in ('compressed_bytes','database_bytes'):
        if type(d[key]) is not int or d[key]<1 or d[key]!=entry[key]:raise ValueError('Invalid archive byte count')
    if d['database_sha256']!=entry['database_sha256']:raise ValueError('Changed database binding')
    with tempfile.TemporaryDirectory(dir=destination.parent) as td:
        packed=Path(td)/'packed';compressed_hash=hashlib.sha256();total=0
        with packed.open('xb') as out:
            for i,part in enumerate(d['parts']):
                if set(part)!={'path','bytes','sha256'} or type(part['bytes']) is not int or part['bytes']<1:
                    raise ValueError('Invalid archive part')
                path=Path(part['path'])
                if path!=source.parent/f'history.gz.part-{i:04d}':raise ValueError('Unexpected archive part path')
                count=0;digest=hashlib.sha256()
                with path.open('rb') as inp:
                    for block in iter(lambda:inp.read(BLOCK),b''):
                        count+=len(block);total+=len(block)
                        if count>part['bytes'] or total>d['compressed_bytes']:raise ValueError('Oversized archive part')
                        digest.update(block);compressed_hash.update(block);out.write(block)
                if count!=part['bytes'] or digest.hexdigest()!=part['sha256']:raise ValueError('Changed archive part')
        if total!=d['compressed_bytes'] or compressed_hash.hexdigest()!=d['compressed_sha256']:
            raise ValueError('Changed concatenated archive')
        raw=Path(td)/'database';digest=hashlib.sha256();total=0
        with gzip.open(packed,'rb') as inp,raw.open('xb') as out:
            for block in iter(lambda:inp.read(BLOCK),b''):
                total+=len(block)
                if total>d['database_bytes']:raise ValueError('Oversized database')
                digest.update(block);out.write(block)
        if total!=d['database_bytes'] or digest.hexdigest()!=d['database_sha256']:
            raise ValueError('Changed history database')
        os.link(raw,destination)
