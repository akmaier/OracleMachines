#!/usr/bin/env python3
"""Count which prepared proof kinds are actually referenced; read-only."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile


def main(directory):
    target=directory/'references.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    archive=next(a for a in report['archives'] if a['mode']=='retained');counts=Counter();rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'a.db'
        with gzip.open(archive['path'],'rb') as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==archive['database_sha256']
        db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
        for key,payload in db.execute('SELECT id,payload FROM cnf_patterns_v1'):
            node=json.loads(payload)
            if node['kind']!='retained_plan':continue
            old=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(node['reference'],)).fetchone()[0])
            assert node['cnf']==old['cnf'] and old['summary']['closed'] is True
            counts[old['kind']]+=1
            rows.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),old_kind=old['kind'],
                literals=sum(map(len,node['cnf'])),depth=node['depth'],
                wrapper_bytes=len(key.encode())+len(payload.encode()),reference_key_bytes=len(node['reference'].encode())))
        db.close()
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),referenced_kinds=dict(counts),
        references=len(rows),wrapper_bytes=sum(r['wrapper_bytes'] for r in rows),
        reference_key_bytes=sum(r['reference_key_bytes'] for r in rows),rows=rows,
        limitations=['Counts persisted references, including unselected alternatives; query counts and unique original sources differ',
                     'A family reference may replace one cheap family node without avoiding descendants; its usefulness requires a total-cost comparison',
                     'Read-only diagnostic on previously fully cold-checked archives; no acquisition timing claim'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('rows','limitations')}),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
