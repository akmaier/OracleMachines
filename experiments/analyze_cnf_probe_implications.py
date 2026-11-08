#!/usr/bin/env python3
"""Measure unused common consequences in already checked inconclusive probes.

This inventories an opportunity only: it neither changes the planner nor counts
these consequences as new coverage. Both assumption traces must be complete and
non-conflicting in a profile already validated by the main cold archive audit.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from analyze_cnf_conditioning import load_nodes


def analyze(directory):
    report=json.loads((directory/'report.json').read_text())
    entry=next(a for a in report['archives'] if a['mode']=='probe4')
    nodes=load_nodes(directory,entry);potential=[];kinds=Counter()
    for key,node in nodes.items():
        p=node['profile'].get('probing',{})
        if p.get('status')!='clear':continue
        attempts=p['attempts'];facts=[]
        for low,high in zip(attempts[::2],attempts[1::2]):
            assert low['variable']==high['variable'] and low['value'] is False and high['value'] is True
            assert low['certificate']['conflict'] is None and high['certificate']['conflict'] is None
            a={lit for lit,_ in low['certificate']['units']};b={lit for lit,_ in high['certificate']['units']}
            common=sorted(a&b,key=abs)
            if common:facts.append(dict(variable=low['variable'],common_literals=common))
        if facts:
            kinds[node['kind']]+=1
            potential.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),kind=node['kind'],depth=node['depth'],facts=facts))
    return dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        nodes_by_kind=dict(kinds),potential=potential,
        limitations=['Existing checked traces only; no new search or coverage result',
                     'Common consequence follows by Boolean case split; no uniform completeness or cost guarantee',
                     'Applying consequences changes residuals, candidate ordering and reuse; matched implementation study still required'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'common-implication-opportunity.json'
    if out.exists():raise ValueError('Preserve earlier opportunity analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
