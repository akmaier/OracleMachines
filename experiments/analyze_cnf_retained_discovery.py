#!/usr/bin/env python3
"""Account for certified reductions, exact identity reuse and repeated admissions.

Read-only analysis of the separately reconstructed checkpoint. Repeated shapes
or rule names describe a method pattern, not transport between CNF identities.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import sys
import tempfile


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_json(bound):
    assert sha(bound['path']) == bound['sha256']
    return load(bound['path'])


def run(out):
    r = load(out/'report.json'); cold = load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256'] == sha(out/'report.json')
    findings = load(out/'structural-findings.json')
    costs = load(out/'cost-summary.json')
    arms = [bound_json(a) for a in r['arms'] if a['repeat'] == 0]
    entries = Counter(k for a in arms for k in a['admitted_state_sha256'])
    completed = set(k for a in arms for k in a['completed_new_state_sha256'])
    assert sum(len(a['completed_new_state_sha256']) for a in arms) == len(completed)
    prefixes = [b for a in findings['arms'] if a['repeat'] == 0
                for s in a['splits'] for b in s['branches']]
    uses = Counter(n['key_sha256'] for b in prefixes for n in b['prefix']['nodes'])
    old_prefixes = load('experiments/results/cnf-case1227/structural-findings.json')['arms'][0]['splits']
    old_keys = {n['key_sha256'] for s in old_prefixes for b in s['branches'] for n in b['prefix']['nodes']}
    by_original = {}
    for arm in findings['arms']:
        if arm['repeat'] != 0: continue
        original=arm['focus_lineage']['original_case']
        group=by_original.setdefault(original,dict(batches=[],prefix_nodes=set(),new_prefix_nodes=set()))
        group['batches'].append(arm['batch'])
        for split in arm['splits']:
            for branch in split['branches']:
                for node in branch['prefix']['nodes']:
                    group['prefix_nodes'].add(node['key_sha256'])
                    if node['key_sha256'] in completed:group['new_prefix_nodes'].add(node['key_sha256'])
    cross_original = []
    for left in sorted(by_original):
        for right in sorted(by_original):
            if left>=right:continue
            shared=by_original[left]['prefix_nodes'] & by_original[right]['prefix_nodes']
            cross_original.append(dict(left=left,right=right,shared_prefix_nodes=sorted(shared),
                shared_new_prefix_nodes=sorted(shared & completed)))
    original_summaries=[dict(original_case=k,batches=v['batches'],distinct_prefix_nodes=len(v['prefix_nodes']),
        new_prefix_nodes=len(v['new_prefix_nodes'])) for k,v in sorted(by_original.items())]
    d = r['delta']; assert sha(d['path']) == d['sha256']
    with tempfile.TemporaryDirectory() as td:
        dbpath = Path(td)/'delta'
        dbpath.write_bytes(gzip.decompress(Path(d['path']).read_bytes()))
        assert sha(dbpath) == d['database_sha256']
        with sqlite3.connect(dbpath) as db:
            rows = list(db.execute('SELECT id,payload FROM cnf_patterns_v1'))
    assert {hashlib.sha256(k.encode()).hexdigest() for k, _ in rows} == completed
    kinds = Counter(json.loads(p)['kind'] for _, p in rows)
    assert dict(kinds) == r['new_node_kinds']
    nodes = [json.loads(p) for _, p in rows]
    families = [dict(key_sha256=hashlib.sha256(k.encode()).hexdigest(),
                    variables=len({abs(x) for c in n['cnf'] for x in c}), clauses=len(n['cnf']),
                    literals=sum(map(len,n['cnf'])), outcomes=n['profile']['outcomes'])
                for (k,p),n in zip(rows,nodes,strict=True) if n['kind']=='family']
    sequences = costs['sequences']
    means = dict(complete_sequence_seconds=statistics.mean(s['seconds'] for s in sequences),
        initial_handoff_seconds=statistics.mean(s['handoff_costs']['seconds'] for s in sequences),
        workers_seconds=statistics.mean(s['worker_seconds'] for s in sequences),
        local_expansion_seconds=statistics.mean(sum(a['expansion_seconds'] for a in costs['batches'] if a['repeat']==s['repeat']) for s in sequences),
        updated_global_query_seconds=statistics.mean(sum(q['query_seconds'] for q in s['global_queries']) for s in sequences),
        query_serialization_seconds=statistics.mean(sum(q['serialization_seconds'] for q in s['global_queries']) for s in sequences))
    summary=dict(report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        structural_findings_sha256=sha(out/'structural-findings.json'),cost_summary_sha256=sha(out/'cost-summary.json'),
        admitted_entries=sum(entries.values()),distinct_admitted=len(entries),repeated_entries=sum(entries.values())-len(entries),
        original_summaries=original_summaries,cross_original= cross_original,stored_patterns=len(completed),unstored_after_sequence=sorted(set(entries)-completed),new_node_kinds=dict(kinds),families=families,
        prefix_node_occurrences=sum(uses.values()),distinct_prefix_nodes=len(uses),
        repeated_prefix_occurrences=sum(uses.values())-len(uses),
        inherited_prefix_nodes=len(set(uses)-completed),new_prefix_nodes=len(set(uses)&completed),
        exact_prefix_nodes_shared_with_previous_case=sorted(set(uses)&old_keys),
        pattern_key_bytes=sum(len(k.encode()) for k,p in rows),pattern_payload_bytes=sum(len(p.encode()) for k,p in rows),
        stored_cnf_literal_slots=sum(sum(map(len,n['cnf'])) for n in nodes),
        timing_means=means,history_growth_bytes=r['expanded_database_bytes']-r['seed_database_bytes'],
        limitations=[
            'Prefix counts describe stored single-edge chains of touched split branches, not every route or alternative in the original proof.',
            'Repeated prefix visits include deliberate pending-split replay; a repeated visit is not a fresh stored record.',
            'Matching rule names and family outcomes are not equivalent CNFs. Exact key intersections identify already bound pattern records only.',
            'Source keys and node CNFs repeat serialized data, but these byte counts do not establish realizable net compression savings. SQLite pages, indexes, gzip and reconstruction are separate costs.',
            'Two repeated development runs establish logical reproducibility, not a baseline speedup or a bound on arbitrary SAT.'])
    (out/'discovery-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:summary[k] for k in ('admitted_entries','distinct_admitted','repeated_entries','stored_patterns','history_growth_bytes','timing_means')}))


if __name__=='__main__':
    run(Path(sys.argv[1]))
