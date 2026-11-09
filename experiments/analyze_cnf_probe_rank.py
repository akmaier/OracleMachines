#!/usr/bin/env python3
"""Retain where existing probe information changes order or is unavailable."""
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
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_rank import choices_after_checked_probes
from experiments.cnf_residual_dag import normalize


def main(directory):
    target=directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    path=directory/'report.json';report=json.loads(path.read_text());nodes={}
    for archive in report['archives']:
        assert archive['audit']['bytes_unchanged']
        raw=gzip.decompress(Path(archive['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==archive['database_sha256']
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/'history.db';dbpath.write_bytes(raw)
            db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
            nodes[archive['mode']]={(n['depth'],encode(n['cnf'])):n for payload, in db.execute('SELECT payload FROM cnf_patterns_v1') for n in [json.loads(payload)]}
            db.close()
    sources={}
    for i,case in enumerate(report['cases']):
        cnf,_=normalize(case['source'])
        sources.setdefault(encode(cnf),[]).append(i)
    rows=[];counts=Counter()
    for key,new in nodes['probe_rank'].items():
        if new['kind']!='or':continue
        old=nodes['baseline'].get(key)
        assert old and old['kind']=='or'
        source=new['cnf'];probing=new['profile']['probing'];limit=report['modes']['probe_rank']['options'].get('candidate_limit',4)
        a=shortest_balanced_choices(source,limit,Counter())
        b=choices_after_checked_probes(source,probing,limit,Counter())
        assert set(a)==set(b)
        attempts={(p['variable'],p['value']):p for p in probing.get('attempts',[])}
        effects=[]
        for v in a:
            sizes=[len(attempts[v,value]['certificate']['units']) if (v,value) in attempts else None for value in (False,True)]
            measured=all(s is not None for s in sizes)
            counts['measured_candidates' if measured else 'unknown_candidates']+=1
            effects.append(dict(variable=v,original_unit_counts=sizes))
        binary=sum(len(c)==2 for c in source)
        counts['or_nodes']+=1;counts['changed_orders']+=a!=b;counts['without_binary_clauses']+=binary==0
        counts['baseline_attempts']+=len(old['alternatives']);counts['probe_rank_attempts']+=len(new['alternatives'])
        def winner(node):
            return next((a['variable'] for a in node['alternatives'] if a['summary']['closed']),None)
        rows.append(dict(source_cases=sources.get(key[1],[]),depth=key[0],cnf=source,binary_clauses=binary,
            before=a,after=b,effects=effects,
            baseline_attempts=[a['variable'] for a in old['alternatives']],
            probe_rank_attempts=[a['variable'] for a in new['alternatives']],
            baseline_winner=winner(old),probe_rank_winner=winner(new)))
    payload=dict(report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counts=dict(counts),rows=rows,
        limitations=['Reads the complete independently cold-checked archives bound in the report; does not acquire new proofs',
          'Counts distinct acquired OR nodes; discovery/check operation counters in report can count the same node twice',
          'Only original-pass proofs count; missing branches have null counts, not zero',
          'Single-variable unit propagation cannot start on a normalized CNF with all clauses of width at least three',
          'No unit effects does not rule out other useful changes, recognized classes or multi-variable interactions'])
    target.write_text(json.dumps(payload,indent=2)+'\n');print(dict(counts),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
