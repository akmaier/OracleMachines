#!/usr/bin/env python3
"""Measure selected-proof overlap, separating duplicate inputs from reuse.

Owner sets are computed once per distinct canonical root, then checked by
independent DFS. These graph counts are not elapsed-time or acquisition savings.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def shape(key):
    cnf = json.loads(key)[-1]
    return [len({abs(x) for c in cnf for x in c}), len(cnf), sum(map(len, cnf))]


def proof_overlap(proof, case_indices, cases):
    roots = list(dict.fromkeys(proof['roots']))
    assert len(proof['roots']) == len(case_indices)
    root_cases = {root: [] for root in roots}
    for root, index in zip(proof['roots'], case_indices, strict=True):
        root_cases[root].append(index)
    steps = {s['source']: s for s in proof['steps']}
    assert len(steps) == len(proof['steps'])
    owners = {}
    for key, step in steps.items():
        assert all(child in owners for child in step['children'])
        owners[key] = 0
    for i, key in enumerate(roots):
        owners[key] |= 1 << i
    for key, step in reversed(list(steps.items())):
        for child in step['children']:
            owners[child] |= owners[key]
    direct = {key: 0 for key in steps}
    for i, root in enumerate(roots):
        seen = set(); todo = [root]
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key); todo.extend(steps[key]['children'])
        for key in seen:
            direct[key] |= 1 << i
    assert direct == owners and all(owners.values())
    shared = []
    for key, mask in owners.items():
        if mask.bit_count() < 2:
            continue
        shared.append(dict(source_sha256=hashlib.sha256(key.encode()).hexdigest(),
            shape=shape(key), rule=steps[key]['rule']['kind'],
            premises=len(steps[key]['children']), distinct_roots=mask.bit_count(),
            original_indices=sorted(index for i, root in enumerate(roots) if mask & (1 << i)
                                    for index in root_cases[root]),
            distinct_root_groups=dict(Counter(group for i, root in enumerate(roots)
                if mask & (1 << i) for group in {cases[index]['group'] for index in root_cases[root]}))))
    shared.sort(key=lambda n: (-n['shape'][0], -n['distinct_roots'], n['source_sha256']))
    return dict(input_roots=len(proof['roots']), distinct_roots=len(roots),
        duplicate_root_occurrences=len(proof['roots'])-len(roots), steps=len(steps),
        shared_steps=len(shared), shared_nonterminal_steps=sum(n['premises'] > 0 for n in shared),
        shared_rules=dict(Counter(n['rule'] for n in shared)),
        max_shared_variables=max((n['shape'][0] for n in shared), default=0),
        distinct_root_visits=sum(mask.bit_count() for mask in owners.values()), shared=shared)


def analyze(out):
    started = time.perf_counter(); r = json.loads((out/'report.json').read_text())
    assert all(s['covered'] == 1497 for s in r['samples']) and r['no_fresh_discovery']
    entry = r['parts']; assert sha(entry['path']) == entry['sha256']
    parts = json.loads(gzip.decompress(Path(entry['path']).read_bytes()))
    assert sha(r['claims']['path']) == r['claims']['sha256']
    claim = json.loads(Path(r['claims']['path']).read_text())
    assert sha(r['legacy']['path']) == r['legacy']['sha256']
    cases = json.loads(Path(r['legacy']['path']).read_text())['cases']
    assert claim['sources'] == [case['source'] for case in cases]
    results = {name: proof_overlap(part['proof'], claim['partition'][name], cases)
               for name, part in parts.items()}
    a, b = ({s['source']: s for s in parts[name]['proof']['steps']}
            for name in ('retained', 'expanded'))
    common = sorted(set(a) & set(b)); kinds = Counter(); same_rule = 0
    for key in common:
        kinds[a[key]['rule']['kind']] += 1
        same_rule += a[key] == b[key]
    result = dict(passed=True, source_sha256=sha(__file__), report_sha256=sha(out/'report.json'),
        parts=results, cross_policy=dict(exact_step_identities=len(common),
            identical_selected_steps=same_rule, retained_rules=dict(kinds),
            max_shared_variables=max((shape(k)[0] for k in common), default=0)),
        diagnostic_seconds=time.perf_counter()-started,
        limitations=[
            'Only selected positive proofs are measured; historical alternatives and SAT reference proofs are outside this graph.',
            'Repeated source formulas under canonical renaming are collapsed to one owner per policy before counting internal sharing.',
            'Distinct canonical roots can still be related by semantic equivalence or variable permutations beyond the implemented normalizer.',
            'Nested shared nodes do not represent independent additive runtime savings. Larger shared components need matched new-input acquisition tests.'])
    (out/'sharing-findings.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({**{k:v for k,v in result.items() if k not in ('parts','limitations')},
        'parts': {name: {k:v for k,v in part.items() if k != 'shared'} for name, part in results.items()}}))


if __name__ == '__main__':
    analyze(Path(sys.argv[1]))
