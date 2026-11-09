#!/usr/bin/env python3
"""Compare all retained alternatives for the full-study bounded closure loss."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import encode


def main(directory):
    target=directory/'loss-alternatives.json'
    if target.exists():raise FileExistsError(target)
    path=directory/'report.json';report=json.loads(path.read_text());case=1471
    source=encode(report['cases'][case]['source']);graphs={}
    for archive in report['archives']:
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/'a.db'
            with gzip.open(archive['path'],'rb') as a,dbpath.open('wb') as b:shutil.copyfileobj(a,b)
            with dbpath.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==archive['database_sha256']
            db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
            root=next(n['root']['key'] for payload, in db.execute('SELECT payload FROM cnf_pattern_sources_v1')
                      for n in [json.loads(payload)] if encode(n['source'])==source)
            nodes={};stack=[root]
            while stack:
                key=stack.pop()
                if key in nodes:continue
                n=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()[0]);nodes[key]=n
                edges=(n['edges'] if n['kind']=='and' else [e for a in n['alternatives'] for e in a['edges']]
                       if n['kind']=='or' else [n['edge']] if 'edge' in n else [])
                stack.extend(e['key'] for e in edges)
            graphs[archive['mode']]=nodes;db.close()
    before={(n['depth'],encode(n['cnf'])):n for n in graphs['baseline'].values()};changed=[]
    def plan(n):
        return dict(kind=n['kind'],summary=n['summary'],alternatives=[dict(variable=a['variable'],summary=a['summary']) for a in n.get('alternatives',[])])
    for n in graphs['binary_paths'].values():
        old=before.get((n['depth'],encode(n['cnf'])))
        if n['kind']!='binary_paths' or old is None:continue
        child=graphs['binary_paths'][n['edge']['key']]
        changed.append(dict(cnf=n['cnf'],depth=n['depth'],certificate=n['binary_paths'],old=plan(old),
                            after=plan(n),child=plan(child),child_cnf=child['cnf'],child_names=n['edge']['names']))
    target.write_text(json.dumps(dict(case=case,report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),shared_reductions=changed,
        limitations=['All saved alternatives are traversed, not only the different selected plans',
                     'Child variable IDs must be transported through child_names before comparing choices']),indent=2)+'\n')
    print(json.dumps([dict(depth=r['depth'],old=r['old'],after=r['after'],child=r['child'],names=r['child_names']) for r in changed]),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
