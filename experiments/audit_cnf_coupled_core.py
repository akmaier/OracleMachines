#!/usr/bin/env python3
"""Audit the new unresolved core's two-step admission barrier, without recognition."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pivot_alternatives import alternatives
from experiments.cnf_coupled_pivots import project_pair
from experiments.compare_cnf_frontier_pivots import unpack
from experiments.compare_cnf_retained_plans import sha


def main(directory):
    output=directory/'core-admission-audit.json'
    if output.exists():raise FileExistsError(output)
    rp=directory/'report.json';r=json.loads(rp.read_text());d=r['delta'];assert sha(d['path'])==d['sha256'];cores=[]
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'delta';unpack(d['path'],path,d['database_sha256']);db=sqlite3.connect(path)
        for key,payload in db.execute('SELECT id,payload FROM cnf_patterns_v1'):
            node=json.loads(payload)
            if node['kind']!='unresolved':continue
            source=node['cnf'];counts=Counter();pairs=[];first_rows=[]
            # With at most 64 resolvents, allowance 64 cannot reject a
            # pair-admissible single step. This diagnoses a relaxed candidate
            # space only; it changes neither the experiment nor its checker.
            first=alternatives(source,None,counts,pair_limit=64,candidate_limit=64,clause_growth_limit=64)
            for a in first:
                first_rows.append(dict(variable=a['variable'],pairs=a['pairs'],growth=len(a['target'])-len(source)))
                second=alternatives(a['target'],None,counts,pair_limit=64,candidate_limit=64,clause_growth_limit=64)
                for b in second:
                    intermediate,target=project_pair(source,[a['variable'],b['variable']],counts,pair_limit=64,clause_growth_limit=64)
                    assert intermediate==a['target'] and target==b['target']
                    interacting=any(a['variable'] in set(map(abs,c)) and b['variable'] in set(map(abs,c)) for c in source)
                    pairs.append(dict(variables=[a['variable'],b['variable']],first_growth=len(intermediate)-len(source),
                        net_growth=len(target)-len(source),literal_change=sum(map(len,target))-sum(map(len,source)),
                        pair_counts=[a['pairs'],b['pairs']],interacting=interacting,syntactic_family_score=b['score'][0]))
            cores.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),source=source,shape=node['profile']['shape'],
                first_pivots=first_rows,minimum_first_growth=min((x['growth'] for x in first_rows),default=None),
                ordered_pairs=pairs,minimum_pair_growth=min((x['net_growth'] for x in pairs),default=None),
                net_four_candidates=sum(x['net_growth']<=4 for x in pairs),
                net_four_interacting_candidates=sum(x['net_growth']<=4 and x['interacting'] for x in pairs),
                counts=dict(counts)))
        db.close()
    result=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(rp),cores=cores,limitations=[
        'Read-only candidate-space audit of newly archived unresolved nodes, not a change to frozen pair/growth limits or a timed coverage experiment.',
        'Every enumerated two-step projection is independently reconstructed, but no recognizer is called and no endpoint or original closure follows.',
        'Only pair-admissible pivots among the first 64 variables at each step are considered; both orders and interacting/noninteracting pairs are retained.'])
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([dict(shape=x['shape'],first_pivots=len(x['first_pivots']),minimum_first_growth=x['minimum_first_growth'],
        ordered_pairs=len(x['ordered_pairs']),minimum_pair_growth=x['minimum_pair_growth'],net_four_candidates=x['net_four_candidates'],
        net_four_interacting_candidates=x['net_four_interacting_candidates']) for x in cores]))


if __name__=='__main__':main(Path(sys.argv[1]))
