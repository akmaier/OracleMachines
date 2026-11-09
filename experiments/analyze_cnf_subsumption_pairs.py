#!/usr/bin/env python3
"""Count avoidable equal-width comparisons in the saved deterministic searches."""
from bisect import bisect_left
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes


def main(directory):
    target=directory/'pair-costs.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    entry=next(a for a in report['archives'] if a['mode']=='subsumption')
    nodes=load_nodes(directory,entry);total=Counter();records=[]
    for key,node in nodes.items():
        if 'subsumption' not in node:continue
        cnf=node['cnf'];cert=node['subsumption']['certificate'];removed=dict(cert['removed'])
        # The inventory normalization gives distinct clauses with distinct
        # literals. At equal width, inclusion therefore implies equality and
        # cannot hold for two different source clauses.
        assert len(set(map(tuple,cnf)))==len(cnf)
        assert all(len(set(c))==len(c) for c in cnf)
        positions={};widths=[];counts=Counter()
        for j in sorted(range(len(cnf)),key=lambda j:(len(cnf[j]),j)):
            tests=positions[removed[j]]+1 if j in removed else len(widths)
            shorter=min(tests,bisect_left(widths,len(cnf[j])))
            counts['subset_tests']+=tests
            counts['strictly_shorter_tests']+=shorter
            counts['equal_width_tests']+=tests-shorter
            if j not in removed:
                positions[j]=len(widths);widths.append(len(cnf[j]))
        assert sorted(positions)==cert['kept']
        total.update(counts)
        records.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),
            shape=node['profile']['shape'],kind=node['kind'],counts=dict(counts)))
    actual=sum(r['discovery']['metrics'].get('subsumption_discovery_subset_tests',0)
               for r in report['records'] if r['mode']=='subsumption')
    assert total['subset_tests']==actual
    result=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=records,
        counts=dict(total),equal_width_fraction=total['equal_width_tests']/actual,
        limitations=['Counts reconstruct tested prefix lengths from independently replayed saved certificates',
          'Equal-width exclusion requires distinct normalized clauses and distinct literals within each clause',
          'Only discovery comparisons counted here; ordinary validation repeats the same search',
          'This is a diagnostic, not an implemented optimized policy or a measured runtime saving',
          'Proper-width subset tests, proof replay, classification and persistence remain costs'])
    target.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','limitations')}))


if __name__=='__main__':main(Path(sys.argv[1]))
