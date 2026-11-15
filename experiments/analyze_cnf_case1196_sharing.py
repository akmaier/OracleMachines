#!/usr/bin/env python3
"""Measure exact cross-original sharing in the entire checked positive proof.

Counts refer to one selected certificate, not acquisition time or all possible
equivalent representations. Owner bitsets follow its checked premise order.
"""
from collections import Counter
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_case1196_discovery import read_archive, sha, sha_key


def load(path):
    return json.loads(Path(path).read_text())


def analyze(out):
    started=time.perf_counter();report=load(out/'report.json');cold=load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256']==sha(out/'report.json')
    assert all(report['final_closed'])
    proof=read_archive(report['expanded_certificate']);steps=proof['steps'];roots=proof['roots']
    # Cold replay checks this exact ordered root list against the input cases.
    assert len(roots)==len(set(roots))==len(report['cases'])==83
    owners={};by_source={};edges=0
    for step in steps:
        key=step['source'];assert key not in by_source
        assert all(child in by_source for child in step['children'])
        by_source[key]=step;owners[key]=0;edges+=len(step['children'])
    for i,root in enumerate(roots):owners[root]|=1<<i
    for step in reversed(steps):
        mask=owners[step['source']]
        for child in step['children']:owners[child]|=mask
    # Independently compare every bitset with ordinary root-by-root reachability.
    direct={key:0 for key in by_source};visits=[]
    for i,root in enumerate(roots):
        seen=set();stack=[root]
        while stack:
            key=stack.pop()
            if key in seen:continue
            seen.add(key);stack.extend(by_source[key]['children'])
        for key in seen:direct[key]|=1<<i
        visits.append(dict(original_case=report['cases'][i]['original_case'],proof_steps=len(seen)))
    assert owners==direct
    shared=[]
    for key,mask in owners.items():
        if mask.bit_count()<2:continue
        step=by_source[key];cnf=json.loads(key)[-1]
        assert isinstance(cnf,list) and all(isinstance(c,list) and all(type(x) is int for x in c) for c in cnf)
        shared.append(dict(source_sha256=sha_key(key),shape=[len({abs(x) for c in cnf for x in c}),len(cnf),sum(map(len,cnf))],
            certificate_rule=step['rule']['kind'],premises=len(step['children']),owners=mask.bit_count(),
            original_cases=[c['original_case'] for i,c in enumerate(report['cases']) if mask&(1<<i)],
            children_sha256=[sha_key(child) for child in step['children']]))
    shared.sort(key=lambda n:(-n['owners'],n['source_sha256']))
    reachable=sum(bool(mask) for mask in owners.values());separate=sum(mask.bit_count() for mask in owners.values())
    assert separate==sum(row['proof_steps'] for row in visits)
    result=dict(passed=True,report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        source_sha256=sha(__file__),roots=len(roots),certificate_steps=len(steps),certificate_edges=edges,
        reachable_unique_steps=reachable,unreachable_steps=len(steps)-reachable,separate_root_step_visits=separate,
        repeated_step_visits=separate-reachable,shared_steps=len(shared),
        shared_rules=dict(Counter(n['certificate_rule'] for n in shared)),
        shared_nonterminal_steps=sum(n['premises']>0 for n in shared),
        shared_steps_with_variables=sum(n['shape'][0]>0 for n in shared),shared=shared,per_original=visits,
        diagnostic_seconds=time.perf_counter()-started,
        limitations=['One final selected original-coverage certificate; alternative plans, acquisition traces and reference-SAT proof nodes are outside this count.',
            'Repeated step visits measure graph overlap, not avoided fresh-solving work, elapsed-time savings or net compressed bytes.',
            'Nested shared nodes must not be counted as independent additive component savings.',
            'Exact identity sharing does not exhaust variable-renamed or semantically equivalent components.'])
    (out/'sharing-findings.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['shared','per_original','limitations']}))
    print(json.dumps([dict(shape=n['shape'],rule=n['certificate_rule'],premises=n['premises'],owners=n['owners']) for n in shared]))


if __name__=='__main__':analyze(Path(sys.argv[1]))
