#!/usr/bin/env python3
"""Keep the two changed source paths as explicit selection counterexamples."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.cnf_learning_selection import activation_masks
from experiments.cnf_probe_learning import learning_batch


def analyze(directory):
    report=json.loads((directory/'report.json').read_text());mechanisms=json.loads((directory/'mechanisms.json').read_text())
    nodes=load_nodes(directory,next(a for a in report['archives'] if a['mode']=='selection'))
    hashes={hashlib.sha256(k.encode()).hexdigest():k for k in nodes};rows=[]
    for item in mechanisms['changed_nodes']:
        if not item['gained_source_paths'] and not item['lost_source_paths']:continue
        n=nodes[hashes[item['key_sha256']]];attempts=n['profile']['probing']['attempts'];counts=Counter()
        pool=learning_batch(n['cnf'],attempts,16,counts);masks=activation_masks(pool,attempts,counts)
        detail={}
        for label in ('old_batch','new_batch'):
            mask=0
            for b in item[label]:mask|=masks[pool.index(b)]
            detail[label]=dict(active_assumptions=[dict(variable=a['variable'],value=a['value'])
                               for i,a in enumerate(attempts) if mask & (1<<i)],
                               origin_assumptions=len({b['attempt'] for b in item[label]}))
        controls={}
        for label,control in item['controls'].items():
            last=control['attempts'][-1]
            controls[label]=dict(status=control['status'],attempts=len(control['attempts']),
                first_conflict=(dict(variable=last['variable'],value=last['value']) if control['status']=='forced' else None))
        rows.append(dict(key_sha256=item['key_sha256'],parent_cnf=n['cnf'],depth=n['depth'],
            gained_source_paths=item['gained_source_paths'],lost_source_paths=item['lost_source_paths'],
            original_choices=[a['variable'] for a in attempts if not a['value']],
            old_choices=item['old_choices'],new_choices=item['new_choices'],
            old_batch=item['old_batch'],new_batch=item['new_batch'],activation=detail,controls=controls,counters=dict(counts)))
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        mechanisms_sha256=hashlib.sha256((directory/'mechanisms.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),paths=rows,
        limitations=['Summarizes checked local controls; does not run counterfactual whole-source policies',
          'Equal activation counts can describe different assumptions and different propagation strength',
          'Keeping old continuation choices is a next experiment, not a proven coverage-preserving fix'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'selection-paths.json'
    if out.exists():raise ValueError('Preserve earlier path diagnostics')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
