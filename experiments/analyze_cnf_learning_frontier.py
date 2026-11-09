#!/usr/bin/env python3
"""Retain unused checked implication candidates on selected unresolved leaves."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected
from experiments.cnf_probe_learning import learning_batch


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    nodes = load_nodes(directory, next(a for a in report['archives'] if a['mode'] == 'compact'))
    hashes = {hashlib.sha256(k.encode()).hexdigest(): k for k in nodes}
    leaves = {}
    for row in report['records']:
        if row['mode'] != 'compact' or row['discovery']['summary']['closed']: continue
        for key in selected(nodes, hashes[row['discovery']['root_hash']]):
            if nodes[key]['kind'] == 'unresolved': leaves.setdefault(key, []).append(row['case'])
    records = []; counts = Counter(); start = time.perf_counter()
    for key, sources in sorted(leaves.items()):
        node = nodes[key]; p = node['profile']['probing']; local = Counter()
        candidates = learning_batch(node['cnf'], p['attempts'], 16, local)
        retained = p.get('batch', [])
        assert candidates[:len(retained)] == retained
        counts.update(local)
        records.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(), source_cases=sources,
            shape=node['profile']['shape'], status=p['status'], retained=retained,
            candidates_up_to_16=candidates, counters=dict(local),
            retained_assumptions=len({b['attempt'] for b in retained}),
            candidate_assumptions=len({b['attempt'] for b in candidates})))
    seconds = time.perf_counter()-start
    affected = sorted({i for r in records if len(r['candidates_up_to_16']) > len(r['retained']) for i in r['source_cases']})
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        candidate_generation_seconds=seconds, counters=dict(counts), selected_leaves=len(records),
        learning_clear=sum(r['status'] == 'learning_clear' for r in records),
        retained_at_cap=sum(len(r['retained']) == 4 for r in records),
        with_unused_candidates=sum(len(r['candidates_up_to_16']) > len(r['retained']) for r in records),
        additional_candidates=sum(len(r['candidates_up_to_16'])-len(r['retained']) for r in records),
        one_assumption_batches=sum(len(r['retained']) > 0 and r['retained_assumptions'] == 1 for r in records),
        at_diagnostic_cap=sum(len(r['candidates_up_to_16']) == 16 for r in records),
        affected_sources=affected, records=records,
        limitations=['Diagnostic keeps the current candidate order and graph filtering; not exhaustive alternative batches',
          'No additional propagation or alternative batch is executed; counts do not establish a coverage gain',
          'Candidate reasons live in the checked original-source archive; no enlarged production learning cap',
          'Generation time excludes archive loading and selected-path traversal, which are not claimed free'])


if __name__ == '__main__':
    directory = Path(sys.argv[1]); out = directory/'learning-frontier.json'
    if out.exists(): raise ValueError('Preserve earlier analysis')
    out.write_text(json.dumps(analyze(directory), indent=2)+'\n')
