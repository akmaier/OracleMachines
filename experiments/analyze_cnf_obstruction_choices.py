#!/usr/bin/env python3
"""Explain matched frontier gains/losses using exact saved source identities."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_obstruction_choices import obstruction_choices
from experiments.cnf_pattern_inventory import encode


def first_splits(nodes, root):
    out=[];stack=[root];seen=set()
    while stack:
        key=stack.pop()
        if key in seen:continue
        seen.add(key);n=nodes[key]
        if n['kind']=='or':out.append(n)
        elif n['kind']=='and':stack.extend(e['key'] for e in n['edges'])
        elif 'edge' in n:stack.append(n['edge']['key'])
    return out


def main(directory):
    dest=directory/'mechanisms.json'
    if dest.exists():raise FileExistsError(dest)
    path=directory/'report.json';report=json.loads(path.read_text());summary=json.loads((directory/'summary.json').read_text())
    changed={i:'gain' for i in summary[1]['gains']};changed.update({i:'loss' for i in summary[1]['losses']})
    stores={};by_source={};roots={}
    for archive in report['archives']:
        mode=archive['mode'];raw=gzip.decompress(Path(archive['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==archive['database_sha256']
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/'history.db';dbpath.write_bytes(raw);db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
            nodes={k:json.loads(v) for k,v in db.execute('SELECT id,payload FROM cnf_patterns_v1')}
            root_map={hashlib.sha256(k.encode()).hexdigest():k for k in nodes};db.close()
        stores[mode]=nodes;roots[mode]=root_map
        by_source[mode]={(n['depth'],encode(n['cnf'])):n for n in nodes.values()}
    rows=[]
    for case,change in sorted(changed.items()):
        observed={}
        for mode in stores:
            record=next(r for r in report['records'] if r['mode']==mode and r['case']==case)
            root=roots[mode][record['discovery']['root_hash']]
            observed[mode]=first_splits(stores[mode],root)
        pairs=[]
        for old in observed['baseline']:
            source_key=(old['depth'],encode(old['cnf']));new=by_source['obstruction'].get(source_key)
            if new is None or new['kind']!='or':continue
            cert=new['conditioning_obstruction'];old_choices=shortest_balanced_choices(old['cnf'],4,Counter())
            new_choices=obstruction_choices(new['cnf'],cert,4,Counter())
            clauses=sorted({edge[1] for direction in ('forward','backward') for edge in cert.get(direction,[])})
            support=sorted({abs(l) for cid in clauses for l in new['cnf'][cid]})
            winning={}
            for mode,node in (('baseline',old),('obstruction',new)):
                winning[mode]=[a['variable'] for a in node['alternatives'] if a['summary']['closed']]
            pairs.append(dict(cnf=old['cnf'],depth=old['depth'],old_choices=old_choices,new_choices=new_choices,
                winning=winning,certificate=cert,obstruction_clauses=clauses,obstruction_support=support,
                lost_winner_outside_support=[v for v in winning['baseline'] if v not in support],
                gained_winner_outside_old_choices=[v for v in winning['obstruction'] if v not in old_choices]))
        rows.append(dict(case=case,change=change,matched_first_splits=pairs))
    output=dict(report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),changes=rows,
        limits=['Diagnostic reads audited archives without modifying rows or changing either search policy',
                'Variables are local to the exact shared normalized source in each recorded split',
                'One fixed auxiliary refutation need not identify the best conditioning variable',
                'This frontier experiment does not establish additional original-source coverage'])
    dest.write_text(json.dumps(output,indent=2)+'\n')
    for row in rows:
        print(row['case'],row['change'],[(p['old_choices'],p['new_choices'],p['winning'],p['lost_winner_outside_support']) for p in row['matched_first_splits']],flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
