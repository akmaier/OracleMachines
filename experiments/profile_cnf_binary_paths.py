#!/usr/bin/env python3
"""Explain a retained bounded-coverage loss and profile the slowest new query."""
import cProfile
import gzip
import hashlib
import json
from pathlib import Path
import pstats
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_pattern_inventory import encode


def main(directory):
    target=directory/'gap-profile.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    rows={(r['mode'],r['case']):r for r in report['records']}
    losses=[i for i in range(len(report['cases'])) if rows['baseline',i]['discovery']['summary']['closed']
            and not rows['binary_paths',i]['discovery']['summary']['closed']]
    selected={};source_bindings={}
    for archive in report['archives']:
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'a.db'
            with gzip.open(archive['path'],'rb') as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
            with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==archive['database_sha256']
            db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
            wanted={encode(report['cases'][i]['source']):i for i in losses};roots={}
            for payload, in db.execute('SELECT payload FROM cnf_pattern_sources_v1'):
                record=json.loads(payload);i=wanted.get(encode(record['source']))
                if i is not None:roots[i]=record['root']['key']
            for i,root in roots.items():
                seen=set();stack=[root];nodes=[]
                while stack:
                    key=stack.pop()
                    if key in seen:continue
                    seen.add(key);node=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()[0]);nodes.append(node)
                    edges=(node['edges'] if node['kind']=='and' else
                        node['alternatives'][node['selected']]['edges'] if node['kind']=='or' else
                        [node['edge']] if 'edge' in node else [])
                    stack.extend(e['key'] for e in edges)
                selected[archive['mode'],i]=nodes
            db.close()
    explanations=[]
    for i in losses:
        old={(n['depth'],encode(n['cnf'])):n for n in selected['baseline',i]}
        changed=[]
        for new in selected['binary_paths',i]:
            if new['kind']!='binary_paths':continue
            before=old.get((new['depth'],encode(new['cnf'])))
            if before is not None:
                changed.append(dict(source=new['cnf'],depth=new['depth'],old_kind=before['kind'],
                    old_summary=before['summary'],new_summary=new['summary'],certificate=new['binary_paths'],
                    old_alternatives=before.get('alternatives'),new_edge=new['edge']))
        explanations.append(dict(case=i,source=report['cases'][i],shared_reduction_states=changed,
                                 selected_graphs={m:selected[m,i] for m in ('baseline','binary_paths')}))
    worst=max((r for r in report['records'] if r['mode']=='binary_paths'),key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=BinaryPathInventory(Path(tmp)/'profile.db',**report['modes']['binary_paths']['options'])
        profile=cProfile.Profile();profile.enable();result=h.inspect(report['cases'][worst]['source']);profile.disable();h.close()
        functions=[]
        for (file,line,name),(primitive,calls,own,cumulative,_) in pstats.Stats(profile).stats.items():
            if '/experiments/' in file:
                functions.append(dict(file=file,line=line,function=name,calls=calls,own_seconds=own,cumulative_seconds=cumulative))
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),losses=explanations,
        profile=dict(case=worst,instrumented_seconds=result['seconds'],counts=result['metrics'],
                     functions=sorted(functions,key=lambda r:-r['own_seconds'])[:20]),
        limitations=['Read-only archive analysis; all failed and successful plans remain preserved',
          'Shared reduction states explain where exact equivalent rewriting changes the input to the bounded heuristic',
          'Profile is a separate cold single-source run, not full-corpus timing or identical full-history cache state',
          'Nested cumulative times overlap and must not be added; no end-to-end speedup follows'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(losses=[(r['case'],len(r['shared_reduction_states'])) for r in explanations],
                         worst=worst,functions=output['profile']['functions'][:8])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
