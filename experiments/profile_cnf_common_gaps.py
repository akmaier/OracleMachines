#!/usr/bin/env python3
"""Profile a remaining miss and count opportunities on selected residual paths."""
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_common_consequence import CommonConsequenceInventory
from analyze_cnf_conditioning import load_nodes


def run(directory):
    report=json.loads((directory/'report.json').read_text())
    mechanisms=json.loads((directory/'mechanisms.json').read_text())
    entry=next(a for a in report['archives'] if a['mode']=='common');nodes=load_nodes(directory,entry)
    hashes={hashlib.sha256(k.encode()).hexdigest():k for k in nodes}
    indirect={a['key_sha256'] for a in mechanisms['nodes']['common']['equivalence_opportunities']
              if any(not r['explicit_binary_pair'] for r in a['relations'])}
    selected=set();affected=[];all_leaves=set()
    rows=[r for r in report['records'] if r['mode']=='common' and not r['discovery']['summary']['closed']]
    for row in rows:
        seen=set();stack=[hashes[row['discovery']['root_hash']]];potential=[]
        while stack:
            key=stack.pop()
            if key in seen:continue
            seen.add(key);n=nodes[key]
            if n['kind']=='and':stack.extend(e['key'] for e in n['edges'])
            elif n['kind']=='or':stack.extend(e['key'] for e in n['alternatives'][n['selected']]['edges'])
            elif n['kind'] in ('project','simplify','probe'):stack.append(n['edge']['key'])
            elif n['kind']=='unresolved':
                all_leaves.add(key)
                if hashlib.sha256(key.encode()).hexdigest() in indirect:
                    selected.add(key);potential.append(hashlib.sha256(key.encode()).hexdigest())
        if potential:affected.append(dict(case=row['case'],selected_indirect_nodes=potential))
    worst=max(rows,key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=CommonConsequenceInventory(Path(tmp)/'profile.sqlite3',max_depth=2,probe_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        functions=[]
        for (file,line,name),(primitive,calls,own,cumulative,_) in pstats.Stats(profiler).stats.items():
            functions.append(dict(file=file,line=line,name=name,primitive_calls=primitive,calls=calls,
                                  own_seconds=own,cumulative_seconds=cumulative))
    return dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        unresolved_roots=len(rows),selected_distinct_unresolved_nodes=len(all_leaves),
        selected_distinct_indirect_equivalence_nodes=len(selected),affected_roots=affected,
        selected_unresolved_literal_payload=sum(nodes[k]['profile']['shape']['literals'] for k in all_leaves),
        selected_indirect_literal_payload=sum(nodes[k]['profile']['shape']['literals'] for k in selected),
        profile=dict(case=worst,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:40]),
        limitations=['Selected-path opportunity counts do not imply any additional root closure',
                     'Implication pairs are already checked but substitution/transport and cost effects are not implemented',
                     'Profiler is separate from the uninstrumented operation comparison'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'gap-profile.json'
    if out.exists():raise ValueError('Preserve prior gap diagnostic')
    out.write_text(json.dumps(run(directory),indent=2)+'\n')
